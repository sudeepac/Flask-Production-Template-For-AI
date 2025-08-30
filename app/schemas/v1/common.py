"""Common Schema Classes for v1 API (Legacy).

This module contains commonly used v1 schemas.
These schemas are IMMUTABLE and maintained for backwards compatibility only.

DO NOT MODIFY existing schemas in this module.
For new features, use the current version (v2).

See CONTRIBUTING.md §5 for schema versioning guidelines.
"""

from datetime import datetime
from typing import Any, Dict

from marshmallow import fields, validate

from app.schemas.v1.base import BaseSchema


class ErrorSchema(BaseSchema):
    """Legacy v1 error response schema.

    Simplified error format for v1 API compatibility.
    DO NOT MODIFY - Legacy compatibility only.

    Example:
        {
            "error": "Invalid input",
            "code": 400,
            "timestamp": "2024-01-01T12:00:00Z"
        }
    """

    error = fields.Str(required=True)
    code = fields.Int(required=True)
    timestamp = fields.DateTime(default=datetime.utcnow, format="iso", dump_only=True)
    details = fields.Str(missing=None)


class SuccessSchema(BaseSchema):
    """Legacy v1 success response schema.

    Simplified success format for v1 API compatibility.
    DO NOT MODIFY - Legacy compatibility only.

    Example:
        {
            "message": "Success",
            "data": {...},
            "timestamp": "2024-01-01T12:00:00Z"
        }
    """

    message = fields.Str(default="Success")
    data = fields.Dict(missing=None)
    timestamp = fields.DateTime(default=datetime.utcnow, format="iso", dump_only=True)


class PaginationSchema(BaseSchema):
    """Legacy v1 pagination schema.

    Simplified pagination format for v1 API compatibility.
    DO NOT MODIFY - Legacy compatibility only.

    Example:
        {
            "page": 1,
            "total": 100,
            "per_page": 20
        }
    """

    page = fields.Int(required=True, validate=validate.Range(min=1))
    total = fields.Int(required=True, validate=validate.Range(min=0))
    per_page = fields.Int(required=True, validate=validate.Range(min=1, max=100))
