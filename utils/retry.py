"""
Retry and resilience utilities using tenacity.
"""

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import httpx
import requests

from config.settings import settings
from utils.logger import api_logger

# Standard API retry decorator configuration
api_retry_decorator = retry(
    reraise=True,
    stop=stop_after_attempt(settings.max_retries),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.HTTPError, requests.RequestException)),
    before_sleep=lambda retry_state: api_logger.warning(
        f"API call failed (attempt {retry_state.attempt_number}/{settings.max_retries}). Retrying in {retry_state.next_action.sleep}s..."
    ),
)
