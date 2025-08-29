"""Base Schema Classes for v1 API (Legacy).

This module contains the foundational schema classes for v1 API.
These schemas are IMMUTABLE and maintained for backwards compatibility only.

DO NOT MODIFY existing schemas in this module.
For new features, use the current version (v2).

See CONTRIBUTING.md §5 for schema versioning guidelines.
"""

from datetime import datetime
from typing import Any, Dict
from marshmallow import Schema, fields, post_load
import logging

logger = logging.getLogger('app.schemas.v1.base')


class BaseSchema(Schema):
    """Base schema class for v1 API (Legacy).
    
    Provides basic functionality for v1 schemas.
    This is a simplified version compared to v2.
    
    DO NOT MODIFY - Legacy compatibility only.
    
    Example:
        class UserSchemaV1(BaseSchema):
            name = fields.Str(required=True)
            email = fields.Email(required=True)
    """
    
    class Meta:
        """Schema metadata configuration."""
        unknown = 'EXCLUDE'
        ordered = True
        dateformat = '%Y-%m-%dT%H:%M:%SZ'  # Simplified date format for v1
    
    # Basic metadata fields
    created_at = fields.DateTime(dump_only=True, format='iso')
    updated_at = fields.DateTime(dump_only=True, format='iso')
    
    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Post-processing after deserialization (v1 legacy)."""
        return data


class TimestampMixin:
    """Mixin for v1 schemas that need timestamp fields.
    
    Legacy version - DO NOT MODIFY.
    """
    created_at = fields.DateTime(dump_only=True, format='iso')
    updated_at = fields.DateTime(dump_only=True, format='iso')