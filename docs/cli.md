# Command Line Interface

CAsMan provides a comprehensive command-line interface for managing CASM assemblies.

## Usage

```bash
casman [command] [subcommand] [options]
```

## Available Commands

### casman parts

Manage parts in the database

**Subcommands:**

- `list`: List all parts or filter by type/polarization
- `add`: Add new parts interactively

### casman scan

Interactive barcode scanning and assembly

**Subcommands:**

- `connection`: Interactive assembly connection scanning
- `stats`: Display assembly statistics

### casman visualize

Visualize assembly chains and connections

**Subcommands:**

- `chains`: Display ASCII visualization of assembly chains
- `summary`: Show assembly summary statistics
- `web`: Launch web-based visualization interface

### casman barcode

Generate barcodes and printable pages

**Subcommands:**

- `printpages`: Generate printable barcode pages for part types
