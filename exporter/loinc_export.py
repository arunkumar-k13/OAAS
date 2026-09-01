"""
LOINC 2026 CSV and Multi-Sheet Excel Exporter.
Exports LOINC ontology data to clean, deduplicated CSV/Excel files matching Lexicon target rules.
"""

import csv
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from config.constants import LOINC_FIELDS, OUTPUT_DIR
from utils.logger import export_logger


def export_loinc_csv(data: List[Dict[str, Any]], filepath: Optional[Path] = None) -> Path:
    """
    Export list of mapped LOINC terms into CSV format.
    Applies Lexicon rules: empty ID/hasDbXref, pipe-separated list values.
    """
    out_path = filepath or (OUTPUT_DIR / "loinc_2026_ontology.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    export_logger.info(f"Exporting {len(data)} LOINC terms to CSV at {out_path}...")

    # Use LOINC_FIELDS as canonical column order
    all_fields = LOINC_FIELDS

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

    export_logger.info(f"LOINC CSV export completed successfully: {out_path}")
    return out_path


def export_loinc_excel(data: List[Dict[str, Any]], filepath: Optional[Path] = None) -> Path:
    """
    Export LOINC terms to a Multi-Sheet Excel workbook.
    Sheets: LOINC Codes, Term Types, Relation Mapping Rules.
    """
    try:
        import openpyxl
    except ImportError:
        export_logger.error("openpyxl is required for Excel export. Install: pip install openpyxl")
        raise

    out_path = filepath or (OUTPUT_DIR / "LOINC_2026_Ontology_MultiSheet_Export.xlsx")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        wb = openpyxl.Workbook()
    except Exception:
        import time
        ts = int(time.time())
        out_path = OUTPUT_DIR / f"LOINC_2026_Ontology_MultiSheet_Export_{ts}.xlsx"
        wb = openpyxl.Workbook()

    export_logger.info(f"Creating LOINC Excel workbook with {len(data)} terms...")

    # Sheet 1: LOINC Codes
    ws_codes = wb.active
    ws_codes.title = "LOINC Codes"
    ws_codes.append(LOINC_FIELDS)
    for term in data:
        row_data = []
        for field in LOINC_FIELDS:
            if field == "ID" or field == "hasDbXref":
                row_data.append("")
            else:
                val = term.get(field, "")
                if isinstance(val, list):
                    val = "|".join(str(v) for v in val if v)
                row_data.append(str(val) if val else "")
        ws_codes.append(row_data)

    # Sheet 2: Term Types
    ws_types = wb.create_sheet("Term Types")
    ws_types.append(["Term Type ID", "Term Type Name", "Description", "Total Count"])
    ws_types.append(["T0", "LOINC Code", "Logical Observation Identifiers Names and Codes", len(data)])

    # Sheet 3: Relation Mapping Rules
    ws_relations = wb.create_sheet("Relation Mapping Rules")
    ws_relations.append(["Relation Name", "Inverse Relation", "Description"])
    ws_relations.append(["subClassOf", "superClassOf", "Parent-child hierarchy from MultiAxialHierarchy"])
    ws_relations.append(["superClassOf", "subClassOf", "Child-parent hierarchy from MultiAxialHierarchy"])

    # Sheet 4: Summary Statistics
    ws_stats = wb.create_sheet("Statistics")
    ws_stats.append(["Metric", "Value"])
    ws_stats.append(["Total LOINC Codes", len(data)])

    # Count by status
    status_counts = {}
    class_type_counts = {}
    for term in data:
        status = term.get("Status", "Unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        ct = term.get("Class Type", "Unknown")
        class_type_counts[ct] = class_type_counts.get(ct, 0) + 1

    ws_stats.append([])
    ws_stats.append(["--- Status Breakdown ---", ""])
    for status, count in sorted(status_counts.items(), key=lambda x: -x[1]):
        ws_stats.append([f"Status: {status}", count])

    ws_stats.append([])
    ws_stats.append(["--- Class Type Breakdown ---", ""])
    for ct, count in sorted(class_type_counts.items(), key=lambda x: -x[1]):
        ws_stats.append([f"Class Type: {ct}", count])

    # Count hierarchy links
    with_parents = sum(1 for t in data if t.get("subClassOf", "").strip())
    with_children = sum(1 for t in data if t.get("superClassOf", "").strip())
    ws_stats.append([])
    ws_stats.append(["--- Hierarchy ---", ""])
    ws_stats.append(["Terms with subClassOf (parents)", with_parents])
    ws_stats.append(["Terms with superClassOf (children)", with_children])

    # Save workbook
    try:
        wb.save(str(out_path))
    except PermissionError:
        import time
        ts = int(time.time())
        out_path = OUTPUT_DIR / f"LOINC_2026_Ontology_MultiSheet_Export_{ts}.xlsx"
        wb.save(str(out_path))

    export_logger.info(f"LOINC Excel export completed: {out_path}")
    return out_path
