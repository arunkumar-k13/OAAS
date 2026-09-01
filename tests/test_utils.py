"""
Unit tests for helper utilities, retry mechanisms, and endpoint builders.
"""

import pytest
from unittest.mock import MagicMock
from utils.helpers import sanitize_string, ensure_list
from extractor.endpoints import (
    get_token_endpoint,
    get_linearization_base_endpoint,
    get_foundation_base_endpoint,
    get_entity_endpoint,
)


def test_helpers_sanitize_string():
    assert sanitize_string("  hello world  \n") == "hello world"
    assert sanitize_string(None) == ""


def test_helpers_ensure_list():
    assert ensure_list(None) == []
    assert ensure_list("item") == ["item"]
    assert ensure_list(["item1", "item2"]) == ["item1", "item2"]


def test_endpoint_builders():
    token_url = get_token_endpoint()
    assert token_url.endswith("/connect/token")

    linearization_url = get_linearization_base_endpoint()
    assert "/release/11/" in linearization_url

    foundation_url = get_foundation_base_endpoint()
    assert foundation_url.endswith("/entity")

    # Absolute vs Relative URI
    abs_url = "https://id.who.int/icd/release/11/2024-01/mms/1234"
    assert get_entity_endpoint(abs_url) == abs_url

    rel_url = get_entity_endpoint("/1234")
    assert rel_url.endswith("/1234")
