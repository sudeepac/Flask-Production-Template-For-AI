"""Common field definitions and validators for Marshmallow schemas.

This module provides reusable field definitions and validators
to reduce duplication across schema definitions.
"""

from marshmallow import fields, validate


# Common field definitions
class CommonFields:
    """Collection of commonly used field definitions."""

    # ID fields
    id_field = fields.Int(dump_only=True)
    uuid_field = fields.UUID()

    # String fields with common validations
    username = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=50),
    )

    email = fields.Email(required=True)

    password = fields.Str(
        required=True,
        load_only=True,
        validate=validate.Length(min=8, max=128),
    )

    # Text fields
    title = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=200),
    )

    description = fields.Str(
        validate=validate.Length(max=1000),
    )

    bio = fields.Str(validate=validate.Length(max=500))

    content = fields.Str(validate=validate.Length(max=5000))

    # Timestamp fields
    created_at = fields.DateTime(dump_only=True)

    updated_at = fields.DateTime(dump_only=True)

    # Status fields
    status = fields.Str(
        validate=validate.OneOf(["active", "inactive", "pending", "deleted"]),
    )

    is_active = fields.Bool()

    # Metadata fields
    metadata = fields.Dict()

    tags = fields.List(fields.Str(validate=validate.Length(max=50)))


# Common validators
class CommonValidators:
    """Collection of commonly used validators."""

    @staticmethod
    def non_empty_string(value: str) -> str:
        """Validate that string is not empty after stripping."""
        if not value or not value.strip():
            raise validate.ValidationError("Field cannot be empty")
        return value.strip()

    @staticmethod
    def positive_integer(value: int) -> int:
        """Validate that integer is positive."""
        if value <= 0:
            raise validate.ValidationError("Value must be positive")
        return value

    @staticmethod
    def non_negative_integer(value: int) -> int:
        """Validate that integer is non-negative."""
        if value < 0:
            raise validate.ValidationError("Value must be non-negative")
        return value

    @staticmethod
    def valid_url(value: str) -> str:
        """Validate URL format."""
        import re

        url_pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+"  # domain...
            r"(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # host...
            r"localhost|"  # localhost...
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

        if not url_pattern.match(value):
            raise validate.ValidationError("Invalid URL format")
        return value


# Common schema mixins
class TimestampMixin:
    """Mixin for schemas that include timestamp fields."""

    created_at = CommonFields.created_at
    updated_at = CommonFields.updated_at


class MetadataMixin:
    """Mixin for schemas that include metadata fields."""

    metadata = CommonFields.metadata


class StatusMixin:
    """Mixin for schemas that include status fields."""

    status = CommonFields.status
    is_active = CommonFields.is_active


# Pagination schema
class PaginationSchema:
    """Common pagination fields."""

    page = fields.Int(
        load_default=1,
        validate=CommonValidators.positive_integer,
    )

    per_page = fields.Int(
        load_default=20,
        validate=validate.Range(min=1, max=100),
    )

    sort_by = fields.Str(load_default="created_at")

    sort_order = fields.Str(
        load_default="desc",
        validate=validate.OneOf(["asc", "desc"]),
    )


# Response schema helpers
def create_response_schema(data_schema, message_default="Success"):
    """Create a standardized response schema.

    Args:
        data_schema: Schema class for the data field
        message_default: Default success message

    Returns:
        Response schema class
    """
    from marshmallow import Schema

    class ResponseSchema(Schema):
        """Schema for standardized API responses."""

        success = fields.Bool(dump_only=True)
        message = fields.Str(dump_only=True)
        data = fields.Nested(data_schema, dump_only=True)
        meta = fields.Dict(dump_only=True)

    return ResponseSchema


def create_error_schema():
    """Create a standardized error response schema."""
    from marshmallow import Schema

    class ErrorSchema(Schema):
        """Schema for standardized API error responses."""

        success = fields.Bool(dump_only=True)
        message = fields.Str(dump_only=True)
        error = fields.Dict(dump_only=True)

    return ErrorSchema
