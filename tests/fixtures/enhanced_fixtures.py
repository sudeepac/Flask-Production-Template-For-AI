"""Enhanced test fixtures and mock data for comprehensive testing.

This module provides reusable fixtures and mock data that can be used
across different test modules to ensure consistency and reduce duplication.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest
from marshmallow import Schema, fields

from app.utils.error_handlers import APIError, ValidationAPIError


class MockUser:
    """Mock user model for testing."""

    def __init__(
        self,
        id=1,
        username="testuser",
        email="test@example.com",
        created_at=None,
        is_active=True,
    ):
        self.id = id
        self.username = username
        self.email = email
        self.created_at = created_at or datetime.utcnow()
        self.is_active = is_active
        self.posts = []

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active,
            "posts_count": len(self.posts),
        }


class MockPost:
    """Mock post model for testing."""

    def __init__(
        self,
        id=1,
        title="Test Post",
        content="Test content",
        user_id=1,
        created_at=None,
        published=True,
    ):
        self.id = id
        self.title = title
        self.content = content
        self.user_id = user_id
        self.created_at = created_at or datetime.utcnow()
        self.published = published

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "published": self.published,
        }


class TestDataFactory:
    """Factory for creating test data with various scenarios."""

    @staticmethod
    def create_user_data(override=None):
        """Create user data with optional overrides."""
        base_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepassword123",
            "first_name": "Test",
            "last_name": "User",
            "age": 25,
        }
        if override:
            base_data.update(override)
        return base_data

    @staticmethod
    def create_post_data(override=None):
        """Create post data with optional overrides."""
        base_data = {
            "title": "Test Post Title",
            "content": "This is test post content with sufficient length.",
            "tags": ["test", "example"],
            "published": True,
            "category": "general",
        }
        if override:
            base_data.update(override)
        return base_data

    @staticmethod
    def create_invalid_user_data():
        """Create various invalid user data scenarios."""
        return [
            {},  # Empty data
            {"username": ""},  # Empty username
            {"email": "invalid-email"},  # Invalid email
            {"username": "a" * 101},  # Username too long
            {"age": -5},  # Negative age
            {"age": "not_a_number"},  # Invalid age type
        ]

    @staticmethod
    def create_invalid_post_data():
        """Create various invalid post data scenarios."""
        return [
            {},  # Empty data
            {"title": ""},  # Empty title
            {"content": "x" * 10001},  # Content too long
            {"title": "x" * 201},  # Title too long
            {"tags": "not_a_list"},  # Invalid tags type
        ]


class MockDatabaseSession:
    """Mock database session for testing database operations."""

    def __init__(self):
        self.added_objects = []
        self.deleted_objects = []
        self.committed = False
        self.rolled_back = False
        self.query_results = {}

    def add(self, obj):
        """Mock add operation."""
        self.added_objects.append(obj)

    def delete(self, obj):
        """Mock delete operation."""
        self.deleted_objects.append(obj)

    def commit(self):
        """Mock commit operation."""
        self.committed = True

    def rollback(self):
        """Mock rollback operation."""
        self.rolled_back = True

    def query(self, model):
        """Mock query operation."""
        mock_query = Mock()
        mock_query.filter_by.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = self.query_results.get(model)
        mock_query.all.return_value = self.query_results.get(model, [])
        mock_query.count.return_value = len(self.query_results.get(model, []))
        return mock_query

    def set_query_result(self, model, result):
        """Set mock query result for a model."""
        self.query_results[model] = result


class MockRequest:
    """Mock Flask request object for testing."""

    def __init__(
        self,
        method="GET",
        endpoint="test_endpoint",
        json_data=None,
        form_data=None,
        args_data=None,
    ):
        self.method = method
        self.endpoint = endpoint
        self._json_data = json_data
        self._form_data = form_data or {}
        self._args_data = args_data or {}
        self.headers = {}

    def get_json(self, force=False, silent=False):
        """Mock get_json method."""
        if self._json_data is None and not silent:
            return None
        return self._json_data

    @property
    def form(self):
        """Mock form data."""
        return self._form_data

    @property
    def args(self):
        """Mock query arguments."""
        return self._args_data


class MockResponse:
    """Mock Flask response object for testing."""

    def __init__(self, data=None, status_code=200, headers=None):
        self.data = data
        self.status_code = status_code
        self.headers = headers or {}
        self.json = data if isinstance(data, dict) else None

    def get_json(self):
        """Get JSON data from response."""
        return self.json


@pytest.fixture
def mock_user():
    """Fixture providing a mock user instance."""
    return MockUser()


@pytest.fixture
def mock_post():
    """Fixture providing a mock post instance."""
    return MockPost()


@pytest.fixture
def mock_users_list():
    """Fixture providing a list of mock users."""
    return [
        MockUser(id=1, username="user1", email="user1@example.com"),
        MockUser(id=2, username="user2", email="user2@example.com"),
        MockUser(id=3, username="user3", email="user3@example.com", is_active=False),
    ]


@pytest.fixture
def mock_posts_list():
    """Fixture providing a list of mock posts."""
    return [
        MockPost(id=1, title="First Post", user_id=1),
        MockPost(id=2, title="Second Post", user_id=1),
        MockPost(id=3, title="Third Post", user_id=2, published=False),
    ]


@pytest.fixture
def test_data_factory():
    """Fixture providing the test data factory."""
    return TestDataFactory()


@pytest.fixture
def mock_db_session():
    """Fixture providing a mock database session."""
    return MockDatabaseSession()


@pytest.fixture
def mock_request_factory():
    """Fixture providing a factory for creating mock requests."""

    def _create_request(**kwargs):
        return MockRequest(**kwargs)

    return _create_request


@pytest.fixture
def mock_response_factory():
    """Fixture providing a factory for creating mock responses."""

    def _create_response(**kwargs):
        return MockResponse(**kwargs)

    return _create_response


@pytest.fixture
def api_error_scenarios():
    """Fixture providing various API error scenarios for testing."""
    return {
        "validation_error": ValidationAPIError(
            "Validation failed", details={"field": ["Required field"]}
        ),
        "not_found_error": APIError("Resource not found", 404),
        "unauthorized_error": APIError("Unauthorized access", 401),
        "server_error": APIError("Internal server error", 500),
        "rate_limit_error": APIError("Rate limit exceeded", 429),
    }


@pytest.fixture
def datetime_scenarios():
    """Fixture providing various datetime scenarios for testing."""
    now = datetime.utcnow()
    return {
        "now": now,
        "past": now - timedelta(days=30),
        "future": now + timedelta(days=30),
        "yesterday": now - timedelta(days=1),
        "tomorrow": now + timedelta(days=1),
        "last_week": now - timedelta(weeks=1),
        "next_week": now + timedelta(weeks=1),
    }


@pytest.fixture
def validation_test_cases():
    """Fixture providing validation test cases for different scenarios."""
    return {
        "valid_email": "test@example.com",
        "invalid_emails": [
            "invalid-email",
            "@example.com",
            "test@",
            "test.example.com",
            "",
        ],
        "valid_usernames": [
            "testuser",
            "test_user",
            "testuser123",
            "user-name",
        ],
        "invalid_usernames": [
            "",
            "a",  # Too short
            "a" * 101,  # Too long
            "test user",  # Contains space
            "test@user",  # Contains @
        ],
        "valid_passwords": [
            "password123",
            "SecurePass123!",
            "my-secure-password",
        ],
        "invalid_passwords": [
            "",
            "123",  # Too short
            "password",  # Too simple
        ],
    }


@pytest.fixture
def performance_test_data():
    """Fixture providing data for performance testing."""
    return {
        "small_dataset": list(range(10)),
        "medium_dataset": list(range(100)),
        "large_dataset": list(range(1000)),
        "bulk_users": [
            TestDataFactory.create_user_data(
                {"username": f"user{i}", "email": f"user{i}@example.com"}
            )
            for i in range(100)
        ],
        "bulk_posts": [
            TestDataFactory.create_post_data(
                {"title": f"Post {i}", "content": f"Content for post {i}"}
            )
            for i in range(50)
        ],
    }


class TestSchemaFactory:
    """Factory for creating test schemas for validation testing."""

    @staticmethod
    def create_user_schema():
        """Create a user validation schema for testing."""

        class UserSchema(Schema):
            username = fields.Str(required=True, validate=lambda x: len(x) >= 3)
            email = fields.Email(required=True)
            age = fields.Int(required=False, validate=lambda x: x >= 0)
            password = fields.Str(required=True, validate=lambda x: len(x) >= 8)

        return UserSchema()

    @staticmethod
    def create_post_schema():
        """Create a post validation schema for testing."""

        class PostSchema(Schema):
            title = fields.Str(required=True, validate=lambda x: len(x) <= 200)
            content = fields.Str(required=True, validate=lambda x: len(x) <= 10000)
            published = fields.Bool(required=False, load_default=True)
            tags = fields.List(fields.Str(), required=False)

        return PostSchema()


@pytest.fixture
def test_schema_factory():
    """Fixture providing the test schema factory."""
    return TestSchemaFactory()
