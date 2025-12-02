"""
Scanner Blueprint for CAsMan Web Application

Provides web interface for scanning, connecting, and disconnecting parts.
"""

import logging
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from flask import Blueprint, jsonify, render_template, request

from casman.assembly.connections import (
    record_assembly_connection,
    record_assembly_disconnection,
)
from casman.database.connection import get_database_path
from casman.database.antenna_positions import (
    assign_antenna_position,
    get_antenna_at_position,
    get_antenna_position,
)
from casman.antenna.grid import load_core_layout, parse_grid_code
from casman.parts.types import load_part_types

logger = logging.getLogger(__name__)

# Load part types
PART_TYPES = load_part_types()
ALL_PART_TYPES: List[str] = [name for _, (name, _) in sorted(PART_TYPES.items())]

# Create scanner blueprint
scanner_bp = Blueprint(
    "scanner",
    __name__,
    url_prefix="/scanner",
    template_folder=os.path.join(
        os.path.dirname(__file__), "..", "templates", "scanner"
    ),
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_part_details(part_number: str) -> Optional[Tuple[str, str]]:
    """Get part details from the database."""
    try:
        db_path = get_database_path("parts.db", None)
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT part_type, polarization FROM parts WHERE part_number = ?",
                (part_number,),
            )
            result = cursor.fetchone()
            if result:
                return result
    except sqlite3.Error as e:
        logger.error("Database error getting part details: %s", e)
    return None


def validate_snap_part(part_number: str) -> bool:
    """Validate SNAP part number format (SNAP<chassis><slot><port>)."""
    import re

    # Format: SNAP<chassis 1-4><slot A-K><port 00-11>
    pattern = r"^SNAP[1-4][A-K](0[0-9]|1[01])$"
    return bool(re.match(pattern, part_number))


def validate_connection_sequence(first_type: str, second_type: str) -> tuple[bool, str]:
    """Validate that connection follows the proper chain sequence."""
    # Build valid chain from config (sorted by key order)
    VALID_CHAIN = [name for _, (name, _) in sorted(PART_TYPES.items())]

    try:
        first_idx = VALID_CHAIN.index(first_type)
        second_idx = VALID_CHAIN.index(second_type)

        # Second part must be exactly the next in chain
        if second_idx != first_idx + 1:
            valid_next = (
                VALID_CHAIN[first_idx + 1]
                if first_idx < len(VALID_CHAIN) - 1
                else "none"
            )
            return (
                False,
                f"{first_type} can only connect to {valid_next}, not {second_type}",
            )

        return True, ""
    except ValueError:
        return False, f"Invalid part type in connection: {first_type} or {second_type}"


def format_snap_part(chassis: int, slot: str, port: int) -> str:
    """Format SNAP part number from chassis, slot, and port.

    Args:
        chassis: Chassis number (1-4)
        slot: SNAP slot letter (A-K)
        port: Port number (0-11)

    Returns:
        Formatted SNAP part number (e.g., SNAP1A00)
    """
    return f"SNAP{chassis}{slot}{str(port).zfill(2)}"


def get_existing_connections(part_number: str) -> List[Dict]:
    """Get all existing connections for a part where latest status is 'connected'."""
    try:
        db_path = get_database_path("assembled_casm.db", None)
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Normalize part pairs to handle bidirectional connections
            # (A,B) and (B,A) should be treated as the same connection
            cursor.execute(
                """
                WITH normalized_pairs AS (
                    SELECT 
                        CASE WHEN part_number < connected_to 
                            THEN part_number ELSE connected_to END as part1,
                        CASE WHEN part_number < connected_to 
                            THEN connected_to ELSE part_number END as part2,
                        part_number,
                        connected_to,
                        connected_to_type,
                        connection_status,
                        scan_time
                    FROM assembly
                    WHERE part_number = ? OR connected_to = ?
                ),
                latest_per_pair AS (
                    SELECT part1, part2, MAX(scan_time) as max_time
                    FROM normalized_pairs
                    GROUP BY part1, part2
                )
                SELECT np.part_number, np.connected_to, np.connected_to_type, np.scan_time
                FROM normalized_pairs np
                INNER JOIN latest_per_pair lpp
                    ON np.part1 = lpp.part1 
                    AND np.part2 = lpp.part2 
                    AND np.scan_time = lpp.max_time
                WHERE np.connection_status = 'connected'
                ORDER BY np.scan_time DESC
                """,
                (part_number, part_number),
            )
            rows = cursor.fetchall()
            return [
                {
                    "part_number": row[0],
                    "connected_to": row[1],
                    "connected_to_type": row[2],
                    "scan_time": row[3],
                }
                for row in rows
            ]
    except sqlite3.Error as e:
        logger.error("Database error getting connections: %s", e)
        return []


# ============================================================================
# ROUTES
# ============================================================================


@scanner_bp.route("/")
def scanner_index():
    """Render the scanner interface."""
    # Build connection chain (part type -> next part type)
    sorted_types = [name for _, (name, _) in sorted(PART_TYPES.items())]
    connection_chain = {
        sorted_types[i]: sorted_types[i + 1] for i in range(len(sorted_types) - 1)
    }

    # Build prefix mapping (part type -> abbreviation)
    part_prefixes = {name: abbrev for _, (name, abbrev) in PART_TYPES.items()}

    # Identify coax types (contain 'COAX' in name) and terminal type (last in chain)
    coax_types = [name for name in sorted_types if "COAX" in name.upper()]
    terminal_type = sorted_types[-1] if sorted_types else None

    return render_template(
        "scanner.html",
        part_types=ALL_PART_TYPES,
        connection_chain=connection_chain,
        part_prefixes=part_prefixes,
        coax_types=coax_types,
        terminal_type=terminal_type,
    )


@scanner_bp.route("/api/validate-part", methods=["POST"])
def validate_part():
    """Validate a scanned or entered part number and return existing connections."""
    data = request.json
    part_number = data.get("part_number", "").strip()

    if not part_number:
        return jsonify({"success": False, "error": "Part number is required"})

    # Get existing connections for this part
    existing = get_existing_connections(part_number)
    logger.info(
        "Validating part %s, found %d active connections", part_number, len(existing)
    )

    if part_number.startswith("SNAP"):
        if validate_snap_part(part_number):
            return jsonify(
                {
                    "success": True,
                    "part_type": "SNAP",
                    "polarization": "N/A",
                    "part_number": part_number,
                    "existing_connections": existing,
                }
            )
        else:
            return jsonify(
                {
                    "success": False,
                    "error": "Invalid SNAP format. Expected SNAP<chassis 1-4><slot A-K><port 00-11>",
                }
            )

    part_details = get_part_details(part_number)
    if part_details:
        part_type, polarization = part_details
        logger.info("Valid part: %s (%s, pol=%s)", part_number, part_type, polarization)
        return jsonify(
            {
                "success": True,
                "part_type": part_type,
                "polarization": polarization,
                "part_number": part_number,
                "existing_connections": existing,
            }
        )
    else:
        logger.warning("Part validation failed: %s not found in database", part_number)
        return jsonify(
            {"success": False, "error": f"Part {part_number} not found in database"}
        )


@scanner_bp.route("/api/get-connections", methods=["POST"])
def get_connections():
    """Get all active connections for a part."""
    data = request.json
    part_number = data.get("part_number", "").strip()

    if not part_number:
        return jsonify({"success": False, "error": "Part number is required"})

    connections = get_existing_connections(part_number)

    return jsonify(
        {"success": True, "connections": connections, "count": len(connections)}
    )


@scanner_bp.route("/api/check-snap-ports", methods=["POST"])
def check_snap_ports():
    """Check which SNAP ports are already connected for a given chassis and slot."""
    data = request.json
    chassis = data.get("chassis")
    slot = data.get("slot", "").strip().upper()

    if not chassis or not slot:
        return jsonify({"success": False, "error": "Chassis and slot are required"})

    # Check all 12 ports (0-11) for this chassis/slot combination
    occupied_ports = {}
    for port in range(12):
        snap_part = format_snap_part(chassis, slot, port)
        existing = get_existing_connections(snap_part)

        if existing:
            # Find what BACBOARD is connected
            connected_bacboard = None
            for conn in existing:
                if conn["part_number"] != snap_part:
                    connected_bacboard = conn["part_number"]
                    break
                elif conn["connected_to"] != snap_part:
                    connected_bacboard = conn["connected_to"]
                    break

            occupied_ports[port] = {
                "snap_part": snap_part,
                "connected_to": connected_bacboard or "unknown",
            }

    return jsonify({"success": True, "occupied_ports": occupied_ports})


@scanner_bp.route("/api/format-snap", methods=["POST"])
def format_snap_part_route():
    """Format SNAP part number from chassis, slot, and port."""
    data = request.json
    chassis = data.get("chassis")
    slot = data.get("slot", "").strip().upper()
    port = data.get("port")
    action = data.get("action", "connect")  # Default to connect mode

    if not chassis or not slot or port is None:
        return jsonify(
            {"success": False, "error": "Chassis, slot, and port are required"}
        )

    # Validate chassis (1-4)
    try:
        chassis = int(chassis)
        if chassis < 1 or chassis > 4:
            return jsonify(
                {"success": False, "error": "Chassis must be between 1 and 4"}
            )
    except ValueError:
        return jsonify({"success": False, "error": "Invalid chassis number"})

    # Validate slot (A-K)
    if slot not in ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K"]:
        return jsonify({"success": False, "error": "Slot must be A through K"})

    # Validate port (0-11)
    try:
        port = int(port)
        if port < 0 or port > 11:
            return jsonify({"success": False, "error": "Port must be between 0 and 11"})
    except ValueError:
        return jsonify({"success": False, "error": "Invalid port number"})

    # Format SNAP part number
    snap_part = format_snap_part(chassis, slot, port)

    # Check if this SNAP port already has a connection
    # In disconnect mode, we want to show what's connected (not an error)
    # In connect mode, we want to prevent duplicate connections
    existing = get_existing_connections(snap_part)
    if existing:
        # Find the BACBOARD connected to this SNAP port
        connected_bacboard = None
        for conn in existing:
            if conn["part_number"] != snap_part:
                connected_bacboard = conn["part_number"]
            elif conn["connected_to"] != snap_part:
                connected_bacboard = conn["connected_to"]

        # In connect mode, existing connection is an error
        # In disconnect mode, existing connection is expected
        if action == "connect":
            return jsonify(
                {
                    "success": False,
                    "error": f"Port already connected to {connected_bacboard if connected_bacboard else 'another part'}",
                    "snap_part": snap_part,
                    "connected_to": connected_bacboard,
                }
            )
        # In disconnect mode, return success with connection info
        else:
            return jsonify(
                {
                    "success": True,
                    "snap_part": snap_part,
                    "part_type": "SNAP",
                    "polarization": "N/A",
                    "connected_to": connected_bacboard,
                }
            )

    return jsonify(
        {
            "success": True,
            "snap_part": snap_part,
            "part_type": "SNAP",
            "polarization": "N/A",
        }
    )


@scanner_bp.route("/api/record-connection", methods=["POST"])
def record_connection():
    """Record a new connection between two parts, preventing duplicates."""
    data = request.json

    try:
        part_number = data["part_number"]
        part_type = data["part_type"]
        polarization = data["polarization"]
        connected_to = data["connected_to"]
        connected_to_type = data["connected_to_type"]
        connected_polarization = data["connected_polarization"]

        # Validate polarization match (SNAP excluded as it's N/A)
        if part_type != "SNAP" and connected_to_type != "SNAP":
            if polarization != connected_polarization:
                return jsonify(
                    {
                        "success": False,
                        "error": f"Polarization mismatch: {part_type} is P{polarization} but {connected_to_type} is P{connected_polarization}. Parts must have matching polarization.",
                    }
                )

        # Validate connection sequence (e.g., BACBOARD must connect to SNAP)
        is_valid_seq, seq_error = validate_connection_sequence(
            part_type, connected_to_type
        )
        if not is_valid_seq:
            return jsonify({"success": False, "error": seq_error})

        # Check if this exact connection already exists
        existing = get_existing_connections(part_number)
        for conn in existing:
            # Check if part_number is already connected to this specific part
            if (
                conn["part_number"] == part_number
                and conn["connected_to"] == connected_to
            ):
                return jsonify(
                    {
                        "success": False,
                        "error": f"{part_number} is already connected to {connected_to}",
                    }
                )
            # Check if the connected_to part is already connected to part_number (reverse)
            if (
                conn["part_number"] == connected_to
                and conn["connected_to"] == part_number
            ):
                return jsonify(
                    {
                        "success": False,
                        "error": f"{connected_to} is already connected to {part_number}",
                    }
                )

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        success = record_assembly_connection(
            part_number=data["part_number"],
            part_type=data["part_type"],
            polarization=data["polarization"],
            scan_time=current_time,
            connected_to=data["connected_to"],
            connected_to_type=data["connected_to_type"],
            connected_polarization=data["connected_polarization"],
            connected_scan_time=current_time,
        )

        if success:
            logger.info(
                "Connection recorded: %s → %s",
                data["part_number"],
                data["connected_to"],
            )
            return jsonify(
                {
                    "success": True,
                    "message": f"Successfully connected {data['part_number']} → {data['connected_to']}",
                }
            )
        else:
            logger.error(
                "Failed to record connection: %s → %s",
                data["part_number"],
                data["connected_to"],
            )
            return jsonify({"success": False, "error": "Failed to record connection"})

    except Exception as e:
        logger.error("Error recording connection: %s", e)
        return jsonify({"success": False, "error": str(e)})


@scanner_bp.route("/api/record-disconnection", methods=["POST"])
def record_disconnection():
    """Record a disconnection between two parts."""
    data = request.json

    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        success = record_assembly_disconnection(
            part_number=data["part_number"],
            part_type=data["part_type"],
            polarization=data["polarization"],
            scan_time=current_time,
            connected_to=data["connected_to"],
            connected_to_type=data["connected_to_type"],
            connected_polarization=data["connected_polarization"],
            connected_scan_time=current_time,
        )

        if success:
            logger.info(
                "Disconnection recorded: %s -X-> %s",
                data["part_number"],
                data["connected_to"],
            )
            return jsonify(
                {
                    "success": True,
                    "message": f"Successfully disconnected {data['part_number']} -X-> {data['connected_to']}",
                }
            )
        else:
            logger.error(
                "Failed to record disconnection: %s -X-> %s",
                data["part_number"],
                data["connected_to"],
            )
            return jsonify(
                {"success": False, "error": "Failed to record disconnection"}
            )

    except Exception as e:
        logger.error("Error recording disconnection: %s", e)
        return jsonify({"success": False, "error": str(e)})


@scanner_bp.route("/api/add-parts", methods=["POST"])
def add_parts():
    """Add new part numbers for a given part type."""
    data = request.json
    part_type = data.get("part_type", "").strip()
    count = data.get("count")
    polarization = data.get("polarization", "").strip()

    if not part_type:
        return jsonify({"success": False, "error": "Part type is required"})

    if not count or count <= 0:
        return jsonify({"success": False, "error": "Count must be greater than 0"})

    if polarization not in ["1", "2"]:
        return jsonify({"success": False, "error": "Polarization must be 1 or 2"})

    try:
        from casman.parts.generation import generate_part_numbers

        new_parts = generate_part_numbers(part_type, count, polarization)

        logger.info(
            "Created %d new %s parts with polarization %s",
            len(new_parts),
            part_type,
            polarization,
        )

        return jsonify(
            {
                "success": True,
                "parts": new_parts,
                "count": len(new_parts),
                "part_type": part_type,
                "polarization": polarization,
            }
        )

    except Exception as e:
        logger.error("Error creating parts: %s", e)
        return jsonify({"success": False, "error": str(e)})


@scanner_bp.route("/api/part-history", methods=["POST"])
def get_part_history():
    """Get complete connection/disconnection history for a part."""
    data = request.json
    part_number = data.get("part_number", "").strip()

    if not part_number:
        return jsonify({"success": False, "error": "Part number is required"})

    try:
        db_path = get_database_path("assembled_casm.db", None)
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Get all records where this part appears, deduplicated by normalized pairs
            # This prevents showing duplicate entries for bidirectional connections
            cursor.execute(
                """
                WITH normalized AS (
                    SELECT 
                        id,
                        part_number,
                        part_type,
                        connected_to,
                        connected_to_type,
                        connection_status,
                        scan_time,
                        CASE WHEN part_number < connected_to 
                            THEN part_number ELSE connected_to END as part1,
                        CASE WHEN part_number < connected_to 
                            THEN connected_to ELSE part_number END as part2
                    FROM assembly
                    WHERE part_number = ? OR connected_to = ?
                ),
                ranked AS (
                    SELECT *,
                        ROW_NUMBER() OVER (PARTITION BY part1, part2, scan_time, connection_status ORDER BY id) as rn
                    FROM normalized
                )
                SELECT 
                    id,
                    part_number,
                    part_type,
                    connected_to,
                    connected_to_type,
                    connection_status,
                    scan_time
                FROM ranked
                WHERE rn = 1
                ORDER BY scan_time DESC
                """,
                (part_number, part_number),
            )

            rows = cursor.fetchall()

            history = []
            for row in rows:
                history.append(
                    {
                        "id": row[0],
                        "part_number": row[1],
                        "part_type": row[2],
                        "connected_to": row[3],
                        "connected_to_type": row[4],
                        "status": row[5],
                        "timestamp": row[6],
                    }
                )

            logger.info(
                "Retrieved %d history records for part %s", len(history), part_number
            )
            return jsonify(
                {"success": True, "part_number": part_number, "history": history}
            )

    except sqlite3.Error as e:
        logger.error("Database error getting part history for %s: %s", part_number, e)
        return jsonify({"success": False, "error": str(e)})


# ============================================================================
# ANTENNA GRID POSITION ASSIGNMENT
# ============================================================================


@scanner_bp.route("/api/grid-config", methods=["GET"])
def get_grid_config():
    """Get grid configuration for UI."""
    try:
        array_id, north_rows, south_rows, east_columns, allow_expansion = (
            load_core_layout()
        )
        return jsonify(
            {
                "success": True,
                "array_id": array_id,
                "north_rows": north_rows,
                "south_rows": south_rows,
                "east_columns": east_columns,
                "allow_expansion": allow_expansion,
            }
        )
    except Exception as e:
        logger.error("Error loading grid config: %s", e)
        return jsonify({"success": False, "error": str(e)})


@scanner_bp.route("/api/check-position", methods=["POST"])
def check_position_status():
    """Check if a grid position is occupied."""
    try:
        data = request.get_json()
        grid_code = data.get("grid_code", "").strip().upper()

        if not grid_code:
            return jsonify({"success": False, "error": "Grid code required"})

        # Validate grid code
        try:
            parse_grid_code(grid_code)
        except ValueError as e:
            return jsonify({"success": False, "error": f"Invalid grid code: {e}"})

        # Check if position occupied
        antenna_info = get_antenna_at_position(grid_code)

        if antenna_info:
            return jsonify(
                {
                    "success": True,
                    "occupied": True,
                    "antenna": antenna_info["antenna_number"],
                    "grid_code": grid_code,
                }
            )
        else:
            return jsonify({"success": True, "occupied": False, "grid_code": grid_code})

    except Exception as e:
        logger.error("Error checking position status: %s", e)
        return jsonify({"success": False, "error": str(e)})


@scanner_bp.route("/api/assign-position", methods=["POST"])
def api_assign_position():
    """Assign an antenna to a grid position."""
    try:
        data = request.get_json()
        antenna_number = data.get("antenna_number", "").strip().upper()
        grid_code = data.get("grid_code", "").strip().upper()
        notes = data.get("notes", "").strip() or None
        allow_overwrite = data.get("allow_overwrite", False)

        if not antenna_number:
            return jsonify({"success": False, "error": "Antenna number required"})
        if not grid_code:
            return jsonify({"success": False, "error": "Grid code required"})

        # Validate antenna exists in parts database
        part_details = get_part_details(antenna_number)
        if not part_details:
            # Try without polarization
            from casman.database.antenna_positions import strip_polarization

            antenna_base = strip_polarization(antenna_number)
            part_details = get_part_details(f"{antenna_base}P1")
            if not part_details:
                return jsonify(
                    {
                        "success": False,
                        "error": f"Antenna {antenna_number} not found in database",
                    }
                )

        # Assign position
        result = assign_antenna_position(
            antenna_number, grid_code, notes=notes, allow_overwrite=allow_overwrite
        )

        logger.info("Assigned %s to %s", result["antenna"], result["grid_code"])
        return jsonify(result)

    except ValueError as e:
        logger.warning("Position assignment validation error: %s", e)
        return jsonify({"success": False, "error": str(e)})
    except Exception as e:
        logger.error("Error assigning position: %s", e)
        return jsonify({"success": False, "error": str(e)})


@scanner_bp.route("/api/get-antenna-position", methods=["POST"])
def api_get_antenna_position():
    """Get grid position for an antenna."""
    try:
        data = request.get_json()
        antenna_number = data.get("antenna_number", "").strip().upper()

        if not antenna_number:
            return jsonify({"success": False, "error": "Antenna number required"})

        position_info = get_antenna_position(antenna_number)

        if position_info:
            return jsonify({"success": True, "found": True, **position_info})
        else:
            return jsonify(
                {
                    "success": True,
                    "found": False,
                    "message": f"{antenna_number} not assigned to any position",
                }
            )

    except Exception as e:
        logger.error("Error getting antenna position: %s", e)
        return jsonify({"success": False, "error": str(e)})
