"""Common imports module to reduce import duplication across the codebase."""

# Flask imports

# JWT imports

# Marshmallow imports
from marshmallow import Schema

# Logging imports
from app.utils.logging_config import (
    get_logger,
)

# Common validation imports

# Extension imports

# Common field imports

# Decorator imports

# Error handling imports


# Response helper imports


# Utility function to get logger for a module
def get_module_logger(module_name: str):
    """Get a logger instance for a module.

    Args:
        module_name: The module name (usually __name__)

    Returns:
        Logger instance
    """
    return get_logger(module_name)


def get_utc_timestamp(with_z_suffix: bool = False) -> str:
    """Get current UTC timestamp in ISO format.

    Args:
        with_z_suffix: Whether to append 'Z' to indicate UTC timezone

    Returns:
        ISO formatted timestamp string
    """
    from datetime import datetime

    timestamp = datetime.utcnow().isoformat()
    return timestamp + "Z" if with_z_suffix else timestamp


# Common schema base classes
class BaseRequestSchema(Schema):
    """Base schema for request validation."""


class BaseResponseSchema(Schema):
    """Base schema for response serialization."""
