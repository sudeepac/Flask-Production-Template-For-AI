"""Simplified Configuration Manager.

This module provides a clean interface for managing application
configuration with essential validation and environment support.
"""

import logging
import os
from datetime import timedelta
from typing import Any, Dict


def _get_database_config(env: str) -> Dict[str, Any]:
    """Get database configuration."""
    if env == "testing":
        url = "sqlite:///:memory:"
    else:
        url = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    
    config = {
        "SQLALCHEMY_DATABASE_URI": url,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SQLALCHEMY_RECORD_QUERIES": env == "development",
    }
    
    # Add pool settings for non-SQLite databases
    if "sqlite" not in url.lower():
        config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_size": int(os.environ.get("DB_POOL_SIZE", "10")),
            "pool_timeout": int(os.environ.get("DB_POOL_TIMEOUT", "30")),
            "pool_recycle": int(os.environ.get("DB_POOL_RECYCLE", "3600")),
        }
    
    return config


def _get_cache_config() -> Dict[str, Any]:
    """Get cache configuration."""
    redis_url = os.environ.get("REDIS_URL")
    cache_type = "redis" if redis_url else "simple"
    
    return {
        "CACHE_TYPE": cache_type,
        "CACHE_REDIS_URL": redis_url or "redis://localhost:6379/0",
        "CACHE_DEFAULT_TIMEOUT": int(os.environ.get("CACHE_DEFAULT_TIMEOUT", "300")),
        "CACHE_KEY_PREFIX": os.environ.get("CACHE_KEY_PREFIX", "flask_app"),
    }


def _get_security_config(env: str) -> Dict[str, Any]:
    """Get security configuration."""
    secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    jwt_secret_key = os.environ.get("JWT_SECRET_KEY", secret_key)
    
    # Validate for production
    if env == "production":
        _validate_secret_key(secret_key, env, "SECRET_KEY")
        if jwt_secret_key != secret_key:
            _validate_secret_key(jwt_secret_key, env, "JWT_SECRET_KEY")
    
    return {
        "SECRET_KEY": secret_key,
        "JWT_SECRET_KEY": jwt_secret_key,
        "JWT_ACCESS_TOKEN_EXPIRES": timedelta(
            hours=int(os.environ.get("JWT_ACCESS_EXPIRES_HOURS", "1"))
        ),
        "JWT_REFRESH_TOKEN_EXPIRES": timedelta(
            days=int(os.environ.get("JWT_REFRESH_EXPIRES_DAYS", "30"))
        ),
        "FORCE_HTTPS": env == "production",
        "WTF_CSRF_ENABLED": os.environ.get("CSRF_ENABLED", "true").lower() == "true",
    }


def _validate_secret_key(key: str, env: str, key_name: str) -> None:
    """Validate secret key strength."""
    weak_defaults = [
        "dev-secret-key-change-in-production",
        "development-key",
        "dev-key",
        "secret",
        "password",
        "123456",
        "changeme",
    ]

    if env == "production":
        if key in weak_defaults:
            raise ValueError(
                f"{key_name} cannot use weak default value in production"
            )

        if len(key) < 32:
            raise ValueError(
                f"{key_name} must be at least 32 characters long in production"
            )

        # Check for common weak patterns
        if key.lower() in ["secret", "password", "key"] or key.isdigit():
            raise ValueError(f"{key_name} is too weak for production use")

    elif env == "development" and len(key) < 16:
        logging.warning(f"{key_name} is shorter than recommended (16+ characters)")


def _get_api_config() -> Dict[str, Any]:
    """Get API configuration."""
    cors_origins = os.environ.get("CORS_ORIGINS", "")
    origins = [
        origin.strip() for origin in cors_origins.split(",") if origin.strip()
    ]
    
    return {
        "API_VERSION": os.environ.get("API_VERSION", "v2"),
        "API_RATE_LIMIT": os.environ.get("API_RATE_LIMIT", "100 per hour"),
        "API_DOCS_ENABLED": os.environ.get("API_DOCS_ENABLED", "True").lower() == "true",
        "CORS_ORIGINS": origins,
        "MAX_CONTENT_LENGTH": int(
            os.environ.get("MAX_CONTENT_LENGTH", str(16 * 1024 * 1024))
        ),
    }


def _get_logging_config(env: str) -> Dict[str, Any]:
    """Get logging configuration."""
    level_map = {
        "development": "DEBUG",
        "testing": "WARNING",
        "production": "WARNING",
    }
    
    default_level = level_map.get(env, "INFO")
    
    return {
        "LOG_LEVEL": os.environ.get("LOG_LEVEL", default_level),
        "LOG_FORMAT": os.environ.get(
            "LOG_FORMAT", "%(asctime)s %(levelname)s %(name)s: %(message)s"
        ),
        "LOG_FILE": os.environ.get("LOG_FILE"),
        "STRUCTURED_LOGGING": os.environ.get("STRUCTURED_LOGGING", "False").lower() == "true",
    }


class ConfigManager:
    """Simplified configuration manager.

    This class provides a clean interface for managing all application
    configuration with proper validation and environment-specific defaults.
    """

    def __init__(self, env: str = None):
        """Initialize configuration manager.

        Args:
            env: Environment name (development, testing, production)
        """
        self.env = env or os.environ.get("FLASK_ENV", "development")
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment and defaults."""
        # Load component configurations
        config = {
            # Flask core
            "DEBUG": self.env == "development",
            "TESTING": self.env == "testing",
            # File uploads
            "UPLOAD_FOLDER": os.environ.get("UPLOAD_FOLDER", "uploads/"),
            "ALLOWED_EXTENSIONS": set(
                os.environ.get(
                    "ALLOWED_EXTENSIONS", "txt,pdf,png,jpg,jpeg,gif,csv,json"
                ).split(",")
            ),
            # Security headers
            "SECURITY_HEADERS": {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block",
            },
        }
        
        # Merge component configurations
        config.update(_get_database_config(self.env))
        config.update(_get_cache_config())
        config.update(_get_security_config(self.env))
        config.update(_get_api_config())
        config.update(_get_logging_config(self.env))

        return config

    def get_config(self) -> Dict[str, Any]:
        """Get the complete configuration dictionary."""
        return self._config.copy()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)

    def validate(self) -> None:
        """Basic validation for production environment."""
        if self.env == "production":
            if not os.environ.get("SECRET_KEY"):
                raise ValueError("SECRET_KEY is required for production")
            if self._config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:"):
                logging.warning("SQLite is not recommended for production")


# Convenience function
def get_config(env: str = None) -> Dict[str, Any]:
    """Get configuration dictionary for the specified environment.
    
    Args:
        env: Environment name (development, testing, production)
        
    Returns:
        Configuration dictionary
    """
    manager = ConfigManager(env)
    manager.validate()
    return manager.get_config()
