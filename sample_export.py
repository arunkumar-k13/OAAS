"""
sample_export.py — Jan 2026 Browser-URL Sample Export
------------------------------------------------------
Re-transforms and exports a small sample of the WHO ICD-11 2026-01 MMS data
(top chapters + immediate children, ~350 terms) from the existing icd11_raw
collection using max_depth=2, then writes to:
  output/icd11_sample_jan2026.csv
  output/icd11_sample_jan2026.json

This script does NOT modify any production collections.
BrowserUrl column is included with human-openable https://icd.who.int/browse/... links.
"""

import json
import csv
from pathlib import Path
from collections import deque

from database.mongo import get_db
from transformer.mapper import ICD11Mapper
from transformer.hierarchy import HierarchyGenerator
from config.constants import OAAS_SCHEMA_FIELDS

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

CSV_PATH  = OUTPUT_DIR / "icd11_sample_jan2026_v2.csv"
JSON_PATH = OUTPUT_DIR / "icd11_sample_jan2026_v2.json"


MAX_DEPTH = 2   # Top MMS root (depth 0) + chapters (depth 1) + blocks (depth 2)


def fetch_sample_from_raw(db, max_depth: int):
    """
    BFS walk of icd11_raw using parent/child links to collect only
    entities up to max_depth. Returns list of raw_json dicts.
    """
    raw_col = db["icd11_raw"]

    # Build entity_id → raw_json map and child lists
    print("Loading icd11_raw into memory for BFS walk...")
    all_docs = list(raw_col.find({}, {"raw_json": 1, "_id": 0}))
    id_map = {}
    for doc in all_docs:
        rj = doc["raw_json"]
        eid = rj.get("@id", "")
        if eid:
            id_map[eid] = rj
    print(f"  Loaded {len(id_map)} raw entities.")

    # Find the MMS root (no parent)
    root_id = None
    for eid, rj in id_map.items():
        parents = rj.get("parent", [])
        if isinstance(parents, str):
            parents = [parents]
        if not parents:
            root_id = eid
            break

    if not root_id:
        raise ValueError("Could not find MMS root entity (no parent) in icd11_raw.")
    print(f"  Root entity: {root_id}")

    # BFS up to max_depth
    visited = set()
    queue = deque([(root_id, 0)])
    collected = []

    while queue:
        eid, depth = queue.popleft()
        if eid in visited or depth > max_depth:
            continue
        visited.add(eid)

        rj = id_map.get(eid)
        if rj:
            collected.append(rj)
            if depth < max_depth:
                children = rj.get("child", [])
                if isinstance(children, str):
                    children = [children]
                for child_uri in children:
                    if child_uri not in visited:
                        queue.append((child_uri, depth + 1))

    print(f"  BFS collected {len(collected)} entities up to depth {max_depth}.")
    return collected


def run():
    db = get_db()
    mapper = ICD11Mapper()

    # Step 1: Collect sample raw entities via BFS
    sample_raw = fetch_sample_from_raw(db, MAX_DEPTH)

    # Step 2: Map to OAAS schema
    print("Mapping to OAAS schema...")
    mapped = mapper.map_batch(sample_raw)
    print(f"  Mapped {len(mapped)} terms.")

    # Step 3: Resolve hierarchy (subClassOf / superClassOf → Concept Names)
    print("Resolving hierarchy links to Concept Names...")
    hg = HierarchyGenerator(resolve_to_name=True)
    terms = hg.build_bidirectional_links(mapped)
    print(f"  Hierarchy resolved for {len(terms)} terms.")


    # Step 4: Export CSV
    print("Writing CSV => " + str(CSV_PATH))
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OAAS_SCHEMA_FIELDS)
        writer.writeheader()
        for term in terms:
            row = {}
            for field in OAAS_SCHEMA_FIELDS:
                # Write browser-openable URL in place of raw API URI
                if field == "URI":
                    val = term.get("BrowserUrl") or term.get("URI", "")
                else:
                    val = term.get(field, "")
                if isinstance(val, list):
                    row[field] = "|".join(str(i) for i in val if i)
                elif isinstance(val, bool):
                    row[field] = str(val)
                else:
                    row[field] = str(val) if val is not None else ""
            writer.writerow(row)


    # Step 5: Export JSON
    print("Writing JSON => " + str(JSON_PATH))
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(terms, f, ensure_ascii=False, indent=2)

    # Step 6: Quick verification
    total      = len(terms)
    has_browser = sum(1 for t in terms if t.get("BrowserUrl"))
    print()
    print("=" * 60)
    print("Sample Export Complete!")
    print("  Total terms exported : " + str(total))
    print("  Terms with BrowserUrl: " + str(has_browser) + " (" + f"{has_browser/total*100:.1f}" + "%)")
    print("  CSV  => " + str(CSV_PATH.resolve()))
    print("  JSON => " + str(JSON_PATH.resolve()))
    print()

    # Show a few sample browser URLs
    print("Sample BrowserUrl values:")
    shown = 0
    for t in terms:
        if t.get("BrowserUrl"):
            print("  [" + t["Name"] + "] => " + t["BrowserUrl"])
            shown += 1
            if shown >= 5:
                break
    print("=" * 60)



if __name__ == "__main__":
    run()
