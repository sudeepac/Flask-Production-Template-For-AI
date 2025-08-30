"""Base Schema Classes for API.

This module contains the foundational schema classes that all other
schemas inherit from. Provides common functionality, validation,
and serialization patterns.

See CONTRIBUTING.md §5 for schema design guidelines.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from marshmallow import Schema, fields, post_load, pre_dump

from app.schemas.common_fields import CommonFields

logger = logging.getLogger("app.schemas.base")


class BaseSchema(Schema):
    """Base schema class for all API schemas.

    Provides common functionality:
    - Automatic timestamp handling
    - Consistent error formatting
    - Metadata injection
    - Validation helpers
    - Serialization utilities

    All schemas should inherit from this class.

    Example:
        class UserSchema(BaseSchema):
            name = fields.Str(required=True, validate=Length(min=1, max=100))
            email = fields.Email(required=True)
    """

    class Meta:
        """Schema metadata configuration."""

        # Include unknown fields in deserialization
        unknown = "EXCLUDE"  # EXCLUDE, INCLUDE, or RAISE
        # Preserve field order
        ordered = True
        # Date format for datetime fields
        dateformat = "%Y-%m-%dT%H:%M:%S.%fZ"

    # Common timestamp fields
    created_at = fields.DateTime(dump_only=True, format="iso")
    updated_at = fields.DateTime(dump_only=True, format="iso")

    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Post-processing after deserialization."""
        return data

    @pre_dump
    def prepare_data(self, data: Any, **kwargs) -> Any:
        """Pre-processing before serialization."""
        return data

    def handle_error(self, error, data, **kwargs):
        """Custom error handling for validation errors."""
        logger.warning(f"Schema validation error: {error.messages}")
        raise error


class TimestampMixin:
    """Mixin for schemas that need timestamp fields."""

    created_at = fields.DateTime(dump_only=True, format="iso")
    updated_at = fields.DateTime(dump_only=True, format="iso")


class PaginationSchema(BaseSchema):
    """Schema for pagination metadata."""

    page = fields.Int(required=True, validate=lambda x: x > 0)
    per_page = fields.Int(required=True, validate=lambda x: 0 < x <= 100)
    total = fields.Int(dump_only=True)
    pages = fields.Int(dump_only=True)
    has_prev = fields.Bool(dump_only=True)
    has_next = fields.Bool(dump_only=True)
    prev_num = fields.Int(dump_only=True, allow_none=True)
    next_num = fields.Int(dump_only=True, allow_none=True)


class ResponseSchema(BaseSchema):
    """Standard API response schema."""

    status = fields.Str(required=True, validate=lambda x: x in ["success", "error"])
    message = fields.Str()
    data = fields.Raw()
    errors = fields.Dict()
    timestamp = fields.DateTime(dump_only=True, format="iso")