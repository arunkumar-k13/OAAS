"""
CSV Exporter for OAAS Ontology terms with graceful file locking fallback.
"""

import csv
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from config.constants import OAAS_SCHEMA_FIELDS
from config.settings import settings
from utils.logger import export_logger


def export_csv(data: List[Dict[str, Any]], filepath: Optional[Path] = None) -> Path:
    """
    Export list of ontology term dictionaries into a CSV file with pipe-delimited list fields.

    Args:
        data: List of mapped OAAS ontology terms.
        filepath: Target output Path. Defaults to `output/icd11_ontology.csv`.

    Returns:
        Path to generated CSV file.
    """
    out_path = filepath or (settings.output_dir / "icd11_ontology.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    export_logger.info(f"Exporting {len(data)} terms to CSV at {out_path}...")
    fieldnames = OAAS_SCHEMA_FIELDS

    try:
        f = open(out_path, "w", newline="", encoding="utf-8")
    except PermissionError:
        import time
        ts = int(time.time())
        fallback_path = settings.output_dir / f"{out_path.stem}_{ts}.csv"
        export_logger.warning(
            f"File '{out_path.name}' is currently locked by Excel or another application. "
            f"Saving output to '{fallback_path.name}' instead."
        )
        out_path = fallback_path
        f = open(out_path, "w", newline="", encoding="utf-8")

    with f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for term in data:
            row = {}
            for field in fieldnames:
                # ID field is left blank for Lexicon internal ID auto-generation upon import
                if field == "ID":
                    val = ""
                # hasDbXref cleared for now per user request
                elif field == "hasDbXref":
                    val = ""
                # Write the browser-openable URL in place of the raw API URI (enforcing 2026-01 release)
                elif field == "URI":
                    val = term.get("BrowserUrl") or term.get("URI", "")
                    if "2024-01" in str(val):
                        val = str(val).replace("2024-01", "2026-01")
                else:
                    val = term.get(field, "")

                if isinstance(val, list):
                    clean_items = []
                    for item in val:
                        if item and str(item).strip():
                            # Handle raw WHO text strings that contain embedded || or | separators
                            sub_items = [sub.strip() for sub in re.split(r"\|+", str(item)) if sub.strip()]
                            for s in sub_items:
                                s = re.sub(r"^\s*!markdown\s*", "", s, flags=re.IGNORECASE)
                                if s and s not in clean_items:
                                    clean_items.append(s)
                    row[field] = "|".join(clean_items)
                elif isinstance(val, bool):
                    row[field] = str(val)
                else:
                    s = str(val).strip() if val is not None else ""
                    s = re.sub(r"^\s*!markdown\s*", "", s, flags=re.IGNORECASE)
                    row[field] = s
            writer.writerow(row)


    export_logger.info(f"CSV export completed: {out_path}")
    return out_path
