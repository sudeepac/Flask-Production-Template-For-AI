"""Tests for service helpers module."""

import pytest
from app.utils.service_helpers import (
    ServiceError,
    ValidationError,
    safe_execute,
    validate_required_fields,
)
from tests.fixtures.app_fixtures import app, client, runner
from tests.fixtures.data_fixtures import sample_data


class TestServiceExceptions:
    """Test custom service exceptions."""

    def test_service_error_creation(self):
        """Test ServiceError creation."""
        error = ServiceError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_validation_error_creation(self):
        """Test ValidationError creation."""
        error = ValidationError("Validation failed")
        assert str(error) == "Validation failed"
        assert isinstance(error, ServiceError)


class TestValidateRequiredFields:
    """Test validate_required_fields function."""

    def test_valid_data(self):
        """Test validation with valid data."""
        data = {"name": "test", "email": "test@example.com"}
        required_fields = ["name", "email"]
        
        # Should not raise an exception
        validate_required_fields(data, required_fields)

    def test_missing_fields(self):
        """Test validation with missing fields."""
        data = {"name": "test"}
        required_fields = ["name", "email"]
        
        with pytest.raises(ValidationError, match="Missing required fields: email"):
            validate_required_fields(data, required_fields)

    def test_invalid_data_type(self):
        """Test validation with invalid data type."""
        data = "not a dict"
        required_fields = ["name"]
        
        with pytest.raises(ValidationError, match="Data must be a dictionary"):
            validate_required_fields(data, required_fields)

    def test_multiple_missing_fields(self):
        """Test validation with multiple missing fields."""
        data = {}
        required_fields = ["name", "email", "age"]
        
        with pytest.raises(ValidationError, match="Missing required fields: name, email, age"):
            validate_required_fields(data, required_fields)


class TestSafeExecute:
    """Test safe_execute function."""

    def test_successful_execution(self):
        """Test safe execution of successful function."""
        def test_func():
            return "success"
        
        result = safe_execute(test_func)
        assert result == "success"

    def test_exception_handling(self):
        """Test safe execution with exception returns default value."""
        def test_func():
            raise ValueError("Test error")
        
        result = safe_execute(test_func, default_return="default")
        assert result == "default"

    def test_exception_handling_none_default(self):
        """Test safe execution with exception returns None by default."""
        def test_func():
            raise ValueError("Test error")
        
        result = safe_execute(test_func)
        assert result is None

    def test_with_arguments(self):
        """Test safe execution with function arguments."""
        def test_func(a, b, c=None):
            return f"{a}-{b}-{c}"
        
        result = safe_execute(test_func, "arg1", "arg2", c="kwarg1")
        assert result == "arg1-arg2-kwarg1"

    def test_with_arguments_and_exception(self):
        """Test safe execution with arguments and exception."""
        def test_func(a, b):
            raise ValueError(f"Error with {a} and {b}")
        
        result = safe_execute(test_func, "arg1", "arg2", default_return="fallback")
        assert result == "fallback"