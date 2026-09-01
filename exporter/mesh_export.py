"""
MeSH 2026 CSV and JSON Exporter.
Exports MeSH ontology data to clean, deduplicated CSV/JSON files matching Lexicon target rules.
"""

import csv
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from config.constants import MESH_DESCRIPTOR_FIELDS, OUTPUT_DIR
from utils.logger import export_logger


def export_mesh_csv(data: List[Dict[str, Any]], filepath: Optional[Path] = None) -> Path:
    """
    Export list of mapped MeSH terms into CSV format.
    """
    out_path = filepath or (OUTPUT_DIR / "mesh_2026_ontology_deduplicated.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    export_logger.info(f"Exporting {len(data)} MeSH terms to CSV at {out_path}...")

    # Determine fieldnames from data or default to Descriptor fields
    if data:
        all_fields = list(data[0].keys())
    else:
        all_fields = MESH_DESCRIPTOR_FIELDS

    try:
        f = open(out_path, "w", newline="", encoding="utf-8")
    except PermissionError:
        import time
        ts = int(time.time())
        fallback_path = OUTPUT_DIR / f"{out_path.stem}_{ts}.csv"
        export_logger.warning(f"File '{out_path.name}' locked. Writing to '{fallback_path.name}' instead.")
        out_path = fallback_path
        f = open(out_path, "w", newline="", encoding="utf-8")

    with f:
        writer = csv.DictWriter(f, fieldnames=all_fields)
        writer.writeheader()

        for term in data:
            row = {}
            for field in all_fields:
                if field == "ID" or field == "hasDbXref":
                    val = ""
                else:
                    val = term.get(field, "")

                if isinstance(val, list):
                    clean_items = []
                    for item in val:
                        if item and str(item).strip():
                            parts = [p.strip() for p in re.split(r"\|+", str(item)) if p.strip()]
                            for p in parts:
                                if p not in clean_items:
                                    clean_items.append(p)
                    row[field] = "|".join(clean_items)
                else:
                    s = str(val).strip() if val is not None else ""
                    row[field] = s

            writer.writerow(row)

    export_logger.info(f"MeSH CSV export completed successfully: {out_path}")
    return out_path
