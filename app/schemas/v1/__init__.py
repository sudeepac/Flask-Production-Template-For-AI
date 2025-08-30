"""Schema Package v1 - Legacy API Schemas.

This package contains v1 API schemas that are IMMUTABLE after release.
These schemas are maintained for backwards compatibility only.

DO NOT MODIFY existing schemas in this package.
For new features, use the current version (v2).

See CONTRIBUTING.md §5 for schema versioning guidelines.
"""

# Import all v1 schemas for easy access
try:
    from app.schemas.v1.base import BaseSchema
    from app.schemas.v1.common import ErrorSchema, SuccessSchema

    # Legacy feature schemas (add as needed)
    # from app.schemas.v1.users import UserSchemaV1
    # from app.schemas.v1.predictions import PredictionSchemaV1

except ImportError:
    # Schemas not yet created
    BaseSchema = None
    ErrorSchema = None
    SuccessSchema = None

# Version metadata
VERSION = "v1"
STATUS = "legacy"  # legacy, active, deprecated
DEPRECATED = True
SUPPORTED_UNTIL = "2025-12-31"  # ISO date when support ends

# Export all v1 schemas
__all__ = [
    "BaseSchema",
    "ErrorSchema",
    "SuccessSchema",
    "VERSION",
    "STATUS",
    "DEPRECATED",
    "SUPPORTED_UNTIL",
]
