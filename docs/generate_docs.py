#!/usr/bin/env python3
"""
Modern documentation generator for CAsMan.

This script automatically generates comprehensive Markdown documentation
from the Python modules in the casman package using modern Python practices.
"""

import ast
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
import sys

from casman.config.utils import setup_logging

# Configure logging from config
setup_logging()
logger = logging.getLogger(__name__)

# Add the project root to the path so we can import casman
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class FunctionInfo:
    """Information about a function extracted from source code."""
    name: str
    docstring: str
    args: List[str] = field(default_factory=list)
    return_annotation: Optional[str] = None
    is_async: bool = False
    decorators: List[str] = field(default_factory=list)


@dataclass
class ClassInfo:
    """Information about a class extracted from source code."""
    name: str
    docstring: str
    methods: Dict[str, FunctionInfo] = field(default_factory=dict)
    base_classes: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)


@dataclass
class ModuleInfo:
    """Information about a module extracted from source code."""
    name: str
    path: Path
    docstring: str
    functions: Dict[str, FunctionInfo] = field(default_factory=dict)
    classes: Dict[str, ClassInfo] = field(default_factory=dict)
    imports: Set[str] = field(default_factory=set)
    constants: Dict[str, Any] = field(default_factory=dict)


class DocstringParser:
    """Parser for extracting structured information from docstrings."""
    
    SECTION_HEADERS = {
        'parameters', 'params', 'arguments', 'args',
        'returns', 'return', 'yields', 'yield',
        'raises', 'except', 'exceptions',
        'examples', 'example',
        'notes', 'note',
        'see also', 'references', 'ref'
    }
    
    @classmethod
    def parse(cls, docstring: Optional[str]) -> Dict[str, str]:
        """Parse a docstring into structured sections."""
        if not docstring:
            return {"description": "No description available."}
        
        lines = docstring.strip().split('\n')
        sections = {}
        current_section = None
        current_content: List[str] = []
        description_lines: List[str] = []
        
        for line in lines:
            line = line.strip()
            lower_line = line.lower()
            
            # Check if this line starts a new section
            section_found = None
            for header in cls.SECTION_HEADERS:
                if lower_line.startswith(header):
                    section_found = header
                    break
            
            if section_found:
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                elif current_content:
                    description_lines.extend(current_content)
                
                # Start new section
                current_section = section_found
                current_content = []
            elif current_section:
                if line and not line.startswith('---'):
                    current_content.append(line)
            else:
                if line:
                    description_lines.append(line)
        
        # Save final section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content)
        elif current_content:
            description_lines.extend(current_content)
        
        result = {"description": ' '.join(description_lines)}
        result.update(sections)
        return result


class ModuleAnalyzer:
    """Analyzer for extracting information from Python modules."""
    
    def __init__(self):
        self.parser = DocstringParser()
    
    def analyze_file(self, file_path: Path) -> ModuleInfo:
        """Analyze a Python file and extract module information."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            module_name = file_path.stem
            
            module_info = ModuleInfo(
                name=module_name,
                path=file_path,
                docstring=ast.get_docstring(tree) or "No module docstring available."
            )
            
            # Extract module-level information
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not node.name.startswith('_'):  # Skip private functions
                        func_info = self._extract_function_info(node)
                        module_info.functions[node.name] = func_info
                
                elif isinstance(node, ast.AsyncFunctionDef):
                    if not node.name.startswith('_'):
                        func_info = self._extract_function_info(node, is_async=True)
                        module_info.functions[node.name] = func_info
                
                elif isinstance(node, ast.ClassDef):
                    if not node.name.startswith('_'):  # Skip private classes
                        class_info = self._extract_class_info(node)
                        module_info.classes[node.name] = class_info
                
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        module_info.imports.add(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_info.imports.add(node.module)
                
                elif isinstance(node, ast.Assign):
                    # Extract module-level constants
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id.isupper():
                            try:
                                if isinstance(node.value, ast.Constant):
                                    module_info.constants[target.id] = node.value.value
                            except Exception:
                                pass  # Skip complex constants
            
            return module_info
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return ModuleInfo(
                name=file_path.stem,
                path=file_path,
                docstring=f"Error analyzing module: {e}"
            )
    
    def _extract_function_info(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], is_async: bool = False) -> FunctionInfo:
        """Extract information from a function node."""
        args = []
        for arg in node.args.args:
            if arg.arg != 'self':  # Skip self parameter
                if arg.annotation:
                    args.append(f"{arg.arg}: {ast.unparse(arg.annotation)}")
                else:
                    args.append(arg.arg)
        
        # Handle *args and **kwargs
        if node.args.vararg:
            vararg = f"*{node.args.vararg.arg}"
            if node.args.vararg.annotation:
                vararg += f": {ast.unparse(node.args.vararg.annotation)}"
            args.append(vararg)
        
        if node.args.kwarg:
            kwarg = f"**{node.args.kwarg.arg}"
            if node.args.kwarg.annotation:
                kwarg += f": {ast.unparse(node.args.kwarg.annotation)}"
            args.append(kwarg)
        
        return_annotation = None
        if node.returns:
            return_annotation = ast.unparse(node.returns)
        
        decorators = []
        for decorator in node.decorator_list:
            try:
                decorators.append(ast.unparse(decorator))
            except Exception:
                decorators.append(str(decorator))
        
        return FunctionInfo(
            name=node.name,
            docstring=ast.get_docstring(node) or "No docstring available.",
            args=args,
            return_annotation=return_annotation,
            is_async=is_async,
            decorators=decorators
        )
    
    def _extract_class_info(self, node: ast.ClassDef) -> ClassInfo:
        """Extract information from a class node."""
        base_classes = []
        for base in node.bases:
            try:
                base_classes.append(ast.unparse(base))
            except Exception:
                base_classes.append(str(base))
        
        decorators = []
        for decorator in node.decorator_list:
            try:
                decorators.append(ast.unparse(decorator))
            except Exception:
                decorators.append(str(decorator))
        
        class_info = ClassInfo(
            name=node.name,
            docstring=ast.get_docstring(node) or "No docstring available.",
            base_classes=base_classes,
            decorators=decorators
        )
        
        # Extract methods
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not item.name.startswith('_') or item.name in ['__init__', '__str__', '__repr__']:
                    is_async = isinstance(item, ast.AsyncFunctionDef)
                    method_info = self._extract_function_info(item, is_async)
                    class_info.methods[item.name] = method_info
        
        return class_info


class MarkdownGenerator:
    """Generator for creating Markdown documentation."""
    
    def __init__(self):
        self.parser = DocstringParser()
    
    def generate_module_docs(self, module_info: ModuleInfo) -> str:
        """Generate markdown documentation for a module."""
        lines = []
        
        # Module header
        lines.extend([
            f"# {module_info.name.title()} Module",
            "",
            module_info.docstring,
            ""
        ])
        
        # Constants section
        if module_info.constants:
            lines.extend(["## Constants", ""])
            for name, value in module_info.constants.items():
                lines.extend([
                    f"### {name}",
                    "",
                    f"**Value:** `{repr(value)}`",
                    ""
                ])
        
        # Functions section
        if module_info.functions:
            lines.extend(["## Functions", ""])
            for func_info in module_info.functions.values():
                lines.extend(self._generate_function_docs(func_info))
        
        # Classes section
        if module_info.classes:
            lines.extend(["## Classes", ""])
            for class_info in module_info.classes.values():
                lines.extend(self._generate_class_docs(class_info))
        
        return '\n'.join(lines)
    
    def _generate_function_docs(self, func_info: FunctionInfo) -> List[str]:
        """Generate documentation for a function."""
        lines = []
        
        # Function header
        async_prefix = "async " if func_info.is_async else ""
        signature = f"{async_prefix}{func_info.name}({', '.join(func_info.args)})"
        if func_info.return_annotation:
            signature += f" -> {func_info.return_annotation}"
        
        lines.extend([
            f"### {func_info.name}",
            ""
        ])
        
        # Decorators
        if func_info.decorators:
            for decorator in func_info.decorators:
                lines.append(f"*@{decorator}*")
            lines.append("")
        
        lines.extend([
            f"**Signature:** `{signature}`",
            ""
        ])
        
        # Parse and add docstring sections
        docstring_info = self.parser.parse(func_info.docstring)
        lines.extend([docstring_info["description"], ""])
        
        # Parameters
        if "parameters" in docstring_info or "params" in docstring_info:
            params = docstring_info.get("parameters") or docstring_info.get("params")
            lines.extend(["**Parameters:**", "", params, ""])
        
        # Returns
        if "returns" in docstring_info or "return" in docstring_info:
            returns = docstring_info.get("returns") or docstring_info.get("return")
            lines.extend(["**Returns:**", "", returns, ""])
        
        # Raises
        if "raises" in docstring_info or "exceptions" in docstring_info:
            raises = docstring_info.get("raises") or docstring_info.get("exceptions")
            lines.extend(["**Raises:**", "", raises, ""])
        
        # Examples
        if "examples" in docstring_info or "example" in docstring_info:
            examples = docstring_info.get("examples") or docstring_info.get("example")
            lines.extend(["**Examples:**", "", "```python", examples, "```", ""])
        
        lines.extend(["---", ""])
        return lines
    
    def _generate_class_docs(self, class_info: ClassInfo) -> List[str]:
        """Generate documentation for a class."""
        lines = []
        
        # Class header
        class_signature = class_info.name
        if class_info.base_classes:
            class_signature += f"({', '.join(class_info.base_classes)})"
        
        lines.extend([
            f"### {class_info.name}",
            ""
        ])
        
        # Decorators
        if class_info.decorators:
            for decorator in class_info.decorators:
                lines.append(f"*@{decorator}*")
            lines.append("")
        
        lines.extend([
            f"**Class:** `{class_signature}`",
            "",
            class_info.docstring,
            ""
        ])
        
        # Methods
        if class_info.methods:
            lines.extend(["#### Methods", ""])
            for method_info in class_info.methods.values():
                method_lines = self._generate_function_docs(method_info)
                # Adjust header level for methods
                method_lines = [line.replace("### ", "##### ") if line.startswith("### ") else line for line in method_lines]
                lines.extend(method_lines)
        
        lines.extend(["---", ""])
        return lines


class DocumentationGenerator:
    """Main documentation generator coordinating all components."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.casman_path = project_root / "casman"
        self.docs_path = project_root / "docs" / "auto-generated"
        self.analyzer = ModuleAnalyzer()
        self.markdown_generator = MarkdownGenerator()
        
        # Ensure auto-generated docs directory exists
        self.docs_path.mkdir(parents=True, exist_ok=True)
    
    def generate_all_docs(self) -> None:
        """Generate documentation for all modules."""
        logger.info("Starting documentation generation...")
        
        # Generate package documentation
        packages = ['assembly', 'cli', 'config', 'database', 'parts', 'visualization']
        for package_name in packages:
            self._generate_package_docs(package_name)
        
        # Generate API reference
        self._generate_api_reference()
        
        # Generate CLI documentation
        self._generate_cli_docs()
        
        logger.info("Documentation generation completed!")
    
    def _generate_package_docs(self, package_name: str) -> None:
        """Generate documentation for a specific package."""
        package_path = self.casman_path / package_name
        
        if not package_path.exists():
            logger.warning(f"Package {package_name} not found at {package_path}")
            return
        
        if not package_path.is_dir():
            # It's a module file
            if package_path.with_suffix('.py').exists():
                module_info = self.analyzer.analyze_file(package_path.with_suffix('.py'))
                docs = self.markdown_generator.generate_module_docs(module_info)
                
                output_file = self.docs_path / f"{package_name}.md"
                self._write_docs(output_file, docs)
                logger.info(f"✓ Generated {package_name}.md")
            else:
                logger.warning(f"✗ Module {package_name}.py not found")
            return
        
        # It's a package directory
        all_modules = []
        
        # Analyze __init__.py first
        init_file = package_path / "__init__.py"
        if init_file.exists():
            module_info = self.analyzer.analyze_file(init_file)
            all_modules.append(module_info)
        
        # Analyze all Python files in the package
        for py_file in package_path.glob("*.py"):
            if py_file.name != "__init__.py":
                module_info = self.analyzer.analyze_file(py_file)
                all_modules.append(module_info)
        
        # Generate combined documentation
        docs = self._generate_package_overview(package_name, all_modules)
        
        output_file = self.docs_path / f"{package_name}.md"
        self._write_docs(output_file, docs)
        logger.info(f"✓ Generated {package_name}.md (package)")
    
    def _generate_package_overview(self, package_name: str, modules: List[ModuleInfo]) -> str:
        """Generate overview documentation for a package."""
        lines = []
        
        # Package header
        lines.extend([
            f"# {package_name.title()} Package",
            "",
            f"Documentation for the `casman.{package_name}` package.",
            ""
        ])
        
        # Package overview
        init_module = next((m for m in modules if m.name == "__init__"), None)
        if init_module and init_module.docstring != "No module docstring available.":
            lines.extend([
                "## Overview",
                "",
                init_module.docstring,
                ""
            ])
        
        # Module listing
        non_init_modules = [m for m in modules if m.name != "__init__"]
        if non_init_modules:
            lines.extend([
                "## Modules",
                ""
            ])
            
            for module in non_init_modules:
                lines.extend([
                    f"### {module.name}",
                    "",
                    module.docstring,
                    ""
                ])
                
                # Add function/class summaries
                if module.functions:
                    lines.append("**Functions:**")
                    for func_name, func_info in module.functions.items():
                        lines.append(f"- `{func_name}()` - {func_info.docstring.split('.')[0]}")
                    lines.append("")
                
                if module.classes:
                    lines.append("**Classes:**")
                    for class_name, class_info in module.classes.items():
                        lines.append(f"- `{class_name}` - {class_info.docstring.split('.')[0]}")
                    lines.append("")
        
        # Detailed documentation for each module
        for module in modules:
            if module.functions or module.classes:
                lines.extend([
                    f"## {module.name.title()} Module Details",
                    ""
                ])
                module_docs = self.markdown_generator.generate_module_docs(module)
                # Remove the module header since we already have it
                module_lines = module_docs.split('\n')[4:]  # Skip first 4 lines
                lines.extend(module_lines)
        
        return '\n'.join(lines)
    
    def _generate_api_reference(self) -> None:
        """Generate comprehensive API reference."""
        lines = [
            "# CAsMan API Reference",
            "",
            "This document provides a comprehensive reference for all CAsMan modules and functions.",
            "",
            "## Package Overview",
            "",
            "CAsMan is organized into focused, modular packages:",
            "",
        ]
        
        # Add package summaries
        packages = {
            'assembly': 'Assembly management and connection tracking',
            'cli': 'Command-line interface',
            'config': 'Configuration management',
            'database': 'Database operations',
            'parts': 'Part management and validation',
            'visualization': 'ASCII visualization'
        }
        
        lines.extend([
            "### Core Packages",
            "",
            "| Package | Purpose |",
            "|---------|---------|"
        ])
        
        for package, description in packages.items():
            package_path = self.casman_path / package
            if package_path.exists():
                lines.append(f"| `casman.{package}` | {description} |")
        
        lines.extend(["", "## Import Guide", ""])
        
        # Add import examples for each package
        for package in packages:
            package_path = self.casman_path / package
            if package_path.exists() and package_path.is_dir():
                lines.extend([
                    f"### {package.title()} Package",
                    "",
                    "```python",
                    "# Import specific functions",
                    f"from casman.{package} import function_name",
                    "",
                    "# Import entire package",
                    f"from casman import {package}",
                    "```",
                    ""
                ])
        
        output_file = self.docs_path / "api_reference.md"
        self._write_docs(output_file, '\n'.join(lines))
        logger.info("✓ Generated api_reference.md")
    
    def _generate_cli_docs(self) -> None:
        """Generate CLI documentation."""
        lines = [
            "# Command Line Interface",
            "",
            "CAsMan provides a comprehensive command-line interface for managing CASM assemblies.",
            "",
            "## Usage",
            "",
            "```bash",
            "casman [command] [subcommand] [options]",
            "```",
            "",
            "## Available Commands",
            ""
        ]
        
        # CLI commands (this could be extracted from actual CLI code)
        commands: Dict[str, Dict[str, Union[str, Dict[str, str]]]] = {
            "parts": {
                "description": "Manage parts in the database",
                "subcommands": {
                    "list": "List all parts or filter by type/polarization",
                    "add": "Add new parts interactively"
                }
            },
            "scan": {
                "description": "Interactive barcode scanning and assembly",
                "subcommands": {
                    "connection": "Interactive assembly connection scanning",
                    "stats": "Display assembly statistics"
                }
            },
            "visualize": {
                "description": "Visualize assembly chains and connections",
                "subcommands": {
                    "chains": "Display ASCII visualization of assembly chains",
                    "summary": "Show assembly summary statistics",
                    "web": "Launch web-based visualization interface"
                }
            },
            "barcode": {
                "description": "Generate barcodes and printable pages",
                "subcommands": {
                    "printpages": "Generate printable barcode pages for part types"
                }
            }
        }
        
        for cmd, info in commands.items():
            description = info["description"]
            if isinstance(description, str):
                lines.extend([
                    f"### casman {cmd}",
                    "",
                    description,
                    ""
                ])
            
            subcommands = info.get("subcommands")
            if subcommands and isinstance(subcommands, dict):
                lines.extend(["**Subcommands:**", ""])
                for subcmd, desc in subcommands.items():
                    lines.append(f"- `{subcmd}`: {desc}")
                lines.append("")
        
        output_file = self.docs_path / "cli.md"
        self._write_docs(output_file, '\n'.join(lines))
        logger.info("✓ Generated cli.md")
    
    def _write_docs(self, output_file: Path, content: str) -> None:
        """Write documentation content to a file."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
        except OSError as e:
            logger.error("Error writing %s: %s", output_file, e)


def main() -> None:
    """Main entry point for the documentation generator."""
    try:
        generator = DocumentationGenerator(PROJECT_ROOT)
        generator.generate_all_docs()
        
        print("\nAuto-generated documentation created in", PROJECT_ROOT / "docs" / "auto-generated")
        print("Files created:")
        docs_path = PROJECT_ROOT / "docs" / "auto-generated"
        for md_file in sorted(docs_path.glob("*.md")):
            print(f"  - {md_file.name}")
            
    except (OSError, ImportError, AttributeError) as e:
        logger.error("Documentation generation failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
