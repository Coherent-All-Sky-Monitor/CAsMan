
"""
Command-line interface for CAsMan.

This module provides the main entry point for all CAsMan CLI functionality.
The actual command implementations are now modularized in the cli/ subpackage.
"""

from .cli import main

if __name__ == "__main__":
    main()
