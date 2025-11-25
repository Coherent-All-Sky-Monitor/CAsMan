"""
Visualization Blueprint for CAsMan Web Application

Provides web interface for viewing assembly chain connections.
"""

import logging
import os
import sqlite3
from typing import Dict, List, Optional, Tuple

from flask import (Blueprint, render_template_string, request,
                   send_from_directory)

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
    part_types = load_part_types()
    # Exclude terminal type (highest key)
    terminal_key = max(part_types.keys())
    part_types_for_builder = {k: v for k, v in part_types.items() if k != terminal_key}
    
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
        part_types=part_types_for_builder,
    )
