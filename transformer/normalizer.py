"""
Text, label, and list normalization utilities for ICD-11 raw JSON values.
"""

from typing import Any, List, Optional, Union
import re
from html import unescape


def normalize_text(text: Optional[str]) -> str:
    """
    Clean, strip whitespace, unescape HTML entities, and normalize string text.
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)

    # Unescape HTML entities (e.g. &amp;)
    cleaned = unescape(text)
    # Strip any leading WHO !markdown tags (case-insensitive, optional leading whitespace)
    cleaned = re.sub(r"^\s*!markdown\s*", "", cleaned, flags=re.IGNORECASE)
    # Strip any embedded !markdown tags
    cleaned = re.sub(r"!markdown\s*", "", cleaned, flags=re.IGNORECASE)
    # Replace multiple spaces/newlines with single space
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def extract_label_value(val: Any) -> str:
    """
    Extract string label from WHO multi-language dict or nested dict/string.
    e.g., {"label": {"@value": "Cholera", "@language": "en"}} -> "Cholera"
    """
    if not val:
        return ""
    if isinstance(val, str):
        return normalize_text(val)
    if isinstance(val, dict):
        # Handle nested dicts like {"label": {"@value": "Asiatic cholera"}}
        label = val.get("label") or val.get("@value") or val.get("value")
        if isinstance(label, (dict, str)):
            return extract_label_value(label)
        return normalize_text(str(val))
    return normalize_text(str(val))


def normalize_list(items: Any) -> List[str]:
    """
    Normalize arbitrary input (strings, dicts, lists) into a clean list of unique strings.
    """
    if not items:
        return []

    result = []
    seen = set()

    if not isinstance(items, list):
        items = [items]

    for item in items:
        label = extract_label_value(item)
        if label and label not in seen:
            seen.add(label)
            result.append(label)

    return result
