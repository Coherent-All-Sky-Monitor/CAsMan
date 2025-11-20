# CAsMan Unified Web Application

The unified web application serves both the scanner and visualization interfaces in a single Flask application.

## Features

### Scanner Interface (`/scanner`)

- Connect and disconnect parts using barcode scanners or manual entry

- Real-time validation against database

- Chain-aware connection validation

- Used for **commissioning** and **repairs**

### Visualization Interface (`/visualize`)

- View assembly chains with timestamps

- Detect duplicate connections

- Filter by specific parts

- Dark/light mode support

## Usage

### Run Both Interfaces (Default)

```bash

casman web

```python

Access at: http://localhost:5000

- Home page with links to both interfaces

- Scanner: http://localhost:5000/scanner

- Visualization: http://localhost:5000/visualize

### Run Scanner Only (For Commissioning/Repairs)

```bash

casman web --scanner-only

```python

### Run Visualization Only

```bash

casman web --visualize-only

```python

### Custom Port

```bash

casman web --port 8080

```python

### Configuration File

Edit `config.yaml` to set defaults:

```yaml

web_app:
  port: 5000
  host: "0.0.0.0"
  enable_scanner: true         # Enable scanner interface
  enable_visualization: true   # Enable visualization interface

```python

## Production Deployment

For production, it's recommended to use a WSGI server like Gunicorn:

```bash

# Install gunicorn
pip install gunicorn

# Run with gunicorn (both interfaces)
gunicorn -w 4 -b 0.0.0.0:5000 "casman.unified_web_app:create_app()"

# Run scanner only
gunicorn -w 4 -b 0.0.0.0:5000 "casman.unified_web_app:create_app(enable_scanner=True, enable_visualization=False)"

# Run visualization only
gunicorn -w 4 -b 0.0.0.0:5000 "casman.unified_web_app:create_app(enable_scanner=False, enable_visualization=True)"

```

## Architecture

- **Blueprints**: Each interface is a separate Flask blueprint

- **CSS**: Each interface maintains its own CSS styling

- **Templates**: Separate template folders for each interface

- **Static Files**: Scanner uses local mono-color CSS, visualization uses National Park fonts

- **Home Page**: Landing page with links (only shown when both interfaces enabled)

## Legacy Commands

The original separate commands still work:

```bash

casman scanner                    # Scanner only (port 5001)
casman visualize web              # Visualization only (port 5000)

```

Use `casman web` for the unified interface instead.
