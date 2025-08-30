"""Pytest Configuration and Shared Fixtures.

This module contains pytest configuration and shared fixtures
that are used across multiple test modules.

Fixtures:
- app: Flask application instance for testing
- client: Test client for making HTTP requests
- db: Database instance for testing
- auth_headers: Authentication headers for API tests
- sample_data: Sample data for testing

See AI_INSTRUCTIONS.md §7 for testing guidelines.
"""

import os
import tempfile

import pytest

from app import create_app
from app.extensions import db as _db
from tests import TEST_CONFIG


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
def runner(app):
    """Create test runner for CLI commands.

    Args:
        app: Flask application fixture

    Returns:
        FlaskCliRunner: CLI test runner instance
    """
    return app.test_cli_runner()


@pytest.fixture(scope="function")
def db(app):
    """Create database instance for testing.

    Args:
        app: Flask application fixture

    Returns:
        SQLAlchemy: Database instance
    """
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope="function")
def session(db):
    """Create database session for testing.

    Args:
        db: Database fixture

    Returns:
        Session: Database session
    """
    connection = db.engine.connect()
    transaction = connection.begin()

    # Configure session to use the connection
    session = db.create_scoped_session(options={"bind": connection, "binds": {}})

    # Make session available to the app
    db.session = session

    yield session

    # Cleanup
    transaction.rollback()
    connection.close()
    session.remove()


@pytest.fixture(scope="function")
def auth_headers():
    """Create authentication headers for API tests.

    Returns:
        dict: Headers with authentication token
    """
    # This would typically create a JWT token for testing
    # For now, return basic headers
    return {"Content-Type": "application/json", "Authorization": "Bearer test-token"}


@pytest.fixture(scope="function")
def api_headers():
    """Create standard API headers for testing.

    Returns:
        dict: Standard API headers
    """
    return {"Content-Type": "application/json", "Accept": "application/json"}


@pytest.fixture(scope="session")
def sample_user_data():
    """Sample user data for testing.

    Returns:
        dict: Sample user data
    """
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User",
    }


@pytest.fixture(scope="session")
def sample_ml_data():
    """Sample ML data for testing.

    Returns:
        dict: Sample ML input data
    """
    return {
        "features": [1.0, 2.0, 3.0, 4.0, 5.0],
        "metadata": {"source": "test", "timestamp": "2024-01-01T00:00:00Z"},
    }


@pytest.fixture(scope="session")
def sample_api_response():
    """Sample API response for testing.

    Returns:
        dict: Sample API response structure
    """
    return {
        "status": "success",
        "data": {"result": "test"},
        "message": "Operation completed successfully",
        "timestamp": "2024-01-01T00:00:00Z",
    }


@pytest.fixture(scope="function")
def mock_ml_model(monkeypatch):
    """Mock ML model for testing.

    Args:
        monkeypatch: Pytest monkeypatch fixture

    Returns:
        Mock: Mock ML model object
    """

    class MockModel:
        """
            """
            TODO: Add return description
            Returns:
                """
                TODO: Add return description
                Returns:

                data: TODO: Add description
                Args:

                TODO: Add function description.

                Function predict_proba.
                """

            data: TODO: Add description
            Args:

            TODO: Add function description.

            Function predict.
            """
        TODO: Add class description.

        Class MockModel.
        """
        def predict(self, data):
            return [0.5] * len(data)

        def predict_proba(self, data):
            return [[0.5, 0.5]] * len(data)

    mock_model = MockModel()

    # Patch model loading functions
    monkeypatch.setattr("joblib.load", lambda path: mock_model)

    return mock_model


@pytest.fixture(scope="function")
def temp_model_file():
    """Create temporary model file for testing.

    Returns:
        str: Path to temporary model file
    """
    import pickle

    # Create a simple mock model
    mock_model = {"type": "test_model", "version": "1.0"}

    # Create temporary file
    fd, path = tempfile.mkstemp(suffix=".pkl")

    try:
        with os.fdopen(fd, "wb") as f:
            pickle.dump(mock_model, f)

        yield path

    finally:
        # Cleanup
        if os.path.exists(path):
            os.unlink(path)


@pytest.fixture(scope="function")
def temp_directory():
    """Create temporary directory for testing.

    Returns:
        str: Path to temporary directory
    """
    import shutil
    import tempfile

    temp_dir = tempfile.mkdtemp()

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers.

    Args:
        config: Pytest configuration object
    """
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "api: mark test as an API test")
    config.addinivalue_line("markers", "ml: mark test as an ML test")
    config.addinivalue_line("markers", "performance: mark test as a performance test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically.

    Args:
        config: Pytest configuration object
        items: List of collected test items
    """
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "api" in str(item.fspath):
            item.add_marker(pytest.mark.api)
        elif "ml" in str(item.fspath):
            item.add_marker(pytest.mark.ml)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)

        # Add slow marker for tests that take longer than 1 second
        if hasattr(item, "get_closest_marker"):
            slow_marker = item.get_closest_marker("slow")
            if slow_marker:
                item.add_marker(pytest.mark.slow)