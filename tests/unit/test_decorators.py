"""Tests for decorator utilities."""

import json
from unittest.mock import MagicMock, call, patch

import pytest
from flask import Flask, request
from marshmallow import Schema
from marshmallow import ValidationError as MarshmallowValidationError
from marshmallow import fields

from app.utils.decorators import (
    handle_api_errors,
    log_endpoint_access,
    validate_json_input,
)
from app.utils.error_handlers import (
    APIError,
    NotFoundAPIError,
    RateLimitAPIError,
    UnauthorizedAPIError,
    ValidationAPIError,
)


class ValidationTestSchema(Schema):
    """Test schema for validation tests."""

    name = fields.Str(required=True)
    age = fields.Int(required=True, validate=lambda x: x > 0)
    email = fields.Email(required=False)


@pytest.fixture
def app():
    """Create Flask app for testing."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def app_context(app):
    """Create app context for testing."""
    with app.app_context():
        yield app


class TestHandleApiErrors:
    """Test handle_api_errors decorator."""

    def test_successful_execution(self):
        """Test decorator with successful function execution."""

        @handle_api_errors
        def test_function():
            return "success"

        result = test_function()
        assert result == "success"

    @patch("app.utils.decorators.logger")
    @patch("app.utils.decorators.log_security_event")
    @patch("app.utils.decorators.request")
    def test_marshmallow_validation_error(
        self, mock_request, mock_log_security, mock_logger, app_context
    ):
        """Test handling of MarshmallowValidationError."""
        with app_context.test_request_context("/", method="POST"):
            mock_request.endpoint = "test_endpoint"

            @handle_api_errors
            def test_function():
                raise MarshmallowValidationError({"field": ["error message"]})

            with pytest.raises(ValidationAPIError) as exc_info:
                test_function()

            assert "Invalid input data" in str(exc_info.value)
            assert exc_info.value.details == {"field": ["error message"]}
            mock_logger.warning.assert_called_once()
            mock_log_security.assert_called_once_with(
                event_type="validation_error",
                details={
                    "endpoint": "test_endpoint",
                    "errors": {"field": ["error message"]},
                },
            )

    @patch("app.utils.decorators.logger")
    def test_validation_api_error_passthrough(self, mock_logger):
        """Test that ValidationAPIError is passed through unchanged."""
        original_error = ValidationAPIError("Original error")

        @handle_api_errors
        def test_function():
            raise original_error

        with pytest.raises(ValidationAPIError) as exc_info:
            test_function()

        assert exc_info.value is original_error
        mock_logger.warning.assert_called_once()

    @patch("app.utils.decorators.logger")
    def test_rate_limit_api_error_passthrough(self, mock_logger):
        """Test that RateLimitAPIError is passed through unchanged."""
        original_error = RateLimitAPIError("Rate limit exceeded")

        @handle_api_errors
        def test_function():
            raise original_error

        with pytest.raises(RateLimitAPIError) as exc_info:
            test_function()

        assert exc_info.value is original_error
        mock_logger.warning.assert_called_once()

    @patch("app.utils.decorators.logger")
    def test_not_found_api_error_passthrough(self, mock_logger):
        """Test that NotFoundAPIError is passed through unchanged."""
        original_error = NotFoundAPIError("Resource not found")

        @handle_api_errors
        def test_function():
            raise original_error

        with pytest.raises(NotFoundAPIError) as exc_info:
            test_function()

        assert exc_info.value is original_error
        mock_logger.warning.assert_called_once()

    @patch("app.utils.decorators.logger")
    def test_unauthorized_api_error_passthrough(self, mock_logger):
        """Test that UnauthorizedAPIError is passed through unchanged."""
        original_error = UnauthorizedAPIError("Unauthorized")

        @handle_api_errors
        def test_function():
            raise original_error

        with pytest.raises(UnauthorizedAPIError) as exc_info:
            test_function()

        assert exc_info.value is original_error
        mock_logger.warning.assert_called_once()

    @patch("app.utils.decorators.logger")
    def test_api_error_passthrough(self, mock_logger):
        """Test that APIError is passed through unchanged."""
        original_error = APIError("API error")

        @handle_api_errors
        def test_function():
            raise original_error

        with pytest.raises(APIError) as exc_info:
            test_function()

        assert exc_info.value is original_error
        mock_logger.error.assert_called_once()

    @patch("app.utils.decorators.logger")
    @patch("app.utils.decorators.log_security_event")
    @patch("app.utils.decorators.request")
    def test_unexpected_exception(
        self, mock_request, mock_log_security, mock_logger, app_context
    ):
        """Test handling of unexpected exceptions."""
        with app_context.test_request_context("/", method="POST"):
            mock_request.endpoint = "test_endpoint"

            @handle_api_errors
            def test_function():
                raise ValueError("Unexpected error")

            with pytest.raises(APIError) as exc_info:
                test_function()

            assert "An unexpected error occurred" in str(exc_info.value)
            mock_logger.error.assert_called_once()
            mock_log_security.assert_called_once_with(
                event_type="unexpected_error",
                details={"endpoint": "test_endpoint", "error": "Unexpected error"},
            )

    def test_preserves_function_metadata(self):
        """Test that decorator preserves function metadata."""

        @handle_api_errors
        def test_function():
            """Test function docstring."""
            return "test"

        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ == "Test function docstring."


class TestValidateJsonInput:
    """Test validate_json_input decorator."""

    def test_successful_json_validation(self, app_context):
        """Test successful JSON validation."""
        with app_context.test_request_context(
            "/", method="POST", json={"name": "John", "age": 30}
        ):

            @validate_json_input(ValidationTestSchema)
            def test_function(validated_data):
                return validated_data

            result = test_function()
            assert result["name"] == "John"
            assert result["age"] == 30

    @patch("app.utils.decorators.request")
    def test_no_json_data_provided(self, mock_request, app_context):
        """Test error when no JSON data is provided."""
        with app_context.test_request_context("/", method="POST"):
            mock_request.get_json.return_value = None

            @validate_json_input(ValidationTestSchema)
            def test_function(validated_data):
                return validated_data

            with pytest.raises(ValidationAPIError) as exc_info:
                test_function()

            assert "No JSON data provided" in str(exc_info.value)

    @patch("app.utils.decorators.logger")
    def test_schema_validation_failure(self, mock_logger, app_context):
        """Test schema validation failure."""
        with app_context.test_request_context(
            "/", method="POST", json={"name": "John"}
        ):

            @validate_json_input(ValidationTestSchema)
            def test_function(validated_data):
                return validated_data

            with pytest.raises(ValidationAPIError) as exc_info:
                test_function()

            assert "Invalid input data" in str(exc_info.value)
            assert "age" in str(exc_info.value.details)
            mock_logger.warning.assert_called_once()

    def test_form_data_validation(self, app_context):
        """Test validation with form data."""
        with app_context.test_request_context(
            "/", method="POST", data={"name": "John", "age": "30"}
        ):

            @validate_json_input(ValidationTestSchema, location="form")
            def test_function(validated_data):
                return validated_data

            result = test_function()
            assert result["name"] == "John"
            assert result["age"] == 30

    def test_args_data_validation(self, app_context):
        """Test validation with query args."""
        with app_context.test_request_context("/?name=John&age=30", method="GET"):

            @validate_json_input(ValidationTestSchema, location="args")
            def test_function(validated_data):
                return validated_data

            result = test_function()
            assert result["name"] == "John"
            assert result["age"] == 30

    def test_invalid_location(self, app_context):
        """Test error with invalid location parameter."""
        with app_context.test_request_context("/", method="POST"):

            @validate_json_input(ValidationTestSchema, location="invalid")
            def test_function(validated_data):
                return validated_data

            with pytest.raises(ValueError) as exc_info:
                test_function()

            assert "Invalid location: invalid" in str(exc_info.value)

    def test_passes_additional_args_kwargs(self, app_context):
        """Test that decorator passes additional args and kwargs."""
        with app_context.test_request_context(
            "/", method="POST", json={"name": "John", "age": 30}
        ):

            @validate_json_input(ValidationTestSchema)
            def test_function(validated_data, extra_arg, extra_kwarg=None):
                return {
                    "validated": validated_data,
                    "extra_arg": extra_arg,
                    "extra_kwarg": extra_kwarg,
                }

            result = test_function("test_arg", extra_kwarg="test_kwarg")
            assert result["validated"]["name"] == "John"
            assert result["extra_arg"] == "test_arg"
            assert result["extra_kwarg"] == "test_kwarg"

    def test_preserves_function_metadata(self):
        """Test that decorator preserves function metadata."""

        @validate_json_input(ValidationTestSchema)
        def test_function(validated_data):
            """Test function docstring."""
            return validated_data

        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ == "Test function docstring."


class TestLogEndpointAccess:
    """Test log_endpoint_access decorator."""

    @patch("app.utils.decorators.logger")
    @patch("app.utils.decorators.request")
    def test_logs_endpoint_access(self, mock_request, mock_logger, app_context):
        """Test that endpoint access is logged."""
        with app_context.test_request_context("/", method="GET"):
            mock_request.endpoint = "test_endpoint"
            mock_request.method = "GET"

            @log_endpoint_access
            def test_function():
                return "success"

            result = test_function()

            assert result == "success"
            mock_logger.info.assert_called_once_with(
                "Accessing endpoint: test_endpoint - Method: GET"
            )

    @patch("app.utils.decorators.logger")
    @patch("app.utils.decorators.request")
    def test_logs_different_methods(self, mock_request, mock_logger, app_context):
        """Test logging with different HTTP methods."""
        with app_context.test_request_context("/", method="POST"):
            mock_request.endpoint = "api_endpoint"
            mock_request.method = "POST"

            @log_endpoint_access
            def test_function():
                return "posted"

            result = test_function()

            assert result == "posted"
            mock_logger.info.assert_called_once_with(
                "Accessing endpoint: api_endpoint - Method: POST"
            )

    @patch("app.utils.decorators.request")
    def test_passes_args_kwargs(self, mock_request, app_context):
        """Test that decorator passes args and kwargs correctly."""
        with app_context.test_request_context("/", method="GET"):
            mock_request.endpoint = "test_endpoint"
            mock_request.method = "GET"

            @log_endpoint_access
            def test_function(arg1, arg2, kwarg1=None):
                return {"arg1": arg1, "arg2": arg2, "kwarg1": kwarg1}

            result = test_function("test1", "test2", kwarg1="test3")

            assert result["arg1"] == "test1"
            assert result["arg2"] == "test2"
            assert result["kwarg1"] == "test3"

    def test_preserves_function_metadata(self):
        """Test that decorator preserves function metadata."""

        @log_endpoint_access
        def test_function():
            """Test function docstring."""
            return "test"

        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ == "Test function docstring."

    @patch("app.utils.decorators.logger")
    @patch("app.utils.decorators.request")
    def test_logs_with_exception(self, mock_request, mock_logger, app_context):
        """Test that logging occurs even when function raises exception."""
        with app_context.test_request_context("/", method="DELETE"):
            mock_request.endpoint = "error_endpoint"
            mock_request.method = "DELETE"

            @log_endpoint_access
            def test_function():
                raise ValueError("Test error")

            with pytest.raises(ValueError):
                test_function()

            mock_logger.info.assert_called_once_with(
                "Accessing endpoint: error_endpoint - Method: DELETE"
            )


class TestDecoratorIntegration:
    """Test decorator combinations and integration scenarios."""

    @patch("app.utils.decorators.logger")
    @patch("app.utils.decorators.request")
    def test_combined_decorators(self, mock_request, mock_logger, app_context):
        """Test combining multiple decorators."""
        with app_context.test_request_context(
            "/", method="POST", json={"name": "John", "age": 30}
        ):
            mock_request.endpoint = "combined_endpoint"
            mock_request.method = "POST"
            mock_request.get_json.return_value = {"name": "John", "age": 30}

            @handle_api_errors
            @log_endpoint_access
            @validate_json_input(ValidationTestSchema)
            def test_function(validated_data):
                return {"processed": validated_data}

            result = test_function()

            assert result["processed"]["name"] == "John"
            assert result["processed"]["age"] == 30

            # Check that logging occurred
            mock_logger.info.assert_called_once_with(
                "Accessing endpoint: combined_endpoint - Method: POST"
            )

    @patch("app.utils.decorators.logger")
    @patch("app.utils.decorators.log_security_event")
    @patch("app.utils.decorators.request")
    def test_combined_decorators_with_error(
        self, mock_request, mock_log_security, mock_logger, app_context
    ):
        """Test combined decorators when validation fails."""
        with app_context.test_request_context(
            "/", method="POST", json={"name": "John"}
        ):
            mock_request.endpoint = "error_endpoint"
            mock_request.method = "POST"
            mock_request.get_json.return_value = {"name": "John"}

            @handle_api_errors
            @log_endpoint_access
            @validate_json_input(ValidationTestSchema)
            def test_function(validated_data):
                return validated_data

            with pytest.raises(ValidationAPIError):
                test_function()

            # Check that logging occurred before error
            mock_logger.info.assert_called_with(
                "Accessing endpoint: error_endpoint - Method: POST"
            )

            # Check that validation error was logged
            assert mock_logger.warning.called
