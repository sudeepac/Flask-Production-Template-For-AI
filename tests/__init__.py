"""Test Suite Package.

This package contains all tests for the Flask application.
Tests are organized by functionality and follow pytest conventions.

Test Structure:
- test_*.py: Test modules
- conftest.py: Shared test fixtures and configuration
- fixtures/: Test data and fixtures
- integration/: Integration tests
- unit/: Unit tests
- performance/: Performance tests

Test Categories:
- Unit Tests: Test individual functions and classes
- Integration Tests: Test component interactions
- API Tests: Test API endpoints
- ML Tests: Test ML model functionality
- Performance Tests: Test performance characteristics

Usage:
    # Run all tests
    pytest

    # Run specific test file
    pytest tests/test_api.py

    # Run with coverage
    pytest --cov=app

    # Run specific test category
    pytest -m unit
    pytest -m integration

See AI_INSTRUCTIONS.md §7 for testing guidelines.
"""

import sys
from pathlib import Path

# Add the app directory to the Python path for imports
app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))

# Test configuration
TEST_CONFIG = {
    "TESTING": True,
    "WTF_CSRF_ENABLED": False,
    "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    "SECRET_KEY": "test-secret-key",
    "JWT_SECRET_KEY": "test-jwt-secret",
    "CACHE_TYPE": "simple",
    "ML_MODEL_PATH": "tests/fixtures/models",
    "ML_AUTO_DISCOVER_SERVICES": False,
}

# Test markers for pytest
pytest_plugins = [
    "tests.fixtures.app_fixtures",
    "tests.fixtures.data_fixtures",
]

# Export test utilities
__all__ = [
    "TEST_CONFIG",
]
