"""
Loguru logging infrastructure supporting category-specific log files.
"""

import sys
from pathlib import Path
from loguru import logger
from config.settings import settings
from config.constants import (
    LOG_CATEGORY_API,
    LOG_CATEGORY_MONGO,
    LOG_CATEGORY_MAPPING,
    LOG_CATEGORY_VALIDATION,
    LOG_CATEGORY_EXPORT,
)

# Remove default logger sink
logger.remove()

# Ensure log directory exists
settings.log_dir.mkdir(parents=True, exist_ok=True)

# Console Logger (Standard Output)
logger.add(
    sys.stdout,
    level=settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level:<8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True,
)

# Application-wide main log file
logger.add(
    settings.log_dir / "app.log",
    level=settings.log_level,
    rotation="10 MB",
    retention="14 days",
    compression="zip",
    enqueue=True,
)

# Category-specific Log Files
CATEGORIES = [
    LOG_CATEGORY_API,
    LOG_CATEGORY_MONGO,
    LOG_CATEGORY_MAPPING,
    LOG_CATEGORY_VALIDATION,
    LOG_CATEGORY_EXPORT,
]

for category in CATEGORIES:
    logger.add(
        settings.log_dir / f"{category}.log",
        level="DEBUG",
        filter=lambda record, cat=category: record["extra"].get("category") == cat,
        rotation="10 MB",
        retention="14 days",
        enqueue=True,
    )


def get_logger(category: str = "app"):
    """
    Get a contextualized logger bound to a specific category.

    Args:
        category: Category string ('api', 'mongo', 'mapping', 'validation', 'export')

    Returns:
        Loguru Logger instance bound with category extra field.
    """
    return logger.bind(category=category)


# Exposed Category Loggers
api_logger = get_logger(LOG_CATEGORY_API)
mongo_logger = get_logger(LOG_CATEGORY_MONGO)
mapping_logger = get_logger(LOG_CATEGORY_MAPPING)
validation_logger = get_logger(LOG_CATEGORY_VALIDATION)
export_logger = get_logger(LOG_CATEGORY_EXPORT)
