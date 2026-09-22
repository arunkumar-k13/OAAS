"""
Export Direct Raw Unmapped ChEMBL Data to CSV and display extraction statistics.
Native headers: chembl_id, parent_chembl_id, pref_name, molecule_type, max_phase, first_approval, black_box_warning, synonyms, trade_names, canonical_smiles, standard_inchi, standard_inchi_key, molecular_formula, full_mwt, cross_references, indications, mechanisms, target_action_types, target_organisms, target_uniprot_ids, targets
"""

import csv
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from database.mongo import get_db
from config.constants import OUTPUT_DIR

def run_raw_export_and_stats():
    db = get_db()
    col = db["chembl_37_raw"]
    docs = list(col.find({}, {"_id": 0}))

    if not docs:
        print("❌ Error: No documents found in 'chembl_37_raw' collection!")
        sys.exit(1)

    print(f"\n==================================================")
    print(f"  EMBL-EBI ChEMBL 37 RAW UNMAPPED EXTRACTION REPORT  ")
    print(f"==================================================")
    print(f"Loaded {len(docs):,} raw unmapped ChEMBL documents from MongoDB.")

    # Canonical list of 21 native raw fields as specified
    raw_fields = [
        "chembl_id",
        "parent_chembl_id",
        "pref_name",
        "molecule_type",
        "max_phase",
        "first_approval",
        "black_box_warning",
        "synonyms",
        "trade_names",
        "canonical_smiles",
        "standard_inchi",
        "standard_inchi_key",
        "molecular_formula",
        "full_mwt",
        "cross_references",
        "indications",
        "mechanisms",
        "target_action_types",
        "target_organisms",
        "target_uniprot_ids",
        "targets"
    ]

    # Calculate statistics
    total_compounds = len(docs)
    total_parent = sum(1 for d in docs if str(d.get("parent_chembl_id")) == str(d.get("chembl_id")))
    total_salts = sum(1 for d in docs if str(d.get("parent_chembl_id")) != str(d.get("chembl_id")) and d.get("parent_chembl_id"))
    total_synonyms = sum(len(d.get("synonyms", [])) if isinstance(d.get("synonyms"), list) else (1 if d.get("synonyms") else 0) for d in docs)
    total_trade_names = sum(len(d.get("trade_names", [])) if isinstance(d.get("trade_names"), list) else (1 if d.get("trade_names") else 0) for d in docs)
    total_xrefs = sum(len(d.get("cross_references", [])) if isinstance(d.get("cross_references"), list) else (1 if d.get("cross_references") else 0) for d in docs)
    total_indications = sum(len(d.get("indications", [])) if isinstance(d.get("indications"), list) else (1 if d.get("indications") else 0) for d in docs)
    total_targets = sum(len(d.get("targets", [])) if isinstance(d.get("targets"), list) else (1 if d.get("targets") else 0) for d in docs)

    print("\n--- EXTRACTION STATISTICS ---")
    print(f"  * Total Compounds / Terms Extracted: {total_compounds:,}")
    print(f"  * Parent Base Drugs:                {total_parent:,}")
    print(f"  * Child Salt Derivatives:            {total_salts:,}")
    print(f"  * Total Synonyms Extracted:         {total_synonyms:,}")
    print(f"  * Total Trade Names Extracted:      {total_trade_names:,}")
    print(f"  * Total External DB Cross-Refs:     {total_xrefs:,}")
    print(f"  * Total Disease Indications:        {total_indications:,}")
    print(f"  * Total Target Bioactivity Links:   {total_targets:,}")
    print("------------------------------\n")

    out_csv = OUTPUT_DIR / "ChEMBL_37_Direct_Raw_Content_Unmapped.csv"
    downloads_dir = Path.home() / "Downloads"
    downloads_csv = downloads_dir / "ChEMBL_37_Direct_Raw_Content_Unmapped.csv"

    # Ensure output folder exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write CSV with native headers
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(raw_fields)
        for doc in docs:
            row = []
            for field in raw_fields:
                val = doc.get(field, "")
                if isinstance(val, list):
                    val = "|".join(str(v).strip() for v in val if v)
                row.append(str(val) if val is not None else "")
            writer.writerow(row)

    # Also copy to Downloads folder
    try:
        with open(downloads_csv, "w", newline="", encoding="utf-8") as f_out:
            with open(out_csv, "r", encoding="utf-8") as f_in:
                f_out.write(f_in.read())
        print(f"[SUCCESS] Download Copy Saved: {downloads_csv}")
    except Exception as e:
        print(f"[WARNING] Could not write to Downloads directory: {e}")

    print(f"[SUCCESS] Main CSV Export Saved: {out_csv}")
    print("==================================================\n")

if __name__ == "__main__":
    run_raw_export_and_stats()
