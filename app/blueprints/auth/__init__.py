"""Authentication Blueprint.

This blueprint handles user authentication including:
- User registration
- User login/logout
- JWT token management
- Password reset functionality

Routes:
- POST /auth/register - User registration
- POST /auth/login - User login
- POST /auth/logout - User logout
- POST /auth/refresh - Refresh JWT token
- GET /auth/me - Get current user info

See CONTRIBUTING.md §4 for blueprint development guidelines.
"""

from flask import Blueprint

from app.urls import get_url_prefix

# Create blueprint with URL prefix from centralized configuration
blueprint = Blueprint("auth", __name__, url_prefix=get_url_prefix("auth"))

# Import routes to register them with the blueprint
# This must be at the end to avoid circular imports
from . import routes
