"""Health Check Blueprint.

This blueprint provides health check endpoints for monitoring
application status, database connectivity, and system health.

Endpoints:
- GET /health: Basic health check
- GET /health/detailed: Detailed system status
- GET /health/ready: Readiness probe for Kubernetes
- GET /health/live: Liveness probe for Kubernetes

Usage:
    This blueprint is automatically registered and provides
    essential monitoring endpoints for production deployments.
"""

from flask import Blueprint
from app.urls import get_url_prefix

# Blueprint configuration
BLUEPRINT_NAME = 'health'

# Create blueprint instance
blueprint = Blueprint(
    BLUEPRINT_NAME,
    __name__,
    url_prefix=get_url_prefix(BLUEPRINT_NAME)
)

# Import routes to register them with the blueprint
from . import routes

# Import Flask-RESTX resources for API documentation
try:
    from . import resources
except ImportError:
    # Resources module is optional for backward compatibility
    pass

# Blueprint metadata
__version__ = '1.0.0'
__description__ = 'Health check and monitoring endpoints'
__author__ = 'Flask Production Template'

# Export blueprint for registration
__all__ = ['blueprint']