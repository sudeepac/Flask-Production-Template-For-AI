"""API Routes.

This module contains core API endpoints that demonstrate
RESTful patterns and request/response handling.
"""

from datetime import datetime

from flask import current_app, g, jsonify, request
from flask_jwt_extended import jwt_required
from marshmallow import Schema, ValidationError, fields

from app.extensions import limiter
from app.models.example import Post, User
from app.services.example_service import ExampleService
from app.utils.error_handlers import APIError, NotFoundAPIError, ValidationAPIError
from app.utils.logging_config import get_logger, log_performance, log_security_event

from . import blueprint


class EchoRequestSchema(Schema):
    """Schema for echo endpoint requests."""

    message = fields.Str(required=True, validate=lambda x: len(x) <= 1000)
    metadata = fields.Dict(required=False)


class EchoResponseSchema(Schema):
    """Schema for echo endpoint responses."""

    echo = fields.Str()
    timestamp = fields.Str()
    metadata = fields.Dict()


# Schema instances
echo_request_schema = EchoRequestSchema()
echo_response_schema = EchoResponseSchema()

# Logger
logger = get_logger(__name__)


@blueprint.route("/status", methods=["GET"])
@log_performance
def api_status():
    """Get API status information.

    Returns:
        JSON response with API status and version

    Example:
        GET /api/status

        Response:
        {
            "status": "operational",
            "version": "v2",
            "timestamp": "2024-01-01T12:00:00Z",
            "endpoints": [
                "/api/status",
                "/api/info",
                "/api/echo"
            ]
        }
    """
    return (
        jsonify(
            {
                "status": "operational",
                "version": current_app.config.get("API_VERSION", "v2"),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "endpoints": ["/api/status", "/api/info", "/api/echo"],
            }
        ),
        200,
    )


@blueprint.route("/info", methods=["GET"])
@log_performance
def api_info():
    """Get application information.

    Returns:
        JSON response with application details

    Example:
        GET /api/info

        Response:
        {
            "name": "Flask Production Template for AI",
            "description": "Flask Production Template for AI Coding",
            "version": "1.0.0",
            "environment": "development",
            "debug": true,
            "features": {
                "authentication": true,
                "caching": true,
                "rate_limiting": true,
                "cors": true
            }
        }
    """
    return (
        jsonify(
            {
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
        ),
        200,
    )


@blueprint.route("/echo", methods=["POST"])
@limiter.limit("10 per minute")
@log_performance
def echo():
    """Echo endpoint for testing requests.

    Accepts JSON data and returns it back with timestamp.
    Useful for testing API connectivity and request formatting.

    Request Body:
        {
            "message": "Hello, World!",
            "metadata": {"key": "value"}
        }

    Returns:
        JSON response echoing the input with timestamp

    Example:
        POST /api/echo
        Content-Type: application/json

        {
            "message": "Hello, World!",
            "metadata": {"test": true}
        }

        Response:
        {
            "echo": "Hello, World!",
            "timestamp": "2024-01-01T12:00:00Z",
            "metadata": {"test": true}
        }
    """
    try:
        logger.info("Echo endpoint called", extra={"endpoint": "echo"})

        # Validate request data
        json_data = request.get_json()
        if not json_data:
            raise ValidationAPIError("Request must contain JSON data")

        # Validate using schema
        validated_data = echo_request_schema.load(json_data)

        # Log security event for echo requests
        log_security_event(
            "echo_request",
            {
                "message_length": len(validated_data["message"]),
                "has_metadata": bool(validated_data.get("metadata")),
                "ip_address": request.remote_addr,
            },
        )

        # Create response
        response_data = {
            "echo": validated_data["message"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metadata": validated_data.get("metadata", {}),
        }

        logger.info(
            "Echo request processed successfully",
            extra={"message_length": len(validated_data["message"])},
        )

        return jsonify(response_data), 200

    except ValidationError as e:
        logger.warning(
            f"Schema validation error: {e.messages}",
            extra={"validation_errors": e.messages},
        )
        raise ValidationAPIError("Invalid request data", details=e.messages)

    except ValidationAPIError:
        raise  # Re-raise custom validation errors

    except Exception as e:
        logger.error(
            f"Unexpected error in echo endpoint: {str(e)}",
            extra={"error_type": type(e).__name__},
        )
        raise APIError("An unexpected error occurred")


@blueprint.route("/users/bulk", methods=["POST"])
@jwt_required()
@log_performance
def create_user_with_posts():
    """Create a user with multiple posts using the example service."""
    try:
        data = request.get_json()

        # Input validation
        if not data:
            raise ValidationAPIError("Request body is required")

        required_fields = ["username", "email", "post_titles"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValidationAPIError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )

        username = data["username"].strip()
        email = data["email"].strip().lower()
        post_titles = data["post_titles"]

        if not isinstance(post_titles, list):
            raise ValidationAPIError("post_titles must be a list")

        # Use the example service
        service = ExampleService()
        result = service.create_user_with_posts(username, email, post_titles)

        logger.info(
            f"Successfully created user with posts via service",
            extra={"user_id": result["user"]["id"], "post_count": len(result["posts"])},
        )

        return jsonify(result), 201

    except ValidationAPIError:
        raise  # Re-raise validation errors
    except Exception as e:
        logger.error(
            f"Unexpected error in bulk user creation: {e}",
            extra={"error_type": type(e).__name__},
        )
        raise APIError("Failed to create user with posts")


@blueprint.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded errors."""
    return (
        jsonify(
            {
                "error": "rate_limit_exceeded",
                "message": "Too many requests. Please try again later.",
                "retry_after": e.retry_after,
            }
        ),
        429,
    )
