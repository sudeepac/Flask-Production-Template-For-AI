"""Base Schema Classes for v2 API.

This module contains the foundational schema classes that all other
v2 schemas inherit from. Provides common functionality, validation,
and serialization patterns.

See CONTRIBUTING.md §5 for schema design guidelines.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Type

from marshmallow import Schema, ValidationError, fields, post_load, pre_dump

# marshmallow validate imports removed - not used in this module
from app.schemas.common_fields import CommonFields
from app.schemas.common_fields import TimestampMixin as CommonTimestampMixin

logger = logging.getLogger("app.schemas.v2.base")


class BaseSchema(Schema):
    """Base schema class for all v2 API schemas.

    Provides common functionality:
    - Automatic timestamp handling
    - Consistent error formatting
    - Metadata injection
    - Validation helpers
    - Serialization utilities

    All v2 schemas should inherit from this class.

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
        # Timezone handling
        datetimeformat = "%Y-%m-%dT%H:%M:%S.%fZ"

    # Common metadata fields (optional)
    created_at = CommonFields.created_at
    updated_at = CommonFields.updated_at
    version = fields.Str(dump_only=True, dump_default="v2")

    def __init__(self, *args, **kwargs):
        """Initialize schema with v2-specific settings."""
        super().__init__(*args, **kwargs)
        self._inject_metadata = kwargs.get("inject_metadata", True)

    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Post-processing after deserialization.

        Override this method in subclasses to create custom objects
        or perform additional validation.

        Args:
            data: Deserialized data dictionary
            **kwargs: Additional keyword arguments

        Returns:
            dict: Processed data dictionary
        """
        # Add processing timestamp
        data["_processed_at"] = datetime.utcnow().isoformat()
        return data

    @pre_dump
    def prepare_data(self, obj: Any, **kwargs) -> Dict[str, Any]:
        """Pre-processing before serialization.

        Override this method in subclasses to transform objects
        before serialization.

        Args:
            obj: Object to be serialized
            **kwargs: Additional keyword arguments

        Returns:
            dict: Data dictionary ready for serialization
        """
        if hasattr(obj, "__dict__"):
            # Convert object to dictionary
            data = obj.__dict__.copy()
        elif isinstance(obj, dict):
            data = obj.copy()
        else:
            data = {"value": obj}

        # Inject metadata if enabled
        if self._inject_metadata:
            data.setdefault("version", "v2")
            data.setdefault("_serialized_at", datetime.utcnow().isoformat())

        return data

    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data with enhanced error handling.

        Args:
            data: Data to validate

        Returns:
            dict: Validated data

        Raises:
            ValidationError: If validation fails
        """
        try:
            return self.load(data)
        except ValidationError as e:
            logger.warning(f"Schema validation failed: {e.messages}")
            # Enhance error messages with field context
            enhanced_errors = self._enhance_error_messages(e.messages)
            raise ValidationError(enhanced_errors)

    def serialize_data(self, obj: Any) -> Dict[str, Any]:
        """Serialize object with error handling.

        Args:
            obj: Object to serialize

        Returns:
            dict: Serialized data

        Raises:
            ValidationError: If serialization fails
        """
        try:
            return self.dump(obj)
        except Exception as e:
            logger.error(f"Schema serialization failed: {str(e)}")
            raise ValidationError(f"Serialization error: {str(e)}")

    def _enhance_error_messages(self, errors: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance validation error messages with context.

        Args:
            errors: Original error messages

        Returns:
            dict: Enhanced error messages
        """
        enhanced = {}
        for field, messages in errors.items():
            if isinstance(messages, list):
                enhanced[field] = [f"Field '{field}': {msg}" for msg in messages]
            elif isinstance(messages, dict):
                enhanced[field] = self._enhance_error_messages(messages)
            else:
                enhanced[field] = f"Field '{field}': {messages}"
        return enhanced

    @classmethod
    def create_response_schema(
        cls, data_schema: Type["BaseSchema"]
    ) -> Type["BaseSchema"]:
        """Create a response wrapper schema.

        Args:
            data_schema: Schema class for the data field

        Returns:
            Schema class for API responses

        Example:
            UserResponseSchema = BaseSchema.create_response_schema(UserSchema)
        """

        class ResponseSchema(BaseSchema):
            """Base response schema with common fields."""

            success = fields.Bool(dump_default=True)
            message = fields.Str(dump_default="Success")
            data = fields.Nested(data_schema)
            timestamp = fields.DateTime(dump_default=datetime.utcnow, format="iso")
            version = fields.Str(dump_default="v2")

        return ResponseSchema

    @classmethod
    def create_list_schema(cls, item_schema: Type["BaseSchema"]) -> Type["BaseSchema"]:
        """Create a list wrapper schema.

        Args:
            item_schema: Schema class for list items

        Returns:
            Schema class for lists

        Example:
            UserListSchema = BaseSchema.create_list_schema(UserSchema)
        """

        class ListSchema(BaseSchema):
            """Schema for paginated list responses."""

            items = fields.List(fields.Nested(item_schema))
            count = fields.Int(dump_only=True)
            total = fields.Int(dump_only=True)
            page = fields.Int(dump_only=True)
            per_page = fields.Int(dump_only=True)

            @post_load
            def add_count(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
                """Add count field to the schema."""
                if "items" in data:
                    data["count"] = len(data["items"])
                return data

        return ListSchema


class TimestampMixin(CommonTimestampMixin):
    """Mixin for schemas that need timestamp fields.

    Provides standard created_at and updated_at fields.
    Inherits from common timestamp mixin to reduce duplication.

    Example:
        class UserSchema(BaseSchema, TimestampMixin):
            name = fields.Str(required=True)
    """


class MetadataMixin:
    """Mixin for schemas that need metadata fields.

    Provides standard metadata fields for API responses.

    Example:
        class APIResponseSchema(BaseSchema, MetadataMixin):
            data = fields.Raw()
    """

    request_id = fields.Str(dump_only=True)
    processing_time_ms = fields.Float(dump_only=True)
    api_version = fields.Str(dump_only=True, dump_default="v2")
    server_timestamp = fields.DateTime(
        dump_only=True, format="iso", dump_default=datetime.utcnow
    )
