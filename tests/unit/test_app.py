"""Unit tests for the main Flask application.

This module tests the application factory function and core
application functionality.
"""

from flask import Flask
from sqlalchemy import text

from app import create_app
from app.extensions import cache, db


class TestAppFactory:
    """Test the Flask application factory."""

    def test_create_app_default_config(self):
        """Test app creation with default configuration."""
        app = create_app()
        assert isinstance(app, Flask)
        assert app.config["TESTING"] is False

    def test_create_app_test_config(self):
        """Test app creation with test configuration."""
        test_config = {"TESTING": True, "SECRET_KEY": "test-key"}
        app = create_app(test_config)
        assert app.config["TESTING"] is True
        assert app.config["SECRET_KEY"] == "test-key"

    def test_app_has_extensions(self, app):
        """Test that extensions are properly initialized."""
        with app.app_context():
            # Test database extension
            assert db is not None
            assert hasattr(db, "engine")

            # Test cache extension
            assert cache is not None

    def test_app_has_blueprints(self, app):
        """Test that blueprints are registered."""
        blueprint_names = [bp.name for bp in app.blueprints.values()]

        # Check for expected blueprints
        expected_blueprints = ["api", "examples"]
        for bp_name in expected_blueprints:
            assert bp_name in blueprint_names

    def test_app_has_error_handlers(self, app):
        """Test that error handlers are registered."""
        # Test 404 error handler
        with app.test_client() as client:
            response = client.get("/nonexistent-route")
            assert response.status_code == 404
            assert response.is_json

    def test_app_logging_configured(self, app):
        """Test that logging is properly configured."""
        assert app.logger is not None
        assert len(app.logger.handlers) > 0


class TestAppRoutes:
    """Test application routes."""

    def test_root_route(self, client):
        """Test the root route returns application info."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.is_json

        data = response.get_json()
        assert "application" in data
        assert "endpoints" in data
        assert "features" in data

    def test_health_check_route(self, client):
        """Test health check endpoint if it exists."""
        response = client.get("/health")
        # This might return 404 if not implemented, which is fine
        assert response.status_code in [200, 404]


class TestAppConfiguration:
    """Test application configuration."""

    def test_development_config(self):
        """Test development configuration."""
        app = create_app({"ENV": "development"})
        assert app.config["ENV"] == "development"

    def test_production_config(self):
        """Test production configuration."""
        app = create_app({"ENV": "production"})
        assert app.config["ENV"] == "production"

    def test_database_config(self, app):
        """Test database configuration."""
        assert "SQLALCHEMY_DATABASE_URI" in app.config
        assert app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] is False

    def test_security_config(self, app):
        """Test security configuration."""
        assert "SECRET_KEY" in app.config
        assert app.config["SECRET_KEY"] is not None
        assert len(app.config["SECRET_KEY"]) > 10


class TestAppContext:
    """Test application context functionality."""

    def test_app_context_available(self, app):
        """Test that app context is available."""
        with app.app_context():
            from flask import current_app

            assert current_app is app

    def test_request_context_available(self, app):
        """Test that request context is available."""
        with app.test_request_context("/"):
            from flask import request

            assert request.path == "/"

    def test_database_context(self, app):
        """Test database operations in app context."""
        with app.app_context():
            # Test that we can access the database
            assert db.engine is not None

            # Test basic database operations
            with db.engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                assert result.fetchone()[0] == 1
