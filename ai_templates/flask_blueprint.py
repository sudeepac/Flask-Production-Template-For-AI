"""Flask blueprint template following the project style guide.

This template provides a standard structure for creating Flask blueprints
that comply with the project's coding standards and best practices.

Example:
    from ai_templates.flask_blueprint import create_blueprint_template

    blueprint = create_blueprint_template(
        name='users',
        url_prefix='/api/v1/users'
    )
"""

from typing import Optional

from flask import Blueprint, jsonify, request
from werkzeug.exceptions import BadRequest, NotFound


def create_blueprint_template(
    name: str, url_prefix: str, import_name: Optional[str] = None
) -> Blueprint:
    """Create a standard Flask blueprint following project conventions.

    Args:
        name: The blueprint name (should be snake_case)
        url_prefix: The URL prefix for all routes in this blueprint
        import_name: The import name for the blueprint (defaults to __name__)

    Returns:
        A configured Flask blueprint instance

    Raises:
        ValueError: If name or url_prefix is invalid
    """
    if not name or not isinstance(name, str):
        raise ValueError("Blueprint name must be a non-empty string")

    if not url_prefix or not isinstance(url_prefix, str):
        raise ValueError("URL prefix must be a non-empty string")

    blueprint = Blueprint(
        name=name, import_name=import_name or __name__, url_prefix=url_prefix
    )

    return blueprint


# Example blueprint implementation
example_bp = Blueprint(
    name="example", import_name=__name__, url_prefix="/api/v1/example"
)


@example_bp.route("/", methods=["GET"])
def list_items():
    """List all items with pagination support.

    Returns:
        JSON response containing items list and pagination metadata

    Raises:
        BadRequest: If pagination parameters are invalid
    """
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)

        if page < 1 or per_page < 1 or per_page > 100:
            raise BadRequest("Invalid pagination parameters")

        # TODO: Implement actual data retrieval logic
        items = []
        total = 0

        return jsonify(
            {
                "items": items,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "pages": (total + per_page - 1) // per_page,
                },
            }
        )

    except BadRequest:
        raise
    except Exception as e:
        # Log the error in production
        raise BadRequest(f"Failed to retrieve items: {str(e)}")


@example_bp.route("/<int:item_id>", methods=["GET"])
def get_item(item_id: int):
    """Get a specific item by ID.

    Args:
        item_id: The unique identifier for the item

    Returns:
        JSON response containing the item data

    Raises:
        NotFound: If the item doesn't exist
        BadRequest: If the request is malformed
    """
    try:
        if item_id <= 0:
            raise BadRequest("Item ID must be a positive integer")

        # TODO: Implement actual data retrieval logic
        item = None

        if not item:
            raise NotFound(f"Item with ID {item_id} not found")

        return jsonify({"item": item})

    except (NotFound, BadRequest):
        raise
    except Exception as e:
        # Log the error in production
        raise BadRequest(f"Failed to retrieve item: {str(e)}")


@example_bp.route("/", methods=["POST"])
def create_item():
    """Create a new item.

    Returns:
        JSON response containing the created item data

    Raises:
        BadRequest: If the request data is invalid
    """
    try:
        data = request.get_json()

        if not data:
            raise BadRequest("Request body must contain valid JSON")

        # TODO: Implement validation and creation logic
        # TODO: Add input sanitization
        # TODO: Add database transaction handling

        created_item = {}

        return jsonify({"item": created_item}), 201

    except BadRequest:
        raise
    except Exception as e:
        # Log the error in production
        raise BadRequest(f"Failed to create item: {str(e)}")


@example_bp.errorhandler(BadRequest)
def handle_bad_request(error):
    """Handle bad request errors.

    Args:
        error: The BadRequest exception

    Returns:
        JSON error response
    """
    return jsonify({"error": "Bad Request", "message": str(error.description)}), 400


@example_bp.errorhandler(NotFound)
def handle_not_found(error):
    """Handle not found errors.

    Args:
        error: The NotFound exception

    Returns:
        JSON error response
    """
    return jsonify({"error": "Not Found", "message": str(error.description)}), 404
