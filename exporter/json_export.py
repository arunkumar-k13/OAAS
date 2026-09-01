"""
JSON Exporter for OAAS Ontology terms.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from config.settings import settings
from utils.logger import export_logger


def export_json(data: List[Dict[str, Any]], filepath: Optional[Path] = None) -> Path:
    """
    Export list of ontology term dictionaries into a pretty-printed JSON file.

    Args:
        data: List of mapped OAAS ontology terms.
        filepath: Target output Path. Defaults to `output/icd11_ontology.json`.

    Returns:
        Path to generated JSON file.
    """
    out_path = filepath or (settings.output_dir / "icd11_ontology.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    export_logger.info(f"Exporting {len(data)} terms to JSON at {out_path}...")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    export_logger.info(f"JSON export completed: {out_path}")
    return out_path
