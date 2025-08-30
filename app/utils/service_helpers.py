"""Service Helper Utilities.

This module provides utilities for service layer operations including
error handling, logging, and common service patterns.
"""

import functools
import logging
import time
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar

from app.utils.error_handlers import APIError, ValidationAPIError
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# Type variable for generic function decoration
F = TypeVar("F", bound=Callable[..., Any])


class ServiceError(Exception):
    """Base exception for service layer errors."""


class ValidationError(ServiceError):
    """Exception for validation errors in services."""


class ProcessingError(ServiceError):
    """Exception for processing errors in services."""


class ModelLoadError(ServiceError):
    """Exception for model loading errors."""


class PredictionError(ServiceError):
    """Exception for prediction errors."""


class ServiceMetrics:
    """Common service metrics tracking."""

    def __init__(self):
        """Initialize the instance."""
        self.operation_count = 0
        self.total_time = 0.0
        self.error_count = 0
        self.last_operation = None

    def record_operation(self, duration: float, success: bool = True):
        """Record an operation with its duration and success status."""
        self.operation_count += 1
        self.total_time += duration
        self.last_operation = datetime.now()
        if not success:
            self.error_count += 1

    @property
    def average_time(self) -> float:
        """Get average operation time."""
        if self.operation_count > 0:
            return self.total_time / self.operation_count
        return 0.0

    @property
    def error_rate(self) -> float:
        """Get error rate as percentage."""
        if self.operation_count > 0:
            return self.error_count / self.operation_count * 100
        return 0.0


def handle_service_errors(
    error_message: str = None,
    error_type: type = ServiceError,
    log_level: int = logging.ERROR,
) -> Callable[[F], F]:
    """Decorator to handle common service exceptions.

    Args:
        error_message: Custom error message template
        error_type: Exception type to raise
        log_level: Logging level for errors

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        """Decorator function that applies error handling."""

        @wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapper function that catches and handles exceptions."""
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get service name from class if available
                service_name = "Unknown"
                if args and hasattr(args[0], "__class__"):
                    service_name = args[0].__class__.__name__

                # Create error message
                if error_message:
                    msg = error_message.format(
                        service=service_name, method=func.__name__, error=str(e)
                    )
                else:
                    msg = f"{service_name}.{func.__name__} failed: {str(e)}"

                # Log the error
                logger.log(log_level, msg, exc_info=True)

                # Raise appropriate exception
                raise error_type(msg) from e

        return wrapper

    return decorator


def service_operation(
    operation_name: str = None,
    log_args: bool = False,
    log_result: bool = False,
    track_metrics: bool = True,
    timeout: Optional[float] = None,
) -> Callable[[F], F]:
    """Consolidated decorator for service operations.

    Combines error handling, logging, metrics tracking, and timeout handling.

    Args:
        operation_name: Custom operation name for logging
        log_args: Whether to log function arguments
        log_result: Whether to log function result
        track_metrics: Whether to track operation metrics
        timeout: Operation timeout in seconds

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        """Decorator function that applies timing measurement."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapper function that measures execution time."""
            start_time = time.time()

            # Get service name from class if available
            service_name = "Unknown"
            if args and hasattr(args[0], "__class__"):
                service_name = args[0].__class__.__name__

            op_name = operation_name or f"{service_name}.{func.__name__}"

            # Get metrics tracker if available
            metrics = None
            if track_metrics and args and hasattr(args[0], "_metrics"):
                metrics = args[0]._metrics

            # Log operation start
            log_data = {"operation": op_name}
            if log_args:
                log_data["args"] = str(args[1:])  # Skip self
                log_data["kwargs"] = str(kwargs)

            logger.debug(f"Starting {op_name}", extra=log_data)

            try:
                result = func(*args, **kwargs)

                # Log successful completion
                duration = time.time() - start_time
                log_data.update(
                    {"duration_ms": round(duration * 1000, 2), "status": "success"}
                )

                if log_result and result is not None:
                    log_data["result_type"] = type(result).__name__
                    if hasattr(result, "__len__"):
                        log_data["result_size"] = len(result)

                # Track metrics
                if metrics:
                    metrics.record_operation(duration, success=True)

                logger.info(f"Completed {op_name}", extra=log_data)
                return result

            except Exception as e:
                # Log operation failure
                duration = time.time() - start_time
                log_data.update(
                    {
                        "duration_ms": round(duration * 1000, 2),
                        "status": "failed",
                        "error": str(e),
                    }
                )

                # Track metrics
                if metrics:
                    metrics.record_operation(duration, success=False)

                logger.error(f"Failed {op_name}", extra=log_data)

                # Convert to appropriate API error
                if isinstance(e, (ModelLoadError, PredictionError)):
                    raise APIError(
                        f"Service operation failed: {str(e)}", status_code=500
                    )
                elif isinstance(e, ValidationError):
                    raise ValidationAPIError(str(e))
                else:
                    raise

        return wrapper

    return decorator


def log_service_operation(
    operation_name: str = None, log_args: bool = False, log_result: bool = False
) -> Callable[[F], F]:
    """Legacy decorator - use service_operation instead.

    Args:
        operation_name: Custom operation name
        log_args: Whether to log function arguments
        log_result: Whether to log function result

    Returns:
        Decorated function
    """
    return service_operation(operation_name, log_args, log_result, track_metrics=False)


def validate_input(
    data: Any, required_fields: list = None, field_types: Dict[str, type] = None
) -> None:
    """Validate input data for service operations.

    Args:
        data: Data to validate
        required_fields: List of required field names
        field_types: Dictionary mapping field names to expected types

    Raises:
        ValidationError: If validation fails
    """
    if data is None:
        raise ValidationError("Input data cannot be None")

    if required_fields:
        if not isinstance(data, dict):
            raise ValidationError(
                "Data must be a dictionary when checking required fields"
            )

        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )

    if field_types:
        if not isinstance(data, dict):
            raise ValidationError("Data must be a dictionary when checking field types")

        for field, expected_type in field_types.items():
            if field in data and not isinstance(data[field], expected_type):
                actual_type = type(data[field]).__name__
                expected_type_name = expected_type.__name__
                raise ValidationError(
                    f"Field '{field}' must be of type {expected_type_name}, "
                    f"got {actual_type}"
                )


def safe_execute(
    operation: Callable,
    *args,
    default_return=None,
    error_message: str = None,
    log_errors: bool = True,
    **kwargs,
) -> Any:
    """Safely execute an operation with error handling.

    Args:
        operation: Function to execute
        *args: Arguments for the operation
        default_return: Value to return on error
        error_message: Custom error message
        log_errors: Whether to log errors
        **kwargs: Keyword arguments for the operation

    Returns:
        Operation result or default_return on error
    """
    try:
        return operation(*args, **kwargs)
    except Exception as e:
        if log_errors:
            msg = error_message or f"Operation {operation.__name__} failed: {str(e)}"
            logger.error(msg, exc_info=True)
        return default_return


def retry_operation(
    operation: Callable,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    *args,
    **kwargs,
) -> Any:
    """Retry an operation with exponential backoff.

    Args:
        operation: Function to execute
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff_factor: Factor to multiply delay by after each retry
        *args: Arguments for the operation
        **kwargs: Keyword arguments for the operation

    Returns:
        Operation result

    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    current_delay = delay

    for attempt in range(max_retries + 1):
        try:
            return operation(*args, **kwargs)
        except Exception as e:
            last_exception = e

            if attempt < max_retries:
                logger.warning(
                    f"Operation {operation.__name__} failed "
                    f"(attempt {attempt + 1}/{max_retries + 1}), "
                    f"retrying in {current_delay}s: {str(e)}"
                )
                time.sleep(current_delay)
                current_delay *= backoff_factor
            else:
                logger.error(
                    f"Operation {operation.__name__} failed after "
                    f"{max_retries + 1} attempts: {str(e)}"
                )

    raise last_exception
