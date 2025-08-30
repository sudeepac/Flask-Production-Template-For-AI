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
    """List all items.

    Returns:
        JSON response with items list
    """
    try:
        # TODO: Implement data retrieval
        items = []
        return jsonify({"items": items})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@example_bp.route("/<int:item_id>", methods=["GET"])
def get_item(item_id: int):
    """Get item by ID.

    Args:
        item_id: Item identifier

    Returns:
        JSON response with item data
    """
    try:
        # TODO: Implement data retrieval
        item = {"id": item_id}
        return jsonify({"item": item})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@example_bp.route("/", methods=["POST"])
def create_item():
    """Create new item.

    Returns:
        JSON response with created item
    """
    try:
        data = request.get_json()
        # TODO: Implement validation and creation
        created_item = data or {}
        return jsonify({"item": created_item}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
