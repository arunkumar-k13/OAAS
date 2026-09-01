"""
MongoDB collection index creation and maintenance.
"""

from pymongo import ASCENDING, TEXT
from pymongo.database import Database
from config.constants import (
    COLLECTION_RAW,
    COLLECTION_PROCESSED,
    COLLECTION_ONTOLOGY,
    COLLECTION_MAPPING_LOGS,
    COLLECTION_VALIDATION_LOGS,
    COLLECTION_IMPORT_LOGS,
)
from utils.logger import mongo_logger


def create_all_indexes(db: Database) -> None:
    """Ensure indexes exist across all oaas collections."""
    mongo_logger.info("Initializing database indexes...")

    # icd11_raw indexes
    raw_col = db[COLLECTION_RAW]
    raw_col.create_index([("uri", ASCENDING)], unique=True, sparse=True)
    raw_col.create_index([("id", ASCENDING)], sparse=True)

    # icd11_processed indexes
    processed_col = db[COLLECTION_PROCESSED]
    try:
        processed_col.drop_indexes()
    except Exception:
        pass

    processed_col.create_index([("URI", ASCENDING)], sparse=True)
    processed_col.create_index([("ID", ASCENDING)], sparse=True)
    processed_col.create_index([("Term ID", ASCENDING)], sparse=True)
    processed_col.create_index([("Name", TEXT)])

    # ICD11_2026_ONTOLOGY indexes
    ontology_col = db[COLLECTION_ONTOLOGY]
    try:
        ontology_col.drop_indexes()
    except Exception:
        pass

    ontology_col.create_index([("URI", ASCENDING)], sparse=True)
    ontology_col.create_index([("ID", ASCENDING)], sparse=True)
    ontology_col.create_index([("Term ID", ASCENDING)], sparse=True)
    ontology_col.create_index([("Name", TEXT)])
    ontology_col.create_index([("subClassOf", ASCENDING)])
    ontology_col.create_index([("superClassOf", ASCENDING)])

    # ICD-10 collection indexes
    from config.constants import COLLECTION_ICD10_RAW, COLLECTION_ICD10_PROCESSED, COLLECTION_ICD10_ONTOLOGY
    
    icd10_raw = db[COLLECTION_ICD10_RAW]
    icd10_raw.create_index([("uri", ASCENDING)], sparse=True)
    icd10_raw.create_index([("id", ASCENDING)], sparse=True)

    icd10_proc = db[COLLECTION_ICD10_PROCESSED]
    try:
        icd10_proc.drop_indexes()
    except Exception:
        pass
    icd10_proc.create_index([("URI", ASCENDING)], sparse=True)
    icd10_proc.create_index([("Term ID", ASCENDING)], sparse=True)

    icd10_ont = db[COLLECTION_ICD10_ONTOLOGY]
    try:
        icd10_ont.drop_indexes()
    except Exception:
        pass
    icd10_ont.create_index([("URI", ASCENDING)], sparse=True)
    icd10_ont.create_index([("Term ID", ASCENDING)], sparse=True)
    icd10_ont.create_index([("Name", TEXT)])
    icd10_ont.create_index([("subClassOf", ASCENDING)])
    icd10_ont.create_index([("superClassOf", ASCENDING)])

    # ICD-10-CM collection indexes (CDC FY 2026 Release)
    from config.constants import COLLECTION_ICD10CM_RAW, COLLECTION_ICD10CM_PROCESSED, COLLECTION_ICD10CM_ONTOLOGY

    icd10cm_raw = db[COLLECTION_ICD10CM_RAW]
    icd10cm_raw.create_index([("uri", ASCENDING)], sparse=True)
    icd10cm_raw.create_index([("code", ASCENDING)], sparse=True)

    icd10cm_proc = db[COLLECTION_ICD10CM_PROCESSED]
    try:
        icd10cm_proc.drop_indexes()
    except Exception:
        pass
    icd10cm_proc.create_index([("URI", ASCENDING)], sparse=True)
    icd10cm_proc.create_index([("Term ID", ASCENDING)], sparse=True)

    icd10cm_ont = db[COLLECTION_ICD10CM_ONTOLOGY]
    try:
        icd10cm_ont.drop_indexes()
    except Exception:
        pass
    icd10cm_ont.create_index([("URI", ASCENDING)], sparse=True)
    icd10cm_ont.create_index([("Term ID", ASCENDING)], sparse=True)
    icd10cm_ont.create_index([("Name", TEXT)])
    icd10cm_ont.create_index([("subClassOf", ASCENDING)])
    icd10cm_ont.create_index([("superClassOf", ASCENDING)])

    # Log collection indexes
    for log_col_name in [COLLECTION_MAPPING_LOGS, COLLECTION_VALIDATION_LOGS, COLLECTION_IMPORT_LOGS]:
        db[log_col_name].create_index([("timestamp", ASCENDING)])

    mongo_logger.info("Database indexes successfully created.")
