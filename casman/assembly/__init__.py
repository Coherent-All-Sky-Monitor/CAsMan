"""
Assembly management functionality for CAsMan.

This module provides functionality for recording and retrieving assembly connections,
building connection chains, and interactive assembly scanning.
"""

# Import logger for backward compatibility with tests
import logging

from .chains import build_connection_chains, print_assembly_chains
# Import all functions from submodules
from .connections import record_assembly_connection
from .data import get_assembly_connections, get_assembly_stats
from .interactive import scan_and_assemble_interactive

# Create logger for backward compatibility with tests
logger = logging.getLogger(__name__)

__all__ = [
    'record_assembly_connection',
    'get_assembly_connections',
    'get_assembly_stats',
    'build_connection_chains',
    'print_assembly_chains',
    'scan_and_assemble_interactive',
    'logger',  # Export logger for test compatibility
]
