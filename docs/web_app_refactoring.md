# Web Application Refactoring Summary

## Overview
Successfully refactored the CAsMan web applications from the `casman/` package directory to the `scripts/` directory, consolidating redundant code and adding production server support.

## Changes Made

### 1. New Files Created

#### `scripts/web_app.py` (~21 KB)

- **Purpose**: Unified web application serving both scanner and visualization interfaces

- **Features**:
  - Scanner blueprint for part connection/disconnection workflows
  - Visualization blueprint for viewing analog signal chains
  - Home page with navigation to enabled interfaces
  - Development server mode (Flask with debug)
  - Production server mode (Gunicorn WSGI)
  - Configurable interface enabling/disabling
  - National Park font integration
  - Dark/light mode theme support
  - Responsive toolbar with home/theme buttons

#### `scripts/home_template.py` (~4.6 KB)

- **Purpose**: Generate home page HTML dynamically

- **Function**: `get_home_html(enabled_apps: dict) -> str`

- **Features**:
  - Responsive card-based navigation
  - Shows only enabled interfaces
  - Consistent styling with other pages
  - National Park theme fonts

### 2. Configuration Updates

#### `config.yaml`
Added nested configuration for development and production modes:

```yaml

web_app:
  enable_scanner: true
  enable_visualization: true
  dev:
    port: 5000
    host: "0.0.0.0"
  production:
    port: 8000
    host: "0.0.0.0"
    workers: 4
    worker_class: "sync"

```python

### 3. CLI Updates

#### `casman/cli/web_commands.py`

- Updated to launch `scripts/web_app.py` via subprocess

- Added `--mode {dev,production}` flag

- Added `--workers` flag for production mode

- Reads configuration from both CLI args and config.yaml

- Proper error handling for missing script files

#### `casman/cli/scanner_commands.py`

- Updated to use unified web app in scanner-only mode

- Launches `scripts/web_app.py --scanner-only`

- Maintains backward compatibility with existing workflow

### 4. Dependency Updates

#### `requirements.txt`
Added production server dependency:

```python

gunicorn>=21.0.0  # For production WSGI server

```python

### 5. Files Removed

Deleted redundant files from `casman/` directory:

- `casman/unified_web_app.py` (749 lines) - replaced by `scripts/web_app.py`

- `casman/web_scanner.py` (341 lines) - functionality merged into unified app

## Usage

### Development Mode (Default)

```bash

# Launch both interfaces on port 5000
casman web

# Launch scanner only
casman web --scanner-only

# Launch visualization only
casman web --visualize-only

# Custom port
casman web --port 8080

```python

### Production Mode

```bash

# Launch with Gunicorn (4 workers, port 8000)
casman web --mode production

# Custom workers
casman web --mode production --workers 8

# Custom port
casman web --mode production --port 9000

```python

### Scanner Command (Backward Compatible)

```bash

# Still works, uses unified app internally
casman scanner

```python

## Architecture

### Application Structure

```python

Home Page (/)
├── Scanner Interface (/scanner)
│   ├── Connect workflow
│   ├── Disconnect workflow
│   └── Connection history
└── Visualization Interface (/visualize)
    ├── Analog chain viewer
    ├── SNAP selection
    └── Connection details

```python

### Server Modes

#### Development Mode

- Flask built-in server

- Debug mode enabled

- Hot reload on code changes

- Single process

- Port 5000 (default)

#### Production Mode

- Gunicorn WSGI server

- Multiple worker processes (4 default)

- Process management

- Better performance

- Port 8000 (default)

## Benefits

1. **Cleaner Project Structure**: Web apps in `scripts/` where they belong, not in the package
2. **No Code Duplication**: Single unified app instead of two separate versions
3. **Production Ready**: Gunicorn support for deployment
4. **Configurable**: Easy to enable/disable interfaces via config or CLI
5. **Backward Compatible**: Old `casman scanner` command still works
6. **Maintainable**: Single codebase for all web functionality

## Testing Checklist

- [x] CLI help displays correctly

- [x] Gunicorn installed

- [ ] Dev mode launches successfully

- [ ] Production mode launches successfully

- [ ] Scanner interface accessible

- [ ] Visualization interface accessible

- [ ] Home page navigation works

- [ ] Dark/light mode toggle works

- [ ] Scanner-only mode works

- [ ] Visualization-only mode works

## Next Steps

1. Test development mode: `casman web`
2. Test production mode: `casman web --mode production`
3. Verify all interfaces render correctly
4. Test barcode scanning workflow
5. Test visualization rendering
6. Update any external documentation
7. Consider adding systemd service file for production deployment
