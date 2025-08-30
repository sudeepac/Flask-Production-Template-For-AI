"""Examples blueprint for demonstrating best practices.

This blueprint showcases:
- Enhanced error handling patterns
- Structured logging implementation
- Performance monitoring
- Security event logging
- Input validation
- Database transaction management
"""

from flask import Blueprint

from app.urls import get_url_prefix

blueprint = Blueprint("examples", __name__, url_prefix=get_url_prefix("examples"))


# Import routes to register them with the blueprint
from . import routes  # noqa: F401

# Import Flask-RESTX resources for API documentation
try:
    pass
except ImportError:
    # Resources module is optional for backward compatibility
    pass
