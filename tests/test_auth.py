"""
Unit tests for WHO ICD-11 OAuth2 authentication handler.
"""

import time
import pytest
from unittest.mock import patch, MagicMock
from extractor.auth import WHOAuth
from models.responses import TokenResponse


@pytest.fixture
def clean_auth_singleton():
    """Reset WHOAuth singleton before each test."""
    auth = WHOAuth()
    auth._access_token = None
    auth._token_expiry_timestamp = 0.0
    return auth


@patch.object(WHOAuth, "_fetch_new_token")
def test_get_token_fetches_and_caches(mock_fetch, clean_auth_singleton):
    mock_fetch.return_value = TokenResponse(
        access_token="test_mock_token_123",
        token_type="Bearer",
        expires_in=3600,
    )

    auth = clean_auth_singleton
    token1 = auth.get_token()
    token2 = auth.get_token()

    assert token1 == "test_mock_token_123"
    assert token2 == "test_mock_token_123"
    assert mock_fetch.call_count == 1


@patch.object(WHOAuth, "_fetch_new_token")
def test_get_token_refreshes_when_expired(mock_fetch, clean_auth_singleton):
    mock_fetch.return_value = TokenResponse(
        access_token="initial_token",
        token_type="Bearer",
        expires_in=10,  # Short expiry
    )

    auth = clean_auth_singleton
    token1 = auth.get_token()
    assert token1 == "initial_token"

    # Simulate token expiration
    auth._token_expiry_timestamp = time.time() - 100

    mock_fetch.return_value = TokenResponse(
        access_token="refreshed_token",
        token_type="Bearer",
        expires_in=3600,
    )

    token2 = auth.get_token()
    assert token2 == "refreshed_token"
    assert mock_fetch.call_count == 2


@patch.object(WHOAuth, "get_token")
def test_get_auth_headers(mock_get_token, clean_auth_singleton):
    mock_get_token.return_value = "valid_bearer_token"
    auth = clean_auth_singleton
    headers = auth.get_auth_headers()

    assert headers["Authorization"] == "Bearer valid_bearer_token"
    assert headers["Accept"] == "application/json"
    assert headers["API-Version"] == "v2"
