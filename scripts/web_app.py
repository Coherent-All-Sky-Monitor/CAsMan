#!/usr/bin/env python3
"""
CAsMan Web Application

Unified Flask application serving scanner and visualization interfaces.
Can be run in development or production mode.
"""

from casman.parts.types import load_part_types
from casman.database.initialization import init_all_databases
from casman.database.connection import get_database_path
from casman.config.core import get_config
from casman.assembly.connections import (
    record_assembly_connection,
    record_assembly_disconnection,
)
import logging
import os
import sqlite3
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from flask import (
    Blueprint,
    Flask,
    jsonify,
    redirect,
    render_template,
    render_template_string,
    request,
    send_from_directory,
)

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from flask_cors import CORS

    HAS_CORS = True
except ImportError:
    HAS_CORS = False


logger = logging.getLogger(__name__)

# Configuration for which apps to serve
APP_CONFIG = {
    "enable_scanner": True,
    "enable_visualization": True,
}


def configure_apps(
    enable_scanner: bool = True, enable_visualization: bool = True
) -> None:
    """Configure which applications to enable."""
    APP_CONFIG["enable_scanner"] = enable_scanner
    APP_CONFIG["enable_visualization"] = enable_visualization


# ============================================================================
# SCANNER BLUEPRINT
# ============================================================================

scanner_bp = Blueprint(
    "scanner",
    __name__,
    url_prefix="/scanner",
    template_folder=os.path.join(
        os.path.dirname(__file__), "..", "casman", "templates", "scanner"
    ),
)

# Load part types
PART_TYPES = load_part_types()
ALL_PART_TYPES: List[str] = [name for _, (name, _) in sorted(PART_TYPES.items())]


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
    """Validate SNAP part number format (SNAP<crate><slot><port>)."""
    import re

    # Format: SNAP<crate 1-4><slot A-K><port 00-11>
    pattern = r"^SNAP[1-4][A-K](0[0-9]|1[01])$"
    return bool(re.match(pattern, part_number))


def validate_connection_sequence(first_type: str, second_type: str) -> tuple[bool, str]:
    """Validate that connection follows the proper chain sequence."""
    # Define the valid chain sequence
    VALID_CHAIN = ["ANTENNA", "LNA", "COAXSHORT", "COAXLONG", "BACBOARD", "SNAP"]

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


def format_snap_part(crate: int, slot: str, port: int) -> str:
    """Format SNAP part number from crate, slot, and port.

    Args:
        crate: Crate number (1-4)
        slot: SNAP slot letter (A-K)
        port: Port number (0-11)

    Returns:
        Formatted SNAP part number (e.g., SNAP1A00)
    """
    return f"SNAP{crate}{slot}{str(port).zfill(2)}"


def get_existing_connections(part_number: str) -> List[Dict]:
    """Get all existing connections for a part where latest status is 'connected'."""
    try:
        db_path = get_database_path("assembled_casm.db", None)
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT a.part_number, a.connected_to, a.connected_to_type, a.scan_time
                   FROM assembly a
                   INNER JOIN (
                       SELECT part_number, connected_to, MAX(scan_time) as max_time
                       FROM assembly
                       WHERE part_number = ? OR connected_to = ?
                       GROUP BY part_number, connected_to
                   ) latest
                   ON a.part_number = latest.part_number
                   AND a.connected_to = latest.connected_to
                   AND a.scan_time = latest.max_time
                   WHERE a.connection_status = 'connected'
                   AND (a.part_number = ? OR a.connected_to = ?)
                   ORDER BY a.scan_time DESC""",
                (part_number, part_number, part_number, part_number),
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


@scanner_bp.route("/")
def scanner_index():
    """Render the scanner interface."""
    return render_template("scanner.html", part_types=ALL_PART_TYPES)


@scanner_bp.route("/api/validate-part", methods=["POST"])
def validate_part():
    """Validate a scanned or entered part number and return existing connections."""
    data = request.json
    part_number = data.get("part_number", "").strip()

    if not part_number:
        return jsonify({"success": False, "error": "Part number is required"})

    # Get existing connections for this part
    existing = get_existing_connections(part_number)

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
                    "error": f"Invalid SNAP format. Expected SNAP<crate 1-4><slot A-K><port 00-11>",
                }
            )

    part_details = get_part_details(part_number)
    if part_details:
        part_type, polarization = part_details
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
    """Check which SNAP ports are already connected for a given crate and slot."""
    data = request.json
    crate = data.get("crate")
    slot = data.get("slot", "").strip().upper()

    if not crate or not slot:
        return jsonify({"success": False, "error": "Crate and slot are required"})

    # Check all 12 ports (0-11) for this crate/slot combination
    occupied_ports = {}
    for port in range(12):
        snap_part = format_snap_part(crate, slot, port)
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
def format_snap():
    """Format SNAP part number from crate, slot, and port."""
    data = request.json
    crate = data.get("crate")
    slot = data.get("slot", "").strip().upper()
    port = data.get("port")

    if not crate or not slot or port is None:
        return jsonify(
            {"success": False, "error": "Crate, slot, and port are required"}
        )

    # Validate crate (1-4)
    try:
        crate = int(crate)
        if crate < 1 or crate > 4:
            return jsonify({"success": False, "error": "Crate must be between 1 and 4"})
    except ValueError:
        return jsonify({"success": False, "error": "Invalid crate number"})

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
    snap_part = format_snap_part(crate, slot, port)

    # Check if this SNAP port already has a connection
    existing = get_existing_connections(snap_part)
    if existing:
        # Find the BACBOARD connected to this SNAP port
        connected_bacboard = None
        for conn in existing:
            if conn["part_number"] != snap_part:
                connected_bacboard = conn["part_number"]
            elif conn["connected_to"] != snap_part:
                connected_bacboard = conn["connected_to"]

        return jsonify(
            {
                "success": False,
                "error": f"Port already connected to {connected_bacboard if connected_bacboard else 'another part'}",
                "snap_part": snap_part,
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
        connected_to = data["connected_to"]
        connected_to_type = data["connected_to_type"]

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
            return jsonify(
                {
                    "success": True,
                    "message": f"Successfully connected {data['part_number']} → {data['connected_to']}",
                }
            )
        else:
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
            return jsonify(
                {
                    "success": True,
                    "message": f"Successfully disconnected {data['part_number']} -X-> {data['connected_to']}",
                }
            )
        else:
            return jsonify(
                {"success": False, "error": "Failed to record disconnection"}
            )

    except Exception as e:
        logger.error("Error recording disconnection: %s", e)
        return jsonify({"success": False, "error": str(e)})


# ============================================================================
# VISUALIZATION BLUEPRINT
# ============================================================================

visualize_bp = Blueprint(
    "visualize",
    __name__,
    url_prefix="/visualize",
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
)


def load_viz_template() -> str:
    """Load the visualization HTML template from file."""
    template_path = os.path.join(
        os.path.dirname(__file__), "templates", "analog_chains.html"
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

    c.execute(
        """SELECT a.part_number, a.connected_to, a.scan_time, a.connected_scan_time
           FROM assembly a
           INNER JOIN (
               SELECT part_number, connected_to, MAX(scan_time) as max_time
               FROM assembly
               GROUP BY part_number, connected_to
           ) latest
           ON a.part_number = latest.part_number
           AND a.connected_to = latest.connected_to
           AND a.scan_time = latest.max_time
           WHERE a.connection_status = 'connected'
           ORDER BY a.scan_time DESC"""
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

    c.execute(
        """SELECT a.connected_to, GROUP_CONCAT(a.part_number, ', ') as sources
           FROM assembly a
           INNER JOIN (
               SELECT part_number, connected_to, MAX(scan_time) as max_time
               FROM assembly
               GROUP BY part_number, connected_to
           ) latest
           ON a.part_number = latest.part_number
           AND a.connected_to = latest.connected_to
           AND a.scan_time = latest.max_time
           WHERE a.connection_status = 'connected'
           GROUP BY a.connected_to
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
    return "<br>".join(display_lines)


@visualize_bp.route("/static/<path:filename>")
def visualize_static(filename):
    """Serve static files for visualization (fonts, etc.)."""
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    return send_from_directory(static_dir, filename)


@visualize_bp.route("/", methods=["GET", "POST"])
@visualize_bp.route("/chains", methods=["GET", "POST"])
def visualize_index():
    """Render the visualization interface."""
    selected_part = (
        request.form.get("part")
        if request.method == "POST"
        else request.args.get("part")
    )
    parts = get_all_parts()
    chains, connections = get_all_chains(selected_part)
    duplicates = get_duplicate_info()
    last_update = get_last_update()

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
    )


# ============================================================================
# MAIN APPLICATION
# ============================================================================


def create_app(enable_scanner: bool = True, enable_visualization: bool = True) -> Flask:
    """Create and configure the unified Flask application."""
    configure_apps(enable_scanner, enable_visualization)

    app = Flask(
        __name__,
        template_folder=os.path.join(
            os.path.dirname(__file__), "..", "casman", "templates"
        ),
        static_folder=os.path.join(os.path.dirname(__file__), "..", "casman", "static"),
    )

    # Enable CORS for mobile browser access
    if HAS_CORS:
        CORS(app)
        logger.info("CORS enabled for cross-origin requests")
    else:
        logger.warning(
            "CORS not available - mobile browsers may have issues. Install with: pip install flask-cors"
        )

    if APP_CONFIG["enable_scanner"]:
        app.register_blueprint(scanner_bp)

    if APP_CONFIG["enable_visualization"]:
        app.register_blueprint(visualize_bp)
        app.jinja_env.globals.update(format_display_data=format_display_data)

    @app.route("/")
    def home():
        """Home page with links to available interfaces."""
        enabled_apps = []
        if APP_CONFIG["enable_scanner"]:
            enabled_apps.append(
                (
                    "Scanner",
                    "/scanner",
                    "🔍 Connect/Disconnect parts (commissioning & repairs)",
                )
            )
        if APP_CONFIG["enable_visualization"]:
            enabled_apps.append(
                (
                    "Visualization",
                    "/visualize",
                    "📊 View assembly chains and connections",
                )
            )

        if len(enabled_apps) == 1:
            return redirect(enabled_apps[0][1])

        return render_template("home.html", enabled_apps=enabled_apps)

    return app


def run_dev_server(
    host: str = "0.0.0.0",
    port: int = 5000,
    enable_scanner: bool = True,
    enable_visualization: bool = True,
) -> None:
    """Run the development server."""
    init_all_databases()
    app = create_app(enable_scanner, enable_visualization)

    print("🚀 Starting CAsMan Web Application (Development Mode)")
    print(f"📡 Server: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
    print()

    if enable_scanner and enable_visualization:
        print("✓ Scanner interface: /scanner")
        print("✓ Visualization interface: /visualize")
    elif enable_scanner:
        print("✓ Scanner interface only (commissioning/repairs)")
    elif enable_visualization:
        print("✓ Visualization interface only (view chains)")

    print()
    print("Press Ctrl+C to stop")

    app.run(host=host, port=port, debug=True)


def run_production_server(
    host: str = "0.0.0.0",
    port: int = 5000,
    workers: int = 4,
    enable_scanner: bool = True,
    enable_visualization: bool = True,
) -> None:
    """Run the production server using Gunicorn."""
    try:
        import gunicorn.app.base
    except ImportError:
        print("❌ Gunicorn is required for production mode")
        print("💡 Install with: pip install gunicorn")
        sys.exit(1)

    init_all_databases()

    class StandaloneApplication(gunicorn.app.base.BaseApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super().__init__()

        def load_config(self):
            for key, value in self.options.items():
                if key in self.cfg.settings and value is not None:
                    self.cfg.set(key.lower(), value)

        def load(self):
            return self.application

    app = create_app(enable_scanner, enable_visualization)

    options = {
        "bind": f"{host}:{port}",
        "workers": workers,
        "worker_class": "sync",
        "accesslog": "-",
        "errorlog": "-",
        "loglevel": "info",
    }

    print("🚀 Starting CAsMan Web Application (Production Mode)")
    print(f"📡 Server: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
    print(f"⚙️  Workers: {workers}")
    print()

    if enable_scanner and enable_visualization:
        print("✓ Scanner interface: /scanner")
        print("✓ Visualization interface: /visualize")
    elif enable_scanner:
        print("✓ Scanner interface only (commissioning/repairs)")
    elif enable_visualization:
        print("✓ Visualization interface only (view chains)")

    print()
    print("Press Ctrl+C to stop")

    StandaloneApplication(app, options).run()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CAsMan Web Application")
    parser.add_argument(
        "--mode", choices=["dev", "prod"], default="dev", help="Server mode"
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host address")
    parser.add_argument("--port", type=int, default=5000, help="Port number")
    parser.add_argument(
        "--workers", type=int, default=4, help="Number of workers (production only)"
    )
    parser.add_argument(
        "--scanner-only", action="store_true", help="Enable only scanner"
    )
    parser.add_argument(
        "--visualize-only", action="store_true", help="Enable only visualization"
    )

    args = parser.parse_args()

    enable_scanner = not args.visualize_only
    enable_visualization = not args.scanner_only

    if args.mode == "prod":
        run_production_server(
            args.host, args.port, args.workers, enable_scanner, enable_visualization
        )
    else:
        run_dev_server(args.host, args.port, enable_scanner, enable_visualization)
