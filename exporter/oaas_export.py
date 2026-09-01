"""
OAAS Lexicon Import Format Exporter.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from config.settings import settings
from utils.logger import export_logger


def export_oaas_format(data: List[Dict[str, Any]], filepath: Optional[Path] = None) -> Path:
    """
    Export ontology terms wrapped in standard OAAS Lexicon Import JSON format.

    Args:
        data: List of mapped OAAS ontology terms.
        filepath: Target output Path. Defaults to `output/oaas_lexicon_import.json`.

    Returns:
        Path to generated OAAS import JSON file.
    """
    out_path = filepath or (settings.output_dir / "oaas_lexicon_import.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    export_logger.info(f"Exporting {len(data)} terms to OAAS Lexicon Import JSON at {out_path}...")

    payload = {
        "lexicon_name": f"WHO ICD-11 MMS Medical Ontology ({settings.icd11_release_id})",
        "ontology_version": settings.icd11_release_id,
        "language": settings.icd11_language,
        "total_terms": len(data),
        "terms": data,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    export_logger.info(f"OAAS Lexicon export completed: {out_path}")
    return out_path
