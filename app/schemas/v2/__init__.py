"""Schema Package v2 - Current API Schemas.

This package contains the current active API schemas (v2).
These schemas define the structure for all API requests and responses.

Once released, schemas in this package become IMMUTABLE.
For breaking changes, create a new version (v3).

See CONTRIBUTING.md §5 for schema versioning guidelines.
"""

# Import all v2 schemas for easy access
try:
    from app.schemas.v2.base import BaseSchema
    from app.schemas.v2.common import (
        ErrorSchema,
        MetadataSchema,
        PaginationSchema,
        SuccessSchema,
    )

    # Feature schemas (add as you create them)
    # from app.schemas.v2.users import UserSchema, UserCreateSchema, UserUpdateSchema
    # from app.schemas.v2.auth import LoginSchema, TokenSchema, RefreshSchema
    # from app.schemas.v2.predictions import (
    #     PredictionSchema,
    #     PredictionRequestSchema,
    #     PredictionResponseSchema,
    #     BatchPredictionSchema,
    # )
    # from app.schemas.v2.models import (
    #     MLModelSchema,
    #     ModelMetricsSchema,
    #     ModelVersionSchema,
    # )

except ImportError:
    # Schemas not yet created
    BaseSchema = None
    ErrorSchema = None
    SuccessSchema = None
    PaginationSchema = None
    MetadataSchema = None

# Version metadata
VERSION = "v2"
STATUS = "active"  # active, legacy, deprecated
DEPRECATED = False
RELEASE_DATE = "2024-01-01"  # ISO date when version was released

# Schema validation settings
STRICT_VALIDATION = True
ALLOW_UNKNOWN_FIELDS = False
REQUIRE_ALL_FIELDS = True

# Export all v2 schemas
__all__ = [
    # Base schemas
    "BaseSchema",
    "ErrorSchema",
    "SuccessSchema",
    "PaginationSchema",
    "MetadataSchema",
    # Feature schemas (uncomment as you add them)
    # 'UserSchema',
    # 'UserCreateSchema',
    # 'UserUpdateSchema',
    # 'LoginSchema',
    # 'TokenSchema',
    # 'RefreshSchema',
    # 'PredictionSchema',
    # 'PredictionRequestSchema',
    # 'PredictionResponseSchema',
    # 'BatchPredictionSchema',
    # 'MLModelSchema',
    # 'ModelMetricsSchema',
    # 'ModelVersionSchema',
    # Metadata
    "VERSION",
    "STATUS",
    "DEPRECATED",
    "RELEASE_DATE",
    "STRICT_VALIDATION",
    "ALLOW_UNKNOWN_FIELDS",
    "REQUIRE_ALL_FIELDS",
]
