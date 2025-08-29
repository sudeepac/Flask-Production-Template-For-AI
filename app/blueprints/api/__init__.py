"""API Blueprint.

This blueprint provides core API endpoints and demonstrates
RESTful patterns and best practices for the Flask Production Template for AI.

Endpoints:
- GET /api/status: API status information
- GET /api/info: Application information
- POST /api/echo: Echo endpoint for testing

Usage:
    This blueprint serves as a working example of how to
    structure API endpoints using the boilerplate architecture.
"""

from flask import Blueprint
from app.urls import get_url_prefix

# Blueprint configuration
BLUEPRINT_NAME = 'api'

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
__description__ = 'Core API endpoints and examples'
__author__ = 'Flask Production Template for AI'

# Export blueprint for registration
__all__ = ['blueprint']