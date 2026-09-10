"""
Constants for the OAAS ICD-11, ICD-10, ICD-10-CM, MeSH, and LOINC Ontology ETL Pipeline.
"""

from pathlib import Path

# Base Directory Paths
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
LOGS_DIR = BASE_DIR / "logs"
OUTPUT_DIR = BASE_DIR / "output"

# Configuration Files
MAPPING_YAML_PATH = CONFIG_DIR / "mapping.yaml"

# MongoDB Database & Collections
DEFAULT_DB_NAME = "oaas"

COLLECTION_RAW = "icd11_raw"
COLLECTION_PROCESSED = "icd11_processed"
COLLECTION_ONTOLOGY = "ICD11_2026_ONTOLOGY"

# ICD-10 MongoDB Collections
COLLECTION_ICD10_RAW = "icd10_raw"
COLLECTION_ICD10_PROCESSED = "icd10_processed"
COLLECTION_ICD10_ONTOLOGY = "ICD10_2019_ONTOLOGY"

# ICD-10-CM MongoDB Collections (CDC FY 2026 Release)
COLLECTION_ICD10CM_RAW = "icd10cm_2026_raw"
COLLECTION_ICD10CM_PROCESSED = "icd10cm_2026_processed"
COLLECTION_ICD10CM_ONTOLOGY = "ICD10CM_2026_ONTOLOGY"

# MeSH MongoDB Collections (NLM 2026 Release)
COLLECTION_MESH_RAW = "mesh_2026_raw"
COLLECTION_MESH_PROCESSED = "mesh_2026_processed"
COLLECTION_MESH_ONTOLOGY = "MESH_2026_ONTOLOGY"

# LOINC MongoDB Collections (Regenstrief v2.83 / 2026 Release)
COLLECTION_LOINC_RAW = "loinc_2026_raw"
COLLECTION_LOINC_PROCESSED = "loinc_2026_processed"
COLLECTION_LOINC_ONTOLOGY = "LOINC_2026_ONTOLOGY"

# ChEMBL MongoDB Collections (EMBL-EBI ChEMBL 37 Release)
COLLECTION_CHEMBL_RAW = "chembl_37_raw"
COLLECTION_CHEMBL_PROCESSED = "chembl_37_processed"
COLLECTION_CHEMBL_ONTOLOGY = "CHEMBL_37_ONTOLOGY"

COLLECTION_MAPPING_LOGS = "mapping_logs"
COLLECTION_VALIDATION_LOGS = "validation_logs"
COLLECTION_IMPORT_LOGS = "import_logs"

ALL_COLLECTIONS = [
    COLLECTION_RAW,
    COLLECTION_PROCESSED,
    COLLECTION_ONTOLOGY,
    COLLECTION_ICD10_RAW,
    COLLECTION_ICD10_PROCESSED,
    COLLECTION_ICD10_ONTOLOGY,
    COLLECTION_ICD10CM_RAW,
    COLLECTION_ICD10CM_PROCESSED,
    COLLECTION_ICD10CM_ONTOLOGY,
    COLLECTION_MESH_RAW,
    COLLECTION_MESH_PROCESSED,
    COLLECTION_MESH_ONTOLOGY,
    COLLECTION_LOINC_RAW,
    COLLECTION_LOINC_PROCESSED,
    COLLECTION_LOINC_ONTOLOGY,
    COLLECTION_CHEMBL_RAW,
    COLLECTION_CHEMBL_PROCESSED,
    COLLECTION_CHEMBL_ONTOLOGY,
    COLLECTION_MAPPING_LOGS,
    COLLECTION_VALIDATION_LOGS,
    COLLECTION_IMPORT_LOGS,
]

# OAAS Ontology Schema Required Fields (Standard ICD Schema)
OAAS_SCHEMA_FIELDS = [
    "Name",
    "ID",
    "Term ID",
    "URI",
    "Synonyms",
    "Short Description",
    "Long Description",
    "Condition Group",
    "hasDbXref",
    "Definition",
    "Type I Exclude",
    "Type II Exclude",
    "Includes",
    "Applicable To",
    "forMapping",
    "mcXref",
    "Version",
    "PossiblePrefix",
    "superClassOf",
    "subClassOf",
]

# MeSH Descriptor Attributes (28 attributes + 2 relationships)
MESH_DESCRIPTOR_FIELDS = [
    "Name",
    "ID",
    "Term ID",
    "EntryTerm Name",
    "Synonyms",
    "Qualifier ID",
    "History note",
    "Online note",
    "Public MeSH note",
    "Tree Number",
    "Previous Indexing Term",
    "Note",
    "Term UI ID",
    "Pharmacological action",
    "Pharmacological ID",
    "CASN Name",
    "Annotation",
    "Registry number",
    "Related Registry number",
    "NLM Classification number",
    "mcXref",
    "forMapping",
    "hasDbXref",
    "PossiblePrefix",
    "isTopic",
    "Version",
    "Qualifier Name",
    "Concept UI ID",
    "superClassOf",
    "subClassOf",
]

# MeSH Concept Attributes (22 attributes + 2 relationships)
MESH_CONCEPT_FIELDS = [
    "Name",
    "ID",
    "Term ID",
    "Mapped To Descriptor",
    "Synonyms",
    "EntryTerm Name",
    "Source",
    "Frequency",
    "Note",
    "Concept ID",
    "Concept Name",
    "Registry number",
    "Term UI ID",
    "Previous Indexing Term",
    "Mapped To Qualifier",
    "Indexing Descriptor ID",
    "Indexing Qualifier ID",
    "mcXref",
    "forMapping",
    "hasDbXref",
    "PossiblePrefix",
    "Version",
    "superClassOf",
    "subClassOf",
]

# MeSH Qualifier Attributes (16 attributes + 2 relationships)
MESH_QUALIFIER_FIELDS = [
    "Name",
    "ID",
    "Term ID",
    "Abbrevation",
    "Tree Number",
    "EntryTerm Name",
    "Synonyms",
    "Note",
    "History note",
    "Term UI ID",
    "Annotation",
    "mcXref",
    "forMapping",
    "hasDbXref",
    "PossiblePrefix",
    "Version",
    "superClassOf",
    "subClassOf",
]

# LOINC Observation Code Attributes (Lexicon Schema)
LOINC_FIELDS = [
    "Name",
    "ID",
    "Term ID",
    "URI",
    "Component",
    "Property",
    "Time Aspect",
    "System (Specimen)",
    "Scale Type",
    "Method Type",
    "Class",
    "Class Type",
    "Status",
    "Short Name",
    "Consumer Name",
    "Order/Observation",
    "Synonyms",
    "Long Description",
    "Units Required",
    "Version",
    "mcXref",
    "forMapping",
    "hasDbXref",
    "PossiblePrefix",
    "superClassOf",
    "subClassOf",
]

# ChEMBL Bioactive Compounds Attributes (Lexicon Schema)
CHEMBL_FIELDS = [
    "Name",
    "ID",
    "Term ID",
    "URI",
    "Molecule Type",
    "Max Phase",
    "First Approval Year",
    "Black Box Warning",
    "Synonyms",
    "SMILES",
    "InChI",
    "InChI Key",
    "Molecular Formula",
    "Molecular Weight",
    "AlogP",
    "HBA",
    "HBD",
    "PSA",
    "Rotatable Bonds",
    "Indications",
    "Mechanisms",
    "Biological Targets",
    "Version",
    "mcXref",
    "forMapping",
    "hasDbXref",
    "PossiblePrefix",
    "superClassOf",
    "subClassOf",
]

# Logging Categories
LOG_CATEGORY_API = "api"
LOG_CATEGORY_MONGO = "mongo"
LOG_CATEGORY_MAPPING = "mapping"
LOG_CATEGORY_VALIDATION = "validation"
LOG_CATEGORY_EXPORT = "export"
