"""
Endpoint definitions and URL resolution for WHO ICD-11 REST API.
"""

from typing import Optional
from config.settings import settings


def get_token_endpoint() -> str:
    """Return WHO OAuth2 token endpoint URL."""
    return settings.who_auth_url.strip()


def get_linearization_base_endpoint() -> str:
    """Return base endpoint URL for linearizations (e.g., MMS)."""
    base = settings.who_api_base_url.rstrip("/")
    release = settings.icd11_release_id.strip()
    linearization = settings.icd11_linearization.strip()
    return f"{base}/release/11/{release}/{linearization}"


def get_foundation_base_endpoint() -> str:
    """Return base endpoint URL for ICD-11 foundation entities."""
    base = settings.who_api_base_url.rstrip("/")
    return f"{base}/entity"


def get_icd10_base_endpoint() -> str:
    """Return base endpoint URL for WHO ICD-10 2019 release."""
    base = settings.who_api_base_url.rstrip("/")
    return f"{base}/release/10/2019"


def get_entity_endpoint(entity_identifier: str) -> str:
    """
    Resolve full endpoint URL for a given entity URI, relative path, or code.

    Args:
        entity_identifier: Entity code, relative URI/ID, or full URI.

    Returns:
        Full absolute HTTP URL for the WHO API request.
    """
    cleaned = entity_identifier.strip()
    if cleaned.startswith("http://"):
        cleaned = "https://" + cleaned[7:]
    if cleaned.startswith("https://"):
        return cleaned

    base = get_linearization_base_endpoint()
    if cleaned.startswith("/"):
        return f"{settings.who_api_base_url.rstrip('/')}{cleaned}".replace("http://", "https://")
    
    return f"{base}/{cleaned}"
