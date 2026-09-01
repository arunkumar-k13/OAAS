"""
OAuth2 Authentication handler for WHO ICD-11 API with automatic caching and refresh.
"""

import time
import threading
from typing import Dict, Optional
import httpx

from config.settings import settings
from extractor.endpoints import get_token_endpoint
from models.responses import TokenResponse
from utils.logger import api_logger
from utils.retry import api_retry_decorator


class WHOAuth:
    """Manages Client Credentials Grant authentication and token caching for WHO ICD-11 API."""

    _instance: Optional["WHOAuth"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "WHOAuth":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(WHOAuth, cls).__new__(cls)
                cls._instance._access_token = None
                cls._instance._token_expiry_timestamp = 0.0
            return cls._instance

    @api_retry_decorator
    def _fetch_new_token(self) -> TokenResponse:
        """Request a fresh OAuth2 access token from WHO Access Management."""
        url = get_token_endpoint()
        client_id = settings.who_client_id.strip()
        client_secret = settings.who_client_secret.strip()

        if not client_id or not client_secret:
            api_logger.warning("WHO API Client ID or Client Secret is missing in environment settings.")

        payload = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "icdapi_access",
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        api_logger.info(f"Requesting WHO API access token from {url}")
        with httpx.Client(timeout=settings.request_timeout_seconds, follow_redirects=True) as client:
            response = client.post(url, data=payload, headers=headers)
            response.raise_for_status()
            token_data = TokenResponse.model_validate(response.json())
            return token_data

    def get_token(self, force_refresh: bool = False) -> str:
        """
        Get active OAuth2 access token. Refreshes token if expired or forced.

        Args:
            force_refresh: If True, force fetch a new token regardless of expiration.

        Returns:
            Bearer access token string.
        """
        with self._lock:
            now = time.time()
            # Buffer of 60 seconds before actual expiration
            if force_refresh or not self._access_token or now >= (self._token_expiry_timestamp - 60):
                api_logger.info("Access token expired or missing. Refreshing token...")
                try:
                    token_data = self._fetch_new_token()
                    self._access_token = token_data.access_token
                    self._token_expiry_timestamp = now + token_data.expires_in
                    api_logger.info(f"Successfully obtained WHO API access token (expires in {token_data.expires_in}s).")
                except Exception as err:
                    api_logger.error(f"Failed to fetch WHO API access token: {err}")
                    raise RuntimeError(f"Authentication failed: {err}") from err

            return self._access_token

    def get_auth_headers(self) -> Dict[str, str]:
        """Generate Authorization and API headers for HTTP requests."""
        token = self.get_token()
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Accept-Language": settings.icd11_language,
            "API-Version": "v2",
        }


# Exposed convenience singleton instance
auth_manager = WHOAuth()
