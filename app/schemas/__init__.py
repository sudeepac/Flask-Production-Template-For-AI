"""Schema package for API serialization and validation.

This package contains Marshmallow schemas for API request/response
serialization and validation.

Structure:
- base.py: Base schema classes and common functionality
- common_fields.py: Shared field definitions and validators
- Additional schema modules as needed

See CONTRIBUTING.md §5 for schema design guidelines.
"""

# Import schemas for easy access
from app.schemas.base import BaseSchema, PaginationSchema, ResponseSchema, TimestampMixin
from app.schemas.common_fields import CommonFields

__all__ = [
    "BaseSchema",
    "PaginationSchema", 
    "ResponseSchema",
    "TimestampMixin",
    "CommonFields",
]
