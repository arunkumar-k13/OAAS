"""
ChEMBL 37 CSV and Multi-Sheet Excel Exporter.
Exports ChEMBL bioactive compound data to clean, deduplicated CSV/Excel files matching Lexicon target rules.
"""

import csv
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from config.constants import CHEMBL_FIELDS, OUTPUT_DIR
from utils.logger import export_logger


def export_chembl_csv(data: List[Dict[str, Any]], filepath: Optional[Path] = None) -> Path:
    """
    Export list of mapped ChEMBL terms into CSV format.
    Applies Lexicon rules: empty ID/hasDbXref, pipe-separated list values.
    """
    out_path = filepath or (OUTPUT_DIR / "chembl_37_ontology.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    export_logger.info(f"Exporting {len(data)} ChEMBL terms to CSV at {out_path}...")
    all_fields = CHEMBL_FIELDS

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

    export_logger.info(f"ChEMBL CSV export completed successfully: {out_path}")
    return out_path


def export_chembl_excel(data: List[Dict[str, Any]], filepath: Optional[Path] = None) -> Path:
    """
    Export ChEMBL terms to a Multi-Sheet Excel workbook.
    Sheets: Bioactive Compounds, Term Types, Relation Mapping Rules, Statistics.
    """
    try:
        import openpyxl
    except ImportError:
        export_logger.error("openpyxl is required for Excel export. Install: pip install openpyxl")
        raise

    out_path = filepath or (OUTPUT_DIR / "ChEMBL_37_Ontology_MultiSheet_Export.xlsx")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        wb = openpyxl.Workbook()
    except Exception:
        import time
        ts = int(time.time())
        out_path = OUTPUT_DIR / f"ChEMBL_37_Ontology_MultiSheet_Export_{ts}.xlsx"
        wb = openpyxl.Workbook()

    export_logger.info(f"Creating ChEMBL Excel workbook with {len(data)} terms...")

    # Sheet 1: Bioactive Compounds
    ws_compounds = wb.active
    ws_compounds.title = "Bioactive Compounds"
    ws_compounds.append(CHEMBL_FIELDS)
    for term in data:
        row_data = []
        for field in CHEMBL_FIELDS:
            if field == "ID" or field == "hasDbXref":
                row_data.append("")
            else:
                val = term.get(field, "")
                if isinstance(val, list):
                    val = "|".join(str(v) for v in val if v)
                row_data.append(str(val) if val else "")
        ws_compounds.append(row_data)

    # Sheet 2: Term Types
    ws_types = wb.create_sheet("Term Types")
    ws_types.append(["Term Type ID", "Term Type Name", "Description", "Total Count"])
    ws_types.append(["T0", "Bioactive Compound", "Bioactive molecules and clinical drugs from ChEMBL 37", len(data)])

    # Sheet 3: Relation Mapping Rules
    ws_relations = wb.create_sheet("Relation Mapping Rules")
    ws_relations.append(["Relation Name", "Inverse Relation", "Description"])
    ws_relations.append(["subClassOf", "superClassOf", "Parent salt or parent molecule derivative link"])
    ws_relations.append(["superClassOf", "subClassOf", "Child salt or derivative compound link"])

    # Sheet 4: Summary Statistics
    ws_stats = wb.create_sheet("Statistics")
    ws_stats.append(["Metric", "Value"])
    ws_stats.append(["Total Bioactive Compounds", len(data)])

    # Count by Max Phase
    phase_counts = {}
    type_counts = {}
    for term in data:
        p = term.get("Max Phase", "Unknown")
        phase_counts[p] = phase_counts.get(p, 0) + 1
        t = term.get("Molecule Type", "Unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    ws_stats.append([])
    ws_stats.append(["--- Clinical Trial Phase Breakdown ---", ""])
    for phase, count in sorted(phase_counts.items(), key=lambda x: str(x[0])):
        ws_stats.append([f"Phase: {phase}", count])

    ws_stats.append([])
    ws_stats.append(["--- Molecule Type Breakdown ---", ""])
    for mtype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        ws_stats.append([f"Type: {mtype}", count])

    # Save workbook
    try:
        wb.save(str(out_path))
    except PermissionError:
        import time
        ts = int(time.time())
        out_path = OUTPUT_DIR / f"ChEMBL_37_Ontology_MultiSheet_Export_{ts}.xlsx"
        wb.save(str(out_path))

    export_logger.info(f"ChEMBL Excel export completed: {out_path}")
    return out_path
