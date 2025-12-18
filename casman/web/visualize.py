"""
Visualization Blueprint for CAsMan Web Application

Provides web interface for viewing assembly chain connections.
"""

import logging
import os
import sqlite3
from typing import Dict, List, Optional, Tuple

from flask import Blueprint, jsonify, render_template_string, request, send_from_directory

from casman.config import get_config

logger = logging.getLogger(__name__)

# Create visualization blueprint
visualize_bp = Blueprint(
    "visualize",
    __name__,
    url_prefix="/visualize",
    template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
    static_folder=os.path.join(
        os.path.dirname(__file__), "..", "..", "scripts", "static"
    ),
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def load_viz_template() -> str:
    """Load the visualization HTML template from file."""
    template_path = os.path.join(
        os.path.dirname(__file__), "..", "templates", "analog_chains.html"
    )
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def get_all_parts() -> List[str]:
    """Fetch all unique part numbers from the assembled_casm.db database."""
    db_path = get_config("CASMAN_ASSEMBLED_DB", "database/assembled_casm.db")
    if db_path is None:
        raise ValueError("Database path for assembled_casm.db is not set.")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        "SELECT DISTINCT part_number FROM assembly UNION "
        "SELECT DISTINCT connected_to FROM assembly"
    )
    parts = [row[0] for row in c.fetchall()]
    conn.close()
    return parts


def get_all_chains(
    selected_part: Optional[str] = None,
) -> Tuple[
    List[List[str]], Dict[str, Tuple[Optional[str], Optional[str], Optional[str]]]
]:
    """Fetch all connection chains from the assembled_casm.db database."""
    db_path = get_config("CASMAN_ASSEMBLED_DB", "database/assembled_casm.db")
    if db_path is None:
        raise ValueError("Database path for assembled_casm.db is not set.")

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Get latest status for each part pair (checking both directions)
    # Only include if most recent status is 'connected'
    c.execute(
        """WITH latest_connections AS (
               SELECT 
                   CASE 
                       WHEN part_number < connected_to THEN part_number
                       ELSE connected_to
                   END as part_a,
                   CASE 
                       WHEN part_number < connected_to THEN connected_to
                       ELSE part_number
                   END as part_b,
                   MAX(scan_time) as latest_time
               FROM assembly
               WHERE part_number IS NOT NULL AND connected_to IS NOT NULL
               GROUP BY part_a, part_b
           ),
           pair_status AS (
               SELECT 
                   a.part_number,
                   a.connected_to,
                   a.scan_time,
                   a.connected_scan_time,
                   a.connection_status
               FROM assembly a
               INNER JOIN latest_connections lc
               ON (
                   (a.part_number = lc.part_a AND a.connected_to = lc.part_b) OR
                   (a.part_number = lc.part_b AND a.connected_to = lc.part_a)
               )
               AND a.scan_time = lc.latest_time
           )
           SELECT DISTINCT 
               ps.part_number, 
               ps.connected_to, 
               ps.scan_time, 
               ps.connected_scan_time
           FROM pair_status ps
           WHERE ps.connection_status = 'connected'
           ORDER BY ps.scan_time DESC"""
    )

    rows = c.fetchall()
    conn.close()

    if not rows:
        return [], {}

    connections: Dict[str, Tuple[Optional[str], Optional[str], Optional[str]]] = {}
    graph: Dict[str, List[str]] = {}
    reverse_graph: Dict[str, str] = {}

    for row in rows:
        part_number, connected_to, scan_time, connected_scan_time = row
        connections[part_number] = (connected_to, scan_time, connected_scan_time)

        if part_number not in graph:
            graph[part_number] = []
        graph[part_number].append(connected_to)
        reverse_graph[connected_to] = part_number

    start_parts = [p for p in graph.keys() if p not in reverse_graph]

    chains = []
    for start in start_parts:
        chain = [start]
        current = start
        while current in connections:
            next_part = connections[current][0]
            if next_part:
                chain.append(next_part)
                current = next_part
            else:
                break
        chains.append(chain)

    if selected_part:
        chains = [chain for chain in chains if selected_part in chain]

    return chains, connections


def get_duplicate_info() -> Dict[str, List[str]]:
    """Get information about duplicate connections."""
    db_path = get_config("CASMAN_ASSEMBLED_DB", "database/assembled_casm.db")
    if db_path is None:
        raise ValueError("Database path for assembled_casm.db is not set.")

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Get latest status for each part pair (checking both directions)
    c.execute(
        """WITH latest_connections AS (
               SELECT 
                   CASE 
                       WHEN part_number < connected_to THEN part_number
                       ELSE connected_to
                   END as part_a,
                   CASE 
                       WHEN part_number < connected_to THEN connected_to
                       ELSE part_number
                   END as part_b,
                   MAX(scan_time) as latest_time
               FROM assembly
               WHERE part_number IS NOT NULL AND connected_to IS NOT NULL
               GROUP BY part_a, part_b
           ),
           pair_status AS (
               SELECT 
                   a.part_number,
                   a.connected_to,
                   a.connection_status
               FROM assembly a
               INNER JOIN latest_connections lc
               ON (
                   (a.part_number = lc.part_a AND a.connected_to = lc.part_b) OR
                   (a.part_number = lc.part_b AND a.connected_to = lc.part_a)
               )
               AND a.scan_time = lc.latest_time
           )
           SELECT ps.connected_to, GROUP_CONCAT(ps.part_number, ', ') as sources
           FROM pair_status ps
           WHERE ps.connection_status = 'connected'
           GROUP BY ps.connected_to
           HAVING COUNT(*) > 1"""
    )

    duplicates = {}
    for row in c.fetchall():
        duplicates[row[0]] = row[1].split(", ")

    conn.close()
    return duplicates


def get_last_update() -> Optional[str]:
    """Get the latest timestamp from the database."""
    db_path = get_config("CASMAN_ASSEMBLED_DB", "database/assembled_casm.db")
    if db_path is None:
        raise ValueError("Database path for assembled_casm.db is not set.")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        "SELECT MAX(latest_time) FROM ("
        "SELECT scan_time AS latest_time FROM assembly "
        "UNION ALL "
        "SELECT connected_scan_time AS latest_time FROM assembly)"
    )
    last_update = c.fetchone()[0]
    conn.close()
    return str(last_update) if last_update is not None else None


def format_display_data(
    part: str,
    connections: Dict[str, Tuple[Optional[str], Optional[str], Optional[str]]],
    duplicates: Dict[str, List[str]],
    snap_board_info: Optional[Dict[Tuple[int, str], Dict[str, str]]] = None,
) -> str:
    """Format part display data for visualization."""
    part_class = "national-park-bold"
    part_style = ""

    if part in duplicates:
        part_style = "color: red;"

    frm_time: Optional[str] = None
    now_time: Optional[str] = None
    nxt_time: Optional[str] = None

    for src, (dest, _, _) in connections.items():
        if dest == part:
            frm_row = connections.get(src)
            if frm_row:
                frm_time = frm_row[2]
            break

    part_row: Optional[Tuple[Optional[str], Optional[str], Optional[str]]] = (
        connections.get(part)
    )
    if part_row is not None:
        now_time = part_row[1]
        nxt_time = part_row[2]

    ts_placeholder = "&nbsp;" * 19

    def ts(val: Optional[str]) -> str:
        return val if val else ts_placeholder

    display_lines: List[str] = [
        f"<span class='{part_class}' style='{part_style}'>{part}</span>",
        "<br>",
        f"<span class='monospace'>FRM: {ts(frm_time)}</span>",
        f"<span class='monospace'>NOW: {ts(now_time)}</span>",
        f"<span class='monospace'>NXT: {ts(nxt_time)}</span>",
    ]
    
    # Add SNAP board info if this is a SNAP part
    if part.startswith('SNAP') and snap_board_info:
        try:
            snap_str = part[4:]  # Remove 'SNAP' prefix
            chassis = int(snap_str[0])
            slot = snap_str[1]
            port = int(snap_str[2:])
            board_info = snap_board_info.get((chassis, slot), {})
            
            if board_info:
                feng_id = board_info.get('feng_id', 0)
                packet_index = feng_id * 12 + port
                display_lines.append("<br>")
                display_lines.append(f"<span class='monospace' style='font-size: 0.85em;'>SN: {board_info.get('serial_number', 'N/A')}</span>")
                display_lines.append(f"<span class='monospace' style='font-size: 0.85em;'>FENG: {feng_id} | PKT: {packet_index}</span>")
                display_lines.append(f"<span class='monospace' style='font-size: 0.85em;'>MAC: {board_info.get('mac_address', 'N/A')}</span>")
                display_lines.append(f"<span class='monospace' style='font-size: 0.85em;'>IP: {board_info.get('ip_address', 'N/A')}</span>")
        except (IndexError, ValueError):
            pass  # Malformed SNAP part number
    
    return "<br>".join(display_lines)


# ============================================================================
# ROUTES
# ============================================================================


@visualize_bp.route("/static/<path:filename>")
def visualize_static(filename):
    """Serve static files for visualization (fonts, etc.)."""
    static_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "scripts", "static"
    )
    return send_from_directory(static_dir, filename)


@visualize_bp.route("/", methods=["GET", "POST"])
@visualize_bp.route("/chains", methods=["GET", "POST"])
def visualize_index():
    """Render the visualization interface."""
    # Get selected part from form, search input, or query string
    selected_part = None
    if request.method == "POST":
        # Check search input first, then dropdown
        selected_part = request.form.get("search_part") or request.form.get("part")
    else:
        selected_part = request.args.get("part")

    # Load part types for the part builder
    from casman.parts.types import load_part_types
    from casman.database.snap_boards import get_all_snap_boards

    part_types = load_part_types()
    # Exclude terminal type (highest key)
    terminal_key = max(part_types.keys())
    part_types_for_builder = {k: v for k, v in part_types.items() if k != terminal_key}

    parts = get_all_parts()
    chains, connections = get_all_chains(selected_part)
    duplicates = get_duplicate_info()
    last_update = get_last_update()
    
    # Get SNAP board info
    snap_boards_list = get_all_snap_boards()
    snap_board_info = {}
    for board in snap_boards_list:
        key = (board['chassis'], board['slot'])
        snap_board_info[key] = {
            'serial_number': board['serial_number'],
            'mac_address': board['mac_address'],
            'ip_address': board['ip_address'],
            'feng_id': board['feng_id']
        }

    template = load_viz_template()
    return render_template_string(
        template,
        parts=parts,
        chains=chains,
        connections=connections,
        duplicates=duplicates,
        selected_part=selected_part,
        last_update=last_update,
        format_display_data=format_display_data,
        snap_board_info=snap_board_info,
        part_types=part_types_for_builder,
    )


@visualize_bp.route("/grid")
def antenna_grid():
    """Display antenna grid position visualization."""
    from casman.antenna.grid import load_core_layout, format_grid_code
    from casman.database.antenna_positions import get_all_antenna_positions
    from casman.antenna.chain import get_snap_ports_for_antenna, format_snap_port
    from casman.antenna.kernel_index import grid_to_kernel_index

    # Load grid configuration
    array_id, north_rows, south_rows, east_columns, allow_expansion = load_core_layout()

    # Get all antenna positions
    positions = get_all_antenna_positions(array_id=array_id)

    # Build grid data structure (43 rows × 6 columns)
    # Row order: N21, N20, ..., N01, C00, S01, ..., S20, S21
    grid_data = []

    # North rows (reversed so N21 is at top)
    for row_offset in range(north_rows, 0, -1):
        row = {"label": f"N{row_offset:03d}", "cells": []}
        for col in range(1, east_columns + 1):  # 1-based column indexing
            grid_code = format_grid_code(array_id, 'N', row_offset, col)
            kernel_idx = grid_to_kernel_index(grid_code)
            cell = {"row_offset": row_offset, "east_col": col, "antenna": None, 
                    "grid_code": grid_code, "kernel_index": kernel_idx}
            # Find antenna at this position
            for pos in positions:
                if pos["row_offset"] == row_offset and pos["east_col"] == col:
                    cell["antenna"] = pos["antenna_number"]
                    break
            row["cells"].append(cell)
        grid_data.append(row)

    # Center row
    row = {"label": "C000", "cells": []}
    for col in range(1, east_columns + 1):  # 1-based column indexing
        grid_code = format_grid_code(array_id, 'C', 0, col)
        kernel_idx = grid_to_kernel_index(grid_code)
        cell = {"row_offset": 0, "east_col": col, "antenna": None,
                "grid_code": grid_code, "kernel_index": kernel_idx}
        for pos in positions:
            if pos["row_offset"] == 0 and pos["east_col"] == col:
                cell["antenna"] = pos["antenna_number"]
                break
        row["cells"].append(cell)
    grid_data.append(row)

    # South rows
    for row_offset in range(-1, -(south_rows + 1), -1):
        row = {"label": f"S{abs(row_offset):03d}", "cells": []}
        for col in range(1, east_columns + 1):  # 1-based column indexing
            grid_code = format_grid_code(array_id, 'S', abs(row_offset), col)
            kernel_idx = grid_to_kernel_index(grid_code)
            cell = {"row_offset": row_offset, "east_col": col, "antenna": None,
                    "grid_code": grid_code, "kernel_index": kernel_idx}
            for pos in positions:
                if pos["row_offset"] == row_offset and pos["east_col"] == col:
                    cell["antenna"] = pos["antenna_number"]
                    break
            row["cells"].append(cell)
        grid_data.append(row)

    # Get search parameters
    search_antenna = request.args.get("antenna", "").strip()
    search_grid = request.args.get("grid", "").strip()
    search_kernel = request.args.get("kernel", "").strip()

    # Determine selected antenna and position
    selected_antenna = None
    selected_position = None
    snap_info = None

    if search_antenna:
        # Search by antenna number
        for pos in positions:
            if pos["antenna_number"] == search_antenna:
                selected_antenna = search_antenna
                selected_position = pos
                # Add kernel index to position info
                selected_position["kernel_index"] = grid_to_kernel_index(pos["grid_code"])
                # Get SNAP ports
                snap_info = get_snap_ports_for_antenna(search_antenna)
                break
    elif search_grid:
        # Search by grid code
        for pos in positions:
            if pos["grid_code"] == search_grid:
                selected_antenna = pos["antenna_number"]
                selected_position = pos
                # Add kernel index to position info
                selected_position["kernel_index"] = grid_to_kernel_index(pos["grid_code"])
                # Get SNAP ports
                snap_info = get_snap_ports_for_antenna(selected_antenna)
                break
    elif search_kernel:
        # Search by kernel index
        from casman.antenna.kernel_index import kernel_index_to_grid
        try:
            kernel_idx = int(search_kernel)
            target_grid_code = kernel_index_to_grid(kernel_idx)
            if target_grid_code:
                for pos in positions:
                    if pos["grid_code"] == target_grid_code:
                        selected_antenna = pos["antenna_number"]
                        selected_position = pos
                        # Add kernel index to position info
                        selected_position["kernel_index"] = kernel_idx
                        # Get SNAP ports
                        snap_info = get_snap_ports_for_antenna(selected_antenna)
                        break
        except ValueError:
            pass  # Invalid kernel index input

    # Load grid template
    template_path = os.path.join(
        os.path.dirname(__file__), "..", "templates", "visualize", "grid.html"
    )
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    return render_template_string(
        template,
        grid_data=grid_data,
        array_id=array_id,
        north_rows=north_rows,
        south_rows=south_rows,
        east_columns=east_columns,
        selected_antenna=selected_antenna,
        selected_position=selected_position,
        snap_info=snap_info,
        search_antenna=search_antenna,
        search_grid=search_grid,
        search_kernel=search_kernel,
        format_snap_port=format_snap_port,
    )


@visualize_bp.route("/snap-ports")
def snap_ports():
    """Display SNAP port visualization with 4x3 grids for each chassis/slot."""
    import sqlite3
    from collections import defaultdict
    from casman.config import get_config
    from casman.database.antenna_positions import get_all_antenna_positions
    from casman.database.snap_boards import get_all_snap_boards
    from casman.antenna.kernel_index import grid_to_kernel_index
    from casman.antenna.grid import load_core_layout
    
    # Get filter parameters
    selected_chassis = request.args.get('chassis', '')
    selected_slot = request.args.get('slot', '')
    
    # Get all connections from database
    db_path = get_config("CASMAN_ASSEMBLED_DB", "database/assembled_casm.db")
    if db_path is None:
        raise ValueError("Database path for assembled_casm.db is not set.")
    
    # Get antenna positions to lookup grid codes and kernel indices
    array_id, _, _, _, _ = load_core_layout()
    positions = get_all_antenna_positions(array_id=array_id)
    
    # Create lookup dict: antenna_number -> {grid_code, kernel_index}
    antenna_info = {}
    for pos in positions:
        antenna_info[pos['antenna_number']] = {
            'grid_code': pos['grid_code'],
            'kernel_index': grid_to_kernel_index(pos['grid_code'])
        }
    
    # Get SNAP board info
    snap_boards_list = get_all_snap_boards()
    snap_board_info = {}
    for board in snap_boards_list:
        key = (board['chassis'], board['slot'])
        snap_board_info[key] = {
            'serial_number': board['serial_number'],
            'mac_address': board['mac_address'],
            'ip_address': board['ip_address'],
            'feng_id': board['feng_id']
        }
    
    # Build SNAP port mapping
    # Structure: snap_ports[chassis][slot][port] = {'p1': {...}, 'p2': {...}}
    snap_ports = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    
    # SNAP configuration: 4 chassis, 11 slots (A-K), 12 ports (0-11)
    all_chassis_list = [1, 2, 3, 4]
    all_slot_list = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K']
    
    # Apply filters
    if selected_chassis:
        try:
            chassis_list = [int(selected_chassis)]
        except ValueError:
            chassis_list = all_chassis_list
    else:
        chassis_list = all_chassis_list
    
    if selected_slot:
        slot_list = [selected_slot.upper()] if selected_slot.upper() in all_slot_list else all_slot_list
    else:
        slot_list = all_slot_list
    
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all connections that end at SNAP boards
        # Use same logic as chains view - only show latest status for each pair
        cursor.execute("""
            WITH RECURSIVE
            latest_connections AS (
                SELECT 
                    CASE 
                        WHEN part_number < connected_to THEN part_number
                        ELSE connected_to
                    END as part_a,
                    CASE 
                        WHEN part_number < connected_to THEN connected_to
                        ELSE part_number
                    END as part_b,
                    MAX(scan_time) as latest_time
                FROM assembly
                WHERE part_number IS NOT NULL AND connected_to IS NOT NULL
                GROUP BY part_a, part_b
            ),
            pair_status AS (
                SELECT 
                    a.part_number,
                    a.connected_to,
                    a.connected_to_type,
                    a.connection_status
                FROM assembly a
                INNER JOIN latest_connections lc
                ON (
                    (a.part_number = lc.part_a AND a.connected_to = lc.part_b) OR
                    (a.part_number = lc.part_b AND a.connected_to = lc.part_a)
                )
                AND a.scan_time = lc.latest_time
            ),
            chain AS (
                SELECT 
                    part_number,
                    connected_to,
                    connected_to_type,
                    1 as depth,
                    part_number as start_part
                FROM pair_status
                WHERE connection_status = 'connected'
                
                UNION ALL
                
                SELECT 
                    ps.part_number,
                    ps.connected_to,
                    ps.connected_to_type,
                    c.depth + 1,
                    c.start_part
                FROM pair_status ps
                JOIN chain c ON ps.part_number = c.connected_to
                WHERE ps.connection_status = 'connected' AND c.depth < 10
            )
            SELECT DISTINCT start_part, connected_to as snap_part
            FROM chain
            WHERE connected_to_type = 'SNAP' OR connected_to LIKE 'SNAP%'
        """)
        
        for row in cursor.fetchall():
            start_part = row['start_part']
            snap_part = row['snap_part']
            
            # Parse SNAP part: SNAP[chassis][slot][port]
            # e.g. SNAP1A05 -> chassis=1, slot=A, port=5
            try:
                snap_str = snap_part[4:]  # Remove 'SNAP' prefix
                chassis = int(snap_str[0])
                slot = snap_str[1]
                port = int(snap_str[2:])
                
                # Determine polarization from start part
                if start_part.endswith('P1'):
                    pol = 'p1'
                    antenna = start_part[:-2]  # Remove P1 suffix
                elif start_part.endswith('P2'):
                    pol = 'p2'
                    antenna = start_part[:-2]  # Remove P2 suffix
                else:
                    continue  # Skip if not a polarized antenna
                
                # Get grid code and kernel index for this antenna
                info = antenna_info.get(antenna, {})
                snap_ports[chassis][slot][port][pol] = {
                    'antenna': antenna,
                    'grid_code': info.get('grid_code', ''),
                    'kernel_index': info.get('kernel_index', '')
                }
                
            except (IndexError, ValueError):
                # Malformed SNAP part number
                continue
    
    # Convert to regular dicts for template
    snap_ports_dict = {}
    for chassis in all_chassis_list:
        snap_ports_dict[chassis] = {}
        for slot in all_slot_list:
            snap_ports_dict[chassis][slot] = {}
            for port in range(12):  # 0-11
                snap_ports_dict[chassis][slot][port] = snap_ports[chassis][slot][port]
    
    # Load SNAP ports template
    template_path = os.path.join(
        os.path.dirname(__file__), "..", "templates", "visualize", "snap_ports.html"
    )
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
    
    return render_template_string(
        template,
        chassis_list=chassis_list,
        slot_list=slot_list,
        all_chassis_list=all_chassis_list,
        all_slot_list=all_slot_list,
        snap_ports=snap_ports_dict,
        snap_board_info=snap_board_info,
        selected_chassis=selected_chassis,
        selected_slot=selected_slot,
    )


# ============================================================================
# ADMIN ROUTES
# ============================================================================


@visualize_bp.route("/admin")
def admin():
    """Display admin panel."""
    template_path = os.path.join(
        os.path.dirname(__file__), "..", "templates", "admin.html"
    )
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
    return render_template_string(template)


@visualize_bp.route("/admin/load-grid-positions", methods=["POST"])
def load_grid_positions():
    """Load grid positions from CSV."""
    try:
        from casman.database.antenna_positions import load_grid_coordinates_from_csv
        
        result = load_grid_coordinates_from_csv()
        
        # Check for errors in result
        if result.get('errors'):
            error_msg = "; ".join(result['errors'])
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        message = f"✓ Updated: {result['updated']} position(s), "
        message += f"Skipped: {result['skipped']}"
        
        return jsonify({
            'success': True,
            'message': message,
            'stats': result
        })
    except Exception as e:
        logger.error(f"Error loading grid positions: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@visualize_bp.route("/admin/load-snap-boards", methods=["POST"])
def load_snap_boards():
    """Load SNAP boards from CSV."""
    try:
        from casman.database.snap_boards import load_snap_boards_from_csv
        
        result = load_snap_boards_from_csv()
        
        message = f"✓ Loaded: {result['loaded']} new board(s), "
        message += f"Updated: {result['updated']}, "
        message += f"Skipped: {result['skipped']}"
        
        if result['errors'] > 0:
            message += f", Errors: {result['errors']}"
        
        return jsonify({
            'success': True,
            'message': message,
            'stats': result
        })
    except Exception as e:
        logger.error(f"Error loading SNAP boards: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@visualize_bp.route("/admin/sync-to-github", methods=["POST"])
def sync_to_github():
    """Push databases to GitHub Releases (server-side)."""
    try:
        from pathlib import Path
        from casman.database.github_sync import get_github_sync_manager
        from casman.database.connection import get_database_path
        
        # Get sync manager
        sync_manager = get_github_sync_manager()
        if sync_manager is None:
            return jsonify({
                'success': False,
                'error': 'GitHub sync not configured. Set GITHUB_TOKEN environment variable.'
            }), 500
        
        if not sync_manager.github_token:
            return jsonify({
                'success': False,
                'error': 'GitHub token required for uploads. Set GITHUB_TOKEN environment variable.'
            }), 401
        
        # Get database paths
        parts_db_path = Path(get_database_path("parts.db"))
        assembled_db_path = Path(get_database_path("assembled_casm.db"))
        
        # Create GitHub Release with databases
        logger.info("Creating GitHub Release with database snapshots...")
        tag_name = sync_manager.create_release(
            db_paths=[parts_db_path, assembled_db_path],
            description="Manual sync from web admin panel"
        )
        
        if tag_name:
            message = f"✓ Successfully created release: {tag_name}"
            return jsonify({
                'success': True,
                'message': message,
                'release': tag_name
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create GitHub Release. Check logs for details.'
            }), 500
            
    except Exception as e:
        logger.error(f"Error syncing to GitHub: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@visualize_bp.route("/admin/sync-status", methods=["GET"])
def sync_status():
    """Get current sync status."""
    try:
        from casman.database.github_sync import get_github_sync_manager
        
        sync_manager = get_github_sync_manager()
        if sync_manager is None:
            return jsonify({
                'success': False,
                'error': 'GitHub sync not configured'
            }), 500
        
        # Get latest release info
        latest_release = sync_manager.get_latest_release()
        
        # Get last check time
        last_check = sync_manager.get_last_check_time()
        
        status = {
            'configured': True,
            'has_token': sync_manager.github_token is not None,
            'last_check': last_check.isoformat() if last_check else None,
        }
        
        if latest_release:
            status['latest_release'] = {
                'name': latest_release.release_name,
                'timestamp': latest_release.timestamp.isoformat(),
                'size_mb': round(latest_release.size_bytes / (1024 * 1024), 2),
                'assets': latest_release.assets,
            }
        else:
            status['latest_release'] = None
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
