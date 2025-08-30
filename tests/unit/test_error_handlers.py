from unittest.mock import MagicMock, Mock, patch

import pytest
from flask import Flask
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.exceptions import BadRequest, HTTPException, InternalServerError

from app.utils.error_handlers import (
    APIError,
    ConflictAPIError,
    ForbiddenAPIError,
    NotFoundAPIError,
    RateLimitAPIError,
    ServiceUnavailableAPIError,
    UnauthorizedAPIError,
    ValidationAPIError,
    format_error_response,
    get_request_id,
    handle_validation_error,
    log_error,
    register_error_handlers,
)


class TestAPIError:
    """Test the APIError class and its subclasses."""

    def test_api_error_basic(self):
        """Test basic APIError creation."""
        error = APIError("Test error", 400)
        assert str(error) == "Test error"
        assert error.status_code == 400
        assert error.details is None

    def test_api_error_with_details(self):
        """Test APIError with details."""
        details = {"field": "value"}
        error = APIError("Test error", 400, details=details)
        assert str(error) == "Test error"
        assert error.status_code == 400
        assert error.details == details

    def test_validation_api_error(self):
        """Test ValidationAPIError."""
        error = ValidationAPIError("Validation failed")
        assert str(error) == "Validation failed"
        assert error.status_code == 400

    def test_not_found_api_error(self):
        """Test NotFoundAPIError."""
        error = NotFoundAPIError("Resource not found")
        assert str(error) == "Resource not found"
        assert error.status_code == 404

    def test_unauthorized_api_error(self):
        """Test UnauthorizedAPIError."""
        error = UnauthorizedAPIError("Unauthorized access")
        assert str(error) == "Unauthorized access"
        assert error.status_code == 401

    def test_forbidden_api_error(self):
        """Test ForbiddenAPIError."""
        error = ForbiddenAPIError("Access forbidden")
        assert str(error) == "Access forbidden"
        assert error.status_code == 403

    def test_conflict_api_error(self):
        """Test ConflictAPIError."""
        error = ConflictAPIError("Resource conflict")
        assert str(error) == "Resource conflict"
        assert error.status_code == 409

    def test_rate_limit_api_error(self):
        """Test RateLimitAPIError."""
        error = RateLimitAPIError("Rate limit exceeded")
        assert str(error) == "Rate limit exceeded"
        assert error.status_code == 429

    def test_service_unavailable_api_error(self):
        """Test ServiceUnavailableAPIError."""
        error = ServiceUnavailableAPIError("Service unavailable")
        assert str(error) == "Service unavailable"
        assert error.status_code == 503


class TestGetRequestId:
    """Test the get_request_id function."""

    @patch("app.utils.error_handlers.g")
    def test_get_request_id_existing(self, mock_g):
        """Test getting existing request ID."""
        mock_g.request_id = "existing-id"
        result = get_request_id()
        assert result == "existing-id"

    @patch("app.utils.error_handlers.uuid4")
    @patch("app.utils.error_handlers.g")
    def test_get_request_id_new(self, mock_g, mock_uuid):
        """Test generating new request ID."""
        mock_g.request_id = None
        mock_uuid.return_value = Mock()
        mock_uuid.return_value.__str__ = Mock(return_value="new-id")

        result = get_request_id()
        assert result == "new-id"
        assert mock_g.request_id == "new-id"


class TestFormatErrorResponse:
    """Test the format_error_response function."""

    @patch("app.utils.error_handlers.hasattr")
    @patch("app.utils.error_handlers.g")
    @patch("app.utils.error_handlers.current_app")
    @patch("app.utils.error_handlers.datetime")
    @patch("app.utils.error_handlers.get_request_id")
    def test_format_error_response_basic(
        self, mock_get_request_id, mock_datetime, mock_app, mock_g, mock_hasattr
    ):
        """Test basic error response formatting."""
        mock_get_request_id.return_value = "test-request-id"
        mock_datetime.utcnow.return_value.isoformat.return_value = "2023-01-01T00:00:00"
        mock_app.debug = False
        mock_hasattr.return_value = False

        response, status_code = format_error_response(
            "TEST_ERROR", "Test error message", 400
        )

        assert status_code == 400
        assert response["error"]["code"] == "TEST_ERROR"
        assert response["error"]["message"] == "Test error message"
        assert response["error"]["request_id"] == "test-request-id"
        assert response["error"]["timestamp"] == "2023-01-01T00:00:00Z"

    @patch("app.utils.error_handlers.hasattr")
    @patch("app.utils.error_handlers.g")
    @patch("app.utils.error_handlers.current_app")
    @patch("app.utils.error_handlers.datetime")
    @patch("app.utils.error_handlers.get_request_id")
    def test_format_error_response_with_details(
        self, mock_get_request_id, mock_datetime, mock_app, mock_g, mock_hasattr
    ):
        """Test error response formatting with details."""
        mock_get_request_id.return_value = "test-request-id"
        mock_datetime.utcnow.return_value.isoformat.return_value = "2023-01-01T00:00:00"
        mock_app.debug = False
        mock_hasattr.return_value = False

        details = {"field": "value"}
        response, status_code = format_error_response(
            "TEST_ERROR", "Test error message", 400, details=details
        )

        assert response["error"]["details"] == details

    @patch("app.utils.error_handlers.hasattr")
    @patch("app.utils.error_handlers.g")
    @patch("app.utils.error_handlers.current_app")
    @patch("app.utils.error_handlers.datetime")
    @patch("app.utils.error_handlers.get_request_id")
    def test_format_error_response_debug_mode(
        self, mock_get_request_id, mock_datetime, mock_app, mock_g, mock_hasattr
    ):
        """Test error response formatting in debug mode."""
        mock_get_request_id.return_value = "test-request-id"
        mock_datetime.utcnow.return_value.isoformat.return_value = "2023-01-01T00:00:00"
        mock_app.debug = True
        mock_hasattr.return_value = True
        mock_g.error_traceback = "traceback info"

        response, status_code = format_error_response(
            "TEST_ERROR", "Test error message", 400
        )

        assert "traceback" in response["error"]
        assert response["error"]["traceback"] == "traceback info"


class TestLogError:
    """Test the log_error function."""

    @patch("app.utils.error_handlers.current_app")
    @patch("app.utils.error_handlers.request")
    @patch("app.utils.error_handlers.logger")
    @patch("app.utils.error_handlers.get_request_id")
    def test_log_error_basic(
        self, mock_get_request_id, mock_logger, mock_request, mock_app
    ):
        """Test basic error logging."""
        mock_get_request_id.return_value = "test-request-id"
        mock_request.endpoint = "/test"
        mock_request.method = "GET"
        mock_request.url = "http://test.com/test"
        mock_request.headers.get.return_value = "test-agent"
        mock_request.remote_addr = "127.0.0.1"
        mock_app.debug = False

        error = Exception("Test error")
        log_error(error)

        mock_logger.log.assert_called_once()
        args, kwargs = mock_logger.log.call_args
        assert args[0] == 40  # logging.ERROR
        assert "Test error" in args[1]
        assert kwargs["exc_info"] is True
        assert "context" in kwargs["extra"]

    @patch("app.utils.error_handlers.current_app")
    @patch("app.utils.error_handlers.request")
    @patch("app.utils.error_handlers.logger")
    @patch("app.utils.error_handlers.get_request_id")
    def test_log_error_with_context(
        self, mock_get_request_id, mock_logger, mock_request, mock_app
    ):
        """Test error logging with additional context."""
        mock_get_request_id.return_value = "test-request-id"
        mock_request.endpoint = "/test"
        mock_request.method = "GET"
        mock_request.url = "http://test.com/test"
        mock_request.headers.get.return_value = "test-agent"
        mock_request.remote_addr = "127.0.0.1"
        mock_app.debug = False

        error = Exception("Test error")
        context = {"user_id": 123}
        log_error(error, context=context)

        mock_logger.log.assert_called_once()
        args, kwargs = mock_logger.log.call_args
        assert kwargs["extra"]["context"]["user_id"] == 123


class TestHandleValidationError:
    """Test the standalone handle_validation_error function."""

    @patch("app.utils.error_handlers.format_error_response")
    def test_handle_validation_error_basic(self, mock_format_error):
        """Test basic validation error handling."""
        mock_format_error.return_value = ({"error": "validation failed"}, 400)

        error = ValidationError("Field is required")
        response, status_code = handle_validation_error(error)

        assert status_code == 400
        mock_format_error.assert_called_once_with(
            "VALIDATION_ERROR", "Field is required", 400, details=None
        )

    @patch("app.utils.error_handlers.format_error_response")
    def test_handle_validation_error_with_messages(self, mock_format_error):
        """Test validation error handling with field messages."""
        mock_format_error.return_value = ({"error": "validation failed"}, 400)

        error = ValidationError({"email": ["Invalid email"], "name": ["Required"]})
        response, status_code = handle_validation_error(error)

        assert status_code == 400
        mock_format_error.assert_called_once_with(
            "VALIDATION_ERROR",
            "Validation failed",
            400,
            details={"email": ["Invalid email"], "name": ["Required"]},
        )


class TestRegisterErrorHandlers:
    """Test the register_error_handlers function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True

    def test_register_error_handlers_integration(self):
        """Test error handlers registration and basic functionality."""
        register_error_handlers(self.app)

        with self.app.test_client() as client:
            # Test that the app has error handlers registered
            assert len(self.app.error_handler_spec[None]) > 0

            # Test a simple route to ensure the app works
            @self.app.route("/test")
            def test_route():
                return "OK"

            response = client.get("/test")
            assert response.status_code == 200

    def test_api_error_handler_integration(self):
        """Test APIError handler through actual request."""
        register_error_handlers(self.app)

        @self.app.route("/test-api-error")
        def test_api_error():
            raise APIError("Test API error", 400)

        with self.app.test_client() as client:
            response = client.get("/test-api-error")
            assert response.status_code == 400
            data = response.get_json()
            assert "error" in data

    def test_validation_error_handler_integration(self):
        """Test ValidationError handler through actual request."""
        register_error_handlers(self.app)

        @self.app.route("/test-validation-error")
        def test_validation_error():
            raise ValidationError("Validation failed")

        with self.app.test_client() as client:
            response = client.get("/test-validation-error")
            assert response.status_code == 400
            data = response.get_json()
            assert "error" in data

    def test_http_exception_handler_integration(self):
        """Test HTTPException handler through actual request."""
        register_error_handlers(self.app)

        @self.app.route("/test-http-error")
        def test_http_error():
            raise BadRequest("Bad request")

        with self.app.test_client() as client:
            response = client.get("/test-http-error")
            assert response.status_code == 400
            data = response.get_json()
            assert "error" in data

    def test_database_error_handler_integration(self):
        """Test database error handler through actual request."""
        register_error_handlers(self.app)

        @self.app.route("/test-db-error")
        def test_db_error():
            raise SQLAlchemyError("Database error")

        with self.app.test_client() as client:
            response = client.get("/test-db-error")
            assert response.status_code == 500
            data = response.get_json()
            assert "error" in data

    def test_general_exception_handler_integration(self):
        """Test general exception handler through actual request."""
        register_error_handlers(self.app)

        @self.app.route("/test-general-error")
        def test_general_error():
            raise Exception("General error")

        with self.app.test_client() as client:
            response = client.get("/test-general-error")
            assert response.status_code == 500
            data = response.get_json()
            assert "error" in data
