"""
visualize_analog_chains_web.py

A Flask web application to visualize the analog chain from parts recorded in the
assembled_casm.db database.
"""

import os
import sqlite3
import sys
from typing import Dict, List, Optional, Tuple

from flask import Flask, render_template_string, request

from casman.config import get_config

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "casman"))
)
app = Flask(__name__)


def load_template() -> str:
    """Load the HTML template from file."""
    template_path = os.path.join(
        os.path.dirname(__file__), "templates", "analog_chains.html"
    )
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


@app.route("/", methods=["GET", "POST"])
def index() -> str:
    """
    Render the main page displaying the analog chain.

    Returns
    -------
    str
        Rendered HTML page as a string.
    """
    # Get the selected part from the form (if POST), otherwise None
    selected_part = request.form.get("part") if request.method == "POST" else None
    # Fetch all unique parts
    parts = get_all_parts()
    # Fetch all chains and connection data
    chains, connections = get_all_chains(selected_part)
    # Get duplicate information
    duplicates = get_duplicate_info()
    # Get the last update timestamp
    last_update = get_last_update()
    # Render the HTML template with the data
    template = load_template()
    return render_template_string(
        template,
        parts=parts,
        chains=chains,
        connections=connections,
        duplicates=duplicates,
        selected_part=selected_part,
        last_update=last_update,
    )


def get_all_parts() -> List[str]:
    """
    Fetch all unique part numbers from the assembled_casm.db database.

    Returns:
        List[str]: List of all unique part numbers found in the database.
    """
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
    """
    Fetch all connection chains from the assembled_casm.db database.
    
    This function builds proper chains with duplicate detection,
    ensuring ANT parts are connected to their LNA chains.

    Args:
        selected_part (Optional[str]): \
          If provided, only chains containing this part will be returned.

    Returns:
        Tuple[List[List[str]], Dict[str, Tuple[Optional[str], Optional[str], Optional[str]]]]: \
          (all_chains, connections)
            all_chains: List of all connection chains (each chain is a list of part numbers).
            connections: Mapping from part_number to (connected_to, scan_time, connected_scan_time).
    """
    db_path = get_config("CASMAN_ASSEMBLED_DB", "database/assembled_casm.db")
    if db_path is None:
        raise ValueError("Database path for assembled_casm.db is not set.")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        "SELECT part_number, connected_to, scan_time, connected_scan_time "
        "FROM assembly ORDER BY scan_time"
    )
    records = c.fetchall()
    conn.close()
    
    # Build chains with duplicate detection
    all_chains, connections = build_chains_with_duplicates_web(records)
    
    if selected_part:
        all_chains = [chain for chain in all_chains if any(selected_part in part for part in chain)]
    
    return all_chains, connections


def build_chains_with_duplicates_web(records):
    """
    Build chains while detecting and handling duplicates for web interface.
    
    Returns:
        Tuple[List[List[str]], Dict[str, Tuple[Optional[str], Optional[str], Optional[str]]]]: 
        (chains, connections_dict)
    """
    # Use the same logic as the CLI to build basic chains
    from casman.assembly.chains import build_connection_chains
    
    chains_dict = build_connection_chains()
    
    # Build the connections_dict for display data
    connections_dict = {}
    for part_number, connected_to, scan_time, connected_scan_time in records:
        connections_dict[part_number] = (connected_to, scan_time, connected_scan_time)
    
    if not chains_dict:
        return [], connections_dict

    # Track which parts have been printed to avoid duplicates
    printed_parts = set()

    # Find starting points (parts that aren't connected to by others)
    all_connected_parts = set()
    for connected_list in chains_dict.values():
        all_connected_parts.update(connected_list)

    starting_parts = [part for part in chains_dict.keys() if part not in all_connected_parts]

    # If no clear starting points, use all parts
    if not starting_parts:
        starting_parts = list(chains_dict.keys())

    # Build chains starting from each starting point (same as CLI)
    chains = []
    for start_part in sorted(starting_parts):  # Sort for consistent output
        if start_part in printed_parts:
            continue

        # Use BFS to find all connected parts
        chain_queue = [[start_part]]

        while chain_queue:
            chain = chain_queue.pop(0)
            current_part = chain[-1]

            if current_part in printed_parts:
                continue

            printed_parts.add(current_part)

            # Get connected parts
            next_parts = chains_dict.get(current_part, [])

            if not next_parts:
                # If there are no further connections, save the chain
                chains.append(chain)
            else:
                # Extend the chain for each connected part
                for next_part in next_parts:
                    if next_part not in printed_parts:
                        chain_queue.append(chain + [next_part])
    
    return chains, connections_dict


def get_duplicate_info() -> Dict[str, List[Tuple[str, str, str]]]:
    """
    Get information about duplicate connections for display.
    
    Returns:
        Dict[str, List[Tuple[str, str, str]]]: Mapping from part to list of (connected_to, scan_time, connected_scan_time)
    """
    db_path = get_config("CASMAN_ASSEMBLED_DB", "database/assembled_casm.db")
    if db_path is None:
        raise ValueError("Database path for assembled_casm.db is not set.")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        "SELECT part_number, connected_to, scan_time, connected_scan_time "
        "FROM assembly ORDER BY scan_time"
    )
    records = c.fetchall()
    conn.close()
    
    # Group connections by part number to find duplicates
    part_connections: Dict[str, List[Tuple[str, str, str]]] = {}
    for part_number, connected_to, scan_time, connected_scan_time in records:
        if part_number not in part_connections:
            part_connections[part_number] = []
        part_connections[part_number].append((connected_to, scan_time, connected_scan_time))
    
    # Return only parts with duplicates
    duplicates = {}
    for part_number, entries in part_connections.items():
        if len(entries) > 1:
            duplicates[part_number] = entries
    
    return duplicates



def format_display_data(
    part: str,
    connections: Dict[str, Tuple[Optional[str], Optional[str], Optional[str]]],
) -> str:
    """
    Format display data for a given part for HTML rendering.

    Args:
        part (str): The part number to format display data for.
        connections (Dict[str, Tuple[Optional[str], Optional[str], Optional[str]]]): \
          Mapping from part_number to (connected_to, scan_time, connected_scan_time).

    Returns:
        str: HTML-formatted string for display in the web interface.
    """
    # Check if this is a duplicate part (has _N suffix)
    is_duplicate = "_" in part and part.split("_")[-1].isdigit()
    base_part = part.split("_")[0] if is_duplicate else part
    
    # Style for duplicate parts (red)
    part_style = "color: red; font-weight: bold;" if is_duplicate else ""
    part_class = "national-park-bold"

    # FRM: connected_scan_time where this part is connected_to (when previous
    # part connects to this part)
    frm_time = None
    for row in connections.values():
        connected_to, _, connected_scan_time = row
        if connected_to == base_part and connected_scan_time:
            frm_time = connected_scan_time
            break

    # NOW and NXT: from the row where this part is part_number
    now_time: Optional[str] = None
    nxt_time: Optional[str] = None
    part_row: Optional[Tuple[Optional[str], Optional[str], Optional[str]]] = (
        connections.get(part)
    )
    if part_row is not None:
        now_time = part_row[1]  # scan_time
        nxt_time = part_row[2]  # connected_scan_time

    # Use a fixed-width whitespace string for missing timestamps
    ts_placeholder = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"

    def ts(val: Optional[str]) -> str:
        return val if val else ts_placeholder

    display_lines: List[str] = [
        f"<span class='{part_class}' style='{part_style}'>{part}</span>",
        "<br>",  # One line space between part number and timestamps
        f"<span class='monospace'>FRM: {ts(frm_time)}</span>",
        f"<span class='monospace'>NOW: {ts(now_time)}</span>",
        f"<span class='monospace'>NXT: {ts(nxt_time)}</span>",
    ]
    return "<br>".join(display_lines)


def get_last_update() -> Optional[str]:
    """
    Get the latest timestamp from the scan_time and connected_scan_time columns.

    Returns:
        Optional[str]: The latest timestamp value, or None if the table is empty.
    """
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


def ensure_app_configured(flask_app: Flask) -> None:
    """
    Ensure the Flask app is properly configured with Jinja globals.
    
    Args:
        flask_app (Flask): The Flask application instance to configure.
    """
    # Set up Jinja2 globals for the Flask app
    flask_app.jinja_env.globals.update(format_display_data=format_display_data)


def run_flask_with_free_port(
    app: Flask, start_port: int = 5000, max_tries: int = 10
) -> None:
    """
    Run the Flask app, automatically finding a free port if the default is busy.

    Args:
        app (Flask): The Flask application instance.
        start_port (int): The port to try first.
        max_tries (int): Maximum number of ports to try.
    """
    import socket

    # Ensure the Flask app is properly configured
    ensure_app_configured(app)

    port = start_port
    for _ in range(max_tries):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("127.0.0.1", port))
            sock.close()
            print(f"Starting Flask app on port {port}")
            print(f"🌐 Web interface available at: http://127.0.0.1:{port}")
            app.run(debug=False, port=port, use_reloader=False)
            break
        except OSError as e:
            sock.close()
            if "Address already in use" in str(e):
                print(f"Port {port} in use, trying next port...")
                port += 1
            else:
                raise
    else:
        print(
            f"Could not find a free port in range {start_port}-{start_port+max_tries-1}"
        )


if __name__ == "__main__":
    app.jinja_env.globals.update(format_display_data=format_display_data)
    run_flask_with_free_port(app, start_port=5000, max_tries=10)
