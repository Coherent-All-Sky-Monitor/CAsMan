"""
scan_connect_web.py

A standalone Flask web app that replicates the workflow of the `casman scan connect` CLI command, using the CSS from analog_chains.html.
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import sqlite3

# Ensure casman modules are importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "casman")))

app = Flask(__name__)

# --- Backend logic ---

def import_casman():
    global validate_part_in_database, validate_connection_rules, record_assembly_connection
    try:
        from casman.assembly.interactive import validate_part_in_database, validate_connection_rules
        from casman.assembly.connections import record_assembly_connection
    except Exception as e:
        print(f"[ERROR] Could not import casman modules: {e}")
        def validate_part_in_database(part):
            return False, None, None
        def validate_connection_rules(*args, **kwargs):
            return False, "casman not available"
        def record_assembly_connection(*args, **kwargs):
            return False

import_casman()

@app.route("/", methods=["GET"])
def scan_page():
    return render_template("scan_connect.html")

@app.route("/validate-part", methods=["POST"])
def validate_part():
    part = request.json.get('part', '').strip()
    if not part:
        return jsonify({'valid': False, 'error': 'Part number cannot be empty'})
    try:
        is_valid, part_type, polarization = validate_part_in_database(part)
    except Exception as e:
        return jsonify({'valid': False, 'error': f'Internal error: {e}'})
    if is_valid:
        return jsonify({'valid': True, 'type': part_type, 'polarization': polarization})
    else:
        error = 'SNAP part not found in snap_feng_map.yaml' if part.startswith('SNAP') and '_ADC' in part else 'Part not found in parts database'
        return jsonify({'valid': False, 'error': error})

@app.route("/validate-connection", methods=["POST"])
def validate_connection():
    data = request.json
    try:
        valid, error = validate_connection_rules(data['first'], data['first_type'], data['connected'], data['connected_type'])
    except Exception as e:
        return jsonify({'valid': False, 'error': f'Internal error: {e}'})
    return jsonify({'valid': valid, 'error': error})

@app.route("/record-connection", methods=["POST"])
def record_connection():
    data = request.json
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        success = record_assembly_connection(
            part_number=data['first'],
            part_type=data['first_type'],
            polarization=data['first_polarization'],
            scan_time=now,
            connected_to=data['connected'],
            connected_to_type=data['connected_type'],
            connected_polarization=data['connected_polarization'],
            connected_scan_time=now,
        )
    except Exception as e:
        return jsonify({'success': False, 'error': f'Internal error: {e}'})
    if success:
        return jsonify({'success': True, 'message': f"Connection recorded: {data['first']} → {data['connected']}"})
    else:
        return jsonify({'success': False, 'error': 'Failed to record connection to database'})

@app.route('/all-parts')
def all_parts():
    db_path = os.path.join(os.path.dirname(__file__), '../database/parts.db')
    print(f"[DEBUG] Using database at: {os.path.abspath(db_path)}")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        # Try to get all part numbers (flat list)
        cur.execute('SELECT part_number FROM parts ORDER BY part_number COLLATE NOCASE')
        parts = [row[0] for row in cur.fetchall()]
        return jsonify(parts)
    except Exception as e:
        print(f"[ERROR] Could not fetch parts: {e}")
        return jsonify([])
    finally:
        conn.close()

if __name__ == "__main__":
    app.run(debug=True, port=5050)
