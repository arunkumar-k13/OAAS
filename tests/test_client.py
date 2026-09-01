"""
Unit tests for ICD11Client API methods and endpoint resolving.
"""

import pytest
from unittest.mock import patch, MagicMock
from extractor.endpoints import get_entity_endpoint, get_linearization_base_endpoint
from extractor.icd11_client import ICD11Client


def test_endpoint_resolution():
    base = get_linearization_base_endpoint()
    assert base.endswith("/mms") or "mms" in base

    full_url = "https://id.who.int/icd/release/11/2024-01/mms/1630407678"
    assert get_entity_endpoint(full_url) == full_url

    rel_endpoint = get_entity_endpoint("1630407678")
    assert rel_endpoint.endswith("/1630407678")


@patch.object(ICD11Client, "_get")
def test_client_get_entity(mock_get):
    mock_get.return_value = {
        "@id": "http://id.who.int/icd/release/11/2024-01/mms/1435254666",
        "code": "1A00",
        "title": {"@value": "Cholera", "@language": "en"},
    }

    client = ICD11Client()
    entity = client.get_entity("1435254666")

    assert entity["code"] == "1A00"
    assert entity["title"]["@value"] == "Cholera"
    mock_get.assert_called_once()
