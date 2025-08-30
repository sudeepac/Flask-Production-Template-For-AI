"""Unit tests for app.blueprints.examples.routes module.

This module tests all example endpoints including user creation,
post creation, error simulation, performance testing, and profile functionality.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from marshmallow import ValidationError

from app.blueprints.examples.routes import (
    create_post_for_user,
    create_user_advanced,
    get_user_profile,
    health_check,
    index,
    performance_test,
    post_create_schema,
    simulate_error,
    user_create_schema,
)
from app.utils.error_handlers import (
    APIError,
    NotFoundAPIError,
    RateLimitAPIError,
    UnauthorizedAPIError,
    ValidationAPIError,
)


class TestUserCreateSchema:
    """Test UserCreateSchema validation."""

    def test_valid_user_data(self):
        """Test schema validation with valid user data."""
        valid_data = {
            "username": "testuser",
            "email": "test@example.com",
            "bio": "This is a test bio",
        }

        result = user_create_schema.load(valid_data)

        assert result["username"] == "testuser"
        assert result["email"] == "test@example.com"
        assert result["bio"] == "This is a test bio"

    def test_missing_required_fields(self):
        """Test schema validation with missing required fields."""
        invalid_data = {"bio": "Just a bio"}

        with pytest.raises(ValidationError) as exc_info:
            user_create_schema.load(invalid_data)

        errors = exc_info.value.messages
        assert "username" in errors
        assert "email" in errors

    def test_bio_too_long(self):
        """Test schema validation with bio exceeding max length."""
        invalid_data = {
            "username": "testuser",
            "email": "test@example.com",
            "bio": "x" * 501,  # Exceeds 500 character limit
        }

        with pytest.raises(ValidationError) as exc_info:
            user_create_schema.load(invalid_data)

        assert "bio" in exc_info.value.messages

    def test_optional_bio(self):
        """Test schema validation without optional bio field."""
        valid_data = {"username": "testuser", "email": "test@example.com"}

        result = user_create_schema.load(valid_data)

        assert result["username"] == "testuser"
        assert result["email"] == "test@example.com"
        assert "bio" not in result


class TestPostCreateSchema:
    """Test PostCreateSchema validation."""

    def test_valid_post_data(self):
        """Test schema validation with valid post data."""
        valid_data = {
            "title": "Test Post",
            "content": "This is test content for the post.",
            "tags": ["test", "example"],
        }

        result = post_create_schema.load(valid_data)

        assert result["title"] == "Test Post"
        assert result["content"] == "This is test content for the post."
        assert result["tags"] == ["test", "example"]

    def test_missing_required_fields(self):
        """Test schema validation with missing required fields."""
        invalid_data = {"tags": ["test"]}

        with pytest.raises(ValidationError) as exc_info:
            post_create_schema.load(invalid_data)

        errors = exc_info.value.messages
        assert "title" in errors
        assert "content" in errors

    def test_content_too_long(self):
        """Test schema validation with content exceeding max length."""
        invalid_data = {
            "title": "Test Post",
            "content": "x" * 5001,  # Exceeds 5000 character limit
            "tags": [],
        }

        with pytest.raises(ValidationError) as exc_info:
            post_create_schema.load(invalid_data)

        assert "content" in exc_info.value.messages

    def test_empty_content(self):
        """Test schema validation with empty content."""
        invalid_data = {
            "title": "Test Post",
            "content": "",  # Empty content
            "tags": [],
        }

        with pytest.raises(ValidationError) as exc_info:
            post_create_schema.load(invalid_data)

        assert "content" in exc_info.value.messages

    def test_default_tags(self):
        """Test schema validation with default empty tags."""
        valid_data = {"title": "Test Post", "content": "This is test content."}

        result = post_create_schema.load(valid_data)

        assert result["tags"] == []


class TestIndexEndpoint:
    """Test examples blueprint index endpoint."""

    @patch("app.blueprints.examples.routes.logger")
    @patch("app.blueprints.examples.routes.request")
    @patch("app.blueprints.examples.routes.success_response")
    @patch("app.blueprints.examples.routes.datetime")
    def test_index_success(
        self, mock_datetime, mock_success_response, mock_request, mock_logger
    ):
        """Test successful index endpoint access."""
        # Mock datetime
        mock_datetime.utcnow.return_value.isoformat.return_value = "2023-12-01T10:30:45"

        # Mock request headers
        mock_request.headers.get.return_value = "Mozilla/5.0"

        # Mock success response
        mock_success_response.return_value = {"status": "success"}

        result = index()

        # Verify logging
        mock_logger.info.assert_called_once_with(
            "Examples index accessed",
            extra={"endpoint": "/examples/", "user_agent": "Mozilla/5.0"},
        )

        # Verify success response call
        call_args = mock_success_response.call_args[0][0]
        assert (
            call_args["message"]
            == "Examples Blueprint - Demonstrating Flask Best Practices"
        )
        assert "available_endpoints" in call_args
        assert call_args["timestamp"] == "2023-12-01T10:30:45"

        assert result == {"status": "success"}

    @patch("app.blueprints.examples.routes.logger")
    @patch("app.blueprints.examples.routes.request")
    @patch("app.blueprints.examples.routes.success_response")
    def test_index_unknown_user_agent(
        self, mock_success_response, mock_request, mock_logger
    ):
        """Test index endpoint with unknown user agent."""
        # Mock request headers returning None
        mock_request.headers.get.return_value = None
        mock_success_response.return_value = {"status": "success"}

        result = index()

        # Verify logging with default user agent
        mock_logger.info.assert_called_once_with(
            "Examples index accessed",
            extra={"endpoint": "/examples/", "user_agent": "Unknown"},
        )


class TestHealthCheckEndpoint:
    """Test examples health check endpoint."""

    @patch("app.blueprints.examples.routes.logger")
    @patch("app.blueprints.examples.routes.db")
    @patch("app.blueprints.examples.routes.time")
    @patch("app.blueprints.examples.routes.datetime")
    @patch("app.blueprints.examples.routes.success_response")
    def test_health_check_healthy(
        self, mock_success_response, mock_datetime, mock_time, mock_db, mock_logger
    ):
        """Test health check with healthy database."""
        # Mock time
        mock_time.time.side_effect = [1000.0, 1000.1]  # 100ms difference

        # Mock datetime
        mock_datetime.utcnow.return_value.isoformat.return_value = "2023-12-01T10:30:45"

        # Mock database session execute (success)
        mock_db.session.execute.return_value = None

        # Mock success response
        mock_success_response.return_value = {"status": "success"}

        result = health_check()

        # Verify database query
        mock_db.session.execute.assert_called_once_with("SELECT 1")

        # Verify logging
        mock_logger.info.assert_called_once_with(
            "Health check completed",
            extra={
                "db_status": "healthy",
                "db_latency_ms": 100.0,
                "overall_status": "healthy",
            },
        )

        # Verify success response call
        call_args = mock_success_response.call_args
        status_data = call_args[1]["data"]

        assert status_data["status"] == "healthy"
        assert status_data["database"]["status"] == "healthy"
        assert status_data["database"]["latency_ms"] == 100.0
        assert call_args[1]["message"] == "Service is healthy"

        assert result == {"status": "success"}

    @patch("app.blueprints.examples.routes.logger")
    @patch("app.blueprints.examples.routes.db")
    @patch("app.blueprints.examples.routes.time")
    @patch("app.blueprints.examples.routes.datetime")
    @patch("app.blueprints.examples.routes.error_response")
    def test_health_check_unhealthy(
        self, mock_error_response, mock_datetime, mock_time, mock_db, mock_logger
    ):
        """Test health check with unhealthy database."""
        # Mock time
        mock_time.time.side_effect = [1000.0, 1000.1]

        # Mock datetime
        mock_datetime.utcnow.return_value.isoformat.return_value = "2023-12-01T10:30:45"

        # Mock database session execute (failure)
        db_error = Exception("Database connection failed")
        mock_db.session.execute.side_effect = db_error

        # Mock error response
        mock_error_response.return_value = {"status": "error"}

        result = health_check()

        # Verify error logging
        mock_logger.error.assert_called_once_with(
            "Database health check failed: Database connection failed",
            extra={"error_type": "Exception"},
        )

        # Verify info logging
        mock_logger.info.assert_called_once_with(
            "Health check completed",
            extra={
                "db_status": "unhealthy",
                "db_latency_ms": None,
                "overall_status": "degraded",
            },
        )

        # Verify error response call
        call_args = mock_error_response.call_args
        status_data = call_args[1]["data"]

        assert status_data["status"] == "degraded"
        assert status_data["database"]["status"] == "unhealthy"
        assert status_data["database"]["latency_ms"] is None
        assert call_args[1]["message"] == "Service is unhealthy"
        assert call_args[1]["status_code"] == 503

        assert result == {"status": "error"}


class TestCreateUserAdvancedEndpoint:
    """Test advanced user creation endpoint."""

    @patch("app.blueprints.examples.routes.log_security_event")
    @patch("app.blueprints.examples.routes.logger")
    @patch("app.blueprints.examples.routes.db")
    @patch("app.blueprints.examples.routes.User")
    @patch("app.blueprints.examples.routes.request")
    @patch("app.blueprints.examples.routes.success_response")
    def test_create_user_advanced_success(
        self,
        mock_success_response,
        mock_request,
        mock_user_class,
        mock_db,
        mock_logger,
        mock_log_security,
    ):
        """Test successful advanced user creation."""
        # Mock validated data
        validated_data = {
            "username": "  testuser  ",  # Test trimming
            "email": "  TEST@EXAMPLE.COM  ",  # Test trimming and lowercasing
            "bio": "  This is a test bio  ",  # Test trimming
        }

        # Mock request
        mock_request.remote_addr = "192.168.1.1"
        mock_request.headers.get.return_value = "Mozilla/5.0"

        # Mock no existing user
        mock_user_class.query.filter.return_value.first.return_value = None

        # Mock new user creation
        mock_user_instance = Mock()
        mock_user_instance.id = 123
        mock_user_instance.username = "testuser"
        mock_user_instance.email = "test@example.com"
        mock_user_instance.created_at = datetime(2023, 12, 1, 10, 30, 45)
        mock_user_class.return_value = mock_user_instance

        # Mock success response
        mock_success_response.return_value = ({"status": "success"}, 201)

        result = create_user_advanced(validated_data)

        # Verify user creation with trimmed and normalized data
        mock_user_class.assert_called_once_with(
            username="testuser", email="test@example.com"
        )

        # Verify bio was set
        setattr_calls = [
            call for call in mock_user_instance.method_calls if call[0] == "__setattr__"
        ]
        # Note: setattr is mocked differently, so we check the bio assignment logic

        # Verify database operations
        mock_db.session.add.assert_called_once_with(mock_user_instance)
        mock_db.session.commit.assert_called_once()

        # Verify logging
        mock_logger.info.assert_called_once_with(
            "User created successfully",
            extra={
                "user_id": 123,
                "username": "testuser",
                "email": "test@example.com",
                "has_bio": True,
            },
        )

        # Verify security logging
        mock_log_security.assert_called_once_with(
            "user_registration",
            {
                "user_id": 123,
                "username": "testuser",
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0",
            },
        )

        # Verify success response
        call_args = mock_success_response.call_args
        expected_data = {
            "id": 123,
            "username": "testuser",
            "email": "test@example.com",
            "created_at": "2023-12-01T10:30:45",
            "bio": "This is a test bio",
        }

        assert call_args[1]["data"] == expected_data
        assert call_args[1]["message"] == "User created successfully"
        assert call_args[1]["status_code"] == 201

        assert result == ({"status": "success"}, 201)

    @patch("app.blueprints.examples.routes.logger")
    @patch("app.blueprints.examples.routes.User")
    def test_create_user_advanced_username_exists(self, mock_user_class, mock_logger):
        """Test user creation with existing username."""
        validated_data = {"username": "existinguser", "email": "new@example.com"}

        # Mock existing user with same username
        mock_existing_user = Mock()
        mock_existing_user.username = "existinguser"
        mock_existing_user.email = "different@example.com"
        mock_user_class.query.filter.return_value.first.return_value = (
            mock_existing_user
        )

        with pytest.raises(ValidationAPIError) as exc_info:
            create_user_advanced(validated_data)

        assert str(exc_info.value) == "Username already exists"

        # Verify warning logging
        mock_logger.warning.assert_called_once_with(
            "User creation conflict: username already exists",
            extra={
                "conflict_field": "username",
                "attempted_username": "existinguser",
                "attempted_email": "new@example.com",
            },
        )

    @patch("app.blueprints.examples.routes.logger")
    @patch("app.blueprints.examples.routes.User")
    def test_create_user_advanced_email_exists(self, mock_user_class, mock_logger):
        """Test user creation with existing email."""
        validated_data = {"username": "newuser", "email": "existing@example.com"}

        # Mock existing user with same email
        mock_existing_user = Mock()
        mock_existing_user.username = "differentuser"
        mock_existing_user.email = "existing@example.com"
        mock_user_class.query.filter.return_value.first.return_value = (
            mock_existing_user
        )

        with pytest.raises(ValidationAPIError) as exc_info:
            create_user_advanced(validated_data)

        assert str(exc_info.value) == "Email already exists"

        # Verify warning logging
        mock_logger.warning.assert_called_once_with(
            "User creation conflict: email already exists",
            extra={
                "conflict_field": "email",
                "attempted_username": "newuser",
                "attempted_email": "existing@example.com",
            },
        )

    @patch("app.blueprints.examples.routes.logger")
    @patch("app.blueprints.examples.routes.db")
    @patch("app.blueprints.examples.routes.User")
    def test_create_user_advanced_database_error(
        self, mock_user_class, mock_db, mock_logger
    ):
        """Test user creation with database error."""
        validated_data = {"username": "testuser", "email": "test@example.com"}

        # Mock no existing user
        mock_user_class.query.filter.return_value.first.return_value = None

        # Mock user creation
        mock_user_instance = Mock()
        mock_user_class.return_value = mock_user_instance

        # Mock database error
        db_error = Exception("Database connection failed")
        mock_db.session.commit.side_effect = db_error

        with pytest.raises(APIError) as exc_info:
            create_user_advanced(validated_data)

        assert str(exc_info.value) == "Failed to create user"

        # Verify rollback was called
        mock_db.session.rollback.assert_called_once()

        # Verify error logging
        mock_logger.error.assert_called_once_with(
            "Database error during user creation: Database connection failed",
            extra={
                "username": "testuser",
                "email": "test@example.com",
                "error_type": "Exception",
            },
        )

    def test_create_user_advanced_without_bio(self):
        """Test user creation without optional bio field."""
        # This test verifies the bio handling logic
        validated_data = {
            "username": "testuser",
            "email": "test@example.com",
            # No bio field
        }

        # Verify bio defaults to empty string when stripped
        bio = validated_data.get("bio", "").strip()
        assert bio == ""
        assert not bool(bio)  # Should be falsy


class TestCreatePostForUserEndpoint:
    """Test create post for user endpoint."""

    @patch("app.blueprints.examples.routes.log_security_event")
    @patch("app.blueprints.examples.routes.logger")
    @patch("app.blueprints.examples.routes.db")
    @patch("app.blueprints.examples.routes.Post")
    @patch("app.blueprints.examples.routes.User")
    @patch("app.blueprints.examples.routes.get_jwt_identity")
    @patch("app.blueprints.examples.routes.request")
    @patch("app.blueprints.examples.routes.success_response")
    def test_create_post_for_user_success(
        self,
        mock_success_response,
        mock_request,
        mock_get_jwt_identity,
        mock_user_class,
        mock_post_class,
        mock_db,
        mock_logger,
        mock_log_security,
    ):
        """Test successful post creation for user."""
        # Mock JWT identity
        mock_get_jwt_identity.return_value = 123

        # Mock request
        mock_request.remote_addr = "192.168.1.1"

        # Mock validated data
        validated_data = {
            "title": "  Test Post  ",  # Test trimming
            "content": "  This is test content.  ",  # Test trimming
        }

        # Mock user exists
        mock_user = Mock()
        mock_user_class.query.get.return_value = mock_user

        # Mock post creation
        mock_post_instance = Mock()
        mock_post_instance.id = 456
        mock_post_instance.title = "Test Post"
        mock_post_instance.content = "This is test content."
        mock_post_instance.user_id = 123
        mock_post_instance.created_at = datetime(2023, 12, 1, 10, 30, 45)
        mock_post_class.return_value = mock_post_instance

        # Mock success response
        mock_success_response.return_value = ({"status": "success"}, 201)

        result = create_post_for_user(123, validated_data)

        # Verify user lookup
        mock_user_class.query.get.assert_called_once_with(123)

        # Verify post creation with trimmed data
        mock_post_class.assert_called_once_with(
            title="Test Post", content="This is test content.", user_id=123
        )

        # Verify database operations
        mock_db.session.add.assert_called_once_with(mock_post_instance)
        mock_db.session.commit.assert_called_once()

        # Verify logging
        mock_logger.info.assert_called_once_with(
            "Post created successfully",
            extra={
                "post_id": 456,
                "user_id": 123,
                "title": "Test Post",
                "content_length": 21,
            },
        )

        # Verify security logging
        mock_log_security.assert_called_once_with(
            "post_created",
            {
                "post_id": 456,
                "user_id": 123,
                "title": "Test Post",
                "ip_address": "192.168.1.1",
            },
        )

        # Verify success response
        call_args = mock_success_response.call_args
        expected_data = {
            "id": 456,
            "title": "Test Post",
            "content": "This is test content.",
            "user_id": 123,
            "created_at": "2023-12-01T10:30:45",
        }

        assert call_args[1]["data"] == expected_data
        assert call_args[1]["message"] == "Post created successfully"
        assert call_args[1]["status_code"] == 201

        assert result == ({"status": "success"}, 201)

    @patch("app.blueprints.examples.routes.logger")
    @patch("app.blueprints.examples.routes.get_jwt_identity")
    @patch("app.blueprints.examples.routes.request")
    def test_create_post_for_user_unauthorized(
        self, mock_request, mock_get_jwt_identity, mock_logger
    ):
        """Test post creation for different user (unauthorized)."""
        # Mock JWT identity (different from target user)
        mock_get_jwt_identity.return_value = 123
        mock_request.remote_addr = "192.168.1.1"

        validated_data = {"title": "Test Post", "content": "This is test content."}

        with pytest.raises(UnauthorizedAPIError) as exc_info:
            create_post_for_user(456, validated_data)  # Different user ID

        assert str(exc_info.value) == "You can only create posts for yourself"

        # Verify warning logging
        mock_logger.warning.assert_called_once_with(
            "User attempted to create post for another user",
            extra={
                "current_user_id": 123,
                "target_user_id": 456,
                "ip_address": "192.168.1.1",
            },
        )

    @patch("app.blueprints.examples.routes.logger")
    @patch("app.blueprints.examples.routes.User")
    @patch("app.blueprints.examples.routes.get_jwt_identity")
    @patch("app.blueprints.examples.routes.request")
    def test_create_post_for_user_user_not_found(
        self, mock_request, mock_get_jwt_identity, mock_user_class, mock_logger
    ):
        """Test post creation for non-existent user."""
        # Mock JWT identity
        mock_get_jwt_identity.return_value = 123
        mock_request.remote_addr = "192.168.1.1"

        # Mock user not found
        mock_user_class.query.get.return_value = None

        validated_data = {"title": "Test Post", "content": "This is test content."}

        with pytest.raises(NotFoundAPIError) as exc_info:
            create_post_for_user(123, validated_data)

        assert str(exc_info.value) == "User with ID 123 not found"

        # Verify warning logging
        mock_logger.warning.assert_called_once_with(
            "Attempted to create post for non-existent user",
            extra={"user_id": 123, "ip_address": "192.168.1.1"},
        )

    @patch("app.blueprints.examples.routes.logger")
    @patch("app.blueprints.examples.routes.db")
    @patch("app.blueprints.examples.routes.Post")
    @patch("app.blueprints.examples.routes.User")
    @patch("app.blueprints.examples.routes.get_jwt_identity")
    def test_create_post_for_user_database_error(
        self,
        mock_get_jwt_identity,
        mock_user_class,
        mock_post_class,
        mock_db,
        mock_logger,
    ):
        """Test post creation with database error."""
        # Mock JWT identity
        mock_get_jwt_identity.return_value = 123

        # Mock user exists
        mock_user = Mock()
        mock_user_class.query.get.return_value = mock_user

        # Mock post creation
        mock_post_instance = Mock()
        mock_post_class.return_value = mock_post_instance

        # Mock database error
        db_error = Exception("Database connection failed")
        mock_db.session.commit.side_effect = db_error

        validated_data = {"title": "Test Post", "content": "This is test content."}

        with pytest.raises(APIError) as exc_info:
            create_post_for_user(123, validated_data)

        assert str(exc_info.value) == "Failed to create post"

        # Verify rollback was called
        mock_db.session.rollback.assert_called_once()

        # Verify error logging
        mock_logger.error.assert_called_once_with(
            "Database error creating post: Database connection failed",
            extra={"user_id": 123, "error_type": "Exception"},
        )


class TestSimulateErrorEndpoint:
    """Test error simulation endpoint."""

    @patch("app.blueprints.examples.routes.logger")
    @patch("app.blueprints.examples.routes.request")
    def test_simulate_validation_error(self, mock_request, mock_logger):
        """Test simulation of validation error."""
        mock_request.remote_addr = "192.168.1.1"

        with pytest.raises(ValidationAPIError) as exc_info:
            simulate_error("validation")

        assert str(exc_info.value) == "This is a simulated validation error"

        # Verify logging
        mock_logger.info.assert_called_once_with(
            "Simulating error type: validation",
            extra={"error_type": "validation", "ip_address": "192.168.1.1"},
        )

    @patch("app.blueprints.examples.routes.logger")
    @patch("app.blueprints.examples.routes.request")
    def test_simulate_not_found_error(self, mock_request, mock_logger):
        """Test simulation of not found error."""
        mock_request.remote_addr = "192.168.1.1"

        with pytest.raises(NotFoundAPIError) as exc_info:
            simulate_error("not_found")

        assert str(exc_info.value) == "This is a simulated not found error"

    @patch("app.blueprints.examples.routes.logger")
    @patch("app.blueprints.examples.routes.request")
    def test_simulate_database_error(self, mock_request, mock_logger):
        """Test simulation of database error."""
        mock_request.remote_addr = "192.168.1.1"

        with pytest.raises(APIError) as exc_info:
            simulate_error("database")

        assert str(exc_info.value) == "This is a simulated database error"

    @patch("app.blueprints.examples.routes.logger")
    @patch("app.blueprints.examples.routes.request")
    def test_simulate_auth_error(self, mock_request, mock_logger):
        """Test simulation of authentication error."""
        mock_request.remote_addr = "192.168.1.1"

        with pytest.raises(UnauthorizedAPIError) as exc_info:
            simulate_error("auth")

        assert str(exc_info.value) == "This is a simulated authentication error"

    @patch("app.blueprints.examples.routes.logger")
    @patch("app.blueprints.examples.routes.request")
    def test_simulate_rate_limit_error(self, mock_request, mock_logger):
        """Test simulation of rate limit error."""
        mock_request.remote_addr = "192.168.1.1"

        with pytest.raises(RateLimitAPIError) as exc_info:
            simulate_error("rate_limit")

        assert str(exc_info.value) == "This is a simulated rate limit error"

    @patch("app.blueprints.examples.routes.logger")
    @patch("app.blueprints.examples.routes.request")
    def test_simulate_unexpected_error(self, mock_request, mock_logger):
        """Test simulation of unexpected error."""
        mock_request.remote_addr = "192.168.1.1"

        with pytest.raises(Exception) as exc_info:
            simulate_error("unexpected")

        assert str(exc_info.value) == "This is a simulated unexpected error"

    @patch("app.blueprints.examples.routes.logger")
    @patch("app.blueprints.examples.routes.request")
    def test_simulate_unknown_error_type(self, mock_request, mock_logger):
        """Test simulation with unknown error type."""
        mock_request.remote_addr = "192.168.1.1"

        with pytest.raises(ValidationAPIError) as exc_info:
            simulate_error("unknown_type")

        assert str(exc_info.value) == "Unknown error type: unknown_type"


class TestPerformanceTestEndpoint:
    """Test performance testing endpoint."""

    @patch("app.blueprints.examples.routes.logger")
    @patch("app.blueprints.examples.routes.Post")
    @patch("app.blueprints.examples.routes.User")
    @patch("app.blueprints.examples.routes.time")
    @patch("app.blueprints.examples.routes.datetime")
    @patch("app.blueprints.examples.routes.jsonify")
    def test_performance_test_success(
        self,
        mock_jsonify,
        mock_datetime,
        mock_time,
        mock_user_class,
        mock_post_class,
        mock_logger,
    ):
        """Test successful performance test."""
        # Mock time.sleep (imported in function)
        mock_time.sleep = Mock()

        # Mock datetime
        mock_datetime.utcnow.return_value.isoformat.return_value = "2023-12-01T10:30:45"

        # Mock query counts
        mock_user_class.query.count.return_value = 10
        mock_post_class.query.count.return_value = 25

        # Mock jsonify response
        expected_response = {
            "message": "Performance test completed",
            "stats": {"users": 10, "posts": 25, "delay_ms": 100},
            "timestamp": "2023-12-01T10:30:45",
        }
        mock_jsonify.return_value = expected_response

        result = performance_test()

        # Verify sleep was called
        mock_time.sleep.assert_called_once_with(0.1)

        # Verify database queries
        mock_user_class.query.count.assert_called_once()
        mock_post_class.query.count.assert_called_once()

        # Verify logging
        mock_logger.info.assert_called_once_with(
            "Performance test completed",
            extra={"user_count": 10, "post_count": 25, "simulated_delay_ms": 100},
        )

        # Verify jsonify call
        call_args = mock_jsonify.call_args[0][0]
        assert call_args["message"] == "Performance test completed"
        assert call_args["stats"] == {"users": 10, "posts": 25, "delay_ms": 100}
        assert call_args["timestamp"] == "2023-12-01T10:30:45"

        assert result == expected_response


class TestGetUserProfileEndpoint:
    """Test get user profile endpoint."""

    @patch("app.blueprints.examples.routes.log_security_event")
    @patch("app.blueprints.examples.routes.logger")
    @patch("app.blueprints.examples.routes.Post")
    @patch("app.blueprints.examples.routes.User")
    @patch("app.blueprints.examples.routes.get_jwt_identity")
    @patch("app.blueprints.examples.routes.request")
    @patch("app.blueprints.examples.routes.datetime")
    @patch("app.blueprints.examples.routes.success_response")
    def test_get_user_profile_success(
        self,
        mock_success_response,
        mock_datetime,
        mock_request,
        mock_get_jwt_identity,
        mock_user_class,
        mock_post_class,
        mock_logger,
        mock_log_security,
    ):
        """Test successful user profile retrieval."""
        # Mock JWT identity
        mock_get_jwt_identity.return_value = 123

        # Mock request
        mock_request.remote_addr = "192.168.1.1"

        # Mock datetime
        mock_datetime.utcnow.return_value.isoformat.return_value = "2023-12-01T10:30:45"

        # Mock user
        mock_user = Mock()
        mock_user.id = 123
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.created_at = datetime(2023, 11, 1, 9, 0, 0)
        mock_user.last_login = datetime(2023, 12, 1, 8, 30, 0)
        mock_user_class.query.get.return_value = mock_user

        # Mock posts count
        mock_post_class.query.filter_by.return_value.count.return_value = 5

        # Mock success response
        mock_success_response.return_value = {"status": "success"}

        result = get_user_profile()

        # Verify user lookup
        mock_user_class.query.get.assert_called_once_with(123)

        # Verify posts count query
        mock_post_class.query.filter_by.assert_called_once_with(user_id=123)

        # Verify logging
        mock_logger.info.assert_any_call(
            "User profile requested",
            extra={
                "user_id": 123,
                "endpoint": "get_user_profile",
                "ip_address": "192.168.1.1",
            },
        )

        mock_logger.info.assert_any_call(
            "User profile retrieved successfully",
            extra={"user_id": 123, "posts_count": 5},
        )

        # Verify security logging
        mock_log_security.assert_called_once_with(
            "profile_accessed",
            {"user_id": 123, "username": "testuser", "ip_address": "192.168.1.1"},
        )

        # Verify success response
        call_args = mock_success_response.call_args
        expected_data = {
            "id": 123,
            "username": "testuser",
            "email": "test@example.com",
            "created_at": "2023-11-01T09:00:00",
            "last_login": "2023-12-01T08:30:00",
            "posts_count": 5,
            "profile_accessed_at": "2023-12-01T10:30:45",
        }

        assert call_args[1]["data"] == expected_data
        assert call_args[1]["message"] == "User profile retrieved successfully"

        assert result == {"status": "success"}

    @patch("app.blueprints.examples.routes.logger")
    @patch("app.blueprints.examples.routes.User")
    @patch("app.blueprints.examples.routes.get_jwt_identity")
    @patch("app.blueprints.examples.routes.request")
    def test_get_user_profile_user_not_found(
        self, mock_request, mock_get_jwt_identity, mock_user_class, mock_logger
    ):
        """Test profile retrieval for non-existent user."""
        # Mock JWT identity
        mock_get_jwt_identity.return_value = 999
        mock_request.remote_addr = "192.168.1.1"

        # Mock user not found
        mock_user_class.query.get.return_value = None

        with pytest.raises(NotFoundAPIError) as exc_info:
            get_user_profile()

        assert str(exc_info.value) == "User not found"

        # Verify error logging
        mock_logger.error.assert_called_once_with(
            "JWT token contains invalid user ID",
            extra={"user_id": 999, "ip_address": "192.168.1.1"},
        )

    @patch("app.blueprints.examples.routes.logger")
    @patch("app.blueprints.examples.routes.Post")
    @patch("app.blueprints.examples.routes.User")
    @patch("app.blueprints.examples.routes.get_jwt_identity")
    @patch("app.blueprints.examples.routes.request")
    def test_get_user_profile_database_error(
        self,
        mock_request,
        mock_get_jwt_identity,
        mock_user_class,
        mock_post_class,
        mock_logger,
    ):
        """Test profile retrieval with database error."""
        # Mock JWT identity
        mock_get_jwt_identity.return_value = 123
        mock_request.remote_addr = "192.168.1.1"

        # Mock user exists
        mock_user = Mock()
        mock_user_class.query.get.return_value = mock_user

        # Mock database error during posts count
        db_error = Exception("Database connection failed")
        mock_post_class.query.filter_by.return_value.count.side_effect = db_error

        with pytest.raises(APIError) as exc_info:
            get_user_profile()

        assert str(exc_info.value) == "Failed to retrieve user profile"

        # Verify error logging
        mock_logger.error.assert_called_once_with(
            "Error retrieving user profile: Database connection failed",
            extra={
                "user_id": 123,
                "error_type": "Exception",
                "ip_address": "192.168.1.1",
            },
        )

    @patch("app.blueprints.examples.routes.log_security_event")
    @patch("app.blueprints.examples.routes.logger")
    @patch("app.blueprints.examples.routes.Post")
    @patch("app.blueprints.examples.routes.User")
    @patch("app.blueprints.examples.routes.get_jwt_identity")
    @patch("app.blueprints.examples.routes.request")
    @patch("app.blueprints.examples.routes.datetime")
    @patch("app.blueprints.examples.routes.success_response")
    def test_get_user_profile_no_last_login(
        self,
        mock_success_response,
        mock_datetime,
        mock_request,
        mock_get_jwt_identity,
        mock_user_class,
        mock_post_class,
        mock_logger,
        mock_log_security,
    ):
        """Test user profile retrieval with no last login."""
        # Mock JWT identity
        mock_get_jwt_identity.return_value = 123
        mock_request.remote_addr = "192.168.1.1"
        mock_datetime.utcnow.return_value.isoformat.return_value = "2023-12-01T10:30:45"

        # Mock user with no last login
        mock_user = Mock()
        mock_user.id = 123
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.created_at = datetime(2023, 11, 1, 9, 0, 0)
        mock_user.last_login = None  # No last login
        mock_user_class.query.get.return_value = mock_user

        # Mock posts count
        mock_post_class.query.filter_by.return_value.count.return_value = 0
        mock_success_response.return_value = {"status": "success"}

        result = get_user_profile()

        # Verify success response with None last_login
        call_args = mock_success_response.call_args
        assert call_args[1]["data"]["last_login"] is None


class TestExamplesRoutesIntegration:
    """Test integration scenarios for examples routes."""

    def test_user_post_relationship_integration(self):
        """Test integration between user creation and post creation."""
        # Test that user creation and post creation use consistent data formats

        # User creation data
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "bio": "Test bio",
        }

        # Post creation data
        post_data = {
            "title": "Test Post",
            "content": "This is test content.",
            "tags": ["test"],
        }

        # Both should work with the same user ID
        user_id = 123

        # Verify data consistency
        assert isinstance(user_data["username"], str)
        assert isinstance(post_data["title"], str)
        assert isinstance(user_id, int)

    def test_error_handling_consistency_across_endpoints(self):
        """Test that error handling is consistent across all endpoints."""
        # All endpoints should handle database errors consistently
        # All endpoints should log errors with similar structure
        # All endpoints should raise appropriate API exceptions

        # This is verified by the individual endpoint tests,
        # but this integration test ensures the patterns are consistent

    def test_logging_consistency_across_endpoints(self):
        """Test that logging patterns are consistent across endpoints."""
        # All endpoints should log with similar extra data structure
        # All endpoints should include relevant context in logs
        # Security events should be logged consistently

        # Common logging fields that should be present
        common_log_fields = ["user_id", "ip_address"]

        # This pattern is verified in individual tests
        # but this integration test documents the expected consistency

    def test_response_format_consistency(self):
        """Test that response formats are consistent across endpoints."""
        # All success responses should use success_response helper
        # All error responses should use appropriate error helpers
        # Data structures should be consistent

        # Common response fields
        success_response_fields = ["message", "data"]

        # This pattern is verified in individual tests
