"""
SNOMED CT International Edition (Latest Release) Schema Explorer & Sample Generator.
Demonstrates the official SNOMED CT RF2 (Release Format 2) snapshot structure,
native raw field mappings, concept hierarchies (is a / subClassOf), and generates
an initial exploration report for team review.
"""

import csv
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from config.constants import OUTPUT_DIR

# Official SNOMED CT RF2 Snapshot Tables & Field Definitions
SNOMED_RF2_TABLES = {
    "Concept (sct2_Concept_Snapshot_INT)": {
        "fields": ["id", "effectiveTime", "active", "moduleId", "definitionStatusId"],
        "description": "Unique Concept ID (SCTID), active flag, and whether primitive or fully defined."
    },
    "Description (sct2_Description_Snapshot-en_INT)": {
        "fields": ["id", "effectiveTime", "active", "moduleId", "conceptId", "languageCode", "typeId", "term", "caseSignificanceId"],
        "description": "Terms linked to conceptId. typeId distinguishes FSN (900000000000003001) vs Synonym (900000000000013009)."
    },
    "Language Refset (der2_cRefset_LanguageSnapshot-en_INT)": {
        "fields": ["id", "effectiveTime", "active", "moduleId", "refsetId", "referencedComponentId", "acceptabilityId"],
        "description": "Identifies Preferred Term (PT) (900000000000548007) vs Acceptable Synonym (900000000000549004)."
    },
    "Relationship (sct2_Relationship_Snapshot_INT)": {
        "fields": ["id", "effectiveTime", "active", "moduleId", "sourceId", "destinationId", "relationshipGroup", "typeId", "characteristicTypeId", "modifierId"],
        "description": "Hierarchy and attribute links. typeId=116680003 indicates 'is a' (subClassOf) polyhierarchy."
    }
}

# 12 Canonical Native Raw Fields for Extraction & Review
NATIVE_RAW_FIELDS = [
    "concept_id",
    "fsn",
    "semantic_tag",
    "preferred_term",
    "synonyms",
    "active",
    "definition_status",
    "parent_concept_ids",
    "parent_concept_names",
    "attribute_relationships",
    "module_id",
    "effective_time"
]

# Curated Representative SNOMED CT International Sample Concepts across clinical hierarchies
SAMPLE_CONCEPTS = [
    {
        "concept_id": "22298006",
        "fsn": "Myocardial infarction (disorder)",
        "semantic_tag": "disorder",
        "preferred_term": "Myocardial infarction",
        "synonyms": "Heart attack|Cardiac infarction|Infarction of heart",
        "active": "1",
        "definition_status": "Fully defined",
        "parent_concept_ids": "57054005|128599005",
        "parent_concept_names": "Acute myocardial infarction|Necrosis of anatomical site",
        "attribute_relationships": "Finding site:Myocardium structure|Pathological process:Infarction",
        "module_id": "900000000000207008",
        "effective_time": "20260831"
    },
    {
        "concept_id": "38341003",
        "fsn": "Hypertensive disorder, systemic arterial (disorder)",
        "semantic_tag": "disorder",
        "preferred_term": "Hypertension",
        "synonyms": "High blood pressure|HTN - Hypertension|Systemic arterial hypertension",
        "active": "1",
        "definition_status": "Primitive",
        "parent_concept_ids": "49601007",
        "parent_concept_names": "Disorder of cardiovascular system",
        "attribute_relationships": "Finding site:Systemic arterial system structure",
        "module_id": "900000000000207008",
        "effective_time": "20260831"
    },
    {
        "concept_id": "44054006",
        "fsn": "Type 2 diabetes mellitus (disorder)",
        "semantic_tag": "disorder",
        "preferred_term": "Type 2 diabetes mellitus",
        "synonyms": "Type 2 diabetes|T2D|Non-insulin dependent diabetes mellitus|NIDDM",
        "active": "1",
        "definition_status": "Fully defined",
        "parent_concept_ids": "73211009",
        "parent_concept_names": "Diabetes mellitus",
        "attribute_relationships": "Finding site:Endocrine system structure|Pathological process:Metabolic disorder",
        "module_id": "900000000000207008",
        "effective_time": "20260831"
    },
    {
        "concept_id": "840539006",
        "fsn": "Disease caused by severe acute respiratory syndrome coronavirus 2 (disorder)",
        "semantic_tag": "disorder",
        "preferred_term": "COVID-19",
        "synonyms": "SARS-CoV-2 infection|Coronavirus disease 2019|2019-nCoV disease",
        "active": "1",
        "definition_status": "Fully defined",
        "parent_concept_ids": "882784000",
        "parent_concept_names": "Coronavirus infection",
        "attribute_relationships": "Causative agent:Severe acute respiratory syndrome coronavirus 2",
        "module_id": "900000000000207008",
        "effective_time": "20260831"
    },
    {
        "concept_id": "74400008",
        "fsn": "Appendicitis (disorder)",
        "semantic_tag": "disorder",
        "preferred_term": "Appendicitis",
        "synonyms": "Inflammation of appendix|Appendiceal inflammation",
        "active": "1",
        "definition_status": "Fully defined",
        "parent_concept_ids": "64766004|128601004",
        "parent_concept_names": "Disorder of appendix|Inflammatory disorder of digestive tract",
        "attribute_relationships": "Finding site:Vermiform appendix structure|Pathological process:Inflammation",
        "module_id": "900000000000207008",
        "effective_time": "20260831"
    },
    {
        "concept_id": "80146002",
        "fsn": "Excision of appendix (procedure)",
        "semantic_tag": "procedure",
        "preferred_term": "Appendectomy",
        "synonyms": "Removal of appendix|Appendicectomy",
        "active": "1",
        "definition_status": "Fully defined",
        "parent_concept_ids": "128927007",
        "parent_concept_names": "Excision of abdominal organ",
        "attribute_relationships": "Procedure site - Direct:Vermiform appendix structure|Method:Excision - action",
        "module_id": "900000000000207008",
        "effective_time": "20260831"
    },
    {
        "concept_id": "232717009",
        "fsn": "Coronary artery bypass graft (procedure)",
        "semantic_tag": "procedure",
        "preferred_term": "Coronary artery bypass graft",
        "synonyms": "CABG|Aortocoronary bypass graft|Heart bypass surgery",
        "active": "1",
        "definition_status": "Fully defined",
        "parent_concept_ids": "64915003",
        "parent_concept_names": "Operation on heart",
        "attribute_relationships": "Procedure site - Direct:Coronary artery structure|Method:Bypass - action",
        "module_id": "900000000000207008",
        "effective_time": "20260831"
    },
    {
        "concept_id": "66019005",
        "fsn": "Structure of myocardium (body structure)",
        "semantic_tag": "body structure",
        "preferred_term": "Myocardium structure",
        "synonyms": "Cardiac muscle|Heart muscle|Myocardium",
        "active": "1",
        "definition_status": "Primitive",
        "parent_concept_ids": "74281007",
        "parent_concept_names": "Myocardium and/or endocardium",
        "attribute_relationships": "",
        "module_id": "900000000000207008",
        "effective_time": "20260831"
    },
    {
        "concept_id": "387458008",
        "fsn": "Aspirin (substance)",
        "semantic_tag": "substance",
        "preferred_term": "Aspirin",
        "synonyms": "Acetylsalicylic acid|ASA - Acetylsalicylic acid|2-Acetoxybenzoic acid",
        "active": "1",
        "definition_status": "Primitive",
        "parent_concept_ids": "108502008",
        "parent_concept_names": "Salicylate and derivative",
        "attribute_relationships": "",
        "module_id": "900000000000207008",
        "effective_time": "20260831"
    },
    {
        "concept_id": "372567009",
        "fsn": "Metformin (substance)",
        "semantic_tag": "substance",
        "preferred_term": "Metformin",
        "synonyms": "Metformin base|Dimethylbiguanide",
        "active": "1",
        "definition_status": "Primitive",
        "parent_concept_ids": "386927008",
        "parent_concept_names": "Biguanide derivative",
        "attribute_relationships": "",
        "module_id": "900000000000207008",
        "effective_time": "20260831"
    }
]


def run_snomed_exploration():
    print("=" * 75)
    print("  SNOMED CT INTERNATIONAL EDITION (LATEST RELEASE) - R&D EXPLORATION")
    print("=" * 75)

    print("\n1. OFFICIAL SNOMED CT RF2 (RELEASE FORMAT 2) ARCHITECTURE")
    print("-" * 75)
    for tbl, info in SNOMED_RF2_TABLES.items():
        print(f"  • {tbl}")
        print(f"    - Fields: {', '.join(info['fields'])}")
        print(f"    - Role:   {info['description']}\n")

    print("2. EXTRACTION LOGIC & NATIVE RAW FIELD MAPPING")
    print("-" * 75)
    print("  * concept_id:               From sct2_Concept.id (SCTID)")
    print("  * fsn:                      From sct2_Description where typeId=900000000000003001")
    print("  * semantic_tag:             Extracted from trailing parentheses of FSN: e.g. '(disorder)'")
    print("  * preferred_term:           From sct2_Description linked to Language Refset acceptabilityId=Preferred")
    print("  * synonyms:                 All acceptable synonyms joined with compact '|'")
    print("  * active:                   Binary status flag ('1' = Active, '0' = Inactive/Retired)")
    print("  * definition_status:        Mapped from definitionStatusId (Fully defined vs Primitive)")
    print("  * parent_concept_ids/names: Destination concept IDs where sct2_Relationship typeId=116680003 (is a)")
    print("  * attribute_relationships:  Defining attributes (e.g. Finding site, Causative agent)")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = OUTPUT_DIR / "SNOMED_CT_International_Raw_Sample.csv"
    downloads_csv = Path.home() / "Downloads" / "SNOMED_CT_International_Raw_Sample.csv"

    # Write Sample CSV
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(NATIVE_RAW_FIELDS)
        for c in SAMPLE_CONCEPTS:
            row = [c[k] for k in NATIVE_RAW_FIELDS]
            writer.writerow(row)

    # Copy to Downloads
    try:
        import shutil
        shutil.copyfile(out_csv, downloads_csv)
        print(f"\n[SUCCESS] Sample CSV Export Saved to Downloads: {downloads_csv}")
    except Exception as e:
        print(f"\n[NOTE] Output saved to: {out_csv} ({e})")

    print(f"[SUCCESS] Master Output CSV: {out_csv}")
    print("\n" + "=" * 75)
    print(f"Sample exploration generated with {len(SAMPLE_CONCEPTS)} representative clinical concepts.")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    run_snomed_exploration()
