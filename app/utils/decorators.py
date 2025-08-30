"""Decorators for common functionality across the application."""

import functools
from typing import Any, Callable

from flask import request
from marshmallow import ValidationError as MarshmallowValidationError

from app.utils.error_handlers import (
    APIError,
    NotFoundAPIError,
    RateLimitAPIError,
    UnauthorizedAPIError,
    ValidationAPIError,
)
from app.utils.logging_config import get_logger
from app.utils.security import log_security_event

logger = get_logger(__name__)


def handle_api_errors(f: Callable) -> Callable:
    """Decorator to handle common API errors and exceptions.

    This decorator centralizes error handling for route handlers,
    reducing code duplication across the application.
    """

    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        """Handle API errors for the decorated function."""
        try:
            return f(*args, **kwargs)
        except MarshmallowValidationError as e:
            logger.warning(f"Validation error in {f.__name__}: {e.messages}")
            log_security_event(
                event_type="validation_error",
                details={"endpoint": request.endpoint, "errors": e.messages},
            )
            raise ValidationAPIError("Invalid input data", details=e.messages)
        except ValidationAPIError as e:
            logger.warning(f"Validation API error in {f.__name__}: {e}")
            raise
        except RateLimitAPIError as e:
            logger.warning(f"Rate limit exceeded in {f.__name__}: {e}")
            raise
        except NotFoundAPIError as e:
            logger.warning(f"Resource not found in {f.__name__}: {e}")
            raise
        except UnauthorizedAPIError as e:
            logger.warning(f"Unauthorized access in {f.__name__}: {e}")
            raise
        except APIError as e:
            logger.error(f"API error in {f.__name__}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {str(e)}")
            log_security_event(
                event_type="unexpected_error",
                details={"endpoint": request.endpoint, "error": str(e)},
            )
            raise APIError("An unexpected error occurred")

    return decorated_function


def validate_json_input(schema_class: Any, location: str = "json") -> Callable:
    """Decorator to validate JSON input using a Marshmallow schema.

    Args:
        schema_class: The Marshmallow schema class to use for validation
        location: Where to get the data from ('json', 'form', 'args')
    """

    def decorator(f: Callable) -> Callable:
        """Decorator function for JSON input validation."""

        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            """Validate input data using the provided schema."""
            schema = schema_class()

            if location == "json":
                data = request.get_json()
                if not data:
                    raise ValidationAPIError("No JSON data provided")
            elif location == "form":
                data = request.form.to_dict()
            elif location == "args":
                data = request.args.to_dict()
            else:
                raise ValueError(f"Invalid location: {location}")

            try:
                validated_data = schema.load(data)
                return f(validated_data, *args, **kwargs)
            except MarshmallowValidationError as e:
                logger.warning(
                    f"Schema validation failed in {f.__name__}: {e.messages}"
                )
                raise ValidationAPIError("Invalid input data", details=e.messages)

        return decorated_function

    return decorator


def log_endpoint_access(f: Callable) -> Callable:
    """Decorator to log endpoint access for monitoring and debugging."""

    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info(
            f"Accessing endpoint: {request.endpoint} - " f"Method: {request.method}"
        )
        return f(*args, **kwargs)

    return decorated_function
