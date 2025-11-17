# Command Line Interface

CAsMan provides a comprehensive command-line interface for managing CASM assemblies.

## Usage

```bash

casman [command] [subcommand] [options]

```python

## Available Commands

### casman parts

Manage parts in the database with comprehensive functionality

**Subcommands:**

- `list`: List all parts or filter by type/polarization

- `add`: Add new parts interactively (single type or all types)

- `search`: Search for parts by criteria

- `validate`: Validate parts against database

**Examples:**

```bash

casman parts list                    # List all parts
casman parts add                     # Interactive part addition
casman parts search --type ANTENNA   # Search for antenna parts
casman parts validate                # Validate part database

```python

### casman scan

Interactive barcode scanning and assembly with real-time validation

**Subcommands:**

- `connection`: Start interactive connection scanning with validation

- `disconnection`: Start interactive disconnection scanning

- `connect`: Full interactive part scanning and assembly operations (recommended)

- `disconnect`: Full interactive part disconnection operations (recommended)

**Examples:**

```bash

casman scan connect        # Full interactive scanning workflow
casman scan connection     # Basic connection scanning
casman scan disconnect     # Full interactive disconnection workflow
casman scan disconnection  # Basic disconnection scanning

```python

### casman database

Database management operations with safety features

**Subcommands:**

- `clear`: Safely clear database contents with confirmations

- `print`: Display formatted database tables and records

**Examples:**

```bash

casman database clear                # Clear both databases (with confirmation)
casman database clear --parts        # Clear only parts database
casman database clear --assembled    # Clear only assembly database
casman database print               # Show formatted database contents

```python

**Safety Features:**

- Visual stop sign warnings for destructive operations

- Double "yes" confirmation required for clearing

- Database existence verification

- Graceful error handling

### casman visualize

Visualize assembly chains and connections

**Subcommands:**

- `chains`: Display ASCII visualization of assembly chains

- `summary`: Show assembly summary statistics

- `web`: Launch web-based visualization interface

### casman barcode

Generate barcodes and printable pages for part identification

**Subcommands:**

- `printpages`: Generate printable barcode pages for labeling

**Examples:**

```bash

casman barcode printpages --part-type ANTENNA --start-number 1 --end-number 50

```python

### casman completion

Shell completion setup instructions

**Description:**
Shows instructions for setting up shell completion for bash, zsh, and other shells.

**Examples:**

```bash

casman completion                    # Show completion setup instructions

```python

## Command Structure Overview

```python

casman
├── parts      - Manage parts (list, add, search, validate)
├── scan       - Interactive scanning and assembly
│   ├── stats      - Display assembly statistics
│   ├── connection - Basic connection scanning  
│   └── connect    - Full interactive scanning workflow
├── database   - Database management operations
│   ├── clear      - Safe database clearing with confirmations
│   └── print      - Formatted database display
├── visualize  - Assembly visualization
│   ├── chains     - ASCII chain visualization
│   └── web        - Web-based visualization
├── barcode    - Barcode generation
│   └── printpages - Generate printable pages
└── completion - Shell completion setup

```python