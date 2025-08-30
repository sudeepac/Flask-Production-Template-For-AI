"""API Resources with OpenAPI Documentation.

This module provides Flask-RESTX resources that integrate with the existing
API routes to provide comprehensive OpenAPI/Swagger documentation.
"""

from datetime import datetime

from flask import current_app, request
from flask_restx import Resource, fields

from app.api_docs import api_docs
from app.extensions import limiter
from app.utils.decorators import (
    handle_api_errors,
    log_endpoint_access,
    validate_json_input,
)
from app.utils.logging_config import get_logger, log_performance

from .routes import echo_request_schema

# Get logger
logger = get_logger(__name__)

# Get API namespace
api_ns = api_docs.get_namespace("api")

# Define models for documentation
echo_request_model = api_ns.model(
    "EchoRequest",
    {
        "message": fields.String(
            required=True,
            description="Message to echo back",
            max_length=1000,
            example="Hello, World!",
        ),
        "metadata": fields.Raw(
            required=False,
            description="Optional metadata dictionary",
            example={"key": "value", "test": True},
        ),
    },
)

echo_response_model = api_ns.model(
    "EchoResponse",
    {
        "echo": fields.String(
            required=True, description="Echoed message", example="Hello, World!"
        ),
        "timestamp": fields.String(
            required=True,
            description="Processing timestamp in ISO 8601 format",
            example="2024-01-01T12:00:00Z",
        ),
        "metadata": fields.Raw(
            required=False,
            description="Echoed metadata",
            example={"key": "value", "test": True},
        ),
    },
)

api_status_model = api_ns.model(
    "APIStatus",
    {
        "status": fields.String(
            required=True, description="API operational status", example="operational"
        ),
        "version": fields.String(
            required=True, description="API version", example="v2"
        ),
        "timestamp": fields.String(
            required=True,
            description="Current timestamp in ISO 8601 format",
            example="2024-01-01T12:00:00Z",
        ),
        "endpoints": fields.List(
            fields.String,
            required=True,
            description="Available API endpoints",
            example=["/api/status", "/api/info", "/api/echo"],
        ),
    },
)

api_info_model = api_ns.model(
    "APIInfo",
    {
        "name": fields.String(
            required=True,
            description="Application name",
            example="Flask Production Template for AI",
        ),
        "description": fields.String(
            required=True,
            description="Application description",
            example="Flask Production Template for AI",
        ),
        "version": fields.String(
            required=True, description="Application version", example="1.0.0"
        ),
        "environment": fields.String(
            required=True, description="Runtime environment", example="development"
        ),
        "debug": fields.Boolean(
            required=True, description="Debug mode status", example=True
        ),
        "features": fields.Raw(
            required=True,
            description="Available application features",
            example={
                "authentication": True,
                "caching": True,
                "rate_limiting": True,
                "cors": True,
            },
        ),
    },
)

bulk_user_request_model = api_ns.model(
    "BulkUserRequest",
    {
        "username": fields.String(
            required=True, description="Username for the new user", example="john_doe"
        ),
        "email": fields.String(
            required=True,
            description="Email address for the new user",
            example="john.doe@example.com",
        ),
        "post_titles": fields.List(
            fields.String,
            required=True,
            description="List of post titles to create for the user",
            example=["My First Post", "Another Great Post", "Final Thoughts"],
        ),
    },
)

bulk_user_response_model = api_ns.model(
    "BulkUserResponse",
    {
        "user": fields.Raw(
            required=True,
            description="Created user information",
            example={
                "id": 1,
                "username": "john_doe",
                "email": "john.doe@example.com",
                "created_at": "2024-01-01T12:00:00Z",
            },
        ),
        "posts": fields.List(
            fields.Raw,
            required=True,
            description="Created posts for the user",
            example=[
                {
                    "id": 1,
                    "title": "My First Post",
                    "user_id": 1,
                    "created_at": "2024-01-01T12:00:00Z",
                }
            ],
        ),
    },
)

error_response_model = api_ns.model(
    "ErrorResponse",
    {
        "error": fields.String(
            required=True,
            description="Error type identifier",
            example="validation_error",
        ),
        "message": fields.String(
            required=True,
            description="Human-readable error message",
            example="Request validation failed",
        ),
        "details": fields.Raw(
            required=False,
            description="Additional error details",
            example={"field": ["This field is required"]},
        ),
        "timestamp": fields.String(
            required=True,
            description="Error timestamp in ISO 8601 format",
            example="2024-01-01T12:00:00Z",
        ),
    },
)

rate_limit_response_model = api_ns.model(
    "RateLimitResponse",
    {
        "error": fields.String(
            required=True,
            description="Error type identifier",
            example="rate_limit_exceeded",
        ),
        "message": fields.String(
            required=True,
            description="Rate limit error message",
            example="Too many requests. Please try again later.",
        ),
        "retry_after": fields.Integer(
            required=True, description="Seconds to wait before retrying", example=60
        ),
    },
)


@api_ns.route("/status")
class APIStatusResource(Resource):
    """API Status endpoint."""

    @api_ns.doc("get_api_status")
    @api_ns.marshal_with(api_status_model)
    @api_ns.response(200, "Success", api_status_model)
    @api_ns.response(500, "Internal Server Error", error_response_model)
    def get(self):
        """Get API status information.

        Returns the current operational status of the API,
        including version information and available endpoints.
        """
        return {
            "status": "operational",
            "version": current_app.config.get("API_VERSION", "v2"),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "endpoints": ["/api/status", "/api/info", "/api/echo", "/api/users/bulk"],
        }


@api_ns.route("/info")
class APIInfoResource(Resource):
    """API Information endpoint."""

    @api_ns.doc("get_api_info")
    @api_ns.marshal_with(api_info_model)
    @api_ns.response(200, "Success", api_info_model)
    @api_ns.response(500, "Internal Server Error", error_response_model)
    def get(self):
        """Get application information.

        Returns detailed information about the application,
        including name, version, environment, and available features.
        """
        return {
            "name": "Flask Production Template for AI",
            "description": "Flask Production Template for AI",
            "version": getattr(current_app, "version", "1.0.0"),
            "environment": current_app.config.get("FLASK_ENV", "development"),
            "debug": current_app.debug,
            "features": {
                "authentication": True,
                "caching": True,
                "rate_limiting": True,
                "cors": True,
            },
        }


@api_ns.route("/echo")
class EchoResource(Resource):
    """Echo endpoint for testing."""

    @api_ns.doc("echo_message")
    @api_ns.expect(echo_request_model, validate=True)
    @api_ns.marshal_with(echo_response_model)
    @api_ns.response(200, "Success", echo_response_model)
    @api_ns.response(400, "Validation Error", error_response_model)
    @api_ns.response(429, "Rate Limit Exceeded", rate_limit_response_model)
    @api_ns.response(500, "Internal Server Error", error_response_model)
    @limiter.limit("10 per minute")
    @handle_api_errors
    @validate_json_input(echo_request_schema)
    @log_endpoint_access
    @log_performance
    def post(self, validated_data):
        """Echo endpoint for testing requests.

        Accepts JSON data and returns it back with a timestamp.
        Useful for testing API connectivity and request formatting.

        The endpoint validates the input message length (max 1000 characters)
        and optionally accepts metadata that will be echoed back.

        Rate limited to 10 requests per minute per IP address.
        """
        # Create response
        response_data = {
            "message": validated_data["message"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metadata": validated_data.get("metadata", {}),
        }

        logger.info(
            "Echo request processed successfully",
            extra={"message_length": len(validated_data["message"])},
        )

        return response_data


@api_ns.route("/users/bulk")
class BulkUserResource(Resource):
    """Bulk user creation endpoint."""

    @api_ns.doc("create_user_with_posts")
    @api_ns.expect(bulk_user_request_model, validate=True)
    @api_ns.marshal_with(bulk_user_response_model)
    @api_ns.response(
        201, "User and posts created successfully", bulk_user_response_model
    )
    @api_ns.response(400, "Validation Error", error_response_model)
    @api_ns.response(500, "Internal Server Error", error_response_model)
    @log_performance
    def post(self):
        """Create a user with multiple posts.

        Creates a new user and associated posts in a single transaction.
        This endpoint demonstrates bulk operations and transaction management.

        The request must include:
        - username: Unique username for the new user
        - email: Valid email address for the user
        - post_titles: List of post titles to create for the user

        All operations are performed within a database transaction,
        ensuring data consistency.
        """
        try:
            from app.services.example_service import ExampleService

            data = request.get_json()

            # Input validation
            if not data:
                api_ns.abort(400, "Request body is required")

            required_fields = ["username", "email", "post_titles"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                api_ns.abort(
                    400, f"Missing required fields: {', '.join(missing_fields)}"
                )

            username = data["username"].strip()
            email = data["email"].strip().lower()
            post_titles = data["post_titles"]

            if not isinstance(post_titles, list):
                api_ns.abort(400, "post_titles must be a list")

            # Use the example service
            service = ExampleService()
            result = service.create_user_with_posts(username, email, post_titles)

            logger.info(
                "Successfully created user with posts via service",
                extra={
                    "user_id": result["user"]["id"],
                    "post_count": len(result["posts"]),
                },
            )

            return result, 201

        except Exception as e:
            logger.error(
                f"Unexpected error in bulk user creation: {e}",
                extra={"error_type": type(e).__name__},
            )
            api_ns.abort(500, "Failed to create user with posts")
