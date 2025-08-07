#!/usr/bin/env python3
"""
Documentation generator for CAsMan.

This script automatically generates comprehensive Markdown documentation
from the Python modules in the casman package.
"""

import ast
import inspect
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add the project root to the path so we can import casman
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import casman
    from casman import (assembly, barcode_utils, cli, config, database, parts,
                        visualization)
except ImportError as e:
    print(f"Warning: Could not import casman modules: {e}")
    print("Documentation will be generated from source analysis only.")
    casman = None


def extract_docstring_info(docstring: Optional[str]) -> Dict[str, str]:
    """Extract structured information from a docstring."""
    if not docstring:
        return {"description": "No description available."}

    lines = docstring.strip().split('\n')
    description_lines = []
    current_section = None
    sections = {}

    for line in lines:
        line = line.strip()
        if line in ['Parameters', 'Returns', 'Raises', 'Examples', 'Notes']:
            current_section = line.lower()
            sections[current_section] = []
        elif current_section and line.startswith('---'):
            continue  # Skip separator lines
        elif current_section:
            if line:
                sections[current_section].append(line)
        else:
            if line:
                description_lines.append(line)

    result = {"description": ' '.join(description_lines)}
    for section, content in sections.items():
        result[section] = '\n'.join(content)

    return result


def analyze_module_source(module_path: Path) -> Dict[str, Any]:
    """Analyze a Python module's source code to extract functions and classes."""
    try:
        with open(module_path, 'r', encoding='utf-8') as f:
            source = f.read()

        tree = ast.parse(source)

        module_info = {
            "docstring": ast.get_docstring(tree) or "No module docstring available.",
            "functions": {},
            "classes": {}}

        for node in ast.walk(tree):
            if isinstance(
                    node,
                    ast.FunctionDef) and not node.name.startswith('_'):
                func_info = {
                    "docstring": ast.get_docstring(node) or "No docstring available.",
                    "args": [
                        arg.arg for arg in node.args.args],
                    "returns": None}

                # Try to extract return type annotation
                if node.returns:
                    if isinstance(node.returns, ast.Name):
                        func_info["returns"] = node.returns.id
                    elif isinstance(node.returns, ast.Constant):
                        func_info["returns"] = str(node.returns.value)

                module_info["functions"][node.name] = func_info

            elif isinstance(node, ast.ClassDef) and not node.name.startswith('_'):
                class_info = {"docstring": ast.get_docstring(
                    node) or "No docstring available.", "methods": {}}

                for item in node.body:
                    if isinstance(
                            item, ast.FunctionDef) and not item.name.startswith('_'):
                        method_info = {
                            "docstring": ast.get_docstring(item) or "No docstring available.", "args": [
                                arg.arg for arg in item.args.args if arg.arg != 'self']}
                        class_info["methods"][item.name] = method_info

                module_info["classes"][node.name] = class_info

        return module_info

    except Exception as e:
        return {
            "docstring": f"Error analyzing module: {e}",
            "functions": {},
            "classes": {}
        }


def generate_module_docs(module_name: str, module_path: Path) -> str:
    """Generate markdown documentation for a single module."""
    module_info = analyze_module_source(module_path)

    md_content = [
        f"# {module_name.title()} Module",
        "",
        module_info["docstring"],
        "",
    ]

    # Add functions documentation
    if module_info["functions"]:
        md_content.extend([
            "## Functions",
            ""
        ])

        for func_name, func_info in module_info["functions"].items():
            docstring_info = extract_docstring_info(func_info["docstring"])

            md_content.extend([
                f"### {func_name}",
                "",
                f"**Signature:** `{func_name}({', '.join(func_info['args'])})`",
                "",
                docstring_info["description"],
                ""
            ])

            if "parameters" in docstring_info:
                md_content.extend([
                    "**Parameters:**",
                    "",
                    docstring_info["parameters"],
                    ""
                ])

            if "returns" in docstring_info:
                md_content.extend([
                    "**Returns:**",
                    "",
                    docstring_info["returns"],
                    ""
                ])

            md_content.append("---")
            md_content.append("")

    # Add classes documentation
    if module_info["classes"]:
        md_content.extend([
            "## Classes",
            ""
        ])

        for class_name, class_info in module_info["classes"].items():
            md_content.extend([
                f"### {class_name}",
                "",
                class_info["docstring"],
                ""
            ])

            if class_info["methods"]:
                md_content.extend([
                    "#### Methods",
                    ""
                ])

                for method_name, method_info in class_info["methods"].items():
                    md_content.extend([
                        f"##### {method_name}",
                        "",
                        f"**Signature:** `{method_name}({', '.join(method_info['args'])})`",
                        "",
                        method_info["docstring"],
                        ""
                    ])

            md_content.append("---")
            md_content.append("")

    return '\n'.join(md_content)


def generate_cli_docs() -> str:
    """Generate documentation for CLI commands."""
    md_content = [
        "# Command Line Interface",
        "",
        "CAsMan provides a comprehensive command-line interface for managing CASM assemblies.",
        "",
        "## Available Commands",
        "",
    ]

    # CLI command documentation
    commands = {
        "parts": {
            "description": "Manage parts in the database",
            "subcommands": {
                "list": "List all parts or filter by type/polarization",
                "add": "Add new parts interactively"
            }
        },
        "scan": {
            "description": "Scan and manage parts using barcode scanning",
            "subcommands": {
                "stats": "Show assembly statistics",
                "interactive": "Interactive scanning mode (removed)"
            }
        },
        "visualize": {
            "description": "Visualize assembly chains",
            "subcommands": {
                "chains": "Display ASCII visualization of assembly chains"
            }
        },
        "barcode": {
            "description": "Generate barcodes and printable pages",
            "subcommands": {
                "generate": "Generate individual barcodes",
                "printpages": "Generate printable barcode pages"
            }
        },
        "assemble": {
            "description": "Record assembly connections (streamlined)",
            "subcommands": {
                "connect": "Connect two parts with validation and recording"
            }
        }
    }

    for cmd, info in commands.items():
        md_content.extend([
            f"### casman {cmd}",
            "",
            info["description"],
            ""
        ])

        if "subcommands" in info:
            md_content.extend([
                "**Subcommands:**",
                ""
            ])
            for subcmd, desc in info["subcommands"].items():
                md_content.append(f"- `{subcmd}`: {desc}")
            md_content.append("")

        md_content.extend([
            f"**Usage:** `casman {cmd} --help` for detailed options",
            "",
            "---",
            ""
        ])

    return '\n'.join(md_content)


def generate_overview_docs() -> str:
    """Generate overview documentation."""
    return """# CAsMan - CASM Assembly Manager

CAsMan is a comprehensive Python package for managing Coherent All-Sky Monitor (CASM) assembly operations. It provides tools for part management, barcode generation, assembly tracking, and visualization.

## Features

- **Part Management**: Track and manage electronic parts with barcode identification
- **Assembly Tracking**: Record connections between parts with timestamps
- **Visualization**: ASCII and web-based visualization of assembly chains
- **Barcode Generation**: Create and print barcodes for part identification
- **Database Management**: SQLite-based storage for parts and assembly data
- **Command Line Interface**: Comprehensive CLI tools for all operations

## Quick Start

1. **Install the package:**
   ```bash
   pip install -e .
   ```

2. **Initialize databases:**
   ```bash
   casman parts list  # This will create necessary databases
   ```

3. **Add parts:**
   ```bash
   casman parts add
   ```

4. **Generate barcodes:**
   ```bash
   casman barcode printpages --part-type ANTENNA --start-number 1 --end-number 10
   ```

5. **Record assembly connections:**
   ```bash
   casman assemble connect --part1 ANT-P1-00001 --part1-type ANTENNA --part2 LNA-P1-00001 --part2-type LNA --polarization P1
   ```

6. **Visualize assembly chains:**
   ```bash
   casman visualize chains
   ```

## Project Structure

- `casman/`: Main Python package
  - `assembly.py`: Assembly connection recording and management
  - `barcode_utils.py`: Barcode generation and printing utilities
  - `cli.py`: Command-line interface implementation
  - `config.py`: Configuration management
  - `database.py`: Database initialization and utilities
  - `parts.py`: Part management functions
  - `visualization.py`: ASCII chain visualization
- `scripts/`: Standalone utility scripts
  - `visualize_analog_chains_web.py`: Web-based chain visualization
- `database/`: SQLite database files
- `barcodes/`: Generated barcode images
- `tests/`: Unit tests

## Configuration

Configuration is managed through `config.yaml` in the project root. Key settings include:

- Database paths
- Part types and abbreviations
- SNAP/FENG mappings
- Default polarizations

## Database Schema

### Parts Database (`parts.db`)
- `parts` table: Stores part information including number, type, polarization, and timestamps

### Assembly Database (`assembled_casm.db`)
- `assembly` table: Records connections between parts with scan timestamps

## Development

To set up for development:

1. Clone the repository
2. Install in development mode: `pip install -e .`
3. Run tests: `python -m pytest tests/`
4. Generate documentation: `python docs/generate_docs.py`

## License

This project is part of the Coherent All-Sky Monitor project.
"""


def generate_package_docs(package_name: str, package_path: Path) -> str:
    """Generate markdown documentation for a package with submodules."""
    init_file = package_path / "__init__.py"

    # Get main package info from __init__.py
    package_info = analyze_module_source(init_file)

    md_content = [
        f"# {package_name.title()} Package",
        "",
        package_info["docstring"],
        "",
    ]

    # Add exports from __init__.py
    if package_info["functions"]:
        md_content.extend([
            "## Functions",
            "",
            "*The following functions are available when importing from this package:*",
            ""
        ])

        for func_name, func_info in package_info["functions"].items():
            docstring_info = extract_docstring_info(func_info["docstring"])

            md_content.extend([
                f"### {func_name}",
                "",
                f"**Signature:** `{func_name}{func_info['signature']}`",
                "",
                docstring_info.get("description", "No description available."),
                "",
            ])

            if docstring_info.get("parameters"):
                md_content.extend([
                    "**Parameters:**",
                    "",
                    docstring_info["parameters"],
                    ""
                ])

            if docstring_info.get("returns"):
                md_content.extend([
                    "**Returns:**",
                    "",
                    docstring_info["returns"],
                    ""
                ])

            md_content.append("---")
            md_content.append("")

    # Document submodules
    submodules = []
    for item in package_path.iterdir():
        if item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
            submodules.append(item.stem)

    if submodules:
        md_content.extend([
            "## Submodules",
            "",
            "This package is organized into the following submodules:",
            ""
        ])

        for submodule in sorted(submodules):
            submodule_path = package_path / f"{submodule}.py"
            submodule_info = analyze_module_source(submodule_path)

            md_content.extend([
                f"### {submodule}",
                "",
                submodule_info["docstring"] or f"Functions related to {submodule} functionality.",
                ""
            ])

            # List functions in submodule
            if submodule_info["functions"]:
                func_names = list(submodule_info["functions"].keys())
                md_content.extend([
                    "**Functions:**",
                    ""
                ])
                for func_name in func_names:
                    md_content.append(f"- `{func_name}()`")
                md_content.append("")

    return "\n".join(md_content)


def main():
    """Generate all documentation files."""
    docs_dir = Path(__file__).parent
    casman_dir = project_root / "casman"

    print("Generating CAsMan documentation...")

    # Generate overview
    overview_content = generate_overview_docs()
    (docs_dir / "README.md").write_text(overview_content, encoding='utf-8')
    print("✓ Generated README.md")

    # Generate CLI documentation
    cli_content = generate_cli_docs()
    (docs_dir / "cli.md").write_text(cli_content, encoding='utf-8')
    print("✓ Generated cli.md")

    # Generate module documentation
    modules = [
        "assembly", "barcode_utils", "cli", "config",
        "database", "parts", "visualization"
    ]

    for module_name in modules:
        module_path = casman_dir / f"{module_name}.py"
        package_path = casman_dir / module_name

        if module_path.exists():
            module_content = generate_module_docs(module_name, module_path)
            (docs_dir /
             f"{module_name}.md").write_text(module_content, encoding='utf-8')
            print(f"✓ Generated {module_name}.md")
        elif package_path.is_dir() and (package_path / "__init__.py").exists():
            # Handle package structure
            module_content = generate_package_docs(module_name, package_path)
            (docs_dir /
             f"{module_name}.md").write_text(module_content, encoding='utf-8')
            print(f"✓ Generated {module_name}.md (package)")
        else:
            print(f"✗ Module {module_name}.py not found")

    # Generate API index
    api_index = [
        "# API Documentation",
        "",
        "This section contains detailed documentation for all CAsMan modules.",
        "",
        "## Modules",
        ""
    ]

    for module_name in modules:
        if (docs_dir / f"{module_name}.md").exists():
            api_index.append(f"- [{module_name.title()}]({module_name}.md)")

    api_index.extend([
        "",
        "## Command Line Interface",
        "",
        "- [CLI Commands](cli.md)",
        ""
    ])

    (docs_dir / "api.md").write_text('\n'.join(api_index), encoding='utf-8')
    print("✓ Generated api.md")

    print(f"\nDocumentation generated in {docs_dir}")
    print("Files created:")
    for md_file in sorted(docs_dir.glob("*.md")):
        print(f"  - {md_file.name}")


if __name__ == "__main__":
    main()
