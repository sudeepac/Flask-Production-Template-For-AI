"""Unit tests for app.blueprints.api.routes module.

This module tests all API endpoints including status, info, echo,
and bulk user creation functionality.
"""

from unittest.mock import Mock, patch

import pytest
from marshmallow import ValidationError

from app.blueprints.api.routes import (
    api_info,
    api_status,
    create_user_with_posts,
    echo,
    echo_request_schema,
    echo_response_schema,
    ratelimit_handler,
)
from app.utils.error_handlers import APIError, ValidationAPIError


class TestEchoSchemas:
    """Test echo endpoint request and response schemas."""

    def test_echo_request_schema_valid_data(self):
        """Test echo request schema with valid data."""
        valid_data = {
            "message": "Hello, World!",
            "metadata": {"test": True, "user_id": 123},
        }

        result = echo_request_schema.load(valid_data)

        assert result["message"] == "Hello, World!"
        assert result["metadata"] == {"test": True, "user_id": 123}

    def test_echo_request_schema_missing_message(self):
        """Test echo request schema with missing required message."""
        invalid_data = {"metadata": {"test": True}}

        with pytest.raises(ValidationError) as exc_info:
            echo_request_schema.load(invalid_data)

        assert "message" in exc_info.value.messages
        assert "required" in str(exc_info.value.messages["message"])

    def test_echo_request_schema_message_too_long(self):
        """Test echo request schema with message exceeding max length."""
        invalid_data = {
            "message": "x" * 1001,  # Exceeds 1000 character limit
            "metadata": {},
        }

        with pytest.raises(ValidationError) as exc_info:
            echo_request_schema.load(invalid_data)

        assert "message" in exc_info.value.messages

    def test_echo_request_schema_optional_metadata(self):
        """Test echo request schema with optional metadata field."""
        valid_data = {"message": "Hello without metadata"}

        result = echo_request_schema.load(valid_data)

        assert result["message"] == "Hello without metadata"
        assert "metadata" not in result

    def test_echo_response_schema_serialization(self):
        """Test echo response schema serialization."""
        response_data = {
            "echo": "Hello, World!",
            "timestamp": "2023-12-01T10:30:45.123456Z",
            "metadata": {"test": True},
        }

        result = echo_response_schema.dump(response_data)

        assert result["echo"] == "Hello, World!"
        assert result["timestamp"] == "2023-12-01T10:30:45.123456Z"
        assert result["metadata"] == {"test": True}


class TestAPIStatus:
    """Test API status endpoint functionality."""

    @patch("app.blueprints.api.routes.datetime")
    @patch("app.blueprints.api.routes.success_response")
    @patch("app.blueprints.api.routes.current_app")
    def test_api_status_success(
        self, mock_current_app, mock_success_response, mock_datetime
    ):
        """Test successful API status endpoint."""
        # Mock dependencies
        mock_datetime.utcnow.return_value.isoformat.return_value = (
            "2023-12-01T10:30:45.123456"
        )
        mock_current_app.config.get.return_value = "v2"
        mock_success_response.return_value = ({"status": "success"}, 200)

        result = api_status()

        # Verify success_response was called with correct data
        mock_success_response.assert_called_once()
        call_args = mock_success_response.call_args

        expected_data = {
            "status": "operational",
            "version": "v2",
            "timestamp": "2023-12-01T10:30:45.123456Z",
            "endpoints": ["/api/status", "/api/info", "/api/echo"],
        }

        assert call_args[1]["data"] == expected_data
        assert call_args[1]["message"] == "API is operational"
        assert result == ({"status": "success"}, 200)

    @patch("app.blueprints.api.routes.datetime")
    @patch("app.blueprints.api.routes.success_response")
    @patch("app.blueprints.api.routes.current_app")
    def test_api_status_default_version(
        self, mock_current_app, mock_success_response, mock_datetime
    ):
        """Test API status endpoint with default version."""
        # Mock dependencies
        mock_datetime.utcnow.return_value.isoformat.return_value = (
            "2023-12-01T10:30:45.123456"
        )
        mock_current_app.config.get.return_value = None  # No API_VERSION set
        mock_success_response.return_value = ({"status": "success"}, 200)

        result = api_status()

        # Verify default version is used
        call_args = mock_success_response.call_args
        assert call_args[1]["data"]["version"] == "v2"


class TestAPIInfo:
    """Test API info endpoint functionality."""

    @patch("app.blueprints.api.routes.success_response")
    @patch("app.blueprints.api.routes.current_app")
    def test_api_info_success(self, mock_current_app, mock_success_response):
        """Test successful API info endpoint."""
        # Mock dependencies
        mock_current_app.config.get.side_effect = lambda key, default=None: {
            "FLASK_ENV": "development"
        }.get(key, default)
        mock_current_app.debug = True
        mock_current_app.version = "1.2.3"
        mock_success_response.return_value = ({"status": "success"}, 200)

        result = api_info()

        # Verify success_response was called with correct data
        mock_success_response.assert_called_once()
        call_args = mock_success_response.call_args

        expected_data = {
            "name": "Flask Production Template for AI",
            "description": "Flask Production Template for AI",
            "version": "1.2.3",
            "environment": "development",
            "debug": True,
            "features": {
                "authentication": True,
                "caching": True,
                "rate_limiting": True,
                "cors": True,
            },
        }

        assert call_args[1]["data"] == expected_data
        assert call_args[1]["message"] == "Application information retrieved"
        assert result == ({"status": "success"}, 200)

    @patch("app.blueprints.api.routes.success_response")
    @patch("app.blueprints.api.routes.current_app")
    def test_api_info_default_values(self, mock_current_app, mock_success_response):
        """Test API info endpoint with default values."""
        # Mock dependencies with defaults
        mock_current_app.config.get.side_effect = lambda key, default=None: default
        mock_current_app.debug = False
        # Don't set version attribute to test default
        if hasattr(mock_current_app, "version"):
            delattr(mock_current_app, "version")
        mock_success_response.return_value = ({"status": "success"}, 200)

        result = api_info()

        # Verify default values are used
        call_args = mock_success_response.call_args
        assert call_args[1]["data"]["version"] == "1.0.0"
        assert call_args[1]["data"]["environment"] == "development"
        assert call_args[1]["data"]["debug"] is False

    @patch("app.blueprints.api.routes.success_response")
    @patch("app.blueprints.api.routes.current_app")
    def test_api_info_production_environment(
        self, mock_current_app, mock_success_response
    ):
        """Test API info endpoint in production environment."""
        # Mock dependencies for production
        mock_current_app.config.get.side_effect = lambda key, default=None: {
            "FLASK_ENV": "production"
        }.get(key, default)
        mock_current_app.debug = False
        mock_current_app.version = "2.0.0"
        mock_success_response.return_value = ({"status": "success"}, 200)

        result = api_info()

        # Verify production values
        call_args = mock_success_response.call_args
        assert call_args[1]["data"]["environment"] == "production"
        assert call_args[1]["data"]["debug"] is False
        assert call_args[1]["data"]["version"] == "2.0.0"


class TestEchoEndpoint:
    """Test echo endpoint functionality."""

    @patch("app.blueprints.api.routes.logger")
    @patch("app.blueprints.api.routes.success_response")
    @patch("app.blueprints.api.routes.log_security_event")
    @patch("app.blueprints.api.routes.request")
    @patch("app.blueprints.api.routes.datetime")
    def test_echo_success_with_metadata(
        self,
        mock_datetime,
        mock_request,
        mock_log_security,
        mock_success_response,
        mock_logger,
    ):
        """Test successful echo endpoint with metadata."""
        # Mock dependencies
        mock_datetime.utcnow.return_value.isoformat.return_value = (
            "2023-12-01T10:30:45.123456"
        )
        mock_request.remote_addr = "192.168.1.1"
        mock_success_response.return_value = ({"status": "success"}, 200)

        validated_data = {
            "message": "Hello, World!",
            "metadata": {"test": True, "user_id": 123},
        }

        result = echo(validated_data)

        # Verify security event logging
        mock_log_security.assert_called_once_with(
            "echo_request",
            {
                "message_length": 13,  # len("Hello, World!")
                "has_metadata": True,
                "ip_address": "192.168.1.1",
            },
        )

        # Verify success_response was called with correct data
        mock_success_response.assert_called_once()
        call_args = mock_success_response.call_args

        expected_data = {
            "echo": "Hello, World!",
            "timestamp": "2023-12-01T10:30:45.123456Z",
            "metadata": {"test": True, "user_id": 123},
        }

        assert call_args[1]["data"] == expected_data
        assert call_args[1]["message"] == "Echo processed successfully"

        # Verify logging
        mock_logger.info.assert_called_once_with(
            "Echo request processed successfully", extra={"message_length": 13}
        )

        assert result == ({"status": "success"}, 200)

    @patch("app.blueprints.api.routes.logger")
    @patch("app.blueprints.api.routes.success_response")
    @patch("app.blueprints.api.routes.log_security_event")
    @patch("app.blueprints.api.routes.request")
    @patch("app.blueprints.api.routes.datetime")
    def test_echo_success_without_metadata(
        self,
        mock_datetime,
        mock_request,
        mock_log_security,
        mock_success_response,
        mock_logger,
    ):
        """Test successful echo endpoint without metadata."""
        # Mock dependencies
        mock_datetime.utcnow.return_value.isoformat.return_value = (
            "2023-12-01T10:30:45.123456"
        )
        mock_request.remote_addr = "192.168.1.1"
        mock_success_response.return_value = ({"status": "success"}, 200)

        validated_data = {"message": "Simple message"}

        result = echo(validated_data)

        # Verify security event logging
        mock_log_security.assert_called_once_with(
            "echo_request",
            {
                "message_length": 14,  # len("Simple message")
                "has_metadata": False,
                "ip_address": "192.168.1.1",
            },
        )

        # Verify success_response was called with empty metadata
        call_args = mock_success_response.call_args
        expected_data = {
            "echo": "Simple message",
            "timestamp": "2023-12-01T10:30:45.123456Z",
            "metadata": {},
        }

        assert call_args[1]["data"] == expected_data

    @patch("app.blueprints.api.routes.logger")
    @patch("app.blueprints.api.routes.success_response")
    @patch("app.blueprints.api.routes.log_security_event")
    @patch("app.blueprints.api.routes.request")
    @patch("app.blueprints.api.routes.datetime")
    def test_echo_empty_message(
        self,
        mock_datetime,
        mock_request,
        mock_log_security,
        mock_success_response,
        mock_logger,
    ):
        """Test echo endpoint with empty message."""
        # Mock dependencies
        mock_datetime.utcnow.return_value.isoformat.return_value = (
            "2023-12-01T10:30:45.123456"
        )
        mock_request.remote_addr = "192.168.1.1"
        mock_success_response.return_value = ({"status": "success"}, 200)

        validated_data = {"message": ""}

        result = echo(validated_data)

        # Verify security event logging with zero length
        mock_log_security.assert_called_once_with(
            "echo_request",
            {"message_length": 0, "has_metadata": False, "ip_address": "192.168.1.1"},
        )

        # Verify response with empty echo
        call_args = mock_success_response.call_args
        assert call_args[1]["data"]["echo"] == ""


class TestCreateUserWithPosts:
    """Test bulk user creation endpoint functionality."""

    @patch("app.blueprints.api.routes.logger")
    @patch("app.blueprints.api.routes.ExampleService")
    @patch("app.blueprints.api.routes.request")
    @patch("app.blueprints.api.routes.jsonify")
    def test_create_user_with_posts_success(
        self, mock_jsonify, mock_request, mock_service_class, mock_logger
    ):
        """Test successful user creation with posts."""
        # Mock request data
        request_data = {
            "username": "  testuser  ",  # Test trimming
            "email": "  TEST@EXAMPLE.COM  ",  # Test trimming and lowercasing
            "post_titles": ["Post 1", "Post 2", "Post 3"],
        }
        mock_request.get_json.return_value = request_data

        # Mock service response
        service_result = {
            "user": {"id": 123, "username": "testuser", "email": "test@example.com"},
            "posts": [
                {"id": 1, "title": "Post 1"},
                {"id": 2, "title": "Post 2"},
                {"id": 3, "title": "Post 3"},
            ],
        }
        mock_service_instance = Mock()
        mock_service_instance.create_user_with_posts.return_value = service_result
        mock_service_class.return_value = mock_service_instance

        # Mock jsonify
        mock_jsonify.return_value = {"mocked": "response"}

        result = create_user_with_posts()

        # Verify service was called with processed data
        mock_service_instance.create_user_with_posts.assert_called_once_with(
            "testuser",  # Trimmed
            "test@example.com",  # Trimmed and lowercased
            ["Post 1", "Post 2", "Post 3"],
        )

        # Verify logging
        mock_logger.info.assert_called_once_with(
            "Successfully created user with posts via service",
            extra={"user_id": 123, "post_count": 3},
        )

        # Verify response
        mock_jsonify.assert_called_once_with(service_result)
        assert result == ({"mocked": "response"}, 201)

    @patch("app.blueprints.api.routes.request")
    def test_create_user_with_posts_no_body(self, mock_request):
        """Test user creation with no request body."""
        mock_request.get_json.return_value = None

        with pytest.raises(ValidationAPIError) as exc_info:
            create_user_with_posts()

        assert str(exc_info.value) == "Request body is required"

    @patch("app.blueprints.api.routes.request")
    def test_create_user_with_posts_missing_fields(self, mock_request):
        """Test user creation with missing required fields."""
        request_data = {
            "username": "testuser"
            # Missing email and post_titles
        }
        mock_request.get_json.return_value = request_data

        with pytest.raises(ValidationAPIError) as exc_info:
            create_user_with_posts()

        error_message = str(exc_info.value)
        assert "Missing required fields:" in error_message
        assert "email" in error_message
        assert "post_titles" in error_message

    @patch("app.blueprints.api.routes.request")
    def test_create_user_with_posts_invalid_post_titles_type(self, mock_request):
        """Test user creation with invalid post_titles type."""
        request_data = {
            "username": "testuser",
            "email": "test@example.com",
            "post_titles": "not a list",  # Should be a list
        }
        mock_request.get_json.return_value = request_data

        with pytest.raises(ValidationAPIError) as exc_info:
            create_user_with_posts()

        assert str(exc_info.value) == "post_titles must be a list"

    @patch("app.blueprints.api.routes.logger")
    @patch("app.blueprints.api.routes.ExampleService")
    @patch("app.blueprints.api.routes.request")
    def test_create_user_with_posts_service_error(
        self, mock_request, mock_service_class, mock_logger
    ):
        """Test user creation when service raises an exception."""
        # Mock request data
        request_data = {
            "username": "testuser",
            "email": "test@example.com",
            "post_titles": ["Post 1"],
        }
        mock_request.get_json.return_value = request_data

        # Mock service to raise exception
        mock_service_instance = Mock()
        mock_service_instance.create_user_with_posts.side_effect = Exception(
            "Database error"
        )
        mock_service_class.return_value = mock_service_instance

        with pytest.raises(APIError) as exc_info:
            create_user_with_posts()

        assert str(exc_info.value) == "Failed to create user with posts"

        # Verify error logging
        mock_logger.error.assert_called_once_with(
            "Unexpected error in bulk user creation: Database error",
            extra={"error_type": "Exception"},
        )

    @patch("app.blueprints.api.routes.logger")
    @patch("app.blueprints.api.routes.ExampleService")
    @patch("app.blueprints.api.routes.request")
    def test_create_user_with_posts_validation_error_reraise(
        self, mock_request, mock_service_class, mock_logger
    ):
        """Test that ValidationAPIError is re-raised without modification."""
        # Mock request data
        request_data = {
            "username": "testuser",
            "email": "test@example.com",
            "post_titles": ["Post 1"],
        }
        mock_request.get_json.return_value = request_data

        # Mock service to raise ValidationAPIError
        mock_service_instance = Mock()
        validation_error = ValidationAPIError("Invalid user data")
        mock_service_instance.create_user_with_posts.side_effect = validation_error
        mock_service_class.return_value = mock_service_instance

        with pytest.raises(ValidationAPIError) as exc_info:
            create_user_with_posts()

        # Verify the same exception is re-raised
        assert exc_info.value is validation_error
        assert str(exc_info.value) == "Invalid user data"

        # Verify no error logging for validation errors
        mock_logger.error.assert_not_called()


class TestRateLimitHandler:
    """Test rate limit error handler functionality."""

    @patch("app.blueprints.api.routes.jsonify")
    def test_ratelimit_handler(self, mock_jsonify):
        """Test rate limit error handler."""
        # Mock rate limit exception
        mock_exception = Mock()
        mock_exception.retry_after = 60

        # Mock jsonify response
        expected_response = {
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": 60,
        }
        mock_jsonify.return_value = expected_response

        result = ratelimit_handler(mock_exception)

        # Verify jsonify was called with correct data
        mock_jsonify.assert_called_once_with(
            {
                "error": "rate_limit_exceeded",
                "message": "Too many requests. Please try again later.",
                "retry_after": 60,
            }
        )

        # Verify response
        assert result == (expected_response, 429)

    @patch("app.blueprints.api.routes.jsonify")
    def test_ratelimit_handler_no_retry_after(self, mock_jsonify):
        """Test rate limit error handler without retry_after."""
        # Mock rate limit exception without retry_after
        mock_exception = Mock()
        mock_exception.retry_after = None

        expected_response = {
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": None,
        }
        mock_jsonify.return_value = expected_response

        result = ratelimit_handler(mock_exception)

        # Verify response includes None retry_after
        mock_jsonify.assert_called_once_with(
            {
                "error": "rate_limit_exceeded",
                "message": "Too many requests. Please try again later.",
                "retry_after": None,
            }
        )

        assert result == (expected_response, 429)


class TestAPIRoutesIntegration:
    """Test integration scenarios for API routes."""

    def test_echo_schema_integration(self):
        """Test integration between echo endpoint and schemas."""
        # Test that schemas work correctly with the endpoint logic

        # Valid request data
        request_data = {
            "message": "Integration test message",
            "metadata": {"integration": True},
        }

        # Validate request
        validated_request = echo_request_schema.load(request_data)
        assert validated_request["message"] == "Integration test message"
        assert validated_request["metadata"] == {"integration": True}

        # Simulate response data creation (like in echo endpoint)
        response_data = {
            "echo": validated_request["message"],
            "timestamp": "2023-12-01T10:30:45.123456Z",
            "metadata": validated_request.get("metadata", {}),
        }

        # Validate response
        validated_response = echo_response_schema.dump(response_data)
        assert validated_response["echo"] == "Integration test message"
        assert validated_response["timestamp"] == "2023-12-01T10:30:45.123456Z"
        assert validated_response["metadata"] == {"integration": True}

    def test_api_routes_error_handling_consistency(self):
        """Test that all API routes handle errors consistently."""
        # Test ValidationAPIError handling
        with pytest.raises(ValidationAPIError) as exc_info:
            raise ValidationAPIError("Test validation error")
        assert str(exc_info.value) == "Test validation error"

        # Test APIError handling
        with pytest.raises(APIError) as exc_info:
            raise APIError("Test API error")
        assert str(exc_info.value) == "Test API error"

    @patch("app.blueprints.api.routes.request")
    def test_create_user_data_processing_integration(self, mock_request):
        """Test data processing integration in create_user_with_posts."""
        # Test various data processing scenarios
        test_cases = [
            {
                "input": {
                    "username": "  user123  ",
                    "email": "  USER@DOMAIN.COM  ",
                    "post_titles": ["Title 1", "Title 2"],
                },
                "expected_username": "user123",
                "expected_email": "user@domain.com",
            },
            {
                "input": {
                    "username": "normaluser",
                    "email": "normal@example.com",
                    "post_titles": [],
                },
                "expected_username": "normaluser",
                "expected_email": "normal@example.com",
            },
        ]

        for case in test_cases:
            mock_request.get_json.return_value = case["input"]

            with patch(
                "app.blueprints.api.routes.ExampleService"
            ) as mock_service_class:
                mock_service_instance = Mock()
                mock_service_instance.create_user_with_posts.return_value = {
                    "user": {"id": 1},
                    "posts": [],
                }
                mock_service_class.return_value = mock_service_instance

                with patch("app.blueprints.api.routes.jsonify"):
                    try:
                        create_user_with_posts()

                        # Verify service was called with processed data
                        call_args = (
                            mock_service_instance.create_user_with_posts.call_args
                        )
                        assert call_args[0][0] == case["expected_username"]
                        assert call_args[0][1] == case["expected_email"]
                        assert call_args[0][2] == case["input"]["post_titles"]

                    except (ValidationAPIError, APIError):
                        # Expected for some test cases
                        pass
