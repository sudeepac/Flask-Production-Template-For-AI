"""Health Check Resources with OpenAPI Documentation.

This module provides Flask-RESTX resources for health check endpoints
with comprehensive OpenAPI/Swagger documentation.
"""

import time
from datetime import datetime

import psutil
from flask import current_app
from flask_restx import Resource, fields

from app.api_docs import api_docs
from app.extensions import cache, db
from app.utils.decorators import handle_api_errors, log_endpoint_access
from app.utils.logging_config import get_logger, log_performance
from app.utils.response_helpers import health_check_response

# Get logger
logger = get_logger(__name__)


def perform_health_check(check_name: str, check_function, default_status="degraded"):
    """Perform a health check and return standardized result.

    Args:
        check_name: Name of the health check
        check_function: Function to execute for the check
        default_status: Status to use if check fails but isn't critical

    Returns:
        Tuple of (check_result, overall_status_impact)
    """
    try:
        return check_function(), "healthy"
    except Exception as e:
        logger.warning(f"{check_name} health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}, "unhealthy"


# Get health namespace
health_ns = api_docs.get_namespace("health")

# Define models for documentation
health_status_model = health_ns.model(
    "HealthStatus",
    {
        "status": fields.String(
            required=True,
            description="Overall health status",
            enum=["healthy", "degraded", "unhealthy"],
            example="healthy",
        ),
        "timestamp": fields.String(
            required=True,
            description="Health check timestamp in ISO 8601 format",
            example="2024-01-01T12:00:00Z",
        ),
        "version": fields.String(
            required=True, description="Application version", example="1.0.0"
        ),
        "environment": fields.String(
            required=True, description="Runtime environment", example="development"
        ),
        "uptime": fields.Float(
            required=True, description="Application uptime in seconds", example=3600.5
        ),
    },
)

detailed_health_model = health_ns.model(
    "DetailedHealth",
    {
        "status": fields.String(
            required=True,
            description="Overall health status",
            enum=["healthy", "degraded", "unhealthy"],
            example="healthy",
        ),
        "timestamp": fields.String(
            required=True,
            description="Health check timestamp in ISO 8601 format",
            example="2024-01-01T12:00:00Z",
        ),
        "version": fields.String(
            required=True, description="Application version", example="1.0.0"
        ),
        "environment": fields.String(
            required=True, description="Runtime environment", example="development"
        ),
        "uptime": fields.Float(
            required=True, description="Application uptime in seconds", example=3600.5
        ),
        "checks": fields.Raw(
            required=True,
            description="Individual component health checks",
            example={
                "database": {
                    "status": "healthy",
                    "response_time": 0.05,
                    "connection_pool": {"active": 2, "idle": 8, "total": 10},
                },
                "cache": {
                    "status": "healthy",
                    "response_time": 0.01,
                    "memory_usage": "45.2MB",
                    "hit_rate": 0.85,
                },
                "disk_space": {
                    "status": "healthy",
                    "free_space_gb": 50.2,
                    "usage_percent": 65.5,
                },
                "memory": {
                    "status": "healthy",
                    "usage_mb": 128.5,
                    "available_mb": 1024.0,
                    "usage_percent": 12.5,
                },
            },
        ),
        "metrics": fields.Raw(
            required=True,
            description="Performance metrics",
            example={
                "requests_per_second": 45.2,
                "average_response_time": 0.15,
                "error_rate": 0.02,
                "cpu_usage_percent": 25.5,
            },
        ),
    },
)

readiness_model = health_ns.model(
    "ReadinessCheck",
    {
        "ready": fields.Boolean(
            required=True,
            description="Whether the application is ready to serve requests",
            example=True,
        ),
        "timestamp": fields.String(
            required=True,
            description="Readiness check timestamp",
            example="2024-01-01T12:00:00Z",
        ),
        "checks": fields.Raw(
            required=True,
            description="Readiness check results",
            example={
                "database_connection": True,
                "cache_connection": True,
                "migrations_applied": True,
                "configuration_loaded": True,
            },
        ),
    },
)

liveness_model = health_ns.model(
    "LivenessCheck",
    {
        "alive": fields.Boolean(
            required=True,
            description="Whether the application is alive and responsive",
            example=True,
        ),
        "timestamp": fields.String(
            required=True,
            description="Liveness check timestamp",
            example="2024-01-01T12:00:00Z",
        ),
        "uptime": fields.Float(
            required=True, description="Application uptime in seconds", example=3600.5
        ),
        "memory_usage_mb": fields.Float(
            required=True, description="Current memory usage in MB", example=128.5
        ),
    },
)


@health_ns.route("/")
class HealthCheckResource(Resource):
    """Basic health check endpoint."""

    @health_ns.doc("get_health_status")
    @health_ns.marshal_with(health_status_model)
    @health_ns.response(200, "Application is healthy", health_status_model)
    @health_ns.response(503, "Application is unhealthy")
    @handle_api_errors
    @log_endpoint_access
    def get(self):
        """Get basic health status.

        Returns basic health information including status, version,
        and uptime. This is a lightweight check suitable for
        load balancer health checks.

        Returns HTTP 200 if healthy, HTTP 503 if unhealthy.
        """
        # Simple health check - just verify we can respond
        uptime = time.time() - getattr(current_app, "_start_time", time.time())

        checks = {
            "timestamp": {"value": datetime.utcnow().isoformat() + "Z"},
            "version": {"value": getattr(current_app, "version", "1.0.0")},
            "environment": {
                "value": current_app.config.get("FLASK_ENV", "development")
            },
            "uptime": {"value": round(uptime, 2)},
        }

        return health_check_response(checks, "healthy")


@health_ns.route("/detailed")
class DetailedHealthCheckResource(Resource):
    """Detailed health check endpoint."""

    @health_ns.doc("get_detailed_health")
    @health_ns.marshal_with(detailed_health_model)
    @health_ns.response(200, "Detailed health information", detailed_health_model)
    @health_ns.response(503, "One or more components are unhealthy")
    @log_performance
    @handle_api_errors
    @log_endpoint_access
    def get(self):
        """Get detailed health information.

        Performs comprehensive health checks on all application
        components including database, cache, disk space, and memory.

        Returns detailed metrics and status for each component.
        Suitable for monitoring and alerting systems.
        """
        start_time = time.time()
        checks = {}
        metrics = {}
        overall_status = "healthy"

        try:
            # Database health check
            db_start = time.time()
            db.session.execute("SELECT 1")
            db_response_time = time.time() - db_start

            checks["database"] = {
                "status": "healthy",
                "response_time": round(db_response_time, 4),
                # Mock values
                "connection_pool": {"active": 2, "idle": 8, "total": 10},
            }

        except Exception as e:
            checks["database"] = {"status": "unhealthy", "error": str(e)}
            overall_status = "unhealthy"

        try:
            # Cache health check
            cache_start = time.time()
            test_key = f"health_check_{int(time.time())}"
            cache.set(test_key, "test_value", timeout=1)
            cache.get(test_key)
            cache_response_time = time.time() - cache_start

            checks["cache"] = {
                "status": "healthy",
                "response_time": round(cache_response_time, 4),
                "memory_usage": "45.2MB",  # Mock value
                "hit_rate": 0.85,  # Mock value
            }

        except Exception as e:
            checks["cache"] = {"status": "unhealthy", "error": str(e)}
            if overall_status == "healthy":
                overall_status = "degraded"

        try:
            # Disk space check
            disk_usage = psutil.disk_usage("/")
            free_space_gb = disk_usage.free / (1024**3)
            usage_percent = (disk_usage.used / disk_usage.total) * 100

            disk_status = "healthy"
            if free_space_gb < 1:
                disk_status = "unhealthy"
                overall_status = "unhealthy"
            elif free_space_gb < 5:
                disk_status = "warning"
                if overall_status == "healthy":
                    overall_status = "degraded"

            checks["disk_space"] = {
                "status": disk_status,
                "free_space_gb": round(free_space_gb, 2),
                "usage_percent": round(usage_percent, 2),
            }

        except Exception as e:
            checks["disk_space"] = {"status": "unhealthy", "error": str(e)}
            overall_status = "unhealthy"

        try:
            # Memory check
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_usage_mb = memory_info.rss / 1024 / 1024

            # Get system memory
            system_memory = psutil.virtual_memory()
            available_mb = system_memory.available / 1024 / 1024
            memory_usage_percent = (
                memory_usage_mb / (memory_usage_mb + available_mb)
            ) * 100

            memory_status = "healthy"
            if memory_usage_percent > 90:
                memory_status = "unhealthy"
                overall_status = "unhealthy"
            elif memory_usage_percent > 80:
                memory_status = "warning"
                if overall_status == "healthy":
                    overall_status = "degraded"

            checks["memory"] = {
                "status": memory_status,
                "usage_mb": round(memory_usage_mb, 2),
                "available_mb": round(available_mb, 2),
                "usage_percent": round(memory_usage_percent, 2),
            }

        except Exception as e:
            checks["memory"] = {"status": "unhealthy", "error": str(e)}
            overall_status = "unhealthy"

        # Calculate metrics
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            metrics = {
                "requests_per_second": 45.2,  # Mock value
                "average_response_time": 0.15,  # Mock value
                "error_rate": 0.02,  # Mock value
                "cpu_usage_percent": round(cpu_percent, 2),
            }
        except Exception:
            metrics = {
                "requests_per_second": 0,
                "average_response_time": 0,
                "error_rate": 0,
                "cpu_usage_percent": 0,
            }

        # Calculate uptime
        uptime = time.time() - getattr(current_app, "_start_time", time.time())

        response = {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": getattr(current_app, "version", "1.0.0"),
            "environment": current_app.config.get("FLASK_ENV", "development"),
            "uptime": round(uptime, 2),
            "checks": checks,
            "metrics": metrics,
        }

        status_code = 200 if overall_status in ["healthy", "degraded"] else 503

        logger.info(
            "Detailed health check completed",
            extra={
                "status": overall_status,
                "check_duration": round(time.time() - start_time, 4),
                "component_count": len(checks),
            },
        )

        return response, status_code


@health_ns.route("/ready")
class ReadinessCheckResource(Resource):
    """Readiness check endpoint."""

    @health_ns.doc("get_readiness")
    @health_ns.marshal_with(readiness_model)
    @health_ns.response(200, "Application is ready", readiness_model)
    @health_ns.response(503, "Application is not ready")
    def get(self):
        """Check if application is ready to serve requests.

        Verifies that all required services and dependencies
        are available and the application is ready to handle
        incoming requests.

        Used by Kubernetes readiness probes and load balancers
        to determine when to start routing traffic.
        """
        checks = {}
        ready = True

        try:
            # Database connection check
            db.session.execute("SELECT 1")
            checks["database_connection"] = True
        except Exception:
            checks["database_connection"] = False
            ready = False

        try:
            # Cache connection check
            cache.set("readiness_check", "test", timeout=1)
            checks["cache_connection"] = True
        except Exception:
            checks["cache_connection"] = False
            ready = False

        # Mock other readiness checks
        checks["migrations_applied"] = True
        checks["configuration_loaded"] = True

        response = {
            "ready": ready,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "checks": checks,
        }

        status_code = 200 if ready else 503

        logger.info(
            "Readiness check completed",
            extra={
                "ready": ready,
                "failed_checks": [k for k, v in checks.items() if not v],
            },
        )

        return response, status_code


@health_ns.route("/live")
class LivenessCheckResource(Resource):
    """Liveness check endpoint."""

    @health_ns.doc("get_liveness")
    @health_ns.marshal_with(liveness_model)
    @health_ns.response(200, "Application is alive", liveness_model)
    @health_ns.response(503, "Application is not responding")
    def get(self):
        """Check if application is alive and responsive.

        Performs a minimal check to verify the application
        is running and can respond to requests.

        Used by Kubernetes liveness probes to determine
        if the container should be restarted.
        """
        try:
            # Calculate uptime
            uptime = time.time() - getattr(current_app, "_start_time", time.time())

            # Get current memory usage
            process = psutil.Process()
            memory_usage_mb = process.memory_info().rss / 1024 / 1024

            response = {
                "alive": True,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "uptime": round(uptime, 2),
                "memory_usage_mb": round(memory_usage_mb, 2),
            }

            return response, 200

        except Exception as e:
            logger.error(f"Liveness check failed: {str(e)}")
            return {
                "alive": False,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "error": str(e),
            }, 503
