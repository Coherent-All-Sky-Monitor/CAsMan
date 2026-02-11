# CAsMan Development Guide

This guide provides concise, up-to-date information for developers working on CAsMan.

## Quick Start

### Prerequisites

- Python 3.8 or higher
- pip
- Git

### Setup

```bash
git clone https://github.com/Coherent-All-Sky-Monitor/CAsMan.git
cd CAsMan

python -m venv .venv
source .venv/bin/activate

pip install -e .
pip install -r requirements-dev.txt
```

### Run Tests

```bash
python -m pytest
```

## Architecture Overview

### Package Structure

```text
casman/
├── __init__.py           # Main package exports
├── antenna/              # Antenna grid, array, kernel index utilities
├── assembly/             # Assembly management
│   ├── connections.py
│   ├── data.py
│   ├── chains.py
│   └── interactive.py
├── barcode/              # Barcode generation and print pages
│   ├── generation.py
│   └── printing.py
├── cli/                  # Command-line interface
│   ├── main.py
│   ├── parts_commands.py
│   ├── assembly_commands.py
│   ├── barcode_commands.py
│   ├── visualization_commands.py
│   ├── database_commands.py
│   └── web_commands.py
├── config/               # YAML + env configuration
├── database/             # DB init, access, and sync utilities
├── parts/                # Part class, validation, search
├── visualization/        # ASCII visualization
└── web/                  # Flask app (scanner + visualization)
```

### Design Principles

1. Modular design with focused subpackages
2. Clear separation of concerns
3. NumPy-style docstrings and type annotations
4. Tests for core workflows

## Development Workflow

### Adding Features

1. Create a feature branch
2. Add or update tests
3. Implement changes with type hints and docstrings
4. Run tests
5. Regenerate auto docs

```bash
python docs/generate_docs.py
```

## Database Development

### Database Paths

Use database helpers for consistency:

```python
from casman.database.connection import get_database_path
from casman.database.initialization import init_parts_db, init_assembled_db

init_parts_db("/path/to/db/dir")
init_assembled_db("/path/to/db/dir")

parts_db = get_database_path("parts.db", "/path/to/db/dir")
```

## Documentation

Auto-generated docs are rebuilt from docstrings:

```bash
python docs/generate_docs.py
```
