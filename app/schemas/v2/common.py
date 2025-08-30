"""Common Schema Classes for v2 API.

This module contains commonly used schemas across the application:
- Error responses
- Success responses
- Pagination
- Metadata
- Standard API wrappers

See CONTRIBUTING.md §5 for schema design guidelines.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from marshmallow import fields, post_load, validate

from app.schemas.common_fields import CommonFields
from app.schemas.v2.base import BaseSchema, MetadataMixin


class ErrorSchema(BaseSchema):
    """Standard error response schema.

    Used for all API error responses to ensure consistency.
    Provides structured error information with optional details.

    Example:
        {
            "success": false,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid input data",
                "details": {
                    "field": "email",
                    "reason": "Invalid email format"
                }
            },
            "timestamp": "2024-01-01T12:00:00.000Z",
            "request_id": "req_123456789"
        }
    """

    success = fields.Bool(dump_default=False, dump_only=True)
    error = fields.Dict(required=True)
    timestamp = CommonFields.created_at
    request_id = fields.Str(dump_only=True)

    # Error details structure
    code = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    message = fields.Str(required=True, validate=validate.Length(min=1, max=500))
    details = fields.Dict(load_default=None)
    field = fields.Str(load_default=None)  # For field-specific errors

    @post_load
    def structure_error(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Structure error data into standard format."""
        error_data = {
            "code": data.get("code", "UNKNOWN_ERROR"),
            "message": data.get("message", "An error occurred"),
        }

        if data.get("details"):
            error_data["details"] = data["details"]

        if data.get("field"):
            error_data["field"] = data["field"]

        return {
            "success": False,
            "error": error_data,
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": data.get("request_id"),
        }


class SuccessSchema(BaseSchema):
    """Standard success response schema.

    Used for successful API responses without specific data payload.

    Example:
        {
            "success": true,
            "message": "Operation completed successfully",
            "timestamp": "2024-01-01T12:00:00.000Z",
            "request_id": "req_123456789"
        }
    """

    success = fields.Bool(dump_default=True, dump_only=True)
    message = fields.Str(dump_default="Success", validate=validate.Length(max=500))
    timestamp = CommonFields.created_at
    request_id = fields.Str(dump_only=True)
    data = fields.Dict(load_default=None)  # Optional data payload


class PaginationSchema(BaseSchema):
    """Pagination metadata schema.

    Provides consistent pagination information for list endpoints.

    Example:
        {
            "page": 1,
            "per_page": 20,
            "total": 150,
            "pages": 8,
            "has_next": true,
            "has_prev": false,
            "next_page": 2,
            "prev_page": null
        }
    """

    page = fields.Int(required=True, validate=validate.Range(min=1))
    per_page = fields.Int(required=True, validate=validate.Range(min=1, max=1000))
    total = fields.Int(required=True, validate=validate.Range(min=0))
    pages = fields.Int(dump_only=True)
    has_next = fields.Bool(dump_only=True)
    has_prev = fields.Bool(dump_only=True)
    next_page = fields.Int(dump_only=True, allow_none=True)
    prev_page = fields.Int(dump_only=True, allow_none=True)

    @post_load
    def calculate_pagination(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Calculate pagination metadata."""
        page = data["page"]
        per_page = data["per_page"]
        total = data["total"]

        pages = (total + per_page - 1) // per_page  # Ceiling division
        has_next = page < pages
        has_prev = page > 1

        data.update(
            {
                "pages": pages,
                "has_next": has_next,
                "has_prev": has_prev,
                "next_page": page + 1 if has_next else None,
                "prev_page": page - 1 if has_prev else None,
            }
        )

        return data


class MetadataSchema(BaseSchema, MetadataMixin):
    """Request/response metadata schema.

    Provides detailed metadata about API requests and responses.

    Example:
        {
            "request_id": "req_123456789",
            "processing_time_ms": 45.2,
            "api_version": "v2",
            "server_timestamp": "2024-01-01T12:00:00.000Z",
            "user_agent": "MyApp/1.0",
            "ip_address": "192.168.1.1",
            "endpoint": "/api/v2/users",
            "method": "GET"
        }
    """

    user_agent = fields.Str(dump_only=True)
    ip_address = fields.Str(dump_only=True)
    endpoint = fields.Str(dump_only=True)
    method = fields.Str(
        dump_only=True,
        validate=validate.OneOf(
            ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]
        ),
    )
    query_params = fields.Dict(dump_only=True)
    response_size_bytes = fields.Int(dump_only=True)


class PaginatedResponseSchema(BaseSchema):
    """Paginated response wrapper schema.

    Combines data, pagination, and metadata for list endpoints.

    Example:
        {
            "success": true,
            "data": [...],
            "pagination": {...},
            "metadata": {...}
        }
    """

    success = fields.Bool(dump_default=True, dump_only=True)
    data = fields.List(fields.Dict(), required=True)
    pagination = fields.Nested(PaginationSchema, required=True)
    metadata = fields.Nested(MetadataSchema, dump_only=True)
    timestamp = CommonFields.created_at


class DataResponseSchema(BaseSchema):
    """Generic data response wrapper schema.

    Standard wrapper for single-item API responses.

    Example:
        {
            "success": true,
            "data": {...},
            "metadata": {...}
        }
    """

    success = fields.Bool(dump_default=True, dump_only=True)
    data = fields.Dict(required=True)
    metadata = fields.Nested(MetadataSchema, dump_only=True)
    timestamp = CommonFields.created_at


class HealthCheckSchema(BaseSchema):
    """Health check response schema.

    Used by health check endpoints to report system status.

    Example:
        {
            "status": "healthy",
            "version": "v2",
            "timestamp": "2024-01-01T12:00:00.000Z",
            "uptime_seconds": 3600,
            "checks": {
                "database": "healthy",
                "cache": "healthy",
                "ml_models": "healthy"
            }
        }
    """

    status = fields.Str(
        required=True, validate=validate.OneOf(["healthy", "degraded", "unhealthy"])
    )
    version = fields.Str(dump_default="v2", dump_only=True)
    timestamp = fields.DateTime(
        dump_default=datetime.utcnow, format="iso", dump_only=True
    )
    uptime_seconds = fields.Float(dump_only=True)
    checks = fields.Dict(dump_only=True)
    environment = fields.Str(dump_only=True)
    build_info = fields.Dict(dump_only=True)


class ValidationErrorSchema(ErrorSchema):
    """Validation error response schema.

    Specialized error schema for validation failures.

    Example:
        {
            "success": false,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed",
                "validation_errors": {
                    "email": ["Invalid email format"],
                    "age": ["Must be between 18 and 120"]
                }
            }
        }
    """

    validation_errors = fields.Dict(dump_only=True)

    @post_load
    def structure_validation_error(
        self, data: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        """Structure validation error data."""
        result = super().structure_error(data, **kwargs)

        if data.get("validation_errors"):
            result["error"]["validation_errors"] = data["validation_errors"]

        return result


# Utility functions for creating common response schemas
def create_error_response(
    code: str,
    message: str,
    details: Optional[Dict] = None,
    field: Optional[str] = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a standardized error response.

    Args:
        code: Error code
        message: Error message
        details: Optional error details
        field: Optional field name for field-specific errors
        request_id: Optional request ID

    Returns:
        dict: Formatted error response
    """
    schema = ErrorSchema()
    return schema.load(
        {
            "code": code,
            "message": message,
            "details": details,
            "field": field,
            "request_id": request_id,
        }
    )


def create_success_response(
    message: str = "Success",
    data: Optional[Dict] = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a standardized success response.

    Args:
        message: Success message
        data: Optional data payload
        request_id: Optional request ID

    Returns:
        dict: Formatted success response
    """
    schema = SuccessSchema()
    return schema.dump({"message": message, "data": data, "request_id": request_id})
