"""
Phase 1 sanity tests for configuration, settings, and database connection.
"""

from config.settings import settings
from config.constants import DEFAULT_DB_NAME, ALL_COLLECTIONS
from database.mongo import MongoDBManager


def test_settings_load():
    assert settings.mongo_db_name == DEFAULT_DB_NAME
    assert settings.who_api_base_url == "https://id.who.int/icd"


def test_constants_collections():
    assert len(ALL_COLLECTIONS) == 6
    assert "icd11_raw" in ALL_COLLECTIONS
    assert "ICD11_2026_ONTOLOGY" in ALL_COLLECTIONS


def test_mongo_manager_singleton():
    mgr1 = MongoDBManager()
    mgr2 = MongoDBManager()
    assert mgr1 is mgr2
