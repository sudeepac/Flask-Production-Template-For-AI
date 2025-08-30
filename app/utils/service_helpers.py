"""Service Helper Utilities.

Simple utilities for service layer operations.
"""

import logging
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """Base exception for service layer errors."""
    pass


class ValidationError(ServiceError):
    """Exception for validation errors in services."""
    pass


def validate_required_fields(data: Dict[str, Any], required_fields: list) -> None:
    """Validate that required fields are present in data.
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(data, dict):
        raise ValidationError("Data must be a dictionary")
        
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")


def safe_execute(operation: Callable, *args, default_return=None, **kwargs) -> Any:
    """Safely execute an operation with error handling.
    
    Args:
        operation: Function to execute
        *args: Arguments for the operation
        default_return: Value to return on error
        **kwargs: Keyword arguments for the operation
        
    Returns:
        Operation result or default_return on error
    """
    try:
        return operation(*args, **kwargs)
    except Exception as e:
        logger.error(f"Operation {operation.__name__} failed: {str(e)}")
        return default_return
