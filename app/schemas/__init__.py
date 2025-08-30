"""Schema Package - Versioned API Schemas.

This package contains all input/output schemas organized by API version.
Schemas are immutable once released to ensure backwards compatibility.

Current active version: v2
Supported versions: v1, v2

Usage:
    from app.schemas import CurrentUserSchema, CurrentPredictionSchema
    # or
    from app.schemas.v2.users import UserSchema
    from app.schemas.v1.legacy import LegacySchema

See CONTRIBUTING.md §5 for schema versioning guidelines.
"""

# Import current version schemas for easy access
# Update these imports when changing active API version
try:
    # Current version (v2) - Main schemas
    from app.schemas.v2.base import BaseSchema as CurrentBaseSchema
    from app.schemas.v2.common import ErrorSchema as CurrentErrorSchema
    from app.schemas.v2.common import PaginationSchema as CurrentPaginationSchema
    from app.schemas.v2.common import SuccessSchema as CurrentSuccessSchema

    # Example schemas (remove when adding real schemas)
    # from app.schemas.v2.users import UserSchema as CurrentUserSchema
    # from app.schemas.v2.predictions import PredictionSchema as CurrentPredictionSchema

except ImportError:
    # Fallback if v2 schemas don't exist yet
    CurrentBaseSchema = None
    CurrentErrorSchema = None
    CurrentSuccessSchema = None
    CurrentPaginationSchema = None

# Version mapping for programmatic access
SCHEMA_VERSIONS = {
    "v1": "app.schemas.v1",
    "v2": "app.schemas.v2",
    "current": "app.schemas.v2",
    "latest": "app.schemas.v2",
}

# Current API version
CURRENT_VERSION = "v2"
LATEST_VERSION = "v2"
SUPPORTED_VERSIONS = ["v1", "v2"]


def get_schema_version(version: str = None):
    """Get schema module for specified version.

    Args:
        version: Schema version ('v1', 'v2', 'current', 'latest')
                Defaults to current version.

    Returns:
        module: Schema module for the specified version

    Raises:
        ValueError: If version is not supported

    Example:
        v2_schemas = get_schema_version('v2')
        current_schemas = get_schema_version('current')
    """
    if version is None:
        version = CURRENT_VERSION

    if version not in SCHEMA_VERSIONS:
        raise ValueError(
            f"Unsupported schema version '{version}'. "
            f"Supported versions: {list(SCHEMA_VERSIONS.keys())}"
        )

    module_path = SCHEMA_VERSIONS[version]

    try:
        import importlib

        return importlib.import_module(module_path)
    except ImportError as e:
        raise ImportError(
            f"Schema version '{version}' not found at '{module_path}': {e}"
        )


def list_supported_versions():
    """Get list of all supported schema versions.

    Returns:
        list: List of supported version strings

    Example:
        versions = list_supported_versions()
        # Returns: ['v1', 'v2']
    """
    return SUPPORTED_VERSIONS.copy()


def get_current_version():
    """Get current active schema version.

    Returns:
        str: Current schema version

    Example:
        version = get_current_version()
        # Returns: 'v2'
    """
    return CURRENT_VERSION


def is_version_supported(version: str) -> bool:
    """Check if a schema version is supported.

    Args:
        version: Version string to check

    Returns:
        bool: True if version is supported

    Example:
        if is_version_supported('v2'):
            # Use v2 schemas
            pass
    """
    return version in SUPPORTED_VERSIONS


# Export current version schemas for convenience
__all__ = [
    # Version management
    "get_schema_version",
    "list_supported_versions",
    "get_current_version",
    "is_version_supported",
    "CURRENT_VERSION",
    "LATEST_VERSION",
    "SUPPORTED_VERSIONS",
    "SCHEMA_VERSIONS",
    # Current version schemas (aliases)
    "CurrentBaseSchema",
    "CurrentErrorSchema",
    "CurrentSuccessSchema",
    "CurrentPaginationSchema",
]
