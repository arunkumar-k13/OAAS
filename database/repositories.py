"""
Repository pattern implementations for MongoDB collections in the oaas database.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from pymongo import UpdateOne, TEXT
from pymongo.database import Database
from config.constants import (
    COLLECTION_RAW,
    COLLECTION_PROCESSED,
    COLLECTION_ONTOLOGY,
    COLLECTION_ICD10_RAW,
    COLLECTION_ICD10_PROCESSED,
    COLLECTION_ICD10_ONTOLOGY,
    COLLECTION_ICD10CM_RAW,
    COLLECTION_ICD10CM_PROCESSED,
    COLLECTION_ICD10CM_ONTOLOGY,
    COLLECTION_LOINC_RAW,
    COLLECTION_LOINC_PROCESSED,
    COLLECTION_LOINC_ONTOLOGY,
    COLLECTION_CHEMBL_RAW,
    COLLECTION_CHEMBL_PROCESSED,
    COLLECTION_CHEMBL_ONTOLOGY,
    COLLECTION_MAPPING_LOGS,
    COLLECTION_VALIDATION_LOGS,
    COLLECTION_IMPORT_LOGS,
)
from database.mongo import get_db
from utils.logger import mongo_logger


class BaseRepository:
    """Generic base repository for MongoDB collection operations."""

    def __init__(self, collection_name: str, db: Optional[Database] = None):
        self.db = db if db is not None else get_db()
        self.collection = self.db[collection_name]
        self.collection_name = collection_name

    def count(self) -> int:
        """Return total document count in collection."""
        return self.collection.count_documents({})

    def drop(self) -> None:
        """Drop collection contents."""
        mongo_logger.warning(f"Dropping collection '{self.collection_name}'")
        self.collection.drop()


class RawDataRepository(BaseRepository):
    """Repository for storing and querying raw ICD-11 JSON documents."""

    def __init__(self, db: Optional[Database] = None):
        super().__init__(COLLECTION_RAW, db)

    def insert_or_update_raw_entity(self, raw_data: Dict[str, Any]) -> str:
        """Store raw WHO entity document with metadata."""
        uri = raw_data.get("@id") or raw_data.get("uri") or raw_data.get("id")
        if not uri:
            raise ValueError("Raw entity missing `@id` or `uri` field.")

        entity_id = uri.rstrip("/").split("/")[-1]
        code = raw_data.get("code")

        doc = {
            "uri": uri,
            "id": entity_id,
            "code": code,
            "raw_json": raw_data,
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
        }

        self.collection.replace_one({"uri": uri}, doc, upsert=True)
        return uri

    def bulk_insert_raw_entities(self, raw_entities: List[Dict[str, Any]]) -> int:
        """Bulk upsert raw entity documents into MongoDB."""
        if not raw_entities:
            return 0

        operations = []
        now_str = datetime.now(timezone.utc).isoformat()

        for raw_data in raw_entities:
            uri = raw_data.get("@id") or raw_data.get("uri") or raw_data.get("id")
            if not uri:
                continue
            entity_id = str(uri).rstrip("/").split("/")[-1]
            code = raw_data.get("code")

            doc = {
                "uri": uri,
                "id": entity_id,
                "code": code,
                "raw_json": raw_data,
                "downloaded_at": now_str,
            }
            operations.append(UpdateOne({"uri": uri}, {"$set": doc}, upsert=True))

        if operations:
            result = self.collection.bulk_write(operations, ordered=False)
            return result.upserted_count + result.modified_count
        return 0

    def get_all_downloaded_uris(self) -> Set[str]:
        """Fetch set of all URIs already persisted in icd11_raw."""
        cursor = self.collection.find({}, {"uri": 1})
        return {doc["uri"] for doc in cursor if "uri" in doc}

    def fetch_all_raw_documents(self) -> List[Dict[str, Any]]:
        """Fetch all raw JSON payloads from icd11_raw."""
        cursor = self.collection.find({})
        return [doc["raw_json"] for doc in cursor if "raw_json" in doc]


class ProcessedOntologyRepository(BaseRepository):
    """Repository for mapped and processed OAAS ontology documents."""

    def __init__(self, db: Optional[Database] = None):
        super().__init__(COLLECTION_PROCESSED, db)

    def bulk_upsert(self, terms: List[Dict[str, Any]]) -> int:
        """Bulk upsert processed terms into collection."""
        if not terms:
            return 0
        operations = []
        for term in terms:
            term_uri = term.get("URI") or term.get("ID")
            if term_uri:
                operations.append(UpdateOne({"URI": term_uri}, {"$set": term}, upsert=True))

        if operations:
            result = self.collection.bulk_write(operations, ordered=False)
            return result.upserted_count + result.modified_count
        return 0

    def fetch_all(self) -> List[Dict[str, Any]]:
        """Fetch all documents from icd11_processed excluding Mongo _id."""
        return list(self.collection.find({}, {"_id": 0}))


class FinalOntologyRepository(BaseRepository):
    """Repository for final ICD11_2026_ONTOLOGY collection."""

    def __init__(self, db: Optional[Database] = None):
        super().__init__(COLLECTION_ONTOLOGY, db)

    def sync_from_processed(self) -> int:
        """Copy all terms from processed repository to final ontology collection."""
        proc_repo = getattr(self, "processed_repo", None) or ProcessedOntologyRepository(db=self.db)
        terms = proc_repo.fetch_all()
        if not terms:
            return 0

        self.collection.delete_many({})
        self.collection.insert_many(terms)
        count = len(terms)
        mongo_logger.info(f"Synced {count} terms to final collection '{self.collection_name}'.")
        return count

    def fetch_all(self) -> List[Dict[str, Any]]:
        """Fetch all terms from final ontology collection."""
        return list(self.collection.find({}, {"_id": 0}))

    def get_all_terms(self) -> List[Dict[str, Any]]:
        """Alias for fetch_all()."""
        return self.fetch_all()

    def get_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Find concept term by ID or URI."""
        return self.collection.find_one({"$or": [{"ID": entity_id}, {"URI": entity_id}]}, {"_id": 0})

    def get_by_term_id(self, code: str) -> Optional[Dict[str, Any]]:
        """Find concept term by Term ID (e.g. '1A00')."""
        return self.collection.find_one({"Term ID": code}, {"_id": 0})

    def search_by_name(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search concepts by title/name."""
        regex_query = {"Name": {"$regex": query, "$options": "i"}}
        return list(self.collection.find(regex_query, {"_id": 0}).limit(limit))

    def get_children(self, entity_id: str) -> List[Dict[str, Any]]:
        """Find child terms where subClassOf contains entity_id or URI."""
        term = self.get_by_id(entity_id)
        if not term:
            return []
        uri = term.get("URI") or entity_id
        return list(self.collection.find({"subClassOf": uri}, {"_id": 0}))

    def get_parents(self, entity_id: str) -> List[Dict[str, Any]]:
        """Find parent terms where superClassOf contains entity_id or URI."""
        term = self.get_by_id(entity_id)
        if not term:
            return []
        parents_refs = term.get("subClassOf", [])
        return list(self.collection.find({"$or": [{"URI": {"$in": parents_refs}}, {"ID": {"$in": parents_refs}}]}, {"_id": 0}))


class ICD10RawRepository(RawDataRepository):
    """Repository for storing and querying raw ICD-10 JSON documents."""

    def __init__(self, db: Optional[Database] = None):
        BaseRepository.__init__(self, COLLECTION_ICD10_RAW, db)


class ICD10ProcessedRepository(ProcessedOntologyRepository):
    """Repository for storing transformed ICD-10 ontology terms."""

    def __init__(self, db: Optional[Database] = None):
        BaseRepository.__init__(self, COLLECTION_ICD10_PROCESSED, db)


class ICD10FinalRepository(FinalOntologyRepository):
    """Repository for querying final ICD-10 ontology collection."""

    def __init__(self, db: Optional[Database] = None):
        super().__init__(db)
        self.collection = self.db[COLLECTION_ICD10_ONTOLOGY]
        self.collection_name = COLLECTION_ICD10_ONTOLOGY
        self.processed_repo = ICD10ProcessedRepository(db)


class ICD10CMRawRepository(RawDataRepository):
    """Repository for storing and querying raw 2026 ICD-10-CM JSON documents."""

    def __init__(self, db: Optional[Database] = None):
        BaseRepository.__init__(self, COLLECTION_ICD10CM_RAW, db)


class ICD10CMProcessedRepository(ProcessedOntologyRepository):
    """Repository for storing transformed 2026 ICD-10-CM ontology terms."""

    def __init__(self, db: Optional[Database] = None):
        BaseRepository.__init__(self, COLLECTION_ICD10CM_PROCESSED, db)


class ICD10CMFinalRepository(FinalOntologyRepository):
    """Repository for querying final 2026 ICD-10-CM ontology collection."""

    def __init__(self, db: Optional[Database] = None):
        super().__init__(db)
        self.collection = self.db[COLLECTION_ICD10CM_ONTOLOGY]
        self.collection_name = COLLECTION_ICD10CM_ONTOLOGY
        self.processed_repo = ICD10CMProcessedRepository(db)


class LOINCRawRepository(BaseRepository):
    """Repository for storing and querying raw LOINC 2026 CSV documents."""

    def __init__(self, db: Optional[Database] = None):
        super().__init__(COLLECTION_LOINC_RAW, db)


class LOINCProcessedRepository(ProcessedOntologyRepository):
    """Repository for storing transformed LOINC 2026 ontology terms."""

    def __init__(self, db: Optional[Database] = None):
        BaseRepository.__init__(self, COLLECTION_LOINC_PROCESSED, db)


class LOINCFinalRepository(FinalOntologyRepository):
    """Repository for querying final LOINC 2026 ontology collection."""

    def __init__(self, db: Optional[Database] = None):
        super().__init__(db)
        self.collection = self.db[COLLECTION_LOINC_ONTOLOGY]
        self.collection_name = COLLECTION_LOINC_ONTOLOGY
        self.processed_repo = LOINCProcessedRepository(db)


class ChEMBLRawRepository(BaseRepository):
    """Repository for storing and querying raw ChEMBL 37 compound documents."""

    def __init__(self, db: Optional[Database] = None):
        super().__init__(COLLECTION_CHEMBL_RAW, db)


class ChEMBLProcessedRepository(ProcessedOntologyRepository):
    """Repository for storing transformed ChEMBL 37 compound terms."""

    def __init__(self, db: Optional[Database] = None):
        BaseRepository.__init__(self, COLLECTION_CHEMBL_PROCESSED, db)


class ChEMBLFinalRepository(FinalOntologyRepository):
    """Repository for querying final ChEMBL 37 ontology collection."""

    def __init__(self, db: Optional[Database] = None):
        super().__init__(db)
        self.collection = self.db[COLLECTION_CHEMBL_ONTOLOGY]
        self.collection_name = COLLECTION_CHEMBL_ONTOLOGY
        self.processed_repo = ChEMBLProcessedRepository(db)


class LoggingRepository:
    """Repository for managing mapping_logs, validation_logs, and import_logs."""

    def __init__(self, db: Optional[Database] = None):
        self.db = db if db is not None else get_db()

    def log_mapping_run(self, total_raw: int, total_mapped: int, details: Optional[Dict[str, Any]] = None) -> None:
        """Record mapping execution log."""
        doc = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_raw": total_raw,
            "total_mapped": total_mapped,
            "details": details or {},
        }
        self.db[COLLECTION_MAPPING_LOGS].insert_one(doc)

    def log_import_run(self, export_type: str, record_count: int, file_path: str) -> None:
        """Record export/import execution log."""
        doc = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "export_type": export_type,
            "record_count": record_count,
            "file_path": file_path,
        }
        self.db[COLLECTION_IMPORT_LOGS].insert_one(doc)
