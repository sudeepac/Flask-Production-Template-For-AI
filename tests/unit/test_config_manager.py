"""Unit tests for configuration manager.

This module tests the configuration management functionality including
different config classes and the main ConfigManager class.
"""

import os
from datetime import timedelta
from unittest.mock import patch

import pytest

from app.config_manager import (
    APIConfig,
    CacheConfig,
    ConfigManager,
    DatabaseConfig,
    LoggingConfig,
    SecurityConfig,
    create_config_class,
    get_config,
)


class TestDatabaseConfig:
    """Test DatabaseConfig class functionality."""

    def test_database_config_defaults(self):
        """Test default database configuration values."""
        config = DatabaseConfig()

        assert config.url == "sqlite:///app.db"
        assert config.track_modifications is False
        assert config.record_queries is False
        assert config.pool_size == 10
        assert config.pool_timeout == 30
        assert config.pool_recycle == 3600

    def test_database_config_custom_values(self):
        """Test database configuration with custom values."""
        config = DatabaseConfig(
            url="postgresql://user:pass@localhost/db",
            track_modifications=True,
            record_queries=True,
            pool_size=20,
            pool_timeout=60,
            pool_recycle=7200,
        )

        assert config.url == "postgresql://user:pass@localhost/db"
        assert config.track_modifications is True
        assert config.record_queries is True
        assert config.pool_size == 20
        assert config.pool_timeout == 60
        assert config.pool_recycle == 7200

    def test_database_config_from_env_development(self):
        """Test database config creation from environment for development."""
        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": "postgresql://localhost/dev_db",
                "DB_POOL_SIZE": "15",
                "DB_POOL_TIMEOUT": "45",
                "DB_POOL_RECYCLE": "1800",
            },
        ):
            config = DatabaseConfig.from_env("development")

            assert config.url == "postgresql://localhost/dev_db"
            assert config.record_queries is True  # development enables query recording
            assert config.pool_size == 15
            assert config.pool_timeout == 45
            assert config.pool_recycle == 1800

    def test_database_config_from_env_testing(self):
        """Test database config creation from environment for testing."""
        config = DatabaseConfig.from_env("testing")

        assert config.url == "sqlite:///:memory:"
        assert config.track_modifications is False
        assert config.record_queries is False

    def test_database_config_from_env_defaults(self):
        """Test database config with environment defaults."""
        with patch.dict(os.environ, {}, clear=True):
            config = DatabaseConfig.from_env("production")

            assert config.url == "sqlite:///app.db"
            assert config.pool_size == 10
            assert config.pool_timeout == 30
            assert config.pool_recycle == 3600


class TestCacheConfig:
    """Test CacheConfig class functionality."""

    def test_cache_config_defaults(self):
        """Test default cache configuration values."""
        config = CacheConfig()

        assert config.type == "simple"
        assert config.redis_url == "redis://localhost:6379/0"
        assert config.default_timeout == 300
        assert config.key_prefix == "flask_app"

    def test_cache_config_custom_values(self):
        """Test cache configuration with custom values."""
        config = CacheConfig(
            type="redis",
            redis_url="redis://remote:6379/1",
            default_timeout=600,
            key_prefix="my_app",
        )

        assert config.type == "redis"
        assert config.redis_url == "redis://remote:6379/1"
        assert config.default_timeout == 600
        assert config.key_prefix == "my_app"

    def test_cache_config_from_env_with_redis(self):
        """Test cache config creation with Redis URL."""
        with patch.dict(
            os.environ,
            {
                "REDIS_URL": "redis://localhost:6379/2",
                "CACHE_DEFAULT_TIMEOUT": "900",
                "CACHE_KEY_PREFIX": "test_app",
            },
        ):
            config = CacheConfig.from_env()

            assert config.type == "redis"
            assert config.redis_url == "redis://localhost:6379/2"
            assert config.default_timeout == 900
            assert config.key_prefix == "test_app"

    def test_cache_config_from_env_without_redis(self):
        """Test cache config creation without Redis URL."""
        with patch.dict(os.environ, {}, clear=True):
            config = CacheConfig.from_env()

            assert config.type == "simple"
            assert config.redis_url == "redis://localhost:6379/0"
            assert config.default_timeout == 300
            assert config.key_prefix == "flask_app"


class TestSecurityConfig:
    """Test SecurityConfig class functionality."""

    def test_security_config_defaults(self):
        """Test default security configuration values."""
        config = SecurityConfig()

        assert config.secret_key == "dev-secret-key-change-in-production"
        assert (
            config.jwt_secret_key == "dev-secret-key-change-in-production"
        )  # post_init sets this
        assert config.jwt_access_token_expires == timedelta(hours=1)
        assert config.jwt_refresh_token_expires == timedelta(days=30)
        assert config.force_https is False
        assert config.csrf_enabled is True

    def test_security_config_post_init(self):
        """Test that post_init sets JWT secret key."""
        config = SecurityConfig(secret_key="test-secret")

        assert config.jwt_secret_key == "test-secret"

    def test_security_config_custom_jwt_secret(self):
        """Test security config with custom JWT secret."""
        config = SecurityConfig(secret_key="app-secret", jwt_secret_key="jwt-secret")

        assert config.secret_key == "app-secret"
        assert config.jwt_secret_key == "jwt-secret"

    def test_security_config_from_env(self):
        """Test security config creation from environment."""
        with patch.dict(
            os.environ,
            {
                "SECRET_KEY": "env-secret-key-very-long-and-secure",
                "JWT_SECRET_KEY": "jwt-env-secret-key-also-very-long",
                "JWT_ACCESS_TOKEN_EXPIRES": "7200",
                "JWT_REFRESH_TOKEN_EXPIRES": "7",
                "FORCE_HTTPS": "true",
                "WTF_CSRF_ENABLED": "false",
            },
        ):
            config = SecurityConfig.from_env("development")

            assert config.secret_key == "env-secret-key-very-long-and-secure"
            assert config.jwt_secret_key == "jwt-env-secret-key-also-very-long"
            assert config.jwt_access_token_expires == timedelta(seconds=7200)
            assert config.jwt_refresh_token_expires == timedelta(days=7)
            assert config.force_https is True
            assert config.csrf_enabled is False

    def test_security_config_validate_weak_key_production(self):
        """Test validation of weak secret keys in production."""
        with pytest.raises(ValueError, match="cannot use weak default value"):
            SecurityConfig._validate_secret_key(
                "dev-secret-key-change-in-production", "production", "SECRET_KEY"
            )

    def test_security_config_validate_short_key_production(self):
        """Test validation of short secret keys in production."""
        with pytest.raises(ValueError, match="must be at least 32 characters"):
            SecurityConfig._validate_secret_key("short-key", "production", "SECRET_KEY")

    def test_security_config_validate_weak_pattern_production(self):
        """Test validation of weak patterns in production."""
        with pytest.raises(ValueError, match="is too weak for production"):
            SecurityConfig._validate_secret_key("password", "production", "SECRET_KEY")

    @patch("app.config_manager.logging")
    def test_security_config_validate_short_key_development(self, mock_logging):
        """Test validation warning for short keys in development."""
        SecurityConfig._validate_secret_key("short", "development", "SECRET_KEY")

        mock_logging.warning.assert_called_once()
        assert "shorter than recommended" in mock_logging.warning.call_args[0][0]

    def test_security_config_validate_good_key_production(self):
        """Test validation of good secret key in production."""
        # Should not raise any exception
        SecurityConfig._validate_secret_key(
            "this-is-a-very-long-and-secure-secret-key-for-production-use",
            "production",
            "SECRET_KEY",
        )


class TestAPIConfig:
    """Test APIConfig class functionality."""

    def test_api_config_defaults(self):
        """Test default API configuration values."""
        config = APIConfig()

        assert config.version == "v2"
        assert config.rate_limit == "100 per hour"
        assert config.docs_enabled is True
        assert config.cors_origins == []
        assert config.max_content_length == 16 * 1024 * 1024

    def test_api_config_custom_values(self):
        """Test API configuration with custom values."""
        config = APIConfig(
            version="v3",
            rate_limit="200 per hour",
            docs_enabled=False,
            cors_origins=["http://localhost:3000"],
            max_content_length=32 * 1024 * 1024,
        )

        assert config.version == "v3"
        assert config.rate_limit == "200 per hour"
        assert config.docs_enabled is False
        assert config.cors_origins == ["http://localhost:3000"]
        assert config.max_content_length == 32 * 1024 * 1024

    def test_api_config_from_env(self):
        """Test API config creation from environment."""
        with patch.dict(
            os.environ,
            {
                "API_VERSION": "v1",
                "API_RATE_LIMIT": "500 per hour",
                "API_DOCS_ENABLED": "false",
                "CORS_ORIGINS": "http://localhost:3000,https://example.com",
                "MAX_CONTENT_LENGTH": str(64 * 1024 * 1024),
            },
        ):
            config = APIConfig.from_env()

            assert config.version == "v1"
            assert config.rate_limit == "500 per hour"
            assert config.docs_enabled is False
            assert config.cors_origins == [
                "http://localhost:3000",
                "https://example.com",
            ]
            assert config.max_content_length == 64 * 1024 * 1024

    def test_api_config_cors_origins_parsing(self):
        """Test CORS origins parsing from environment."""
        with patch.dict(
            os.environ,
            {"CORS_ORIGINS": " http://localhost:3000 , https://example.com , "},
        ):
            config = APIConfig.from_env()

            assert config.cors_origins == [
                "http://localhost:3000",
                "https://example.com",
            ]


class TestLoggingConfig:
    """Test LoggingConfig class functionality."""

    def test_logging_config_defaults(self):
        """Test default logging configuration values."""
        config = LoggingConfig()

        assert config.level == "INFO"
        assert config.format == "%(asctime)s %(levelname)s %(name)s: %(message)s"
        assert config.file_path is None
        assert config.structured is False

    def test_logging_config_custom_values(self):
        """Test logging configuration with custom values."""
        config = LoggingConfig(
            level="DEBUG",
            format="%(levelname)s: %(message)s",
            file_path="/var/log/app.log",
            structured=True,
        )

        assert config.level == "DEBUG"
        assert config.format == "%(levelname)s: %(message)s"
        assert config.file_path == "/var/log/app.log"
        assert config.structured is True

    def test_logging_config_from_env_development(self):
        """Test logging config for development environment."""
        config = LoggingConfig.from_env("development")

        assert config.level == "DEBUG"

    def test_logging_config_from_env_testing(self):
        """Test logging config for testing environment."""
        config = LoggingConfig.from_env("testing")

        assert config.level == "WARNING"

    def test_logging_config_from_env_production(self):
        """Test logging config for production environment."""
        config = LoggingConfig.from_env("production")

        assert config.level == "WARNING"

    def test_logging_config_from_env_custom(self):
        """Test logging config with custom environment variables."""
        with patch.dict(
            os.environ,
            {
                "LOG_LEVEL": "ERROR",
                "LOG_FORMAT": "%(message)s",
                "LOG_FILE": "/tmp/app.log",
                "STRUCTURED_LOGGING": "true",
            },
        ):
            config = LoggingConfig.from_env("development")

            assert config.level == "ERROR"
            assert config.format == "%(message)s"
            assert config.file_path == "/tmp/app.log"
            assert config.structured is True


class TestConfigManager:
    """Test ConfigManager class functionality."""

    def test_config_manager_initialization(self):
        """Test ConfigManager initialization."""
        manager = ConfigManager("development")

        assert manager.env == "development"
        assert manager._config is not None
        assert isinstance(manager._config, dict)

    def test_config_manager_default_env(self):
        """Test ConfigManager with default environment."""
        with patch.dict(os.environ, {"FLASK_ENV": "testing"}):
            manager = ConfigManager()

            assert manager.env == "testing"

    def test_config_manager_get_config(self):
        """Test getting complete configuration."""
        manager = ConfigManager("development")
        config = manager.get_config()

        assert isinstance(config, dict)
        assert "SECRET_KEY" in config
        assert "SQLALCHEMY_DATABASE_URI" in config
        assert "DEBUG" in config
        assert config["DEBUG"] is True  # development mode

    def test_config_manager_get_value(self):
        """Test getting specific configuration values."""
        manager = ConfigManager("development")

        assert manager.get("DEBUG") is True
        assert manager.get("TESTING") is False
        assert manager.get("NONEXISTENT_KEY", "default") == "default"

    def test_config_manager_testing_environment(self):
        """Test ConfigManager for testing environment."""
        manager = ConfigManager("testing")
        config = manager.get_config()

        assert config["TESTING"] is True
        assert config["DEBUG"] is False
        assert "sqlite:///:memory:" in config["SQLALCHEMY_DATABASE_URI"]

    def test_config_manager_production_environment(self):
        """Test ConfigManager for production environment."""
        with patch.dict(
            os.environ,
            {
                "SECRET_KEY": "production-secret-key-very-long-and-secure-for-testing",
                "DATABASE_URL": "postgresql://user:pass@localhost/prod_db",
            },
        ):
            manager = ConfigManager("production")
            config = manager.get_config()

            assert config["DEBUG"] is False
            assert config["TESTING"] is False

    @patch("app.config_manager.logging")
    def test_config_manager_validate_production_missing_vars(self, mock_logging):
        """Test production validation with missing required variables."""
        with patch.dict(os.environ, {}, clear=True):
            manager = ConfigManager("production")

            with pytest.raises(ValueError, match="Production configuration errors"):
                manager.validate()

    @patch("app.config_manager.logging")
    def test_config_manager_validate_production_sqlite_warning(self, mock_logging):
        """Test production validation with SQLite warning."""
        with patch.dict(
            os.environ,
            {
                "SECRET_KEY": "production-secret-key-very-long-and-secure-for-testing",
                "DATABASE_URL": "sqlite:///prod.db",
            },
        ):
            manager = ConfigManager("production")
            manager.validate()

            mock_logging.warning.assert_called_with(
                "Using SQLite in production is not recommended"
            )

    @patch("app.config_manager.logging")
    def test_config_manager_validate_testing_sqlite_warning(self, mock_logging):
        """Test testing validation with non-memory SQLite warning."""
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///test.db"}):
            manager = ConfigManager("testing")
            manager.validate()

            mock_logging.warning.assert_called_with(
                "Testing should use in-memory SQLite database"
            )

    @patch("builtins.print")
    def test_config_manager_print_summary(self, mock_print):
        """Test configuration summary printing."""
        manager = ConfigManager("development")
        manager.print_summary()

        # Check that print was called multiple times
        assert mock_print.call_count > 0

        # Check that summary contains expected information
        calls = [call[0][0] for call in mock_print.call_args_list]
        summary_text = "\n".join(calls)

        assert "Configuration Summary (development)" in summary_text
        assert "Database:" in summary_text
        assert "Cache:" in summary_text


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_get_config_function(self):
        """Test get_config convenience function."""
        config = get_config("development")

        assert isinstance(config, dict)
        assert "SECRET_KEY" in config
        assert config["DEBUG"] is True

    def test_create_config_class_function(self):
        """Test create_config_class convenience function."""
        ConfigClass = create_config_class("development")

        assert hasattr(ConfigClass, "SECRET_KEY")
        assert hasattr(ConfigClass, "DEBUG")
        assert ConfigClass.DEBUG is True
        assert hasattr(ConfigClass, "SQLALCHEMY_DATABASE_URI")

    def test_create_config_class_attributes(self):
        """Test that created config class has all expected attributes."""
        ConfigClass = create_config_class("testing")

        # Test some key attributes
        assert ConfigClass.TESTING is True
        assert ConfigClass.DEBUG is False
        assert "sqlite:///:memory:" in ConfigClass.SQLALCHEMY_DATABASE_URI
        assert hasattr(ConfigClass, "CACHE_TYPE")
        assert hasattr(ConfigClass, "API_VERSION")

    def test_config_class_instantiation(self):
        """Test that config class can be instantiated."""
        ConfigClass = create_config_class("development")
        config_instance = ConfigClass()

        assert config_instance is not None
        assert hasattr(config_instance, "SECRET_KEY")
