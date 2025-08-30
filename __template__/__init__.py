"""Blueprint Template.

Standard structure for new Flask blueprints.

Usage:
    1. Copy this template to app/blueprints/your_blueprint_name/
    2. Update BLUEPRINT_NAME below
    3. Implement routes in routes.py
    4. Add schemas, models, services as needed
"""

from flask import Blueprint

from app.urls import get_url_prefix

# TODO: Replace 'template' with your blueprint name
BLUEPRINT_NAME = "template"

# Create blueprint instance
blueprint = Blueprint(
    BLUEPRINT_NAME,
    __name__,
    url_prefix=get_url_prefix(BLUEPRINT_NAME),
)

# Import routes after blueprint creation to avoid circular imports
# from . import routes

__all__ = ["blueprint"]
