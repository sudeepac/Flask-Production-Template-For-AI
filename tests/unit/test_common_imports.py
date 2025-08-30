"""Unit tests for app.utils.common_imports module.

This module tests the utility functions and base classes
provided by the common_imports module.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from marshmallow import Schema, fields

from app.utils.common_imports import (
    BaseRequestSchema,
    BaseResponseSchema,
    get_module_logger,
    get_utc_timestamp,
)


class TestGetModuleLogger:
    """Test get_module_logger functionality."""

    @patch("app.utils.common_imports.get_logger")
    def test_get_module_logger_success(self, mock_get_logger):
        """Test successful logger retrieval."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        module_name = "test.module"
        result = get_module_logger(module_name)

        mock_get_logger.assert_called_once_with(module_name)
        assert result == mock_logger

    @patch("app.utils.common_imports.get_logger")
    def test_get_module_logger_with_dunder_name(self, mock_get_logger):
        """Test logger retrieval with __name__ pattern."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        module_name = "__main__"
        result = get_module_logger(module_name)

        mock_get_logger.assert_called_once_with(module_name)
        assert result == mock_logger

    @patch("app.utils.common_imports.get_logger")
    def test_get_module_logger_empty_string(self, mock_get_logger):
        """Test logger retrieval with empty module name."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        module_name = ""
        result = get_module_logger(module_name)

        mock_get_logger.assert_called_once_with(module_name)
        assert result == mock_logger


class TestGetUtcTimestamp:
    """Test get_utc_timestamp functionality."""

    @patch("app.utils.common_imports.datetime")
    def test_get_utc_timestamp_without_z_suffix(self, mock_datetime):
        """Test UTC timestamp generation without Z suffix."""
        # Mock datetime.utcnow()
        mock_now = Mock()
        mock_now.isoformat.return_value = "2023-12-01T10:30:45.123456"
        mock_datetime.utcnow.return_value = mock_now

        result = get_utc_timestamp()

        mock_datetime.utcnow.assert_called_once()
        mock_now.isoformat.assert_called_once()
        assert result == "2023-12-01T10:30:45.123456"

    @patch("app.utils.common_imports.datetime")
    def test_get_utc_timestamp_with_z_suffix(self, mock_datetime):
        """Test UTC timestamp generation with Z suffix."""
        # Mock datetime.utcnow()
        mock_now = Mock()
        mock_now.isoformat.return_value = "2023-12-01T10:30:45.123456"
        mock_datetime.utcnow.return_value = mock_now

        result = get_utc_timestamp(with_z_suffix=True)

        mock_datetime.utcnow.assert_called_once()
        mock_now.isoformat.assert_called_once()
        assert result == "2023-12-01T10:30:45.123456Z"

    @patch("app.utils.common_imports.datetime")
    def test_get_utc_timestamp_with_z_suffix_false(self, mock_datetime):
        """Test UTC timestamp generation with explicit Z suffix False."""
        # Mock datetime.utcnow()
        mock_now = Mock()
        mock_now.isoformat.return_value = "2023-12-01T10:30:45.123456"
        mock_datetime.utcnow.return_value = mock_now

        result = get_utc_timestamp(with_z_suffix=False)

        mock_datetime.utcnow.assert_called_once()
        mock_now.isoformat.assert_called_once()
        assert result == "2023-12-01T10:30:45.123456"

    def test_get_utc_timestamp_format_integration(self):
        """Test actual timestamp format (integration test)."""
        # Test without mocking to verify actual format
        result = get_utc_timestamp()

        # Verify it's a string
        assert isinstance(result, str)

        # Verify it doesn't end with Z
        assert not result.endswith("Z")

        # Verify it contains expected ISO format elements
        assert "T" in result  # Date-time separator
        assert ":" in result  # Time separator
        assert "-" in result  # Date separator

    def test_get_utc_timestamp_with_z_suffix_integration(self):
        """Test actual timestamp format with Z suffix (integration test)."""
        # Test without mocking to verify actual format
        result = get_utc_timestamp(with_z_suffix=True)

        # Verify it's a string
        assert isinstance(result, str)

        # Verify it ends with Z
        assert result.endswith("Z")

        # Verify it contains expected ISO format elements
        assert "T" in result  # Date-time separator
        assert ":" in result  # Time separator
        assert "-" in result  # Date separator

    def test_get_utc_timestamp_consistency(self):
        """Test that timestamps are consistent in format."""
        timestamp1 = get_utc_timestamp()
        timestamp2 = get_utc_timestamp()

        # Both should be strings
        assert isinstance(timestamp1, str)
        assert isinstance(timestamp2, str)

        # Both should have similar length (allowing for microsecond differences)
        assert abs(len(timestamp1) - len(timestamp2)) <= 1

        # Both should follow ISO format pattern
        for timestamp in [timestamp1, timestamp2]:
            assert "T" in timestamp
            assert ":" in timestamp
            assert "-" in timestamp


class TestBaseRequestSchema:
    """Test BaseRequestSchema functionality."""

    def test_base_request_schema_inheritance(self):
        """Test that BaseRequestSchema inherits from Schema."""
        assert issubclass(BaseRequestSchema, Schema)

    def test_base_request_schema_instantiation(self):
        """Test that BaseRequestSchema can be instantiated."""
        schema = BaseRequestSchema()
        assert isinstance(schema, Schema)
        assert isinstance(schema, BaseRequestSchema)

    def test_base_request_schema_extension(self):
        """Test that BaseRequestSchema can be extended."""

        class TestRequestSchema(BaseRequestSchema):
            name = fields.Str(required=True)
            email = fields.Email(required=True)

        schema = TestRequestSchema()
        assert isinstance(schema, BaseRequestSchema)
        assert isinstance(schema, Schema)

        # Test validation
        valid_data = {"name": "John Doe", "email": "john@example.com"}
        result = schema.load(valid_data)
        assert result == valid_data

    def test_base_request_schema_validation_error(self):
        """Test that extended BaseRequestSchema handles validation errors."""

        class TestRequestSchema(BaseRequestSchema):
            name = fields.Str(required=True)
            email = fields.Email(required=True)

        schema = TestRequestSchema()

        # Test with invalid data
        invalid_data = {"name": "John Doe", "email": "invalid-email"}

        with pytest.raises(Exception):  # Marshmallow ValidationError
            schema.load(invalid_data)

    def test_base_request_schema_empty_by_default(self):
        """Test that BaseRequestSchema has no fields by default."""
        schema = BaseRequestSchema()

        # Should be able to load empty dict
        result = schema.load({})
        assert result == {}

        # Should be able to load any dict
        test_data = {"any_field": "any_value"}
        result = schema.load(test_data)
        assert result == test_data


class TestBaseResponseSchema:
    """Test BaseResponseSchema functionality."""

    def test_base_response_schema_inheritance(self):
        """Test that BaseResponseSchema inherits from Schema."""
        assert issubclass(BaseResponseSchema, Schema)

    def test_base_response_schema_instantiation(self):
        """Test that BaseResponseSchema can be instantiated."""
        schema = BaseResponseSchema()
        assert isinstance(schema, Schema)
        assert isinstance(schema, BaseResponseSchema)

    def test_base_response_schema_extension(self):
        """Test that BaseResponseSchema can be extended."""

        class TestResponseSchema(BaseResponseSchema):
            id = fields.Int()
            name = fields.Str()
            created_at = fields.DateTime()

        schema = TestResponseSchema()
        assert isinstance(schema, BaseResponseSchema)
        assert isinstance(schema, Schema)

        # Test serialization
        test_data = {
            "id": 1,
            "name": "Test Item",
            "created_at": datetime(2023, 12, 1, 10, 30, 45),
        }
        result = schema.dump(test_data)
        assert "id" in result
        assert "name" in result
        assert "created_at" in result

    def test_base_response_schema_partial_data(self):
        """Test that extended BaseResponseSchema handles partial data."""

        class TestResponseSchema(BaseResponseSchema):
            id = fields.Int()
            name = fields.Str()
            optional_field = fields.Str(missing=None)

        schema = TestResponseSchema()

        # Test with partial data
        partial_data = {"id": 1, "name": "Test"}
        result = schema.dump(partial_data)

        assert result["id"] == 1
        assert result["name"] == "Test"
        # optional_field should not be in result if not provided

    def test_base_response_schema_empty_by_default(self):
        """Test that BaseResponseSchema has no fields by default."""
        schema = BaseResponseSchema()

        # Should be able to dump empty dict
        result = schema.dump({})
        assert result == {}

        # Should be able to dump any dict
        test_data = {"any_field": "any_value"}
        result = schema.dump(test_data)
        assert result == test_data

    def test_base_schemas_are_different_classes(self):
        """Test that BaseRequestSchema and BaseResponseSchema are different."""
        assert BaseRequestSchema != BaseResponseSchema
        assert not issubclass(BaseRequestSchema, BaseResponseSchema)
        assert not issubclass(BaseResponseSchema, BaseRequestSchema)

        # But both inherit from Schema
        assert issubclass(BaseRequestSchema, Schema)
        assert issubclass(BaseResponseSchema, Schema)


class TestSchemaIntegration:
    """Test integration between base schemas and common functionality."""

    def test_schemas_with_timestamp_utility(self):
        """Test using schemas with timestamp utility function."""

        class TimestampedResponseSchema(BaseResponseSchema):
            id = fields.Int()
            name = fields.Str()
            created_at = fields.Str()

        schema = TimestampedResponseSchema()

        # Use the timestamp utility
        timestamp = get_utc_timestamp(with_z_suffix=True)

        data = {"id": 1, "name": "Test Item", "created_at": timestamp}

        result = schema.dump(data)

        assert result["created_at"].endswith("Z")
        assert "T" in result["created_at"]

    def test_request_response_schema_workflow(self):
        """Test typical request-response schema workflow."""

        class CreateItemRequestSchema(BaseRequestSchema):
            name = fields.Str(required=True)
            description = fields.Str()

        class ItemResponseSchema(BaseResponseSchema):
            id = fields.Int()
            name = fields.Str()
            description = fields.Str()
            created_at = fields.Str()

        request_schema = CreateItemRequestSchema()
        response_schema = ItemResponseSchema()

        # Simulate request validation
        request_data = {"name": "Test Item", "description": "A test item"}
        validated_request = request_schema.load(request_data)

        # Simulate creating response
        response_data = {
            "id": 1,
            "name": validated_request["name"],
            "description": validated_request["description"],
            "created_at": get_utc_timestamp(with_z_suffix=True),
        }

        serialized_response = response_schema.dump(response_data)

        assert serialized_response["id"] == 1
        assert serialized_response["name"] == "Test Item"
        assert serialized_response["created_at"].endswith("Z")
