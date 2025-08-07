# CAsMan Development Guide

This guide provides comprehensive information for developers working on CAsMan.

## Quick Start for Developers

### Prerequisites

- Python 3.10 or higher
- pip (Python package installer)
- Git

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Coherent-All-Sky-Monitor/CAsMan.git
   cd CAsMan
   ```

2. **Install in development mode:**
   ```bash
   pip install -e .
   pip install -r requirements-dev.txt
   ```

3. **Run tests to verify setup:**
   ```bash
   python -m pytest
   ```

## Architecture Overview

CAsMan follows a modular architecture with clear separation of concerns:

### Package Structure

```
casman/
├── __init__.py           # Main package exports
├── assembly/             # Assembly management (modularized package)
│   ├── __init__.py      # Assembly package exports
│   ├── connections.py   # Recording assembly connections
│   ├── data.py         # Data retrieval and statistics
│   ├── chains.py       # Connection chain analysis
│   └── interactive.py  # Interactive assembly operations
├── cli/                  # Command-line interface (modularized package)
│   ├── __init__.py      # CLI package exports  
│   ├── main.py         # Main CLI entry point
│   ├── parts_commands.py    # Parts management commands
│   ├── assembly_commands.py # Assembly commands
│   ├── barcode_commands.py  # Barcode generation commands
│   ├── visualization_commands.py # Visualization commands
│   └── utils.py        # CLI utility functions
├── parts/                # Parts management (modularized package)
│   ├── __init__.py      # Parts package exports
│   ├── part.py         # Part class and validation
│   ├── part_number.py  # Part number management
│   └── validation.py   # Part validation logic
├── barcode_utils.py      # Barcode generation and printing
├── config.py            # Configuration management
├── database.py          # Database operations
└── visualization.py     # ASCII visualization
```

### Design Principles

1. **Modular Design**: Large modules are broken into focused subpackages
2. **Backward Compatibility**: Existing import paths continue to work
3. **Clear Separation**: Each module has a single responsibility
4. **Type Safety**: Full type annotations throughout
5. **Comprehensive Testing**: 59 tests covering all functionality

## Development Workflow

### Adding New Features

1. **Create a branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Write tests first (TDD approach):**
   ```bash
   # Add tests to appropriate test_*.py file
   python -m pytest tests/test_your_module.py -v
   ```

3. **Implement the feature:**
   - Follow existing code patterns
   - Add type annotations
   - Include docstrings in NumPy format

4. **Run all tests:**
   ```bash
   python -m pytest
   ```

5. **Update documentation:**
   ```bash
   python docs/generate_docs.py
   ```

### Code Style Guidelines

- **Type Annotations**: All functions must have type annotations
- **Docstrings**: Use NumPy-style docstrings
- **Line Length**: Maximum 88 characters (Black formatter standard)
- **Import Order**: Follow PEP 8 import ordering
- **Testing**: Maintain 100% test coverage for new code

### Modularization Guidelines

When modularizing large modules:

1. **Identify Concerns**: Group related functionality
2. **Create Subpackage**: Use a directory with `__init__.py`
3. **Maintain Exports**: Export all public functions from `__init__.py`
4. **Update Tests**: Adjust patch paths for mocking
5. **Update Documentation**: Run the documentation generator

## Testing Strategy

### Test Organization

- **Unit Tests**: Test individual functions in isolation
- **Integration Tests**: Test interaction between modules
- **Mock External Dependencies**: Database operations, file I/O
- **Temporary Directories**: Use pytest fixtures for database tests

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_assembly.py -v

# Run with coverage
python -m pytest --cov=casman

# Run specific test
python -m pytest tests/test_assembly.py::TestAssembly::test_record_connection -v
```

## Database Development

### Database Schema

CAsMan uses SQLite databases with the following structure:

#### Parts Database (`parts.db`)
- **parts**: Core part information
- **part_aliases**: Alternative part names

#### Assembly Database (`assembled_casm.db`)  
- **assembly**: Assembly connection records

### Working with Databases

```python
from casman.database import get_database_path, init_parts_db, init_assembled_db

# Initialize databases
init_parts_db("/path/to/db/dir")
init_assembled_db("/path/to/db/dir")

# Get database paths
parts_db = get_database_path("parts.db", "/path/to/db/dir")
```

## Documentation

### Automatic Generation

Documentation is automatically generated from source code:

```bash
python docs/generate_docs.py
```

### Documentation Standards

- **Module Docstrings**: Describe the module's purpose
- **Function Docstrings**: Use NumPy format with Parameters/Returns sections
- **Type Information**: Included automatically from type annotations
- **Examples**: Include usage examples where helpful

## Release Process

1. **Ensure all tests pass:**
   ```bash
   python -m pytest
   ```

2. **Update documentation:**
   ```bash
   python docs/generate_docs.py
   ```

3. **Update version in setup.py**

4. **Create and merge pull request**

5. **Tag release:**
   ```bash
   git tag v1.x.x
   git push origin v1.x.x
   ```

## Common Development Tasks

### Adding a New CLI Command

1. Add command function to appropriate `*_commands.py` file
2. Import and register in `cli/main.py`
3. Add tests to `tests/test_cli.py`
4. Update documentation

### Adding a New Part Type

1. Update part validation in `parts/validation.py`
2. Add tests for the new type
3. Update configuration if needed
4. Generate new barcodes if required

### Modifying Database Schema

1. Update database initialization functions
2. Create migration script if needed
3. Update all affected queries
4. Test with both new and existing databases

## Troubleshooting

### Common Issues

1. **Import Errors**: Check `__init__.py` exports and Python path
2. **Test Failures**: Verify patch paths after modularization
3. **Database Errors**: Ensure databases are initialized
4. **Type Errors**: Add missing type annotations

### Debug Mode

Run with debug logging:
```bash
CASMAN_DEBUG=1 python -m casman.cli --help
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for your changes
4. Ensure all tests pass
5. Update documentation
6. Submit a pull request

For questions or issues, please open a GitHub issue or contact the development team.
