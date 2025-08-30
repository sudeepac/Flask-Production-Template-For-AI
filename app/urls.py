"""Central URL Prefix Configuration.

This module serves as the EXCLUSIVE source of truth for all URL prefixes
used throughout the application. All blueprints must import their URL
prefix from this module to ensure consistency and avoid conflicts.

See CONTRIBUTING.md §5 for style guidelines.
"""

# URL Prefix Registry
# All blueprint routes MUST use these prefixes
# Format: "<feature_name>": "/<url_prefix>"
URL_PREFIX = {
    # Core API endpoints
    "api": "/api",
    "health": "/health",
    "auth": "/auth",
    # ML Service endpoints
    "ml": "/ml",
    "models": "/models",
    "predictions": "/predictions",
    # Data management endpoints
    "data": "/data",
    "upload": "/upload",
    "export": "/export",
    # User management endpoints
    "users": "/users",
    "profile": "/profile",
    # Admin endpoints
    "admin": "/admin",
    "monitoring": "/monitoring",
    "logs": "/logs",
    # Example feature (remove when adding real features)
    "example": "/example",
    "examples": "/examples",
}


# API Version Prefixes
# Used for versioned API endpoints
API_VERSION_PREFIX = {
    "v1": "/api/v1",
    "v2": "/api/v2",  # Current active version
    "current": "/api/v2",  # Alias for current version
}


def get_url_prefix(feature_name: str) -> str:
    """Get URL prefix for a given feature.

    This function provides a safe way to retrieve URL prefixes
    with validation and error handling.

    Args:
        feature_name: Name of the feature/blueprint

    Returns:
        str: URL prefix for the feature

    Raises:
        KeyError: If feature_name is not registered

    Example:
        prefix = get_url_prefix("auth")
        # Returns: "/auth"
    """
    if feature_name not in URL_PREFIX:
        raise KeyError(
            f"URL prefix for '{feature_name}' not found. "
            f"Available prefixes: {list(URL_PREFIX.keys())}"
        )
    return URL_PREFIX[feature_name]


def get_versioned_prefix(version: str, feature_name: str) -> str:
    """Get versioned API prefix for a feature.

    Combines API version prefix with feature prefix for
    versioned API endpoints.

    Args:
        version: API version (v1, v2, current)
        feature_name: Name of the feature/blueprint

    Returns:
        str: Versioned URL prefix

    Example:
        prefix = get_versioned_prefix("v2", "users")
        # Returns: "/api/v2/users"
    """
    if version not in API_VERSION_PREFIX:
        raise KeyError(
            f"API version '{version}' not found. "
            f"Available versions: {list(API_VERSION_PREFIX.keys())}"
        )

    if feature_name not in URL_PREFIX:
        raise KeyError(
            f"URL prefix for '{feature_name}' not found. "
            f"Available prefixes: {list(URL_PREFIX.keys())}"
        )

    return f"{API_VERSION_PREFIX[version]}{URL_PREFIX[feature_name]}"


def register_new_prefix(feature_name: str, url_prefix: str) -> None:
    """Register a new URL prefix for a feature.

    This function allows dynamic registration of new URL prefixes
    during blueprint creation. Should be used sparingly and only
    during development.

    Args:
        feature_name: Name of the new feature
        url_prefix: URL prefix (must start with '/')

    Raises:
        ValueError: If prefix format is invalid or already exists

    Example:
        register_new_prefix("analytics", "/analytics")
    """
    if not url_prefix.startswith("/"):
        raise ValueError(f"URL prefix must start with '/': {url_prefix}")

    if feature_name in URL_PREFIX:
        raise ValueError(f"Feature '{feature_name}' already registered")

    if url_prefix in URL_PREFIX.values():
        existing_feature = next(
            name for name, prefix in URL_PREFIX.items() if prefix == url_prefix
        )
        raise ValueError(
            f"URL prefix '{url_prefix}' already used by '{existing_feature}'"
        )

    URL_PREFIX[feature_name] = url_prefix


def list_all_prefixes() -> dict:
    """Get all registered URL prefixes.

    Returns:
        dict: Copy of all registered URL prefixes

    Example:
        prefixes = list_all_prefixes()
        print(prefixes)
    """
    return URL_PREFIX.copy()
