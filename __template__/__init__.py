"""Blueprint Template.

This template provides the standard structure for creating new blueprints
in the Flask application. Follow this template to ensure consistency
across all blueprints.

Template Structure:
- __init__.py: Blueprint initialization and registration
- routes.py: Route definitions and handlers
- schemas.py: Request/response schemas for the blueprint
- models.py: Database models (if needed)
- services.py: Business logic services (if needed)
- utils.py: Blueprint-specific utilities (if needed)

Usage:
    1. Copy this template directory to app/blueprints/
    2. Rename the directory to your blueprint name
    3. Update the blueprint name and URL prefix in __init__.py
    4. Implement your routes in routes.py
    5. Define schemas in schemas.py
    6. Add any models, services, or utilities as needed

See AI_INSTRUCTIONS.md §4 for blueprint implementation guidelines.
"""

from flask import Blueprint

from app.urls import get_url_prefix

# TODO: Replace 'template' with your blueprint name
BLUEPRINT_NAME = "template"

# Create blueprint instance
# TODO: Update the blueprint name and description
blueprint = Blueprint(
    BLUEPRINT_NAME,
    __name__,
    url_prefix=get_url_prefix(BLUEPRINT_NAME),
    template_folder="templates",
    static_folder="static",
)

# Import routes to register them with the blueprint
# This import must come after blueprint creation to avoid circular imports
from . import routes

# Optional: Import other modules
# from . import models, services, utils

# Blueprint metadata
__version__ = "1.0.0"
__description__ = "Template blueprint for creating new blueprints"
__author__ = "Your Name"

# Export blueprint for registration
__all__ = ["blueprint"]
