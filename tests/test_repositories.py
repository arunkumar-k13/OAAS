"""
Unit tests for FinalOntologyRepository and LoggingRepository operations.
"""

import pytest
from unittest.mock import MagicMock
from database.repositories import FinalOntologyRepository, LoggingRepository, ProcessedOntologyRepository


def test_final_ontology_repository_queries():
    mock_db = MagicMock()
    mock_col = MagicMock()
    mock_db.__getitem__.return_value = mock_col

    sample_term = {
        "Name": "Cholera",
        "Term ID": "1A00",
        "ID": "1435254666",
        "URI": "http://id.who.int/icd/release/11/2024-01/mms/1435254666",
        "subClassOf": ["http://id.who.int/icd/release/11/2024-01/mms/chap1"],
        "superClassOf": [],
    }

    mock_col.find_one.return_value = sample_term

    repo = FinalOntologyRepository(db=mock_db)

    # Test get_by_id
    term = repo.get_by_id("1435254666")
    assert term["Name"] == "Cholera"
    assert term["Term ID"] == "1A00"

    # Test get_by_term_id
    term_by_code = repo.get_by_term_id("1A00")
    assert term_by_code["ID"] == "1435254666"


def test_logging_repository():
    mock_db = MagicMock()
    mock_col = MagicMock()
    mock_db.__getitem__.return_value = mock_col

    log_repo = LoggingRepository(db=mock_db)
    log_repo.log_mapping_run(total_raw=10, total_mapped=10)

    mock_col.insert_one.assert_called_once()
    saved_doc = mock_col.insert_one.call_args[0][0]
    assert saved_doc["total_raw"] == 10
    assert saved_doc["total_mapped"] == 10
    assert "timestamp" in saved_doc
