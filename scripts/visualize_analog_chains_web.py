
"""
visualize_analog_chains_web.py

A Flask web application to visualize the analog chain from parts recorded in the
assembled_casm.db database.
"""


import os
import sqlite3
import sys
from typing import Dict, List, Optional, Set, Tuple

from flask import Flask, render_template_string, request

from casman.config import get_config

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            '..',
            'casman')))
app = Flask(__name__)


def load_template() -> str:
    """Load the HTML template from file."""
    template_path = os.path.join(
        os.path.dirname(__file__),
        'templates',
        'analog_chains.html')
    with open(template_path, 'r', encoding='utf-8') as f:
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
    selected_part = request.form.get(
        "part") if request.method == "POST" else None
    # Fetch all unique parts
    parts = get_all_parts()
    # Fetch all chains and connection data
    chains, connections = get_all_chains(selected_part)
    # Get the last update timestamp
    last_update = get_last_update()
    # Render the HTML template with the data
    template = load_template()
    return render_template_string(
        template,
        parts=parts,
        chains=chains,
        connections=connections,
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
        selected_part: Optional[str] = None
) -> Tuple[List[List[str]], Dict[str, Tuple[Optional[str], Optional[str], Optional[str]]]]:
    """
    Fetch all connection chains from the assembled_casm.db database.

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
        "FROM assembly"
    )
    records = c.fetchall()
    connections: Dict[str, Tuple[Optional[str],
                                 Optional[str], Optional[str]]] = {}
    for part_number, connected_to, scan_time, connected_scan_time in records:
        connections[part_number] = (
            connected_to, scan_time, connected_scan_time)
    conn.close()
    all_chains: List[List[str]] = []
    visited: Set[str] = set()
    for part in connections:
        if part not in visited:
            chain = build_chain(part, connections, visited)
            all_chains.append(chain)
    if selected_part:
        all_chains = [chain for chain in all_chains if selected_part in chain]
    return all_chains, connections


def build_chain(
    start_part: str,
    connections: Dict[str, Tuple[Optional[str], Optional[str], Optional[str]]],
    visited: Set[str],
) -> List[str]:
    """
    Build a chain of connections starting from the given part.

    Args:
        start_part (str): The part number to start the chain from \
          connections (Dict[str, Tuple[Optional[str], Optional[str], \
            Optional[str]]]): Mapping from part_number to (connected_to, \
              scan_time, connected_scan_time).
        visited (Set[str]): Set of part numbers already visited in this traversal.

    Returns:
        List[str]: The chain of connected part numbers starting from start_part.
    """
    chain: List[str] = []
    queue: List[str] = [start_part]
    while queue:
        current_part = queue.pop(0)
        if current_part in visited:
            continue
        visited.add(current_part)
        chain.append(current_part)
        next_part = connections.get(current_part, (None, None, None))[0]
        if next_part and next_part not in visited:
            queue.append(next_part)
    return chain


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

    # FRM: connected_scan_time where this part is connected_to (when previous
    # part connects to this part)
    frm_time = None
    for row in connections.values():
        connected_to, _, connected_scan_time = row
        if connected_to == part and connected_scan_time:
            frm_time = connected_scan_time
            break

    # NOW and NXT: from the row where this part is part_number

    now_time: Optional[str] = None
    nxt_time: Optional[str] = None
    part_row: Optional[Tuple[Optional[str], Optional[str],
                             Optional[str]]] = connections.get(part)
    if part_row is not None:
        now_time = part_row[1]  # scan_time
        nxt_time = part_row[2]  # connected_scan_time

    # Use a fixed-width whitespace string for missing timestamps
    ts_placeholder = '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'

    def ts(val: Optional[str]) -> str:
        return val if val else ts_placeholder

    display_lines: List[str] = [
        f"<span class='national-park-bold'>{part}</span>",
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


def run_flask_with_free_port(
        app: Flask,
        start_port: int = 5000,
        max_tries: int = 10) -> None:
    """
    Run the Flask app, automatically finding a free port if the default is busy.

    Args:
        app (Flask): The Flask application instance.
        start_port (int): The port to try first.
        max_tries (int): Maximum number of ports to try.
    """
    import socket
    port = start_port
    for _ in range(max_tries):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("127.0.0.1", port))
            sock.close()
            print(f"Starting Flask app on port {port}")
            app.run(debug=True, port=port)
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
            f"Could not find a free port in range {start_port}-{start_port+max_tries-1}")


if __name__ == "__main__":
    app.jinja_env.globals.update(format_display_data=format_display_data)
    run_flask_with_free_port(app, start_port=5000, max_tries=10)
