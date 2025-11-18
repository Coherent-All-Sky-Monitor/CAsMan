"""
Part type configuration utilities for CAsMan.
"""

import ast
from typing import Dict, Tuple

from casman.config import get_config


def load_part_types() -> Dict[int, Tuple[str, str]]:
    """
    Load part types from config.yaml, parsing keys as int and values as tuple.
    Returns
    -------
    Dict[int, Tuple[str, str]]
        Mapping from integer key to (full_name, abbreviation).
    """
    part_types_raw = get_config("PART_TYPES")
    if part_types_raw is None:
        raise RuntimeError("PART_TYPES not defined in config.yaml")
    if isinstance(part_types_raw, str):
        part_types = ast.literal_eval(part_types_raw)
    else:
        part_types = part_types_raw
    return {int(k): tuple(v) for k, v in part_types.items()}
