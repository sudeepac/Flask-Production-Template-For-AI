"""Response helper utilities for consistent API responses."""

from functools import wraps
from typing import Any, Dict, Optional, Tuple

from flask import jsonify
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.utils.error_handlers import format_error_response, get_request_id, log_error


def error_response(
    message: str,
    status_code: int = 400,
    error_code: str = None,
    details: Dict[str, Any] = None,
) -> Tuple[Dict[str, Any], int]:
    """Create a standardized error response.

    Args:
        message: Error message
        status_code: HTTP status code
        error_code: Application-specific error code
        details: Additional error details

    Returns:
        Tuple of (response_dict, status_code)
    """
    if not error_code:
        error_code = f"error_{status_code}"

    response, _ = format_error_response(
        error_code=error_code, message=message, status_code=status_code, details=details
    )

    return jsonify(response), status_code


def success_response(
    message: str = "Success",
    data: Optional[Dict[str, Any]] = None,
    status_code: int = 200,
    flatten_data: bool = False,
) -> Tuple[Dict[str, Any], int]:
    """Create a standardized success response.

    Args:
        message: Success message
        data: Response data
        status_code: HTTP status code
        flatten_data: If True, merge data directly into response
            (for backward compatibility)

    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {"message": message, "request_id": get_request_id()}

    if data is not None:
        if flatten_data:
            # Merge data directly into response for backward compatibility
            response.update(data)
        else:
            response["data"] = data

    return jsonify(response), status_code


def validation_error_response(error: ValidationError) -> Tuple[Dict[str, Any], int]:
    """Create a standardized validation error response.

    Args:
        error: Marshmallow ValidationError

    Returns:
        Tuple of (response_dict, status_code)
    """
    details = {}
    for field, messages in error.messages.items():
        details[field] = messages if isinstance(messages, list) else [messages]

    return error_response(
        message="Validation failed",
        status_code=400,
        error_code="validation_error",
        details=details,
    )


def handle_common_exceptions(func):
    """Decorator to handle common exceptions in routes.

    This decorator catches common exceptions and \
        returns standardized error responses,
    reducing boilerplate code in route handlers.

    Args:
        func: Route function to wrap

    Returns:
        Wrapped function
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        """Wrapper function that handles validation errors."""
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            log_error(e, {"route": func.__name__})
            return validation_error_response(e)
        except IntegrityError as e:
            log_error(e, {"route": func.__name__})
            return error_response(
                message="Data integrity constraint violated",
                status_code=409,
                error_code="integrity_error",
            )
        except SQLAlchemyError as e:
            log_error(e, {"route": func.__name__})
            return error_response(
                message="Database operation failed",
                status_code=500,
                error_code="database_error",
            )
        except Exception as e:
            log_error(e, {"route": func.__name__})
            return error_response(
                message="An unexpected error occurred",
                status_code=500,
                error_code="internal_server_error",
            )

    return wrapper


# Common error responses for frequent use cases
def no_data_provided_error():
    """Standard response for missing request data."""
    return error_response("No data provided", 400, "no_data")


def missing_fields_error(fields: list):
    """Standard response for missing required fields."""
    field_list = ", ".join(fields)
    return error_response(
        f"Required fields missing: {field_list}",
        400,
        "missing_fields",
        {"missing_fields": fields},
    )


def invalid_credentials_error():
    """Standard response for authentication failures."""
    return error_response("Invalid credentials", 401, "invalid_credentials")


def user_not_found_error():
    """Standard response for user not found."""
    return error_response("User not found", 404, "user_not_found")


def already_exists_error(resource: str):
    """Standard response for resource conflicts."""
    return error_response(
        f"{resource} already exists", 409, "resource_exists", {"resource": resource}
    )


def token_revoked_error():
    """Standard response for revoked tokens."""
    return error_response("Token has been revoked", 401, "token_revoked")
