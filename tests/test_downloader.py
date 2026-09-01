"""
Unit tests for raw data repository and BFS hierarchy downloader.
"""

import pytest
from unittest.mock import MagicMock, patch
from database.repositories import RawDataRepository
from extractor.downloader import ICD11Downloader


def test_raw_repository_insert_and_get_uris():
    mock_db = MagicMock()
    mock_col = MagicMock()
    mock_db.__getitem__.return_value = mock_col

    repo = RawDataRepository(db=mock_db)

    # Test single insert
    raw_data = {"@id": "http://id.who.int/icd/release/11/2024-01/mms/12345", "code": "A00"}
    uri = repo.insert_or_update_raw_entity(raw_data)

    assert uri == "http://id.who.int/icd/release/11/2024-01/mms/12345"
    mock_col.replace_one.assert_called_once()


def test_downloader_bfs_traversal():
    mock_client = MagicMock()
    mock_repo = MagicMock()

    # Setup mock existing URIs in repo
    mock_repo.get_all_downloaded_uris.return_value = set()

    # Root payload
    root_payload = {
        "@id": "http://id.who.int/icd/release/11/2024-01/mms",
        "child": [
            "http://id.who.int/icd/release/11/2024-01/mms/chapter1",
            "http://id.who.int/icd/release/11/2024-01/mms/chapter2",
        ],
    }

    # Child payloads
    chapter1 = {
        "@id": "http://id.who.int/icd/release/11/2024-01/mms/chapter1",
        "code": "01",
        "title": {"@value": "Certain infectious diseases"},
        "child": ["http://id.who.int/icd/release/11/2024-01/mms/sub1"],
    }
    chapter2 = {
        "@id": "http://id.who.int/icd/release/11/2024-01/mms/chapter2",
        "code": "02",
        "title": {"@value": "Neoplasms"},
        "child": [],
    }
    sub1 = {
        "@id": "http://id.who.int/icd/release/11/2024-01/mms/sub1",
        "code": "1A00",
        "title": {"@value": "Cholera"},
        "child": [],
    }

    mock_client.get_linearization_root.return_value = root_payload
    mock_client.get_entity.side_effect = lambda uri: {
        "http://id.who.int/icd/release/11/2024-01/mms/chapter1": chapter1,
        "http://id.who.int/icd/release/11/2024-01/mms/chapter2": chapter2,
        "http://id.who.int/icd/release/11/2024-01/mms/sub1": sub1,
    }[uri]

    downloader = ICD11Downloader(client=mock_client, repo=mock_repo)
    count = downloader.download_hierarchy()

    assert count == 3
    assert mock_repo.bulk_insert_raw_entities.call_count >= 1


def test_downloader_resume_checkpoint():
    mock_client = MagicMock()
    mock_repo = MagicMock()

    # Simulate chapter1 already downloaded in DB
    already_in_db = {"http://id.who.int/icd/release/11/2024-01/mms/chapter1"}
    mock_repo.get_all_downloaded_uris.return_value = already_in_db

    root_payload = {
        "@id": "http://id.who.int/icd/release/11/2024-01/mms",
        "child": [
            "http://id.who.int/icd/release/11/2024-01/mms/chapter1",
            "http://id.who.int/icd/release/11/2024-01/mms/chapter2",
        ],
    }

    chapter2 = {
        "@id": "http://id.who.int/icd/release/11/2024-01/mms/chapter2",
        "code": "02",
        "child": [],
    }

    mock_client.get_linearization_root.return_value = root_payload
    mock_client.get_entity.return_value = chapter2

    downloader = ICD11Downloader(client=mock_client, repo=mock_repo)
    count = downloader.download_hierarchy()

    # Only chapter2 should be fetched; chapter1 was skipped due to resume checkpoint
    assert count == 1
    mock_client.get_entity.assert_called_once_with("http://id.who.int/icd/release/11/2024-01/mms/chapter2")
