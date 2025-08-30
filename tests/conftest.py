"""Pytest Configuration and Shared Fixtures.

Essential fixtures for testing Flask applications.
"""

import os
import tempfile
from datetime import datetime
from unittest.mock import Mock

import pytest

from app import create_app
from app.extensions import db as _db
from tests import TEST_CONFIG


# Simple test data
TEST_USER_DATA = {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpassword123",
}

TEST_POST_DATA = {
    "id": 1,
    "title": "Test Post",
    "content": "Test content",
    "user_id": 1,
}


@pytest.fixture(scope="session")
def app():
    """Create Flask application for testing.

    Returns:
        Flask: Configured Flask application instance
    """
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp()

    # Update test config with temporary database
    test_config = TEST_CONFIG.copy()
    test_config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    # Create app with test configuration
    app = create_app(test_config)

    # Establish application context
    with app.app_context():
        # Create all database tables
        _db.create_all()

        yield app

        # Cleanup
        _db.drop_all()

    # Close and remove temporary database file
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope="function")
def client(app):
    """Create test client for making HTTP requests.

    Args:
        app: Flask application fixture

    Returns:
        FlaskClient: Test client instance
    """
    return app.test_client()


@pytest.fixture(scope="function")
def db(app):
    """Create database instance for testing."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope="function")
def auth_headers():
    """Authentication headers for API tests."""
    return {"Content-Type": "application/json", "Authorization": "Bearer test-token"}


@pytest.fixture(scope="session")
def sample_data():
    """Sample data for testing."""
    return {
        "user": TEST_USER_DATA,
        "post": TEST_POST_DATA,
    }


# Pytest configuration


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "api: mark test as an API test")
    config.addinivalue_line("markers", "slow: mark test as slow running")