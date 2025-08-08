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

from casman.config.core import get_config

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "casman"))
)
app = Flask(__name__)


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
    # Get the last update timestamp
    last_update = get_last_update()
    # Render the HTML template with the data
    return render_template_string(
        TEMPLATE,
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
    selected_part: Optional[str] = None,
) -> Tuple[
    List[List[str]], Dict[str, Tuple[Optional[str], Optional[str], Optional[str]]]
]:
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
    connections: Dict[str, Tuple[Optional[str], Optional[str], Optional[str]]] = {}
    for part_number, connected_to, scan_time, connected_scan_time in records:
        connections[part_number] = (connected_to, scan_time, connected_scan_time)
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
    _, scan_time, connected_scan_time = connections.get(part, (None, None, None))
    display_lines: List[str] = [f"<span class='national-park'>{part}</span><br>"]
    ant, lna, bac = "ANTENNA", "LNA", "BACBOARD"
    if "ANT" in part:
        display_lines.append(f"<span class='monospace'>{ant:8s} @ {scan_time}</span>")
        display_lines.append(
            f"<span class='monospace'>{lna:8s} @ {connected_scan_time}</span>"
        )
    elif "LNA" in part:
        ant_entry = next(
            (p for p, (c, _, cs) in connections.items() if c == part), None
        )
        if ant_entry is not None:
            ant_scan_time = connections.get(ant_entry, (None, None, None))[2]
        else:
            ant_scan_time = None
        display_lines.append(
            f"<span class='monospace'>{ant:8s} @ {ant_scan_time}</span>"
        )
        display_lines.append(f"<span class='monospace'>{lna:8s} @ {scan_time}</span>")
        display_lines.append(
            f"<span class='monospace'>{bac:8s} @ {connected_scan_time}</span>"
        )
    elif "BAC" in part:
        lna_entry = next(
            (p for p, (c, _, cs) in connections.items() if c == part), None
        )
        if lna_entry is not None:
            lna_scan_time = connections.get(lna_entry, (None, None, None))[2]
        else:
            lna_scan_time = None
        display_lines.append(
            f"<span class='monospace'>{lna:3s} @ {lna_scan_time}</span>"
        )
    return "\n".join(display_lines)


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


TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>CASM Assembly Connections</title>
  <style>
    @font-face {
      font-family: 'National Park';
      src: url('/static/fonts/NationalPark-Regular.woff') format('woff');
      font-weight: normal;
      font-style: normal;
    }
    @font-face {
      font-family: 'National Park Bold';
      src: url('/static/fonts/NationalPark-Bold.woff') format('woff');
      font-weight: bold;
      font-style: normal;
    }
    body.light-mode { font-family: 'National Park', sans-serif; margin: 20px;
      background-color: #f0f0f5; color: #333; }
    body.dark-mode { font-family: 'National Park', sans-serif; margin: 20px;
      background-color: #333; color: #f0f0f5; }
    h1 { font-family: 'National Park Bold', sans-serif; color: inherit; display: inline; }
    .toolbar { display: flex; justify-content: space-between; align-items: center; }
    .diagram { display: flex; flex-direction: column; align-items: center;
      margin-top: 20px; }
    .chain { margin: 20px 0; display: flex; align-items: center; }
    .box { display: flex; flex-direction: column; justify-content: center;
      align-items: center; padding: 10px; border: 2px solid currentColor;
      border-radius: 8px; background-color: #ffffff; margin: 0; position: relative;
      color: currentColor; text-align: center; white-space: pre-wrap;
      font-weight: normal; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
      transition: transform 0.3s ease; }
    body.dark-mode .box { background-color: #222; }
    .box.selected { color: #FF4500; border-color: #FF4500; }
    .box:hover { transform: scale(1.05); }
    .line { width: 60px; height: 2px; background-color: currentColor; margin: 0; }
    .national-park { font-family: 'National Park', sans-serif; font-weight: bold; }
    .monospace { font-family: 'Courier New', monospace; }
    .dark-mode-toggle { margin-left: 20px; cursor: pointer; font-size: 24px; }
    .sun { display: none; }
    .moon { display: inline; }
    body.dark-mode .sun { display: inline; }
    body.dark-mode .moon { display: none; }
    .dark-mode-toggle span { transition: transform 0.3s ease; }
    .dark-mode-toggle:hover span { transform: rotate(45deg); }
    .controls { display: flex; justify-content: space-between; align-items: center; }
    @media (max-width: 768px) {
      .chain { flex-direction: column; margin-bottom: 20px; }
      .line { margin: 10px 0; }
    }
  </style>
</head>
<body>
  <div class="toolbar">
    <h1>CASM Analog Chains</h1>
    <div class="dark-mode-toggle" onclick="toggleDarkMode()">
      <svg class="moon" xmlns="http://www.w3.org/2000/svg" width="24" height="24"
        viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
        stroke-linecap="round" stroke-linejoin="round" class="feather feather-moon">
        <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"></path>
      </svg>
      <svg class="sun" xmlns="http://www.w3.org/2000/svg" width="24" height="24"
        viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
        stroke-linecap="round" stroke-linejoin="round" class="feather feather-sun">
        <circle cx="12" cy="12" r="5"></circle>
        <line x1="12" y1="1" x2="12" y2="3"></line>
        <line x1="12" y1="21" x2="12" y2="23"></line>
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
        <line x1="1" y1="12" x2="3" y2="12"></line>
        <line x1="21" y1="12" x2="23" y2="12"></line>
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
      </svg>
    </div>
  </div>
  <div class="controls">
    <form method="post" style="display: inline;">
      <label for="part">Select Part:</label>
      <select name="part" id="part">
        <option value="">--Show all assembled Analog Chains--</option>
        {% for part in parts %}
          <option value="{{ part }}" {% if part == selected_part %}selected{% endif %}>
            {{ part }}</option>
        {% endfor %}
      </select>
      <input type="submit" value="Show Connections">
    </form>
    <button onclick="refreshData()">Refresh Data</button>
  </div>
  <div class="diagram">
    {% if chains %}
      {% for chain in chains %}
        <div class="chain">
          {% for part in chain %}
            <div class="box {% if part == selected_part %}selected{% endif %}">
              {{ format_display_data(part, connections) | safe }}
            </div>
            {% if not loop.last %}
              <div class="line"></div>
            {% endif %}
          {% endfor %}
        </div>
      {% endfor %}
    {% else %}
      <p>No records found in the assembled database.</p>
    {% endif %}
  </div>
  <p id="last-update">Last Part scanned on {{ last_update or '' }}</p>
  <script>
    function toggleDarkMode() {
      const body = document.body;
      body.classList.toggle('dark-mode');
      body.classList.toggle('light-mode');
      localStorage.setItem('theme', body.classList.contains('dark-mode') ? 'dark'
        : 'light');
    }

    function refreshData() {
      document.getElementById('last-update').textContent = 'Fetching database...';
      setTimeout(() => location.reload(), 1000);
    }

    document.addEventListener("DOMContentLoaded", function() {
      const savedTheme = localStorage.getItem('theme') || 'light';
      document.body.classList.add(savedTheme + '-mode');

      const chains = document.querySelectorAll('.chain');
      chains.forEach(chain => {
        const boxes = chain.querySelectorAll('.box');
        let maxWidth = 0;
        let maxHeight = 0;

        boxes.forEach(box => {
          const rect = box.getBoundingClientRect();
          if (rect.width > maxWidth) {
            maxWidth = rect.width;
          }
          if (rect.height > maxHeight) {
            maxHeight = rect.height;
          }
        });

        boxes.forEach(box => {
          box.style.width = maxWidth + 'px';
          box.style.height = maxHeight + 'px';
        });
      });
    });
  </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.jinja_env.globals.update(format_display_data=format_display_data)
    app.run(debug=True)
