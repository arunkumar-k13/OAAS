"""
Production HTTP client for WHO ICD-11 API endpoints.
"""

import time
from typing import Any, Dict, List, Optional
import httpx

from config.settings import settings
from extractor.auth import WHOAuth, auth_manager
from extractor.endpoints import (
    get_linearization_base_endpoint,
    get_entity_endpoint,
    get_foundation_base_endpoint,
)
from utils.logger import api_logger
from utils.retry import api_retry_decorator


class ICD11Client:
    """Client for fetching entities, linearizations, and search results from WHO ICD-11 API."""

    def __init__(self, auth: Optional[WHOAuth] = None):
        self.auth = auth or auth_manager
        self.timeout = settings.request_timeout_seconds
        self.rate_limit_delay = settings.rate_limit_delay

    def _get_headers(self) -> Dict[str, str]:
        """Obtain authorization and standard request headers."""
        return self.auth.get_auth_headers()

    @api_retry_decorator
    def _get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute GET request with retries, rate limiting, and 429 response handling.
        """
        if self.rate_limit_delay > 0:
            time.sleep(self.rate_limit_delay)

        headers = self._get_headers()
        api_logger.debug(f"GET Request to WHO API: {url}")

        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            response = client.get(url, headers=headers, params=params)

            # Handle Rate Limiting (HTTP 429)
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 5))
                api_logger.warning(f"Rate limited by WHO API (429). Waiting {retry_after}s...")
                time.sleep(retry_after)
                # Retry once after sleep
                response = client.get(url, headers=headers, params=params)

            # Handle Expired Token (HTTP 401)
            if response.status_code == 401:
                api_logger.warning("Received 401 Unauthorized from WHO API. Force refreshing token...")
                headers = self.auth.get_auth_headers()
                response = client.get(url, headers=headers, params=params)

            response.raise_for_status()
            return response.json()

    def get_linearization_root(self) -> Dict[str, Any]:
        """Fetch top-level MMS linearization root concept (Chapters list)."""
        url = get_linearization_base_endpoint()
        api_logger.info(f"Fetching ICD-11 linearization root from {url}")
        return self._get(url)

    def get_entity(self, entity_id_or_uri: str) -> Dict[str, Any]:
        """
        Fetch entity payload by entity ID, path, or full URI.

        Args:
            entity_id_or_uri: Entity URI (e.g. 'http://id.who.int/icd/release/11/2024-01/mms/1630407678')
                              or ID ('1630407678').

        Returns:
            JSON dictionary containing WHO entity properties.
        """
        url = get_entity_endpoint(entity_id_or_uri)
        return self._get(url)

    def get_entity_by_url(self, url: str) -> Dict[str, Any]:
        """Fetch raw JSON payload for an explicit WHO API URL."""
        return self._get(url)

    def search_entities(self, query: str) -> Dict[str, Any]:
        """Search ICD-11 entities by text query."""
        url = f"{get_linearization_base_endpoint()}/search"
        params = {"q": query}
        api_logger.info(f"Searching ICD-11 API for query: '{query}'")
        return self._get(url, params=params)
