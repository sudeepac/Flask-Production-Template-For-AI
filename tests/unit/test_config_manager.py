"""Unit tests for simplified configuration manager.

This module tests the simplified configuration management functionality
including the ConfigManager class and get_config function.
"""

import os
from unittest.mock import patch

import pytest

from app.config_manager import (
    ConfigManager,
    get_config,
)


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

    def test_config_manager_testing_env(self):
        """Test testing environment configuration."""
        manager = ConfigManager("testing")
        config = manager.get_config()

        assert config["TESTING"] is True
        assert config["DEBUG"] is False
        assert "sqlite:///:memory:" in config["SQLALCHEMY_DATABASE_URI"]

    @patch.dict(os.environ, {"SECRET_KEY": "this-is-a-very-long-and-secure-secret-key-for-production-testing-purposes"})
    def test_config_manager_production_env(self):
        """Test production environment configuration."""
        manager = ConfigManager("production")
        config = manager.get_config()

        assert config["DEBUG"] is False
        assert config["TESTING"] is False

    @patch.dict(os.environ, {"SECRET_KEY": ""})
    def test_config_manager_validation_missing_secret(self):
        """Test validation fails with missing SECRET_KEY in production."""
        with pytest.raises(ValueError, match="SECRET_KEY must be at least 32 characters long in production"):
            ConfigManager("production")

    @patch.dict(os.environ, {"SECRET_KEY": "this-is-a-very-long-and-secure-secret-key-for-production-testing-purposes"})
    def test_config_manager_validation_success(self):
        """Test validation succeeds with proper SECRET_KEY."""
        manager = ConfigManager("production")
        
        # Should not raise an exception
        manager.validate()


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_get_config_function(self):
        """Test get_config convenience function."""
        config = get_config("development")

        assert isinstance(config, dict)
        assert "SECRET_KEY" in config
        assert config["DEBUG"] is True

    def test_get_config_default_env(self):
        """Test get_config with default environment."""
        with patch.dict(os.environ, {"FLASK_ENV": "testing"}):
            config = get_config()

            assert isinstance(config, dict)
            assert config["TESTING"] is True

    @patch.dict(os.environ, {"DATABASE_URL": "postgresql://test"})
    def test_get_config_with_env_vars(self):
        """Test get_config respects environment variables."""
        config = get_config("development")

        assert "postgresql://test" in config["SQLALCHEMY_DATABASE_URI"]

    @patch.dict(os.environ, {"REDIS_URL": "redis://test:6379"})
    def test_get_config_redis_cache(self):
        """Test get_config with Redis cache configuration."""
        config = get_config("development")

        assert config["CACHE_TYPE"] == "redis"
        assert "redis://test:6379" in config["CACHE_REDIS_URL"]
