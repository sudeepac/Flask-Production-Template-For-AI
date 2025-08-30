"""Advanced Logging Configuration.

This module provides comprehensive logging setup for the Flask application.
Includes structured logging, multiple handlers, and environment-specific configurations.

Features:
- Structured JSON logging for production
- Console logging for development
- File rotation and retention
- Request correlation IDs
- Performance logging
- Security event logging
- Third-party library log filtering

Usage:
    from app.utils.logging_config import setup_logging

    # Setup logging for Flask app
    setup_logging(app)
"""

import json
import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from flask import Flask, g, has_request_context, request


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON.

        Args:
            record: Log record to format

        Returns:
            JSON formatted log string
        """
        # Base log data
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request context if available
        if has_request_context():
            log_data.update(
                {
                    "request_id": getattr(g, "request_id", None),
                    "method": request.method,
                    "path": request.path,
                    "remote_addr": request.remote_addr,
                    "user_agent": request.headers.get("User-Agent"),
                }
            )

        # Add extra context if provided
        if hasattr(record, "context"):
            log_data["context"] = record.context

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        # Add performance metrics if available
        if hasattr(record, "duration"):
            log_data["performance"] = {"duration_ms": record.duration}

        return json.dumps(log_data, ensure_ascii=False)


class ColoredConsoleFormatter(logging.Formatter):
    """Colored console formatter for development."""

    # Color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors for console output.

        Args:
            record: Log record to format

        Returns:
            Colored formatted log string
        """
        # Get color for log level
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")

        # Build formatted message
        formatted = f"{color}[{timestamp}] {record.levelname:8s}{reset} "
        formatted += f"{record.name}: {record.getMessage()}"

        # Add request ID if available
        if has_request_context() and hasattr(g, "request_id"):
            formatted += f" [req:{g.request_id[:8]}]"

        # Add exception info if present
        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)

        return formatted


class RequestFilter(logging.Filter):
    """Filter to add request context to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request context to log record.

        Args:
            record: Log record to filter

        Returns:
            True to include the record
        """
        if has_request_context():
            record.request_id = getattr(g, "request_id", "no-request-id")
            record.method = request.method
            record.path = request.path
        else:
            record.request_id = "no-request-context"
            record.method = "N/A"
            record.path = "N/A"

        return True


class PerformanceLogger:
    """Context manager for performance logging."""

    def __init__(self, operation: str, logger: logging.Logger = None):
        """Initialize performance logger.

        Args:
            operation: Name of the operation being measured
            logger: Logger instance to use
        """
        self.operation = operation
        self.logger = logger or logging.getLogger(__name__)
        self.start_time = None

    def __enter__(self):
        """Start timing."""
        self.start_time = datetime.utcnow()
        self.logger.debug(f"Starting operation: {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timing and log performance."""
        if self.start_time:
            duration = (datetime.utcnow() - self.start_time).total_seconds() * 1000

            # Create log record with performance data
            record = logging.LogRecord(
                name=self.logger.name,
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg=f"Operation completed: {self.operation}",
                args=(),
                exc_info=None,
            )
            record.duration = duration

            self.logger.handle(record)


def setup_logging(app: Flask) -> None:
    """Setup comprehensive logging for the Flask application.

    Args:
        app: Flask application instance
    """
    # Get configuration
    log_level = getattr(logging, app.config.get("LOG_LEVEL", "INFO").upper())
    log_dir = Path(app.config.get("LOG_DIR", "logs"))
    log_file = app.config.get("LOG_FILE", "app.log")
    max_bytes = app.config.get("LOG_MAX_BYTES", 10 * 1024 * 1024)  # 10MB
    backup_count = app.config.get("LOG_BACKUP_COUNT", 5)

    # Create log directory
    log_dir.mkdir(exist_ok=True)

    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Set root logger level
    root_logger.setLevel(log_level)

    # Setup console handler for development
    if app.debug or app.config.get("FLASK_ENV") == "development":
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(ColoredConsoleFormatter())
        console_handler.addFilter(RequestFilter())
        root_logger.addHandler(console_handler)

    # Setup file handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)

    # Use structured logging for production
    if app.config.get("FLASK_ENV") == "production":
        file_handler.setFormatter(StructuredFormatter())
    else:
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)-8s %(name)s: %(message)s [%(filename)s:%(lineno)d]"
            )
        )

    file_handler.addFilter(RequestFilter())
    root_logger.addHandler(file_handler)

    # Setup error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / "error.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(StructuredFormatter())
    error_handler.addFilter(RequestFilter())
    root_logger.addHandler(error_handler)

    # Setup security log handler
    security_handler = logging.handlers.RotatingFileHandler(
        log_dir / "security.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    security_handler.setLevel(logging.WARNING)
    security_handler.setFormatter(StructuredFormatter())
    security_handler.addFilter(RequestFilter())

    # Create security logger
    security_logger = logging.getLogger("security")
    security_logger.addHandler(security_handler)
    security_logger.setLevel(logging.WARNING)

    # Configure third-party loggers
    _configure_third_party_loggers(app)

    # Setup Flask app logger
    app.logger.setLevel(log_level)

    app.logger.info(f"Logging configured - Level: {logging.getLevelName(log_level)}")


def _configure_third_party_loggers(app: Flask) -> None:
    """Configure third-party library loggers.

    Args:
        app: Flask application instance
    """
    # Suppress noisy loggers in production
    if not app.debug:
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("boto3").setLevel(logging.WARNING)
        logging.getLogger("botocore").setLevel(logging.WARNING)
        logging.getLogger("s3transfer").setLevel(logging.WARNING)

    # Set SQLAlchemy logging
    if app.config.get("SQLALCHEMY_ECHO"):
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    else:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance.

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_security_event(
    event_type: str,
    message: str,
    details: Dict[str, Any] = None,
    level: int = logging.WARNING,
) -> None:
    """Log security-related events.

    Args:
        event_type: Type of security event
        message: Event message
        details: Additional event details
        level: Log level
    """
    security_logger = logging.getLogger("security")

    # Build security context
    context = {
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    if has_request_context():
        context.update(
            {
                "request_id": getattr(g, "request_id", None),
                "remote_addr": request.remote_addr,
                "user_agent": request.headers.get("User-Agent"),
                "endpoint": request.endpoint,
            }
        )

    if details:
        context.update(details)

    # Create log record with security context
    record = logging.LogRecord(
        name=security_logger.name,
        level=level,
        pathname="",
        lineno=0,
        msg=message,
        args=(),
        exc_info=None,
    )
    record.context = context

    security_logger.handle(record)


def log_performance(func):
    """Decorator for logging function performance.

    Args:
        func: Function to wrap with performance logging

    Returns:
        Wrapped function with performance logging
    """
    import functools
    import time

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger = get_logger(f"performance.{func.__module__}.{func.__name__}")

        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            # Log successful execution
            logger.info(
                f"Function {func.__name__} completed successfully",
                extra={
                    "context": {
                        "function": func.__name__,
                        "module": func.__module__,
                        "duration_ms": round(duration * 1000, 2),
                        "status": "success",
                    }
                },
            )
            return result

        except Exception as e:
            duration = time.time() - start_time

            # Log failed execution
            logger.error(
                f"Function {func.__name__} failed: {str(e)}",
                extra={
                    "context": {
                        "function": func.__name__,
                        "module": func.__module__,
                        "duration_ms": round(duration * 1000, 2),
                        "status": "error",
                        "error": str(e),
                    }
                },
            )
            raise

    return wrapper


# Export public interface
__all__ = [
    "setup_logging",
    "get_logger",
    "log_security_event",
    "log_performance",
    "PerformanceLogger",
    "StructuredFormatter",
    "ColoredConsoleFormatter",
]
