# Web Package

Documentation for the `casman.web` package.

## Overview

Web application module for CAsMan.

Provides Flask-based web interfaces for scanner and visualization.

## Modules

### scanner

Scanner Blueprint for CAsMan Web Application

Provides web interface for scanning, connecting, and disconnecting parts.

**Functions:**
- `get_part_details()` - Get part details from the database
- `validate_snap_part()` - Validate SNAP part number format (SNAP<chassis><slot><port>)
- `validate_connection_sequence()` - Validate that connection follows the proper chain sequence
- `format_snap_part()` - Format SNAP part number from chassis, slot, and port
- `get_existing_connections()` - Get all existing connections for a part where latest status is 'connected'
- `scanner_index()` - Render the scanner interface
- `validate_part()` - Validate a scanned or entered part number and return existing connections
- `get_connections()` - Get all active connections for a part
- `check_snap_ports()` - Check which SNAP ports are already connected for a given chassis and slot
- `format_snap_part_route()` - Format SNAP part number from chassis, slot, and port
- `record_connection()` - Record a new connection between two parts, preventing duplicates
- `record_disconnection()` - Record a disconnection between two parts
- `add_parts()` - Add new part numbers for a given part type
- `get_part_history()` - Get complete connection/disconnection history for a part

### server

Server Management for CAsMan Web Application

Provides development and production server runners.

**Functions:**
- `run_dev_server()` - Run the development server
- `run_production_server()` - Run the production server using Gunicorn
- `load_config()` - No docstring available
- `load()` - No docstring available

**Classes:**
- `StandaloneApplication` - No docstring available

### visualize

Visualization Blueprint for CAsMan Web Application

Provides web interface for viewing assembly chain connections.

**Functions:**
- `load_viz_template()` - Load the visualization HTML template from file
- `get_all_parts()` - Fetch all unique part numbers from the assembled_casm
- `get_all_chains()` - Fetch all connection chains from the assembled_casm
- `get_duplicate_info()` - Get information about duplicate connections
- `get_last_update()` - Get the latest timestamp from the database
- `format_display_data()` - Format part display data for visualization
- `visualize_static()` - Serve static files for visualization (fonts, etc
- `visualize_index()` - Render the visualization interface
- `ts()` - No docstring available

### app

Flask application factory and configuration.

**Functions:**
- `configure_apps()` - Configure which applications to enable
- `create_app()` - Create and configure the unified Flask application
- `home()` - Home page with links to available interfaces

## Scanner Module Details

Provides web interface for scanning, connecting, and disconnecting parts.

## Functions

### get_part_details

**Signature:** `get_part_details(part_number: str) -> Optional[Tuple[str, str]]`

Get part details from the database.

---

### validate_snap_part

**Signature:** `validate_snap_part(part_number: str) -> bool`

Validate SNAP part number format (SNAP<chassis><slot><port>).

---

### validate_connection_sequence

**Signature:** `validate_connection_sequence(first_type: str, second_type: str) -> tuple[bool, str]`

Validate that connection follows the proper chain sequence.

---

### format_snap_part

**Signature:** `format_snap_part(chassis: int, slot: str, port: int) -> str`

Format SNAP part number from chassis, slot, and port.

**Returns:**

Formatted SNAP part number (e.g., SNAP1A00)

---

### get_existing_connections

**Signature:** `get_existing_connections(part_number: str) -> List[Dict]`

Get all existing connections for a part where latest status is 'connected'.

---

### scanner_index

*@scanner_bp.route('/')*

**Signature:** `scanner_index()`

Render the scanner interface.

---

### validate_part

*@scanner_bp.route('/api/validate-part', methods=['POST'])*

**Signature:** `validate_part()`

Validate a scanned or entered part number and return existing connections.

---

### get_connections

*@scanner_bp.route('/api/get-connections', methods=['POST'])*

**Signature:** `get_connections()`

Get all active connections for a part.

---

### check_snap_ports

*@scanner_bp.route('/api/check-snap-ports', methods=['POST'])*

**Signature:** `check_snap_ports()`

Check which SNAP ports are already connected for a given chassis and slot.

---

### format_snap_part_route

*@scanner_bp.route('/api/format-snap', methods=['POST'])*

**Signature:** `format_snap_part_route()`

Format SNAP part number from chassis, slot, and port.

---

### record_connection

*@scanner_bp.route('/api/record-connection', methods=['POST'])*

**Signature:** `record_connection()`

Record a new connection between two parts, preventing duplicates.

---

### record_disconnection

*@scanner_bp.route('/api/record-disconnection', methods=['POST'])*

**Signature:** `record_disconnection()`

Record a disconnection between two parts.

---

### add_parts

*@scanner_bp.route('/api/add-parts', methods=['POST'])*

**Signature:** `add_parts()`

Add new part numbers for a given part type.

---

### get_part_history

*@scanner_bp.route('/api/part-history', methods=['POST'])*

**Signature:** `get_part_history()`

Get complete connection/disconnection history for a part.

---

## Server Module Details

Provides development and production server runners.

## Functions

### run_dev_server

**Signature:** `run_dev_server(host: str, port: int, enable_scanner: bool, enable_visualization: bool) -> None`

Run the development server.

---

### run_production_server

**Signature:** `run_production_server(host: str, port: int, workers: int, enable_scanner: bool, enable_visualization: bool) -> None`

Run the production server using Gunicorn.

---

### load_config

**Signature:** `load_config()`

No docstring available.

---

### load

**Signature:** `load()`

No docstring available.

---

## Classes

### StandaloneApplication

**Class:** `StandaloneApplication(gunicorn.app.base.BaseApplication)`

No docstring available.

#### Methods

##### __init__

**Signature:** `__init__(app, options)`

No docstring available.

---

##### load_config

**Signature:** `load_config()`

No docstring available.

---

##### load

**Signature:** `load()`

No docstring available.

---

---

## Visualize Module Details

Provides web interface for viewing assembly chain connections.

## Functions

### load_viz_template

**Signature:** `load_viz_template() -> str`

Load the visualization HTML template from file.

---

### get_all_parts

**Signature:** `get_all_parts() -> List[str]`

Fetch all unique part numbers from the assembled_casm.db database.

---

### get_all_chains

**Signature:** `get_all_chains(selected_part: Optional[str]) -> Tuple[List[List[str]], Dict[str, Tuple[Optional[str], Optional[str], Optional[str]]]]`

Fetch all connection chains from the assembled_casm.db database.

---

### get_duplicate_info

**Signature:** `get_duplicate_info() -> Dict[str, List[str]]`

Get information about duplicate connections.

---

### get_last_update

**Signature:** `get_last_update() -> Optional[str]`

Get the latest timestamp from the database.

---

### format_display_data

**Signature:** `format_display_data(part: str, connections: Dict[str, Tuple[Optional[str], Optional[str], Optional[str]]], duplicates: Dict[str, List[str]]) -> str`

Format part display data for visualization.

---

### visualize_static

*@visualize_bp.route('/static/<path:filename>')*

**Signature:** `visualize_static(filename)`

Serve static files for visualization (fonts, etc.).

---

### visualize_index

*@visualize_bp.route('/', methods=['GET', 'POST'])*
*@visualize_bp.route('/chains', methods=['GET', 'POST'])*

**Signature:** `visualize_index()`

Render the visualization interface.

---

### ts

**Signature:** `ts(val: Optional[str]) -> str`

No docstring available.

---

## App Module Details

## Constants

### HAS_CORS

**Value:** `False`

## Functions

### configure_apps

**Signature:** `configure_apps(enable_scanner: bool, enable_visualization: bool) -> None`

Configure which applications to enable.

---

### create_app

**Signature:** `create_app(enable_scanner: bool, enable_visualization: bool) -> Flask`

Create and configure the unified Flask application.

---

### home

*@app.route('/')*

**Signature:** `home()`

Home page with links to available interfaces.

---
