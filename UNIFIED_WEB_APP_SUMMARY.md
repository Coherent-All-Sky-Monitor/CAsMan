# Unified Web Application - Implementation Summary

## Overview

Successfully created a unified Flask web application that serves both the scanner and visualization interfaces with configurable options.

## What Was Created

### 1. Unified Web Application (`casman/unified_web_app.py`)
- Single Flask app with two blueprints:
  - **Scanner Blueprint** (`/scanner`): For connecting/disconnecting parts
  - **Visualization Blueprint** (`/visualize`): For viewing assembly chains
- Home page at `/` with links to both interfaces (when both enabled)
- Configurable to serve either or both interfaces

### 2. CLI Command (`casman/cli/web_commands.py`)
```bash
casman web                    # Both interfaces
casman web --scanner-only     # Scanner only (commissioning/repairs)
casman web --visualize-only   # Visualization only
casman web --port 8080        # Custom port
```

### 3. Configuration (`config.yaml`)
```yaml
web_app:
  port: 5000
  host: "0.0.0.0"
  enable_scanner: true
  enable_visualization: true
```

### 4. UI Improvements
- **Home links**: Added "← Home" link to both scanner and visualization pages
- **Separate CSS**: Each interface maintains its own styling
  - Scanner: Mono-color CSS framework (Courier New)
  - Visualization: National Park fonts
- **Dark mode**: Both interfaces support dark mode with localStorage persistence

## Key Features

### Flexibility
- Run both interfaces together or separately
- Configure via CLI flags or config file
- Auto-redirect to single interface when only one enabled

### Separate Styling
- Scanner keeps its minimal monospace aesthetic
- Visualization keeps its National Park font styling
- No CSS conflicts between interfaces

### Home Navigation
- Home page shows available interfaces
- Each interface has "← Home" link in top area
- Single interface mode: redirects directly (no home page)

### Use Cases
1. **Production (both)**: Full access to all features
2. **Commissioning**: Scanner-only mode for field work
3. **Repairs**: Scanner-only mode for troubleshooting
4. **Monitoring**: Visualization-only mode for viewing status

## File Changes

### New Files
- `casman/unified_web_app.py` - Main unified Flask application
- `casman/cli/web_commands.py` - CLI command handler
- `docs/unified_web_app.md` - Documentation

### Modified Files
- `casman/cli/main.py` - Added `web` command routing
- `casman/templates/scanner/scanner.html` - Added home link
- `scripts/templates/analog_chains.html` - Added home link, fixed font paths
- `config.yaml` - Added `web_app` configuration section

## Testing

```bash
# Test help
casman web --help

# Test both interfaces (default)
casman web

# Test scanner only
casman web --scanner-only

# Test visualization only  
casman web --visualize-only

# Test custom port
casman web --port 8080
```

## Production Deployment

### Using Gunicorn (Recommended)
```bash
pip install gunicorn

# Both interfaces
gunicorn -w 4 -b 0.0.0.0:5000 "casman.unified_web_app:create_app()"

# Scanner only
gunicorn -w 4 -b 0.0.0.0:5000 \
  "casman.unified_web_app:create_app(enable_scanner=True, enable_visualization=False)"
```

### Environment Variables (Optional)
Can override config via environment:
```bash
export CASMAN_WEB_PORT=8080
export CASMAN_WEB_HOST=127.0.0.1
```

## Legacy Commands Still Work

The original separate commands remain functional:
```bash
casman scanner           # Port 5001 (scanner only)
casman visualize web     # Port 5000 (visualization only)
```

## Benefits

1. ✅ **Single server**: One process, one port for both interfaces
2. ✅ **Configurable**: Enable/disable interfaces via config or CLI
3. ✅ **Separate CSS**: No style conflicts, each keeps its identity
4. ✅ **Home navigation**: Easy access between interfaces
5. ✅ **Production ready**: Works with WSGI servers like Gunicorn
6. ✅ **Use-case specific**: Scanner-only for commissioning/repairs
7. ✅ **Backwards compatible**: Original commands still functional
