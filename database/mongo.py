"""
MongoDB connection manager and client provider using PyMongo.
"""

from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from config.settings import settings
from utils.logger import mongo_logger


class MongoDBManager:
    """Manages connection lifecycle and provides database access to MongoDB."""

    _instance: Optional["MongoDBManager"] = None
    _client: Optional[MongoClient] = None

    def __new__(cls) -> "MongoDBManager":
        if cls._instance is None:
            cls._instance = super(MongoDBManager, cls).__new__(cls)
        return cls._instance

    def connect(self) -> MongoClient:
        """Establish connection to MongoDB if not already connected."""
        if self._client is None:
            try:
                mongo_logger.info(
                    f"Connecting to MongoDB at {settings.mongo_uri} (Database: {settings.mongo_db_name})"
                )
                self._client = MongoClient(
                    settings.mongo_uri,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=5000,
                )
                # Verify connection with a ping command
                self._client.admin.command("ping")
                mongo_logger.info("Successfully connected to MongoDB.")
            except (ConnectionFailure, ServerSelectionTimeoutError) as err:
                mongo_logger.error(f"Failed to connect to MongoDB: {err}")
                self._client = None
                raise RuntimeError(f"MongoDB connection failed: {err}") from err
        return self._client

    def get_database(self) -> Database:
        """Return reference to the target database ('oaas')."""
        client = self.connect()
        return client[settings.mongo_db_name]

    def check_health(self) -> bool:
        """Check if MongoDB is reachable and active."""
        try:
            client = self.connect()
            client.admin.command("ping")
            return True
        except Exception as err:
            mongo_logger.warning(f"MongoDB health check failed: {err}")
            return False

    def close(self) -> None:
        """Close active MongoDB client connection."""
        if self._client is not None:
            mongo_logger.info("Closing MongoDB connection.")
            self._client.close()
            self._client = None


# Module-level convenience functions
def get_db() -> Database:
    """Get MongoDB database instance."""
    return MongoDBManager().get_database()


def db_healthcheck() -> bool:
    """Perform MongoDB connection health check."""
    return MongoDBManager().check_health()
