"""Unit tests for app.blueprints.health.routes module.

This module tests all health check endpoints including basic health,
detailed health, readiness probe, and liveness probe functionality.
"""

from unittest.mock import Mock, patch

from flask import Flask
from sqlalchemy.exc import SQLAlchemyError

from app.blueprints.health.routes import (
    _check_database,
    _get_system_info,
    detailed_health_check,
    health_check,
    liveness_probe,
    readiness_probe,
)


class TestHealthCheck:
    """Test basic health check functionality."""

    @patch("app.blueprints.health.routes.get_utc_timestamp")
    @patch("app.blueprints.health.routes.success_response")
    def test_health_check_success(self, mock_success_response, mock_get_timestamp):
        """Test successful basic health check."""
        # Mock dependencies
        mock_get_timestamp.return_value = "2023-12-01T10:30:45.123456Z"
        mock_success_response.return_value = ({"status": "success"}, 200)

        app = Flask(__name__)
        app.version = "1.2.3"

        with app.app_context():
            result = health_check()

        # Verify timestamp function was called
        mock_get_timestamp.assert_called_once_with(with_z_suffix=True)

        # Verify success_response was called with correct data
        mock_success_response.assert_called_once()
        call_args = mock_success_response.call_args

        expected_data = {
            "status": "healthy",
            "timestamp": "2023-12-01T10:30:45.123456Z",
            "version": "1.2.3",
        }

        assert call_args[1]["data"] == expected_data
        assert call_args[1]["message"] == "Application is healthy"
        assert result == ({"status": "success"}, 200)

    @patch("app.blueprints.health.routes.get_utc_timestamp")
    @patch("app.blueprints.health.routes.success_response")
    def test_health_check_default_version(
        self, mock_success_response, mock_get_timestamp
    ):
        """Test health check with default version when app.version is not set."""
        # Mock dependencies
        mock_get_timestamp.return_value = "2023-12-01T10:30:45.123456Z"
        mock_success_response.return_value = ({"status": "success"}, 200)

        app = Flask(__name__)
        # Don't set app.version to test default

        with app.app_context():
            result = health_check()

        # Verify success_response was called with default version
        call_args = mock_success_response.call_args
        assert call_args[1]["data"]["version"] == "1.0.0"


class TestDetailedHealthCheck:
    """Test detailed health check functionality."""

    @patch("app.blueprints.health.routes._get_system_info")
    @patch("app.blueprints.health.routes._check_database")
    @patch("app.blueprints.health.routes.get_utc_timestamp")
    @patch("app.blueprints.health.routes.success_response")
    def test_detailed_health_check_healthy(
        self, mock_success_response, mock_get_timestamp, mock_check_db, mock_get_system
    ):
        """Test detailed health check when all systems are healthy."""
        # Mock dependencies
        mock_get_timestamp.return_value = "2023-12-01T10:30:45.123456Z"
        mock_check_db.return_value = {"status": "connected", "response_time_ms": 5.2}
        mock_get_system.return_value = {
            "cpu_percent": 25.5,
            "memory_percent": 45.2,
            "disk_percent": 60.1,
        }
        mock_success_response.return_value = ({"status": "success"}, 200)

        app = Flask(__name__)
        app.version = "1.2.3"

        with app.app_context():
            result = detailed_health_check()

        # Verify all helper functions were called
        mock_get_timestamp.assert_called_once_with(with_z_suffix=True)
        mock_check_db.assert_called_once()
        mock_get_system.assert_called_once()

        # Verify success_response was called with correct data
        call_args = mock_success_response.call_args
        expected_data = {
            "status": "healthy",
            "timestamp": "2023-12-01T10:30:45.123456Z",
            "version": "1.2.3",
            "database": {"status": "connected", "response_time_ms": 5.2},
            "system": {
                "cpu_percent": 25.5,
                "memory_percent": 45.2,
                "disk_percent": 60.1,
            },
        }

        assert call_args[1]["data"] == expected_data
        assert call_args[1]["message"] == "Service is healthy"

    @patch("app.blueprints.health.routes._get_system_info")
    @patch("app.blueprints.health.routes._check_database")
    @patch("app.blueprints.health.routes.get_utc_timestamp")
    @patch("app.blueprints.health.routes.error_response")
    def test_detailed_health_check_unhealthy_database(
        self, mock_error_response, mock_get_timestamp, mock_check_db, mock_get_system
    ):
        """Test detailed health check when database is unhealthy."""
        # Mock dependencies
        mock_get_timestamp.return_value = "2023-12-01T10:30:45.123456Z"
        mock_check_db.return_value = {
            "status": "disconnected",
            "error": "Connection failed",
        }
        mock_get_system.return_value = {
            "cpu_percent": 25.5,
            "memory_percent": 45.2,
            "disk_percent": 60.1,
        }
        mock_error_response.return_value = ({"status": "error"}, 503)

        app = Flask(__name__)

        with app.app_context():
            result = detailed_health_check()

        # Verify error_response was called
        call_args = mock_error_response.call_args
        assert call_args[1]["message"] == "Service unhealthy"
        assert call_args[1]["status_code"] == 503
        assert call_args[1]["data"]["status"] == "unhealthy"
        assert call_args[1]["data"]["database"]["status"] == "disconnected"


class TestReadinessProbe:
    """Test Kubernetes readiness probe functionality."""

    @patch("app.blueprints.health.routes._check_database")
    @patch("app.blueprints.health.routes.datetime")
    @patch("app.blueprints.health.routes.success_response")
    def test_readiness_probe_ready(
        self, mock_success_response, mock_datetime, mock_check_db
    ):
        """Test readiness probe when application is ready."""
        # Mock dependencies
        mock_datetime.utcnow.return_value.isoformat.return_value = (
            "2023-12-01T10:30:45.123456"
        )
        mock_check_db.return_value = {"status": "connected"}
        mock_success_response.return_value = ({"status": "success"}, 200)

        result = readiness_probe()

        # Verify success_response was called
        call_args = mock_success_response.call_args
        expected_data = {"status": "ready", "timestamp": "2023-12-01T10:30:45.123456Z"}

        assert call_args[1]["data"] == expected_data
        assert call_args[1]["message"] == "Application is ready"

    @patch("app.blueprints.health.routes._check_database")
    @patch("app.blueprints.health.routes.datetime")
    @patch("app.blueprints.health.routes.error_response")
    def test_readiness_probe_not_ready_database(
        self, mock_error_response, mock_datetime, mock_check_db
    ):
        """Test readiness probe when database is not available."""
        # Mock dependencies
        mock_datetime.utcnow.return_value.isoformat.return_value = (
            "2023-12-01T10:30:45.123456"
        )
        mock_check_db.return_value = {"status": "disconnected"}
        mock_error_response.return_value = ({"status": "error"}, 503)

        result = readiness_probe()

        # Verify error_response was called
        call_args = mock_error_response.call_args
        expected_data = {
            "status": "not_ready",
            "reason": "database_unavailable",
            "timestamp": "2023-12-01T10:30:45.123456Z",
        }

        assert call_args[1]["data"] == expected_data
        assert call_args[1]["message"] == "Application not ready"
        assert call_args[1]["status_code"] == 503

    @patch("app.blueprints.health.routes._check_database")
    @patch("app.blueprints.health.routes.datetime")
    @patch("app.blueprints.health.routes.error_response")
    def test_readiness_probe_exception(
        self, mock_error_response, mock_datetime, mock_check_db
    ):
        """Test readiness probe when an exception occurs."""
        # Mock dependencies
        mock_datetime.utcnow.return_value.isoformat.return_value = (
            "2023-12-01T10:30:45.123456"
        )
        mock_check_db.side_effect = Exception("Database connection error")
        mock_error_response.return_value = ({"status": "error"}, 503)

        result = readiness_probe()

        # Verify error_response was called with exception details
        call_args = mock_error_response.call_args
        expected_data = {
            "status": "not_ready",
            "reason": "Database connection error",
            "timestamp": "2023-12-01T10:30:45.123456Z",
        }

        assert call_args[1]["data"] == expected_data
        assert call_args[1]["message"] == "Application not ready"
        assert call_args[1]["status_code"] == 503


class TestLivenessProbe:
    """Test Kubernetes liveness probe functionality."""

    @patch("app.blueprints.health.routes.datetime")
    @patch("app.blueprints.health.routes.success_response")
    def test_liveness_probe_success(self, mock_success_response, mock_datetime):
        """Test successful liveness probe."""
        # Mock dependencies
        mock_datetime.utcnow.return_value.isoformat.return_value = (
            "2023-12-01T10:30:45.123456"
        )
        mock_success_response.return_value = ({"status": "success"}, 200)

        result = liveness_probe()

        # Verify success_response was called
        call_args = mock_success_response.call_args
        expected_data = {"status": "alive", "timestamp": "2023-12-01T10:30:45.123456Z"}

        assert call_args[1]["data"] == expected_data
        assert call_args[1]["message"] == "Application is alive"


class TestCheckDatabase:
    """Test database connectivity check functionality."""

    @patch("app.blueprints.health.routes.db")
    @patch("app.blueprints.health.routes.time")
    @patch("app.blueprints.health.routes.text")
    def test_check_database_success(self, mock_text, mock_time, mock_db):
        """Test successful database connectivity check."""
        # Mock dependencies
        mock_time.time.side_effect = [1000.0, 1000.005]  # 5ms difference
        mock_connection = Mock()
        mock_db.engine.connect.return_value.__enter__.return_value = mock_connection
        mock_text.return_value = "SELECT 1"

        result = _check_database()

        # Verify database query was executed
        mock_connection.execute.assert_called_once_with("SELECT 1")

        # Verify result
        expected_result = {"status": "connected", "response_time_ms": 5.0}
        assert result == expected_result

    @patch("app.blueprints.health.routes.db")
    @patch("app.blueprints.health.routes.time")
    def test_check_database_connection_error(self, mock_time, mock_db):
        """Test database connectivity check with connection error."""
        # Mock dependencies
        mock_time.time.return_value = 1000.0
        mock_db.engine.connect.side_effect = SQLAlchemyError("Connection failed")

        result = _check_database()

        # Verify error result
        expected_result = {"status": "disconnected", "error": "Connection failed"}
        assert result == expected_result

    @patch("app.blueprints.health.routes.db")
    @patch("app.blueprints.health.routes.time")
    @patch("app.blueprints.health.routes.text")
    def test_check_database_query_error(self, mock_text, mock_time, mock_db):
        """Test database connectivity check with query execution error."""
        # Mock dependencies
        mock_time.time.return_value = 1000.0
        mock_connection = Mock()
        mock_connection.execute.side_effect = SQLAlchemyError("Query failed")
        mock_db.engine.connect.return_value.__enter__.return_value = mock_connection
        mock_text.return_value = "SELECT 1"

        result = _check_database()

        # Verify error result
        expected_result = {"status": "disconnected", "error": "Query failed"}
        assert result == expected_result

    @patch("app.blueprints.health.routes.db")
    @patch("app.blueprints.health.routes.time")
    @patch("app.blueprints.health.routes.text")
    def test_check_database_response_time_calculation(
        self, mock_text, mock_time, mock_db
    ):
        """Test database response time calculation accuracy."""
        # Mock dependencies - 123.456ms response time
        mock_time.time.side_effect = [1000.0, 1000.123456]
        mock_connection = Mock()
        mock_db.engine.connect.return_value.__enter__.return_value = mock_connection
        mock_text.return_value = "SELECT 1"

        result = _check_database()

        # Verify response time is correctly calculated and rounded
        assert result["response_time_ms"] == 123.46
        assert result["status"] == "connected"


class TestGetSystemInfo:
    """Test system information retrieval functionality."""

    @patch("app.blueprints.health.routes.psutil")
    def test_get_system_info_success(self, mock_psutil):
        """Test successful system information retrieval."""
        # Mock psutil functions
        mock_psutil.cpu_percent.return_value = 25.543
        mock_psutil.virtual_memory.return_value.percent = 45.234
        mock_psutil.disk_usage.return_value.percent = 60.123

        result = _get_system_info()

        # Verify psutil functions were called correctly
        mock_psutil.cpu_percent.assert_called_once_with(interval=1)
        mock_psutil.virtual_memory.assert_called_once()
        mock_psutil.disk_usage.assert_called_once_with("/")

        # Verify result with proper rounding
        expected_result = {
            "cpu_percent": 25.5,
            "memory_percent": 45.2,
            "disk_percent": 60.1,
        }
        assert result == expected_result

    @patch("app.blueprints.health.routes.psutil")
    def test_get_system_info_cpu_error(self, mock_psutil):
        """Test system information retrieval with CPU error."""
        # Mock psutil functions with CPU error
        mock_psutil.cpu_percent.side_effect = Exception("CPU error")
        mock_psutil.virtual_memory.return_value.percent = 45.234
        mock_psutil.disk_usage.return_value.percent = 60.123

        result = _get_system_info()

        # Verify error result
        expected_result = {
            "cpu_percent": "unavailable",
            "memory_percent": "unavailable",
            "disk_percent": "unavailable",
        }
        assert result == expected_result

    @patch("app.blueprints.health.routes.psutil")
    def test_get_system_info_memory_error(self, mock_psutil):
        """Test system information retrieval with memory error."""
        # Mock psutil functions with memory error
        mock_psutil.cpu_percent.return_value = 25.543
        mock_psutil.virtual_memory.side_effect = Exception("Memory error")
        mock_psutil.disk_usage.return_value.percent = 60.123

        result = _get_system_info()

        # Verify error result
        expected_result = {
            "cpu_percent": "unavailable",
            "memory_percent": "unavailable",
            "disk_percent": "unavailable",
        }
        assert result == expected_result

    @patch("app.blueprints.health.routes.psutil")
    def test_get_system_info_disk_error(self, mock_psutil):
        """Test system information retrieval with disk error."""
        # Mock psutil functions with disk error
        mock_psutil.cpu_percent.return_value = 25.543
        mock_psutil.virtual_memory.return_value.percent = 45.234
        mock_psutil.disk_usage.side_effect = Exception("Disk error")

        result = _get_system_info()

        # Verify error result
        expected_result = {
            "cpu_percent": "unavailable",
            "memory_percent": "unavailable",
            "disk_percent": "unavailable",
        }
        assert result == expected_result

    @patch("app.blueprints.health.routes.psutil")
    def test_get_system_info_rounding_precision(self, mock_psutil):
        """Test system information rounding precision."""
        # Mock psutil functions with high precision values
        mock_psutil.cpu_percent.return_value = 25.56789
        mock_psutil.virtual_memory.return_value.percent = 45.23456
        mock_psutil.disk_usage.return_value.percent = 60.12345

        result = _get_system_info()

        # Verify proper rounding to 1 decimal place
        expected_result = {
            "cpu_percent": 25.6,
            "memory_percent": 45.2,
            "disk_percent": 60.1,
        }
        assert result == expected_result


class TestHealthRoutesIntegration:
    """Test integration scenarios for health routes."""

    @patch("app.blueprints.health.routes.psutil")
    @patch("app.blueprints.health.routes.db")
    @patch("app.blueprints.health.routes.time")
    @patch("app.blueprints.health.routes.text")
    def test_detailed_health_integration(
        self, mock_text, mock_time, mock_db, mock_psutil
    ):
        """Test detailed health check integration with all components."""
        # Mock all dependencies for successful health check
        mock_time.time.side_effect = [1000.0, 1000.010]  # 10ms response
        mock_connection = Mock()
        mock_db.engine.connect.return_value.__enter__.return_value = mock_connection
        mock_text.return_value = "SELECT 1"

        mock_psutil.cpu_percent.return_value = 15.5
        mock_psutil.virtual_memory.return_value.percent = 35.2
        mock_psutil.disk_usage.return_value.percent = 50.8

        # Test the actual integration
        db_result = _check_database()
        system_result = _get_system_info()

        # Verify database check
        assert db_result["status"] == "connected"
        assert db_result["response_time_ms"] == 10.0

        # Verify system info
        assert system_result["cpu_percent"] == 15.5
        assert system_result["memory_percent"] == 35.2
        assert system_result["disk_percent"] == 50.8

    def test_health_routes_error_handling_consistency(self):
        """Test that all health routes handle errors consistently."""
        # This test verifies that error handling patterns are consistent
        # across all health check endpoints

        # Test database check error handling
        with patch("app.blueprints.health.routes.db") as mock_db:
            mock_db.engine.connect.side_effect = Exception("Test error")
            result = _check_database()
            assert result["status"] == "disconnected"
            assert "error" in result

        # Test system info error handling
        with patch("app.blueprints.health.routes.psutil") as mock_psutil:
            mock_psutil.cpu_percent.side_effect = Exception("Test error")
            result = _get_system_info()
            assert result["cpu_percent"] == "unavailable"
            assert result["memory_percent"] == "unavailable"
            assert result["disk_percent"] == "unavailable"
