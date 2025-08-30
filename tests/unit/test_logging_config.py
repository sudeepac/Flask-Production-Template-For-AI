"""Tests for app.utils.logging_config module."""

import json
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from flask import Flask

from app.utils.logging_config import (
    ColoredConsoleFormatter,
    PerformanceLogger,
    RequestFilter,
    StructuredFormatter,
    get_logger,
    log_performance,
    log_security_event,
    setup_logging,
)


class TestStructuredFormatter:
    """Test StructuredFormatter class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.formatter = StructuredFormatter()
        self.record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        self.record.module = "test_module"
        self.record.funcName = "test_function"

    def test_format_basic_record(self):
        """Test formatting basic log record."""
        result = self.formatter.format(self.record)
        data = json.loads(result)

        assert data["level"] == "INFO"
        assert data["logger"] == "test.logger"
        assert data["message"] == "Test message"
        assert data["module"] == "test_module"
        assert data["function"] == "test_function"
        assert data["line"] == 42
        assert "timestamp" in data

    def test_format_with_request_context(self):
        """Test formatting with Flask request context."""
        app = Flask(__name__)
        with app.test_request_context(
            "/api/test",
            method="POST",
            environ_base={"REMOTE_ADDR": "127.0.0.1"},
            headers={"User-Agent": "test-agent"},
        ):
            from flask import g

            g.request_id = "test-request-123"

            result = self.formatter.format(self.record)
            data = json.loads(result)

            assert data["request_id"] == "test-request-123"
            assert data["method"] == "POST"
            assert data["path"] == "/api/test"
            assert data["remote_addr"] == "127.0.0.1"
            assert data["user_agent"] == "test-agent"

    def test_format_with_context(self):
        """Test formatting with additional context."""
        self.record.context = {"user_id": 123, "action": "login"}

        result = self.formatter.format(self.record)
        data = json.loads(result)

        assert data["context"] == {"user_id": 123, "action": "login"}

    def test_format_with_exception(self):
        """Test formatting with exception info."""
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            self.record.exc_info = sys.exc_info()

        result = self.formatter.format(self.record)
        data = json.loads(result)

        assert "exception" in data
        assert data["exception"]["type"] == "ValueError"
        assert data["exception"]["message"] == "Test error"
        assert "traceback" in data["exception"]

    def test_format_with_performance(self):
        """Test formatting with performance metrics."""
        self.record.duration = 123.45

        result = self.formatter.format(self.record)
        data = json.loads(result)

        assert data["performance"] == {"duration_ms": 123.45}


class TestColoredConsoleFormatter:
    """Test ColoredConsoleFormatter class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.formatter = ColoredConsoleFormatter()
        self.record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        self.record.created = datetime.now().timestamp()

    def test_format_basic_record(self):
        """Test formatting basic log record with colors."""
        result = self.formatter.format(self.record)

        assert "\033[32m" in result  # Green color for INFO
        assert "\033[0m" in result  # Reset color
        assert "INFO" in result
        assert "test.logger" in result
        assert "Test message" in result

    def test_format_with_request_id(self):
        """Test formatting with request ID."""
        app = Flask(__name__)
        with app.test_request_context():
            from flask import g

            g.request_id = "test-request-123456789"

            result = self.formatter.format(self.record)

            assert "[req:test-req" in result  # First 8 chars of request ID

    def test_format_with_exception(self):
        """Test formatting with exception info."""
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            self.record.exc_info = sys.exc_info()

        result = self.formatter.format(self.record)

        assert "ValueError" in result
        assert "Test error" in result

    def test_color_codes(self):
        """Test different log level colors."""
        levels = [
            (logging.DEBUG, "\033[36m"),  # Cyan
            (logging.INFO, "\033[32m"),  # Green
            (logging.WARNING, "\033[33m"),  # Yellow
            (logging.ERROR, "\033[31m"),  # Red
            (logging.CRITICAL, "\033[35m"),  # Magenta
        ]

        for level, color in levels:
            record = logging.LogRecord(
                name="test",
                level=level,
                pathname="",
                lineno=0,
                msg="test",
                args=(),
                exc_info=None,
            )
            record.created = datetime.now().timestamp()
            result = self.formatter.format(record)
            assert color in result


class TestRequestFilter:
    """Test RequestFilter class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.filter = RequestFilter()
        self.record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None,
        )

    def test_filter_with_request_context(self):
        """Test filter with Flask request context."""
        app = Flask(__name__)
        with app.test_request_context("/api/test", method="GET"):
            from flask import g

            g.request_id = "test-request-123"

            result = self.filter.filter(self.record)

            assert result is True
            assert self.record.request_id == "test-request-123"
            assert self.record.method == "GET"
            assert self.record.path == "/api/test"

    def test_filter_without_request_context(self):
        """Test filter without Flask request context."""
        # No Flask context - should use fallback values
        result = self.filter.filter(self.record)

        assert result is True
        assert self.record.request_id == "no-request-context"
        assert self.record.method == "N/A"
        assert self.record.path == "N/A"

    def test_filter_with_missing_request_id(self):
        """Test filter when request_id is missing from g."""
        app = Flask(__name__)
        with app.test_request_context("/api/test", method="POST"):
            # Don't set g.request_id - should use fallback
            result = self.filter.filter(self.record)

            assert result is True
            assert self.record.request_id == "no-request-id"


class TestPerformanceLogger:
    """Test PerformanceLogger class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_logger = Mock()

    def test_performance_logger_context_manager(self):
        """Test PerformanceLogger as context manager."""
        with PerformanceLogger("test_operation", self.mock_logger):
            pass

        # Check that debug and handle were called
        self.mock_logger.debug.assert_called_once_with(
            "Starting operation: test_operation"
        )
        self.mock_logger.handle.assert_called_once()

        # Check the log record passed to handle
        call_args = self.mock_logger.handle.call_args[0][0]
        assert call_args.msg == "Operation completed: test_operation"
        assert hasattr(call_args, "duration")
        assert call_args.duration >= 0

    def test_performance_logger_with_exception(self):
        """Test PerformanceLogger when exception occurs."""
        try:
            with PerformanceLogger("test_operation", self.mock_logger):
                raise ValueError("Test error")
        except ValueError:
            pass

        # Should still log performance even with exception
        self.mock_logger.debug.assert_called_once()
        self.mock_logger.handle.assert_called_once()

    def test_performance_logger_default_logger(self):
        """Test PerformanceLogger with default logger."""
        with patch("app.utils.logging_config.logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            with PerformanceLogger("test_operation"):
                pass

            mock_logger.debug.assert_called_once()
            mock_logger.handle.assert_called_once()


class TestSetupLogging:
    """Test setup_logging function."""

    @patch("app.utils.logging_config.logging.handlers.RotatingFileHandler")
    @patch("app.utils.logging_config.logging.StreamHandler")
    @patch("app.utils.logging_config.logging.getLogger")
    def test_setup_logging_development(
        self, mock_get_logger, mock_stream_handler, mock_file_handler
    ):
        """Test logging setup for development environment."""
        app = Flask(__name__)
        app.config.update(
            {
                "FLASK_ENV": "development",
                "LOG_LEVEL": "DEBUG",
                "LOG_DIR": "test_logs",
                "LOG_FILE": "test.log",
            }
        )
        app.debug = True

        mock_root_logger = Mock()
        mock_root_logger.handlers = []  # Mock handlers as empty list
        mock_root_logger.getEffectiveLevel.return_value = logging.DEBUG
        mock_root_logger.parent = None  # No parent logger
        mock_get_logger.return_value = mock_root_logger

        with tempfile.TemporaryDirectory() as temp_dir:
            app.config["LOG_DIR"] = temp_dir
            setup_logging(app)

            # Verify logger configuration calls
            mock_root_logger.setLevel.assert_called()
            mock_root_logger.addHandler.assert_called()

    @patch("app.utils.logging_config.logging.handlers.RotatingFileHandler")
    @patch("app.utils.logging_config.logging.getLogger")
    def test_setup_logging_production(self, mock_get_logger, mock_file_handler):
        """Test logging setup for production environment."""
        app = Flask(__name__)
        app.config.update(
            {
                "FLASK_ENV": "production",
                "LOG_LEVEL": "INFO",
                "LOG_DIR": "prod_logs",
                "LOG_FILE": "prod.log",
            }
        )
        app.debug = False

        mock_root_logger = Mock()
        mock_root_logger.handlers = []  # Mock handlers as empty list
        mock_root_logger.getEffectiveLevel.return_value = logging.INFO
        mock_root_logger.parent = None  # No parent logger
        mock_get_logger.return_value = mock_root_logger

        with tempfile.TemporaryDirectory() as temp_dir:
            app.config["LOG_DIR"] = temp_dir
            setup_logging(app)

            # Verify production-specific configuration
            mock_root_logger.setLevel.assert_called()
            mock_root_logger.addHandler.assert_called()


class TestUtilityFunctions:
    """Test utility functions."""

    def test_get_logger(self):
        """Test get_logger function."""
        with patch("app.utils.logging_config.logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            result = get_logger("test.logger")

            mock_get_logger.assert_called_once_with("test.logger")
            assert result == mock_logger

    @patch("logging.getLogger")
    def test_log_security_event(self, mock_get_logger):
        """Test log_security_event function."""
        app = Flask(__name__)
        with app.test_request_context(
            "/",
            environ_base={"REMOTE_ADDR": "127.0.0.1"},
            headers={"User-Agent": "test-agent"},
        ):
            from flask import g

            g.request_id = "test-request-123"

            mock_security_logger = Mock()
            mock_get_logger.return_value = mock_security_logger

            log_security_event(
                "login_attempt", "User login attempt", {"user_id": 123}, logging.ERROR
            )

            mock_get_logger.assert_called_once_with("security")
            mock_security_logger.handle.assert_called_once()

            # Check the log record
            call_args = mock_security_logger.handle.call_args[0][0]
            assert call_args.msg == "User login attempt"
            assert call_args.levelno == logging.ERROR
            assert hasattr(call_args, "context")
            assert call_args.context["event_type"] == "login_attempt"
            assert call_args.context["user_id"] == 123

    def test_log_performance_decorator_success(self):
        """Test log_performance decorator with successful function."""
        with patch("app.utils.logging_config.get_logger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            @log_performance
            def test_function(x, y):
                return x + y

            result = test_function(2, 3)

            assert result == 5
            mock_logger.info.assert_called_once()

            # Check the log call
            call_args = mock_logger.info.call_args
            assert "test_function completed successfully" in call_args[0][0]
            assert "context" in call_args[1]["extra"]
            assert call_args[1]["extra"]["context"]["status"] == "success"

    def test_log_performance_decorator_error(self):
        """Test log_performance decorator with function that raises exception."""
        with patch("app.utils.logging_config.get_logger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            @log_performance
            def test_function():
                raise ValueError("Test error")

            with pytest.raises(ValueError, match="Test error"):
                test_function()

            mock_logger.error.assert_called_once()

            # Check the log call
            call_args = mock_logger.error.call_args
            assert "test_function failed" in call_args[0][0]
            assert "context" in call_args[1]["extra"]
            assert call_args[1]["extra"]["context"]["status"] == "error"
            assert call_args[1]["extra"]["context"]["error"] == "Test error"
