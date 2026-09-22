"""
ChEMBL 37 Bulk Raw Unmapped Extraction Engine.
Extracts all 2,921,148 compounds directly from local SQLite database (chembl_37.db) into:
1. Output CSV: output/ChEMBL_37_Direct_Raw_Content_Unmapped.csv (copied to Downloads)
2. MongoDB Collection: chembl_37_raw
Uses compact pipe ("|") format without spaces for all multi-value attributes.
"""

import csv
import shutil
import sqlite3
import sys
import time
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from database.mongo import get_db
from config.constants import OUTPUT_DIR

DATA_DIR = BASE_DIR / "data"
# Path to local ChEMBL SQLite database
SQLITE_DB_PATH = DATA_DIR / "chembl_37_sqlite" / "chembl_37" / "chembl_37_sqlite" / "chembl_37.db"

RAW_FIELDS = [
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

def load_sparse_lookups(conn):
    """
    Pre-load all sparse relational data (synonyms, trade names, ATC, indications, mechanisms, targets)
    into high-speed in-memory dictionaries indexed by molregno.
    """
    cur = conn.cursor()
    print("\n[INIT] Pre-loading sparse lookups into memory...")
    t_start = time.time()

    # 1. Synonyms and Trade Names
    t0 = time.time()
    cur.execute("SELECT molregno, syn_type, synonyms FROM molecule_synonyms WHERE synonyms IS NOT NULL")
    syn_map = defaultdict(list)
    trade_map = defaultdict(list)
    syn_count = 0
    trade_count = 0
    for molregno, syn_type, syn in cur.fetchall():
        syn_str = str(syn).strip()
        if not syn_str:
            continue
        if syn_type in ("TRADE_NAME", "BRAND_NAME"):
            if syn_str not in trade_map[molregno]:
                trade_map[molregno].append(syn_str)
                trade_count += 1
        else:
            if syn_str not in syn_map[molregno]:
                syn_map[molregno].append(syn_str)
                syn_count += 1
    print(f"  * Synonyms: {syn_count:,} | Trade Names: {trade_count:,} ({time.time()-t0:.2f}s)")

    # 2. ATC Classifications (Cross-references)
    t0 = time.time()
    cur.execute("SELECT molregno, level5 FROM molecule_atc_classification WHERE level5 IS NOT NULL")
    atc_map = defaultdict(list)
    atc_count = 0
    for molregno, code in cur.fetchall():
        code_str = f"ATC:{str(code).strip()}"
        if code_str not in atc_map[molregno]:
            atc_map[molregno].append(code_str)
            atc_count += 1
    print(f"  * ATC Cross-References: {atc_count:,} ({time.time()-t0:.2f}s)")

    # 3. Drug Indications
    t0 = time.time()
    cur.execute("SELECT molregno, mesh_heading, efo_term FROM drug_indication")
    ind_map = defaultdict(list)
    ind_count = 0
    for molregno, mesh_heading, efo_term in cur.fetchall():
        val = str(mesh_heading or efo_term or "").strip()
        if val and val not in ind_map[molregno]:
            ind_map[molregno].append(val)
            ind_count += 1
    print(f"  * Disease Indications: {ind_count:,} ({time.time()-t0:.2f}s)")

    # 4. Mechanisms of Action & Target Protein Bioactivity
    t0 = time.time()
    query_mechs = """
        SELECT dm.molregno, dm.mechanism_of_action, dm.action_type,
               td.pref_name, td.organism, cs.accession
        FROM drug_mechanism dm
        LEFT JOIN target_dictionary td ON dm.tid = td.tid
        LEFT JOIN target_components tc ON td.tid = tc.tid
        LEFT JOIN component_sequences cs ON tc.component_id = cs.component_id
    """
    cur.execute(query_mechs)
    mechs_map = defaultdict(list)
    actions_map = defaultdict(list)
    targets_map = defaultdict(list)
    organisms_map = defaultdict(list)
    uniprots_map = defaultdict(list)
    mech_count = 0

    for molregno, moa, act, t_name, org, uniprot in cur.fetchall():
        if moa and moa not in mechs_map[molregno]:
            mechs_map[molregno].append(str(moa).strip())
        if act and act not in actions_map[molregno]:
            actions_map[molregno].append(str(act).strip())
        if t_name and t_name not in targets_map[molregno]:
            targets_map[molregno].append(str(t_name).strip())
        if org and org not in organisms_map[molregno]:
            organisms_map[molregno].append(str(org).strip())
        if uniprot and uniprot not in uniprots_map[molregno]:
            uniprots_map[molregno].append(str(uniprot).strip())
        mech_count += 1

    print(f"  * Target Bioactivity Links: {mech_count:,} ({time.time()-t0:.2f}s)")
    print(f"[INIT COMPLETE] All lookups pre-loaded in {time.time()-t_start:.2f}s.\n")

    return {
        "syn_map": syn_map,
        "trade_map": trade_map,
        "atc_map": atc_map,
        "ind_map": ind_map,
        "mechs_map": mechs_map,
        "actions_map": actions_map,
        "targets_map": targets_map,
        "organisms_map": organisms_map,
        "uniprots_map": uniprots_map,
    }


def run_bulk_extraction():
    if not SQLITE_DB_PATH.exists():
        print(f"❌ Error: SQLite file not found at {SQLITE_DB_PATH}")
        sys.exit(1)

    print("=" * 70)
    print("  EMBL-EBI ChEMBL 37 BULK RAW UNMAPPED EXTRACTION (FULL 2.92M SET)")
    print("=" * 70)
    print(f"Source Database: {SQLITE_DB_PATH}")

    # Connect to SQLite with fast read PRAGMAs
    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    conn.execute("PRAGMA journal_mode = OFF")
    conn.execute("PRAGMA synchronous = OFF")
    conn.execute("PRAGMA cache_size = 100000")

    # Connect to MongoDB
    db = get_db()
    raw_col = db["chembl_37_raw"]
    print("Clearing previous 'chembl_37_raw' collection in MongoDB...")
    raw_col.delete_many({})

    # Pre-load sparse data lookups
    lookups = load_sparse_lookups(conn)
    syn_map = lookups["syn_map"]
    trade_map = lookups["trade_map"]
    atc_map = lookups["atc_map"]
    ind_map = lookups["ind_map"]
    mechs_map = lookups["mechs_map"]
    actions_map = lookups["actions_map"]
    targets_map = lookups["targets_map"]
    organisms_map = lookups["organisms_map"]
    uniprots_map = lookups["uniprots_map"]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = OUTPUT_DIR / "ChEMBL_37_Direct_Raw_Content_Unmapped.csv"
    downloads_dir = Path.home() / "Downloads"
    downloads_csv = downloads_dir / "ChEMBL_37_Direct_Raw_Content_Unmapped.csv"

    # Query for all compounds joining structures, properties, and parent hierarchy
    query_main = """
        SELECT md.molregno, md.chembl_id, pmd.chembl_id, md.pref_name, md.molecule_type,
               md.max_phase, md.first_approval, md.black_box_warning,
               cs.canonical_smiles, cs.standard_inchi, cs.standard_inchi_key,
               cp.full_molformula, cp.full_mwt
        FROM molecule_dictionary md
        LEFT JOIN compound_structures cs ON md.molregno = cs.molregno
        LEFT JOIN compound_properties cp ON md.molregno = cp.molregno
        LEFT JOIN molecule_hierarchy mh ON md.molregno = mh.molregno
        LEFT JOIN molecule_dictionary pmd ON mh.parent_molregno = pmd.molregno
    """

    cursor = conn.cursor()
    cursor.execute(query_main)

    total_processed = 0
    total_parents = 0
    total_salts = 0
    total_synonyms_count = 0
    total_trade_count = 0
    total_xrefs_count = 0

    batch_size = 10000
    mongo_batch = []
    t_start = time.time()

    print(f"[STREAMING] Writing CSV to {out_csv} and ingesting to MongoDB...")

    with open(out_csv, "w", newline="", encoding="utf-8") as f_csv:
        writer = csv.writer(f_csv)
        writer.writerow(RAW_FIELDS)

        while True:
            rows = cursor.fetchmany(batch_size)
            if not rows:
                break

            csv_rows = []
            for r in rows:
                (molregno, chembl_id, parent_chembl_id, pref_name, mol_type,
                 max_phase, first_approval, bb_warning,
                 smiles, inchi, inchi_key, formula, mwt) = r

                # Hierarchy parent/salt tracking
                p_id = parent_chembl_id or chembl_id
                if p_id == chembl_id:
                    total_parents += 1
                else:
                    total_salts += 1

                # Format multi-values with compact "|" (NO spaces)
                syns = syn_map.get(molregno, [])
                trades = trade_map.get(molregno, [])
                xrefs = atc_map.get(molregno, [])
                inds = ind_map.get(molregno, [])
                mechs = mechs_map.get(molregno, [])
                acts = actions_map.get(molregno, [])
                t_names = targets_map.get(molregno, [])
                t_orgs = organisms_map.get(molregno, [])
                uniprots = uniprots_map.get(molregno, [])

                syns_str = "|".join(syns)
                trades_str = "|".join(trades)
                xrefs_str = "|".join(xrefs)
                inds_str = "|".join(inds)
                mechs_str = "|".join(mechs)
                acts_str = "|".join(acts)
                t_names_str = "|".join(t_names)
                t_orgs_str = "|".join(t_orgs)
                uniprots_str = "|".join(uniprots)

                total_synonyms_count += len(syns)
                total_trade_count += len(trades)
                total_xrefs_count += len(xrefs)

                # CSV row
                csv_row = [
                    chembl_id,
                    p_id,
                    pref_name or chembl_id,
                    mol_type or "Small molecule",
                    max_phase if max_phase is not None else "",
                    first_approval if first_approval is not None else "",
                    bb_warning if bb_warning is not None else 0,
                    syns_str,
                    trades_str,
                    smiles or "",
                    inchi or "",
                    inchi_key or "",
                    formula or "",
                    mwt if mwt is not None else "",
                    xrefs_str,
                    inds_str,
                    mechs_str,
                    acts_str,
                    t_orgs_str,
                    uniprots_str,
                    t_names_str
                ]
                csv_rows.append(csv_row)

                # MongoDB document
                mongo_doc = {
                    "chembl_id": chembl_id,
                    "parent_chembl_id": p_id,
                    "pref_name": pref_name or chembl_id,
                    "molecule_type": mol_type or "Small molecule",
                    "max_phase": max_phase,
                    "first_approval": first_approval,
                    "black_box_warning": bb_warning or 0,
                    "synonyms": syns,
                    "trade_names": trades,
                    "canonical_smiles": smiles or "",
                    "standard_inchi": inchi or "",
                    "standard_inchi_key": inchi_key or "",
                    "molecular_formula": formula or "",
                    "full_mwt": mwt,
                    "cross_references": xrefs,
                    "indications": inds,
                    "mechanisms": mechs,
                    "target_action_types": acts,
                    "target_organisms": t_orgs,
                    "target_uniprot_ids": uniprots,
                    "targets": t_names
                }
                mongo_batch.append(mongo_doc)

            # Write CSV batch
            writer.writerows(csv_rows)

            # Insert MongoDB batch
            if mongo_batch:
                raw_col.insert_many(mongo_batch, ordered=False)
                mongo_batch.clear()

            total_processed += len(rows)
            if total_processed % 50000 == 0:
                elapsed = time.time() - t_start
                rate = total_processed / elapsed if elapsed > 0 else 0
                pct = (total_processed / 2921148) * 100
                print(f"[PROGRESS] {total_processed:,} / 2,921,148 compounds ({pct:.1f}%) | "
                      f"Speed: {rate:,.0f} rows/s | Elapsed: {elapsed:.1f}s")

    conn.close()
    elapsed_total = time.time() - t_start

    print(f"\n[STREAMING COMPLETE] Successfully processed {total_processed:,} compounds in {elapsed_total:.1f}s.")
    print("Copying export file to Downloads folder...")
    try:
        shutil.copyfile(out_csv, downloads_csv)
        print(f"[SUCCESS] Download Copy Saved: {downloads_csv}")
    except Exception as e:
        print(f"[WARNING] Could not copy to Downloads directory: {e}")

    print("\n" + "=" * 70)
    print("  FINAL BULK EXTRACTION STATISTICS (ChEMBL 37)")
    print("=" * 70)
    print(f"  * Total Compounds / Terms Extracted: {total_processed:,}")
    print(f"  * Parent Base Drugs:                {total_parents:,}")
    print(f"  * Child Salt Derivatives:            {total_salts:,}")
    print(f"  * Total Synonyms Extracted:         {total_synonyms_count:,}")
    print(f"  * Total Trade Names Extracted:      {total_trade_count:,}")
    print(f"  * Total External DB Cross-Refs:     {total_xrefs_count:,}")
    print(f"  * Total Ingested to MongoDB:        {raw_col.count_documents({}):,}")
    print(f"  * CSV File Output:                  {out_csv}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_bulk_extraction()
