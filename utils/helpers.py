"""
General helper utilities for string formatting, JSON manipulation, and data transformation.
"""

from typing import Any, Dict, List, Optional
import json


def sanitize_string(text: Optional[str]) -> str:
    """Trim whitespace and normalize string value."""
    if not text:
        return ""
    return text.strip()


def ensure_list(value: Any) -> List[Any]:
    """Wrap single item in list if not already a list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]
