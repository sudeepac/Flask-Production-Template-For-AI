"""Tests for response helper utilities."""

from unittest.mock import patch

from flask import Flask
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.utils.response_helpers import (
    already_exists_error,
    error_response,
    handle_common_exceptions,
    invalid_credentials_error,
    missing_fields_error,
    no_data_provided_error,
    success_response,
    token_revoked_error,
    user_not_found_error,
    validation_error_response,
)


class TestErrorResponse:
    """Test error_response function."""

    @patch("app.utils.response_helpers.get_request_id")
    @patch("app.utils.response_helpers.format_error_response")
    def test_error_response_basic(self, mock_format_error, mock_get_request_id):
        """Test basic error response creation."""
        mock_get_request_id.return_value = "test-request-id"
        mock_format_error.return_value = (
            {"error": "test error", "request_id": "test-request-id"},
            400,
        )

        with Flask(__name__).app_context():
            response, status_code = error_response("Test error message")

        assert status_code == 400
        mock_format_error.assert_called_once_with(
            error_code="error_400",
            message="Test error message",
            status_code=400,
            details=None,
        )

    @patch("app.utils.response_helpers.get_request_id")
    @patch("app.utils.response_helpers.format_error_response")
    def test_error_response_with_custom_params(
        self, mock_format_error, mock_get_request_id
    ):
        """Test error response with custom parameters."""
        mock_get_request_id.return_value = "test-request-id"
        mock_format_error.return_value = (
            {"error": "custom error", "request_id": "test-request-id"},
            500,
        )

        details = {"field": "value"}

        with Flask(__name__).app_context():
            response, status_code = error_response(
                "Custom error",
                status_code=500,
                error_code="custom_error",
                details=details,
            )

        assert status_code == 500
        mock_format_error.assert_called_once_with(
            error_code="custom_error",
            message="Custom error",
            status_code=500,
            details=details,
        )


class TestSuccessResponse:
    """Test success_response function."""

    @patch("app.utils.response_helpers.get_request_id")
    def test_success_response_basic(self, mock_get_request_id):
        """Test basic success response creation."""
        mock_get_request_id.return_value = "test-request-id"

        with Flask(__name__).app_context():
            response, status_code = success_response()

        assert status_code == 200
        response_data = response.get_json()
        assert response_data["message"] == "Success"
        assert response_data["request_id"] == "test-request-id"
        assert "data" not in response_data

    @patch("app.utils.response_helpers.get_request_id")
    def test_success_response_with_data(self, mock_get_request_id):
        """Test success response with data."""
        mock_get_request_id.return_value = "test-request-id"
        test_data = {"user_id": 123, "name": "Test User"}

        with Flask(__name__).app_context():
            response, status_code = success_response(
                message="User created", data=test_data, status_code=201
            )

        assert status_code == 201
        response_data = response.get_json()
        assert response_data["message"] == "User created"
        assert response_data["data"] == test_data
        assert response_data["request_id"] == "test-request-id"

    @patch("app.utils.response_helpers.get_request_id")
    def test_success_response_flatten_data(self, mock_get_request_id):
        """Test success response with flattened data."""
        mock_get_request_id.return_value = "test-request-id"
        test_data = {"user_id": 123, "name": "Test User"}

        with Flask(__name__).app_context():
            response, status_code = success_response(
                message="User retrieved", data=test_data, flatten_data=True
            )

        assert status_code == 200
        response_data = response.get_json()
        assert response_data["message"] == "User retrieved"
        assert response_data["user_id"] == 123
        assert response_data["name"] == "Test User"
        assert response_data["request_id"] == "test-request-id"
        assert "data" not in response_data


class TestValidationErrorResponse:
    """Test validation_error_response function."""

    @patch("app.utils.response_helpers.error_response")
    def test_validation_error_response_simple(self, mock_error_response):
        """Test validation error response with simple messages."""
        mock_error_response.return_value = ("mocked_response", 400)

        error = ValidationError({"email": "Invalid email format"})

        result = validation_error_response(error)

        mock_error_response.assert_called_once_with(
            message="Validation failed",
            status_code=400,
            error_code="validation_error",
            details={"email": ["Invalid email format"]},
        )
        assert result == ("mocked_response", 400)

    @patch("app.utils.response_helpers.error_response")
    def test_validation_error_response_multiple_fields(self, mock_error_response):
        """Test validation error response with multiple fields."""
        mock_error_response.return_value = ("mocked_response", 400)

        error = ValidationError(
            {
                "email": ["Invalid email format", "Email is required"],
                "password": "Password too short",
            }
        )

        result = validation_error_response(error)

        expected_details = {
            "email": ["Invalid email format", "Email is required"],
            "password": ["Password too short"],
        }

        mock_error_response.assert_called_once_with(
            message="Validation failed",
            status_code=400,
            error_code="validation_error",
            details=expected_details,
        )


class TestHandleCommonExceptions:
    """Test handle_common_exceptions decorator."""

    @patch("app.utils.response_helpers.log_error")
    @patch("app.utils.response_helpers.validation_error_response")
    def test_handle_validation_error(self, mock_validation_response, mock_log_error):
        """Test handling ValidationError."""
        mock_validation_response.return_value = ("validation_error_response", 400)

        @handle_common_exceptions
        def test_func():
            raise ValidationError({"field": "error"})

        result = test_func()

        assert result == ("validation_error_response", 400)
        mock_log_error.assert_called_once()
        mock_validation_response.assert_called_once()

    @patch("app.utils.response_helpers.log_error")
    @patch("app.utils.response_helpers.error_response")
    def test_handle_integrity_error(self, mock_error_response, mock_log_error):
        """Test handling IntegrityError."""
        mock_error_response.return_value = ("integrity_error_response", 409)

        @handle_common_exceptions
        def test_func():
            raise IntegrityError("statement", "params", "orig")

        result = test_func()

        assert result == ("integrity_error_response", 409)
        mock_log_error.assert_called_once()
        mock_error_response.assert_called_once_with(
            message="Data integrity constraint violated",
            status_code=409,
            error_code="integrity_error",
        )

    @patch("app.utils.response_helpers.log_error")
    @patch("app.utils.response_helpers.error_response")
    def test_handle_sqlalchemy_error(self, mock_error_response, mock_log_error):
        """Test handling SQLAlchemyError."""
        mock_error_response.return_value = ("database_error_response", 500)

        @handle_common_exceptions
        def test_func():
            raise SQLAlchemyError("Database error")

        result = test_func()

        assert result == ("database_error_response", 500)
        mock_log_error.assert_called_once()
        mock_error_response.assert_called_once_with(
            message="Database operation failed",
            status_code=500,
            error_code="database_error",
        )

    @patch("app.utils.response_helpers.log_error")
    @patch("app.utils.response_helpers.error_response")
    def test_handle_generic_exception(self, mock_error_response, mock_log_error):
        """Test handling generic Exception."""
        mock_error_response.return_value = ("generic_error_response", 500)

        @handle_common_exceptions
        def test_func():
            raise Exception("Unexpected error")

        result = test_func()

        assert result == ("generic_error_response", 500)
        mock_log_error.assert_called_once()
        mock_error_response.assert_called_once_with(
            message="An unexpected error occurred",
            status_code=500,
            error_code="internal_server_error",
        )

    def test_handle_no_exception(self):
        """Test decorator when no exception is raised."""

        @handle_common_exceptions
        def test_func():
            return "success", 200

        result = test_func()
        assert result == ("success", 200)


class TestCommonErrorResponses:
    """Test common error response functions."""

    @patch("app.utils.response_helpers.error_response")
    def test_no_data_provided_error(self, mock_error_response):
        """Test no_data_provided_error function."""
        mock_error_response.return_value = ("no_data_error", 400)

        result = no_data_provided_error()

        mock_error_response.assert_called_once_with("No data provided", 400, "no_data")
        assert result == ("no_data_error", 400)

    @patch("app.utils.response_helpers.error_response")
    def test_missing_fields_error(self, mock_error_response):
        """Test missing_fields_error function."""
        mock_error_response.return_value = ("missing_fields_error", 400)

        fields = ["email", "password"]
        result = missing_fields_error(fields)

        mock_error_response.assert_called_once_with(
            "Required fields missing: email, password",
            400,
            "missing_fields",
            {"missing_fields": fields},
        )
        assert result == ("missing_fields_error", 400)

    @patch("app.utils.response_helpers.error_response")
    def test_invalid_credentials_error(self, mock_error_response):
        """Test invalid_credentials_error function."""
        mock_error_response.return_value = ("invalid_creds_error", 401)

        result = invalid_credentials_error()

        mock_error_response.assert_called_once_with(
            "Invalid credentials", 401, "invalid_credentials"
        )
        assert result == ("invalid_creds_error", 401)

    @patch("app.utils.response_helpers.error_response")
    def test_user_not_found_error(self, mock_error_response):
        """Test user_not_found_error function."""
        mock_error_response.return_value = ("user_not_found_error", 404)

        result = user_not_found_error()

        mock_error_response.assert_called_once_with(
            "User not found", 404, "user_not_found"
        )
        assert result == ("user_not_found_error", 404)

    @patch("app.utils.response_helpers.error_response")
    def test_already_exists_error(self, mock_error_response):
        """Test already_exists_error function."""
        mock_error_response.return_value = ("already_exists_error", 409)

        result = already_exists_error("User")

        mock_error_response.assert_called_once_with(
            "User already exists", 409, "resource_exists", {"resource": "User"}
        )
        assert result == ("already_exists_error", 409)

    @patch("app.utils.response_helpers.error_response")
    def test_token_revoked_error(self, mock_error_response):
        """Test token_revoked_error function."""
        mock_error_response.return_value = ("token_revoked_error", 401)

        result = token_revoked_error()

        mock_error_response.assert_called_once_with(
            "Token has been revoked", 401, "token_revoked"
        )
        assert result == ("token_revoked_error", 401)
