"""API Documentation Configuration.

This module configures OpenAPI/Swagger documentation for the Flask application
using Flask-RESTX. It provides comprehensive API documentation with interactive
Swagger UI and automatic schema generation.

Features:
- Interactive Swagger UI
- Automatic schema generation from Marshmallow schemas
- API versioning support
- Request/response examples
- Authentication documentation
- Error response documentation
"""

import os
from typing import Any, Dict, Optional

from flask import Flask
from flask_restx import Api, Namespace, Resource, fields
from marshmallow import Schema, ValidationError


class APIDocumentation:
    """API Documentation manager using Flask-RESTX."""

    def __init__(self, app: Optional[Flask] = None):
        """Initialize API documentation.

        Args:
            app: Flask application instance
        """
        self.api = None
        self.namespaces = {}

        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize API documentation with Flask app.

        Args:
            app: Flask application instance
        """
        # API configuration
        api_config = {
            "version": app.config.get("API_VERSION", "1.0.0"),
            "title": app.config.get("API_TITLE", "Flask Production Template for AI"),
            "description": app.config.get(
                "API_DESCRIPTION",
                "A production-ready Flask-based Machine Learning API framework",
            ),
            "doc": app.config.get("API_DOC_URL", "/docs/"),
            "prefix": app.config.get("API_PREFIX", "/api"),
            "validate": True,
            "ordered": True,
            "contact": app.config.get("API_CONTACT", "admin@example.com"),
            "contact_email": app.config.get("API_CONTACT_EMAIL", "admin@example.com"),
            "license": app.config.get("API_LICENSE", "MIT"),
            "license_url": app.config.get(
                "API_LICENSE_URL", "https://opensource.org/licenses/MIT"
            ),
            "terms_url": app.config.get("API_TERMS_URL", None),
            "authorizations": self._get_authorizations(app),
        }

        # Create API instance
        self.api = Api(app, **api_config)

        # Configure error handlers
        self._configure_error_handlers()

        # Create namespaces
        self._create_namespaces()

        # Store reference in app
        app.extensions["api_docs"] = self

    def _get_authorizations(self, app: Flask) -> Dict[str, Any]:
        """Get API authorization configurations.

        Args:
            app: Flask application instance

        Returns:
            Authorization configurations for Swagger UI
        """
        return {
            "Bearer": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": "JWT Bearer token. Format: Bearer <token>",
            },
            "ApiKey": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API Key for authentication",
            },
        }

    def _configure_error_handlers(self) -> None:
        """Configure API error handlers for documentation."""

        @self.api.errorhandler
        def default_error_handler(error):
            """Default error handler with documentation."""
            return {
                "error": "internal_server_error",
                "message": "An unexpected error occurred",
                "timestamp": "2024-01-01T12:00:00Z",
            }, 500

        @self.api.errorhandler(ValidationError)
        def validation_error_handler(error):
            """Validation error handler."""
            return {
                "error": "validation_error",
                "message": "Request validation failed",
                "details": error.messages,
                "timestamp": "2024-01-01T12:00:00Z",
            }, 400

        # Note: Flask-RESTX doesn't support HTTP status code error handlers
        # These would be handled by Flask's main error handlers instead

    def _create_namespaces(self) -> None:
        """Create API namespaces for organization."""
        # Core API namespace
        self.namespaces["api"] = self.api.namespace(
            "api", description="Core API endpoints", path="/api"
        )

        # Examples namespace
        self.namespaces["examples"] = self.api.namespace(
            "examples",
            description="Example endpoints demonstrating best practices",
            path="/examples",
        )

        # Health namespace
        self.namespaces["health"] = self.api.namespace(
            "health",
            description="Health check and monitoring endpoints",
            path="/health",
        )

        # ML namespace (for future ML endpoints)
        self.namespaces["ml"] = self.api.namespace(
            "ml", description="Machine Learning service endpoints", path="/ml"
        )

    def get_namespace(self, name: str) -> Optional[Namespace]:
        """Get a namespace by name.

        Args:
            name: Namespace name

        Returns:
            Namespace instance or None if not found
        """
        return self.namespaces.get(name)

    def marshmallow_to_restx_model(self, schema: Schema, name: str) -> fields.Raw:
        """Convert Marshmallow schema to Flask-RESTX model.

        Args:
            schema: Marshmallow schema instance
            name: Model name for documentation

        Returns:
            Flask-RESTX model
        """
        model_fields = {}

        for field_name, field_obj in schema.fields.items():
            # Convert Marshmallow field types to Flask-RESTX field types
            if hasattr(field_obj, "validate") and field_obj.validate:
                # Handle validation constraints
                if hasattr(field_obj.validate, "__name__"):
                    description = f"Validation: {field_obj.validate.__name__}"
                else:
                    description = "Custom validation applied"
            else:
                description = field_obj.metadata.get("description", "")

            # Map field types
            if field_obj.__class__.__name__ == "String":
                model_fields[field_name] = fields.String(
                    required=field_obj.required, description=description
                )
            elif field_obj.__class__.__name__ == "Integer":
                model_fields[field_name] = fields.Integer(
                    required=field_obj.required, description=description
                )
            elif field_obj.__class__.__name__ == "Boolean":
                model_fields[field_name] = fields.Boolean(
                    required=field_obj.required, description=description
                )
            elif field_obj.__class__.__name__ == "DateTime":
                model_fields[field_name] = fields.DateTime(
                    required=field_obj.required, description=description
                )
            elif field_obj.__class__.__name__ == "Dict":
                model_fields[field_name] = fields.Raw(
                    required=field_obj.required,
                    description=description or "Dictionary/Object field",
                )
            else:
                # Default to Raw for unknown types
                model_fields[field_name] = fields.Raw(
                    required=field_obj.required,
                    description=description
                    or f"Field of type {field_obj.__class__.__name__}",
                )

        return self.api.model(name, model_fields)


# Global instance
api_docs = APIDocumentation()


# Common response models
def create_common_models(api: Api) -> Dict[str, Any]:
    """Create common response models for API documentation.

    Args:
        api: Flask-RESTX API instance

    Returns:
        Dictionary of common models
    """
    models = {}

    # Error response model
    models["ErrorResponse"] = api.model(
        "ErrorResponse",
        {
            "error": fields.String(required=True, description="Error type identifier"),
            "message": fields.String(
                required=True, description="Human-readable error message"
            ),
            "details": fields.Raw(description="Additional error details"),
            "timestamp": fields.String(required=True, description="ISO 8601 timestamp"),
            "request_id": fields.String(description="Unique request identifier"),
        },
    )

    # Success response model
    models["SuccessResponse"] = api.model(
        "SuccessResponse",
        {
            "message": fields.String(required=True, description="Success message"),
            "data": fields.Raw(description="Response data"),
            "timestamp": fields.String(required=True, description="ISO 8601 timestamp"),
        },
    )

    # API status model
    models["APIStatus"] = api.model(
        "APIStatus",
        {
            "status": fields.String(
                required=True, description="API operational status"
            ),
            "version": fields.String(required=True, description="API version"),
            "timestamp": fields.String(required=True, description="Current timestamp"),
            "endpoints": fields.List(fields.String, description="Available endpoints"),
        },
    )

    # API info model
    models["APIInfo"] = api.model(
        "APIInfo",
        {
            "name": fields.String(required=True, description="Application name"),
            "description": fields.String(
                required=True, description="Application description"
            ),
            "version": fields.String(required=True, description="Application version"),
            "environment": fields.String(
                required=True, description="Runtime environment"
            ),
            "debug": fields.Boolean(required=True, description="Debug mode status"),
            "features": fields.Raw(required=True, description="Available features"),
        },
    )

    # Echo request model
    models["EchoRequest"] = api.model(
        "EchoRequest",
        {
            "message": fields.String(
                required=True, description="Message to echo back", max_length=1000
            ),
            "metadata": fields.Raw(description="Optional metadata dictionary"),
        },
    )

    # Echo response model
    models["EchoResponse"] = api.model(
        "EchoResponse",
        {
            "echo": fields.String(required=True, description="Echoed message"),
            "timestamp": fields.String(
                required=True, description="Processing timestamp"
            ),
            "metadata": fields.Raw(description="Echoed metadata"),
        },
    )

    # Health check model
    models["HealthCheck"] = api.model(
        "HealthCheck",
        {
            "status": fields.String(required=True, description="Health status"),
            "timestamp": fields.String(required=True, description="Check timestamp"),
            "version": fields.String(description="Application version"),
            "uptime": fields.Float(description="Application uptime in seconds"),
            "checks": fields.Raw(description="Individual health check results"),
        },
    )

    return models


def setup_api_documentation(app: Flask) -> APIDocumentation:
    """Setup API documentation for the Flask application.

    Args:
        app: Flask application instance

    Returns:
        Configured APIDocumentation instance
    """
    # Initialize API documentation
    api_docs.init_app(app)

    # Create common models
    create_common_models(api_docs.api)

    return api_docs
