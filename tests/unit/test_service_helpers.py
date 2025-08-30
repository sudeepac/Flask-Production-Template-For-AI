"""Tests for service helper utilities."""

import logging
import time
from datetime import datetime
from unittest.mock import MagicMock, call, patch

import pytest

from app.utils.error_handlers import APIError, ValidationAPIError
from app.utils.service_helpers import (
    ModelLoadError,
    PredictionError,
    ProcessingError,
    ServiceError,
    ServiceMetrics,
    ValidationError,
    handle_service_errors,
    log_service_operation,
    retry_operation,
    safe_execute,
    service_operation,
    validate_input,
)


class TestServiceExceptions:
    """Test custom service exceptions."""

    def test_service_error(self):
        """Test ServiceError exception."""
        error = ServiceError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_validation_error(self):
        """Test ValidationError exception."""
        error = ValidationError("Validation failed")
        assert str(error) == "Validation failed"
        assert isinstance(error, ServiceError)
        assert isinstance(error, Exception)

    def test_processing_error(self):
        """Test ProcessingError exception."""
        error = ProcessingError("Processing failed")
        assert str(error) == "Processing failed"
        assert isinstance(error, ServiceError)

    def test_model_load_error(self):
        """Test ModelLoadError exception."""
        error = ModelLoadError("Model load failed")
        assert str(error) == "Model load failed"
        assert isinstance(error, ServiceError)

    def test_prediction_error(self):
        """Test PredictionError exception."""
        error = PredictionError("Prediction failed")
        assert str(error) == "Prediction failed"
        assert isinstance(error, ServiceError)


class TestServiceMetrics:
    """Test ServiceMetrics class."""

    def test_init(self):
        """Test ServiceMetrics initialization."""
        metrics = ServiceMetrics()
        assert metrics.operation_count == 0
        assert metrics.total_time == 0.0
        assert metrics.error_count == 0
        assert metrics.last_operation is None

    def test_record_operation_success(self):
        """Test recording successful operation."""
        metrics = ServiceMetrics()
        duration = 1.5

        metrics.record_operation(duration, success=True)

        assert metrics.operation_count == 1
        assert metrics.total_time == duration
        assert metrics.error_count == 0
        assert isinstance(metrics.last_operation, datetime)

    def test_record_operation_failure(self):
        """Test recording failed operation."""
        metrics = ServiceMetrics()
        duration = 2.0

        metrics.record_operation(duration, success=False)

        assert metrics.operation_count == 1
        assert metrics.total_time == duration
        assert metrics.error_count == 1
        assert isinstance(metrics.last_operation, datetime)

    def test_multiple_operations(self):
        """Test recording multiple operations."""
        metrics = ServiceMetrics()

        metrics.record_operation(1.0, success=True)
        metrics.record_operation(2.0, success=False)
        metrics.record_operation(3.0, success=True)

        assert metrics.operation_count == 3
        assert metrics.total_time == 6.0
        assert metrics.error_count == 1

    def test_average_time(self):
        """Test average time calculation."""
        metrics = ServiceMetrics()

        # No operations
        assert metrics.average_time == 0.0

        # With operations
        metrics.record_operation(2.0)
        metrics.record_operation(4.0)

        assert metrics.average_time == 3.0

    def test_error_rate(self):
        """Test error rate calculation."""
        metrics = ServiceMetrics()

        # No operations
        assert metrics.error_rate == 0.0

        # With operations
        metrics.record_operation(1.0, success=True)
        metrics.record_operation(1.0, success=False)
        metrics.record_operation(1.0, success=True)
        metrics.record_operation(1.0, success=False)

        assert metrics.error_rate == 50.0


class TestHandleServiceErrors:
    """Test handle_service_errors decorator."""

    @patch("app.utils.service_helpers.logger")
    def test_successful_execution(self, mock_logger):
        """Test decorator with successful function execution."""

        @handle_service_errors()
        def test_function():
            return "success"

        result = test_function()
        assert result == "success"
        mock_logger.log.assert_not_called()

    @patch("app.utils.service_helpers.logger")
    def test_exception_handling(self, mock_logger):
        """Test decorator with exception."""

        @handle_service_errors()
        def test_function():
            raise ValueError("Test error")

        with pytest.raises(ServiceError) as exc_info:
            test_function()

        assert "test_function failed: Test error" in str(exc_info.value)
        mock_logger.log.assert_called_once()

    @patch("app.utils.service_helpers.logger")
    def test_custom_error_message(self, mock_logger):
        """Test decorator with custom error message."""

        @handle_service_errors(error_message="Custom error in {method}: {error}")
        def test_function():
            raise ValueError("Test error")

        with pytest.raises(ServiceError) as exc_info:
            test_function()

        assert "Custom error in test_function: Test error" in str(exc_info.value)

    @patch("app.utils.service_helpers.logger")
    def test_custom_error_type(self, mock_logger):
        """Test decorator with custom error type."""

        @handle_service_errors(error_type=ProcessingError)
        def test_function():
            raise ValueError("Test error")

        with pytest.raises(ProcessingError):
            test_function()

    @patch("app.utils.service_helpers.logger")
    def test_with_service_class(self, mock_logger):
        """Test decorator with service class method."""

        class TestService:
            @handle_service_errors()
            def test_method(self):
                raise ValueError("Test error")

        service = TestService()
        with pytest.raises(ServiceError) as exc_info:
            service.test_method()

        assert "TestService.test_method failed: Test error" in str(exc_info.value)


class TestServiceOperation:
    """Test service_operation decorator."""

    @patch("app.utils.service_helpers.logger")
    @patch("time.time")
    def test_successful_operation(self, mock_time, mock_logger):
        """Test decorator with successful operation."""
        mock_time.side_effect = [0.0, 1.0]  # start and end times

        @service_operation()
        def test_function():
            return "success"

        result = test_function()
        assert result == "success"

        # Check logging calls
        assert mock_logger.debug.called
        assert mock_logger.info.called

    @patch("app.utils.service_helpers.logger")
    @patch("time.time")
    def test_operation_with_metrics(self, mock_time, mock_logger):
        """Test decorator with metrics tracking."""
        mock_time.side_effect = [0.0, 1.0]

        class TestService:
            def __init__(self):
                self._metrics = ServiceMetrics()

            @service_operation()
            def test_method(self):
                return "success"

        service = TestService()
        result = service.test_method()

        assert result == "success"
        assert service._metrics.operation_count == 1
        assert service._metrics.error_count == 0

    @patch("app.utils.service_helpers.logger")
    def test_operation_with_exception(self, mock_logger):
        """Test decorator with exception handling."""

        @service_operation()
        def test_function():
            raise ValidationError("Test validation error")

        with pytest.raises(ValidationAPIError):
            test_function()

        assert mock_logger.error.called

    @patch("app.utils.service_helpers.logger")
    def test_operation_with_model_error(self, mock_logger):
        """Test decorator with model error."""

        @service_operation()
        def test_function():
            raise ModelLoadError("Model failed to load")

        with pytest.raises(APIError):
            test_function()

    @patch("app.utils.service_helpers.logger")
    def test_operation_with_logging_options(self, mock_logger):
        """Test decorator with logging options."""

        @service_operation(log_args=True, log_result=True)
        def test_function(arg1, arg2, kwarg1=None):
            return [1, 2, 3]

        result = test_function("test1", "test2", kwarg1="test3")
        assert result == [1, 2, 3]

        # Verify logging was called with extra data
        assert mock_logger.debug.called
        assert mock_logger.info.called


class TestLogServiceOperation:
    """Test log_service_operation decorator (legacy)."""

    @patch("app.utils.service_helpers.service_operation")
    def test_legacy_decorator(self, mock_service_operation):
        """Test that legacy decorator calls service_operation."""
        mock_service_operation.return_value = lambda f: f

        @log_service_operation(operation_name="test", log_args=True)
        def test_function():
            return "success"

        mock_service_operation.assert_called_once_with(
            "test", True, False, track_metrics=False
        )


class TestValidateInput:
    """Test validate_input function."""

    def test_none_input(self):
        """Test validation with None input."""
        with pytest.raises(ValidationError, match="Input data cannot be None"):
            validate_input(None)

    def test_valid_input_no_requirements(self):
        """Test validation with valid input and no requirements."""
        # Should not raise any exception
        validate_input({"key": "value"})
        validate_input("string")
        validate_input(123)

    def test_required_fields_success(self):
        """Test validation with required fields - success case."""
        data = {"name": "test", "email": "test@example.com", "age": 25}
        required_fields = ["name", "email"]

        # Should not raise any exception
        validate_input(data, required_fields=required_fields)

    def test_required_fields_missing(self):
        """Test validation with missing required fields."""
        data = {"name": "test"}
        required_fields = ["name", "email", "age"]

        with pytest.raises(
            ValidationError, match="Missing required fields: email, age"
        ):
            validate_input(data, required_fields=required_fields)

    def test_required_fields_non_dict(self):
        """Test validation with required fields on non-dict data."""
        with pytest.raises(
            ValidationError,
            match="Data must be a dictionary when checking required fields",
        ):
            validate_input("string", required_fields=["field"])

    def test_field_types_success(self):
        """Test validation with field types - success case."""
        data = {"name": "test", "age": 25, "active": True}
        field_types = {"name": str, "age": int, "active": bool}

        # Should not raise any exception
        validate_input(data, field_types=field_types)

    def test_field_types_mismatch(self):
        """Test validation with field type mismatch."""
        data = {"name": "test", "age": "25"}  # age should be int
        field_types = {"name": str, "age": int}

        with pytest.raises(
            ValidationError, match="Field 'age' must be of type int, got str"
        ):
            validate_input(data, field_types=field_types)

    def test_field_types_non_dict(self):
        """Test validation with field types on non-dict data."""
        with pytest.raises(
            ValidationError, match="Data must be a dictionary when checking field types"
        ):
            validate_input("string", field_types={"field": str})

    def test_combined_validation(self):
        """Test validation with both required fields and field types."""
        data = {"name": "test", "age": 25}
        required_fields = ["name", "age"]
        field_types = {"name": str, "age": int}

        # Should not raise any exception
        validate_input(data, required_fields=required_fields, field_types=field_types)


class TestSafeExecute:
    """Test safe_execute function."""

    @patch("app.utils.service_helpers.logger")
    def test_successful_execution(self, mock_logger):
        """Test safe execution with successful operation."""

        def test_operation(x, y):
            return x + y

        result = safe_execute(test_operation, 2, 3)
        assert result == 5
        mock_logger.error.assert_not_called()

    @patch("app.utils.service_helpers.logger")
    def test_execution_with_exception(self, mock_logger):
        """Test safe execution with exception."""

        def test_operation():
            raise ValueError("Test error")

        result = safe_execute(test_operation, default_return="default")
        assert result == "default"
        mock_logger.error.assert_called_once()

    @patch("app.utils.service_helpers.logger")
    def test_execution_with_custom_error_message(self, mock_logger):
        """Test safe execution with custom error message."""

        def test_operation():
            raise ValueError("Test error")

        result = safe_execute(
            test_operation, default_return=None, error_message="Custom error occurred"
        )
        assert result is None
        mock_logger.error.assert_called_with("Custom error occurred", exc_info=True)

    @patch("app.utils.service_helpers.logger")
    def test_execution_without_logging(self, mock_logger):
        """Test safe execution without error logging."""

        def test_operation():
            raise ValueError("Test error")

        result = safe_execute(
            test_operation, log_errors=False, default_return="default"
        )
        assert result == "default"
        mock_logger.error.assert_not_called()

    def test_execution_with_kwargs(self):
        """Test safe execution with keyword arguments."""

        def test_operation(x, y, multiplier=1):
            return (x + y) * multiplier

        result = safe_execute(test_operation, 2, 3, multiplier=2)
        assert result == 10


class TestRetryOperation:
    """Test retry_operation function."""

    @patch("time.sleep")
    @patch("app.utils.service_helpers.logger")
    def test_successful_first_attempt(self, mock_logger, mock_sleep):
        """Test retry with successful first attempt."""

        def test_operation():
            return "success"

        result = retry_operation(test_operation)
        assert result == "success"
        mock_sleep.assert_not_called()
        mock_logger.warning.assert_not_called()

    @patch("time.sleep")
    @patch("app.utils.service_helpers.logger")
    def test_successful_after_retries(self, mock_logger, mock_sleep):
        """Test retry with success after some failures."""
        call_count = 0

        def test_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = retry_operation(test_operation, max_retries=3)
        assert result == "success"
        assert mock_sleep.call_count == 2  # Failed twice, then succeeded
        assert mock_logger.warning.call_count == 2

    @patch("time.sleep")
    @patch("app.utils.service_helpers.logger")
    def test_all_retries_fail(self, mock_logger, mock_sleep):
        """Test retry with all attempts failing."""

        def test_operation():
            raise ValueError("Persistent error")

        with pytest.raises(ValueError, match="Persistent error"):
            retry_operation(test_operation, max_retries=2)

        assert mock_sleep.call_count == 2  # 2 retries
        assert mock_logger.warning.call_count == 2
        assert mock_logger.error.call_count == 1

    @patch("time.sleep")
    def test_exponential_backoff(self, mock_sleep):
        """Test exponential backoff timing."""

        def test_operation():
            raise ValueError("Error")

        with pytest.raises(ValueError):
            retry_operation(
                test_operation, max_retries=3, delay=1.0, backoff_factor=2.0
            )

        # Check that sleep was called with increasing delays
        expected_calls = [call(1.0), call(2.0), call(4.0)]
        mock_sleep.assert_has_calls(expected_calls)

    @patch("time.sleep")
    def test_retry_with_args_kwargs(self, mock_sleep):
        """Test retry with function arguments."""
        call_count = 0

        def test_operation(x, y, multiplier=1):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary error")
            return (x + y) * multiplier

        result = retry_operation(test_operation, 3, 0.1, 2.0, 2, 3, multiplier=2)
        assert result == 10
        assert mock_sleep.call_count == 1
