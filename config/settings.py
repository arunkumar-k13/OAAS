"""
Application configuration settings powered by Pydantic Settings.
"""

import os
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from config.constants import BASE_DIR, LOGS_DIR, OUTPUT_DIR, DEFAULT_DB_NAME


class Settings(BaseSettings):
    """Central settings management for ICD-11 ETL pipeline."""
    
    # MongoDB
    mongo_uri: str = Field(default="mongodb://localhost:27017", alias="MONGO_URI")
    mongo_db_name: str = Field(default=DEFAULT_DB_NAME, alias="MONGO_DB_NAME")

    # WHO ICD-11 API Credentials & Endpoints
    who_client_id: str = Field(default="", alias="WHO_CLIENT_ID")
    who_client_secret: str = Field(default="", alias="WHO_CLIENT_SECRET")
    who_auth_url: str = Field(
        default="https://icdaccessmanagement.who.int/connect/token", alias="WHO_AUTH_URL"
    )
    who_api_base_url: str = Field(
        default="https://id.who.int/icd", alias="WHO_API_BASE_URL"
    )

    # ICD-11 Parameters
    icd11_linearization: str = Field(default="mms", alias="ICD11_LINEARIZATION")
    icd11_release_id: str = Field(default="2024-01", alias="ICD11_RELEASE_ID")
    icd11_language: str = Field(default="en", alias="ICD11_LANGUAGE")

    # Resilience & Performance
    max_retries: int = Field(default=5, alias="MAX_RETRIES")
    request_timeout_seconds: float = Field(default=30.0, alias="REQUEST_TIMEOUT_SECONDS")
    rate_limit_delay: float = Field(default=0.2, alias="RATE_LIMIT_DELAY")

    # Paths & Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_dir: Path = Field(default=LOGS_DIR, alias="LOG_DIR")
    output_dir: Path = Field(default=OUTPUT_DIR, alias="OUTPUT_DIR")

    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def setup_directories(self) -> None:
        """Ensure necessary output and log directories exist."""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)


# Global settings singleton
settings = Settings()
settings.setup_directories()
