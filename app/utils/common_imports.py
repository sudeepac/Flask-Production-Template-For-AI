"""Common imports module to reduce import duplication across the codebase."""

# Flask imports
from flask import Blueprint, Flask, current_app, jsonify, request

# JWT imports
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)

# Marshmallow imports
from marshmallow import Schema, ValidationError, fields, post_load, pre_dump, validate

# Common validation imports
from marshmallow.validate import Length, OneOf, Range

# Extension imports
from app.extensions import cache, db, jwt, limiter

# Common field imports
from app.schemas.common_fields import (
    CommonFields,
    MetadataMixin,
    StatusMixin,
    TimestampMixin,
)

# Decorator imports
from app.utils.decorators import (
    handle_api_errors,
    log_endpoint_access,
    validate_json_input,
)

# Error handling imports
from app.utils.error_handlers import (
    APIError,
    ConflictAPIError,
    ForbiddenAPIError,
    NotFoundAPIError,
    RateLimitAPIError,
    ServiceUnavailableAPIError,
    UnauthorizedAPIError,
    ValidationAPIError,
)

# Logging imports
from app.utils.logging_config import (
    PerformanceLogger,
    get_logger,
    log_performance,
    log_security_event,
)

# Response helper imports
from app.utils.response_helpers import (
    error_response,
    handle_common_exceptions,
    paginated_response,
    success_response,
)


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

    pass


class BaseResponseSchema(Schema):
    """Base schema for response serialization."""

    pass
