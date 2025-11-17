"""
scan_connect_web.py

A standalone Flask web app that replicates the workflow of the `casman scan connect` CLI command.
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify

# Ensure casman modules are importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "casman")))

app = Flask(__name__)

SCAN_TEMPLATE = '''
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>CASM Scan Connect (Web)</title>
  <style>
    body { font-family: sans-serif; background: #f0f0f5; color: #222; margin: 0; }
    .container { max-width: 500px; margin: 40px auto; background: #fff; border-radius: 12px; box-shadow: 0 4px 16px #0001; padding: 32px 24px; }
    h1 { font-size: 1.6em; margin-bottom: 24px; }
    label { font-weight: bold; display: block; margin-top: 18px; }
    input[type=text] { width: 100%; padding: 10px; font-size: 1em; border-radius: 6px; border: 1.5px solid #bbb; margin-top: 6px; }
    button { margin-top: 22px; padding: 12px 28px; font-size: 1em; border-radius: 6px; border: none; background: #007acc; color: #fff; font-weight: bold; cursor: pointer; }
    button:disabled { background: #ccc; cursor: not-allowed; }
    .status { margin-top: 18px; padding: 10px 14px; border-radius: 6px; font-size: 1em; }
    .success { background: #e6f9e6; color: #1a7f1a; border: 1.5px solid #1a7f1a; }
    .error { background: #ffeaea; color: #b30000; border: 1.5px solid #b30000; }
    .info { background: #eaf3ff; color: #00529b; border: 1.5px solid #00529b; }
    .details { font-size: 0.97em; color: #555; margin-top: 6px; }
  </style>
</head>
<body>
  <div class="container">
    <h1>CASM Scan Connect (Web)</h1>
    <form id="scan-form" autocomplete="off">
      <label for="first-part">Scan First Part:</label>
      <input type="text" id="first-part" name="first-part" required autofocus autocomplete="off">
      <div id="first-status" class="status info" style="display:none;"></div>
      <label for="connected-part">Scan Connected Part:</label>
      <input type="text" id="connected-part" name="connected-part" required disabled autocomplete="off">
      <div id="connected-status" class="status info" style="display:none;"></div>
      <button type="submit" id="connect-btn" disabled>Validate & Record Connection</button>
    </form>
    <div id="final-status" class="status" style="display:none;"></div>
    <button id="reset-btn" style="display:none; margin-top:18px;">Scan Another Connection</button>
  </div>
  <script>
    const firstInput = document.getElementById('first-part');
    const connectedInput = document.getElementById('connected-part');
    const firstStatus = document.getElementById('first-status');
    const connectedStatus = document.getElementById('connected-status');
    const connectBtn = document.getElementById('connect-btn');
    const finalStatus = document.getElementById('final-status');
    const resetBtn = document.getElementById('reset-btn');
    let firstPartData = null;
    let connectedPartData = null;

    firstInput.addEventListener('input', async function() {
      const val = this.value.trim();
      firstStatus.style.display = 'none';
      connectedInput.value = '';
      connectedInput.disabled = true;
      connectedStatus.style.display = 'none';
      connectBtn.disabled = true;
      finalStatus.style.display = 'none';
      if (val.length < 3) return;
      const resp = await fetch('/validate-part', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({part:val})});
      const data = await resp.json();
      if (data.valid) {
        firstStatus.textContent = `✔️ ${val} (${data.type}, ${data.polarization})`;
        firstStatus.className = 'status success';
        firstStatus.style.display = 'block';
        connectedInput.disabled = false;
        connectedInput.focus();
        firstPartData = data;
      } else {
        firstStatus.textContent = `❌ ${data.error}`;
        firstStatus.className = 'status error';
        firstStatus.style.display = 'block';
        firstPartData = null;
      }
    });

    connectedInput.addEventListener('input', async function() {
      const val = this.value.trim();
      connectedStatus.style.display = 'none';
      connectBtn.disabled = true;
      finalStatus.style.display = 'none';
      if (val.length < 3) return;
      const resp = await fetch('/validate-part', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({part:val})});
      const data = await resp.json();
      if (data.valid) {
        connectedStatus.textContent = `✔️ ${val} (${data.type}, ${data.polarization})`;
        connectedStatus.className = 'status success';
        connectedStatus.style.display = 'block';
        connectedPartData = data;
        // Check connection rules
        const rulesResp = await fetch('/validate-connection', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({first: firstInput.value.trim(), first_type: firstPartData.type, connected: val, connected_type: data.type})});
        const rules = await rulesResp.json();
        if (rules.valid) {
          connectBtn.disabled = false;
        } else {
          connectedStatus.textContent += `\n❌ ${rules.error}`;
          connectedStatus.className = 'status error';
          connectBtn.disabled = true;
        }
      } else {
        connectedStatus.textContent = `❌ ${data.error}`;
        connectedStatus.className = 'status error';
        connectedPartData = null;
      }
    });

    document.getElementById('scan-form').addEventListener('submit', async function(e) {
      e.preventDefault();
      connectBtn.disabled = true;
      finalStatus.style.display = 'none';
      const resp = await fetch('/record-connection', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
        first: firstInput.value.trim(),
        first_type: firstPartData.type,
        first_polarization: firstPartData.polarization,
        connected: connectedInput.value.trim(),
        connected_type: connectedPartData.type,
        connected_polarization: connectedPartData.polarization
      })});
      const data = await resp.json();
      if (data.success) {
        finalStatus.textContent = `✅ ${data.message}`;
        finalStatus.className = 'status success';
        finalStatus.style.display = 'block';
        resetBtn.style.display = 'inline-block';
      } else {
        finalStatus.textContent = `❌ ${data.error}`;
        finalStatus.className = 'status error';
        finalStatus.style.display = 'block';
        connectBtn.disabled = false;
      }
    });
    resetBtn.addEventListener('click', function() {
      firstInput.value = '';
      connectedInput.value = '';
      firstStatus.style.display = 'none';
      connectedStatus.style.display = 'none';
      finalStatus.style.display = 'none';
      connectBtn.disabled = true;
      resetBtn.style.display = 'none';
      firstInput.focus();
    });
  </script>
</body>
</html>
'''

# --- Backend logic ---

def import_casman():
    global validate_part_in_database, validate_connection_rules, record_assembly_connection
    from casman.assembly.interactive import validate_part_in_database, validate_connection_rules
    from casman.assembly.connections import record_assembly_connection

import_casman()

@app.route("/", methods=["GET"])
def scan_page():
    return render_template_string(SCAN_TEMPLATE)

@app.route("/validate-part", methods=["POST"])
def validate_part():
    part = request.json.get('part', '').strip()
    if not part:
        return jsonify({'valid': False, 'error': 'Part number cannot be empty'})
    is_valid, part_type, polarization = validate_part_in_database(part)
    if is_valid:
        return jsonify({'valid': True, 'type': part_type, 'polarization': polarization})
    else:
        error = 'SNAP part not found in snap_feng_map.yaml' if part.startswith('SNAP') and '_ADC' in part else 'Part not found in parts database'
        return jsonify({'valid': False, 'error': error})

@app.route("/validate-connection", methods=["POST"])
def validate_connection():
    data = request.json
    valid, error = validate_connection_rules(data['first'], data['first_type'], data['connected'], data['connected_type'])
    return jsonify({'valid': valid, 'error': error})

@app.route("/record-connection", methods=["POST"])
def record_connection():
    data = request.json
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
    if success:
        return jsonify({'success': True, 'message': f"Connection recorded: {data['first']} → {data['connected']}"})
    else:
        return jsonify({'success': False, 'error': 'Failed to record connection to database'})

if __name__ == "__main__":
    app.run(debug=True, port=5050)
