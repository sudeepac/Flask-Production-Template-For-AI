"""Enhanced Error Handlers.

This module provides comprehensive error handling utilities for the
Flask application.
Includes custom exceptions, error formatters, and centralized error handling.

Features:
- Custom exception classes
- Structured error responses
- Request ID tracking
- Error logging with context
- Validation error handling
- Rate limiting error handling

Usage:
    from app.utils.error_handlers import register_error_handlers

    # Register with Flask app
    register_error_handlers(app)
"""

import logging
import traceback
from datetime import datetime
from typing import Any, Dict, Tuple
from uuid import uuid4

from flask import Flask, current_app, g, request
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


def handle_validation_error(error: ValidationError):
    """Handle Marshmallow validation errors.

    This is a standalone function that can be imported and used
    in routes for manual validation error handling.

    Args:
        error: ValidationError instance

    Returns:
        Tuple of (response_dict, status_code)
    """

    # Log the validation error
    request_id = getattr(g, "request_id", str(uuid4()))
    logger.warning(
        f"Validation error [{request_id}]: {error.messages}",
        extra={
            "request_id": request_id,
            "validation_errors": error.messages,
            "endpoint": request.endpoint if request else None,
        },
    )

    return {
        "error": {
            "code": "validation_error",
            "message": "Request validation failed",
            "details": {"field_errors": error.messages},
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
    }, 400


class APIError(Exception):
    """Base API exception class.

    Attributes:
        message: Error message
        status_code: HTTP status code
        error_code: Application-specific error code
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = None,
        details: Dict[str, Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__.lower()
        self.details = details or {}


class ValidationAPIError(APIError):
    """Validation error exception."""

    def __init__(
        self, message: str = "Validation failed", details: Dict[str, Any] = None
    ):
        super().__init__(message, 400, "validation_error", details)


class NotFoundAPIError(APIError):
    """Resource not found exception."""

    def __init__(self, message: str = "Resource not found", resource_type: str = None):
        details = {"resource_type": resource_type} if resource_type else {}
        super().__init__(message, 404, "not_found", details)


class UnauthorizedAPIError(APIError):
    """Unauthorized access exception."""

    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(message, 401, "unauthorized")


class ForbiddenAPIError(APIError):
    """Forbidden access exception."""

    def __init__(self, message: str = "Access forbidden"):
        super().__init__(message, 403, "forbidden")


class ConflictAPIError(APIError):
    """Resource conflict exception."""

    def __init__(
        self, message: str = "Resource conflict", details: Dict[str, Any] = None
    ):
        super().__init__(message, 409, "conflict", details)


class RateLimitAPIError(APIError):
    """Rate limit exceeded exception."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(message, 429, "rate_limit_exceeded", details)


class ServiceUnavailableAPIError(APIError):
    """Service unavailable exception."""

    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(message, 503, "service_unavailable")


def get_request_id() -> str:
    """Get or generate request ID for tracking.

    Returns:
        Request ID string
    """
    if not hasattr(g, "request_id"):
        g.request_id = str(uuid4())
    return g.request_id


def format_error_response(
    error_code: str,
    message: str,
    status_code: int,
    details: Dict[str, Any] = None,
    request_id: str = None,
) -> Tuple[Dict[str, Any], int]:
    """Format standardized error response.

    Args:
        error_code: Application-specific error code
        message: Human-readable error message
        status_code: HTTP status code
        details: Additional error details
        request_id: Request tracking ID

    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {
        "error": {
            "code": error_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id or get_request_id(),
        }
    }

    if details:
        response["error"]["details"] = details

    # Add debug info in development
    if current_app.debug and hasattr(g, "error_traceback"):
        response["error"]["traceback"] = g.error_traceback

    return response, status_code


def log_error(
    error: Exception, context: Dict[str, Any] = None, level: int = logging.ERROR
) -> None:
    """Log error with context information.

    Args:
        error: Exception instance
        context: Additional context information
        level: Logging level
    """
    request_id = get_request_id()

    # Build log context
    log_context = {
        "request_id": request_id,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "endpoint": request.endpoint if request else None,
        "method": request.method if request else None,
        "url": request.url if request else None,
        "user_agent": request.headers.get("User-Agent") if request else None,
        "remote_addr": request.remote_addr if request else None,
    }

    if context:
        log_context.update(context)

    # Log with structured data
    logger.log(
        level,
        f"Error occurred: {str(error)}",
        extra={"context": log_context},
        exc_info=True,
    )

    # Store traceback for debug mode
    if current_app.debug:
        g.error_traceback = traceback.format_exc().split("\n")


def register_error_handlers(app: Flask) -> None:
    """Register comprehensive error handlers with the Flask app.

    Args:
        app: Flask application instance
    """

    @app.before_request
    def before_request():
        """Initialize request tracking."""
        g.request_id = str(uuid4())
        g.start_time = datetime.utcnow()

    @app.after_request
    def after_request(response):
        """Log request completion."""
        if hasattr(g, "start_time"):
            duration = (datetime.utcnow() - g.start_time).total_seconds()
            logger.info(
                f"Request completed: {request.method} {request.path}",
                extra={
                    "context": {
                        "request_id": get_request_id(),
                        "method": request.method,
                        "path": request.path,
                        "status_code": response.status_code,
                        "duration_seconds": duration,
                    }
                },
            )
        return response

    @app.errorhandler(APIError)
    def handle_api_error(error: APIError):
        """Handle custom API errors."""
        log_error(error, {"error_code": error.error_code})
        return format_error_response(
            error.error_code, error.message, error.status_code, error.details
        )

    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError):
        """Handle Marshmallow validation errors."""
        log_error(error, {"validation_errors": error.messages}, logging.WARNING)
        return format_error_response(
            "validation_error",
            "Request validation failed",
            400,
            {"field_errors": error.messages},
        )

    @app.errorhandler(SQLAlchemyError)
    def handle_database_error(error: SQLAlchemyError):
        """Handle database errors."""
        from app.extensions import db

        db.session.rollback()

        # Handle specific database errors
        if isinstance(error, IntegrityError):
            log_error(error, {"error_type": "integrity_constraint"}, logging.WARNING)
            return format_error_response(
                "integrity_error",
                "Data integrity constraint violation",
                409,
                {"constraint_type": "database_constraint"},
            )

        log_error(error, {"error_type": "database_error"})
        return format_error_response("database_error", "Database operation failed", 500)

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        """Handle HTTP exceptions."""
        # Don't log client errors (4xx) as errors
        log_level = logging.WARNING if 400 <= error.code < 500 else logging.ERROR
        log_error(error, {"http_status": error.code}, log_level)

        return format_error_response(
            f"http_{error.code}",
            error.description or f"HTTP {error.code} error",
            error.code,
        )

    @app.errorhandler(429)
    def handle_rate_limit_error(error):
        """Handle rate limiting errors."""
        retry_after = getattr(error, "retry_after", None)
        log_error(error, {"retry_after": retry_after}, logging.WARNING)

        return format_error_response(
            "rate_limit_exceeded",
            "Too many requests. Please try again later.",
            429,
            {"retry_after": retry_after},
        )

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        """Handle unexpected errors."""
        log_error(error, {"error_type": "unexpected_error"})

        # Don't expose internal error details in production
        message = str(error) if app.debug else "An unexpected error occurred"

        return format_error_response("internal_server_error", message, 500)

    logger.info("Enhanced error handlers registered")
