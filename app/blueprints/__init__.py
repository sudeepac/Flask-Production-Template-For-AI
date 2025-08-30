"""Blueprints Package.

This package contains all Flask blueprints for the application.
Each blueprint represents a logical grouping of routes and functionality.

Blueprint Structure:
- Each blueprint should be in its own subdirectory
- Each blueprint must have __init__.py, routes.py, and schemas.py
- Follow the template in __template__/ directory

Available Blueprints:
- api: Core API endpoints
- ml: Machine Learning service endpoints
- data: Data management endpoints
- user: User management endpoints
- admin: Administrative endpoints

Usage:
    from app.blueprints import register_blueprints

    # Register all blueprints with the Flask app
    register_blueprints(app)

See AI_INSTRUCTIONS.md §4 for blueprint implementation guidelines.
"""

import logging
from typing import Any, Dict, List

from flask import Blueprint, Flask

from app.urls import get_url_prefix

logger = logging.getLogger(__name__)

# Blueprint registry
_BLUEPRINT_REGISTRY: Dict[str, Blueprint] = {}


def register_blueprint(blueprint: Blueprint, name: str = None) -> None:
    """Register a blueprint in the registry.

    Args:
        blueprint: Flask Blueprint instance
        name: Optional name override (defaults to blueprint.name)
    """
    blueprint_name = name or blueprint.name
    _BLUEPRINT_REGISTRY[blueprint_name] = blueprint
    logger.debug(f"Registered blueprint: {blueprint_name}")


def get_blueprint(name: str) -> Blueprint:
    """Get a registered blueprint by name.

    Args:
        name: Blueprint name

    Returns:
        Blueprint: The requested blueprint

    Raises:
        KeyError: If blueprint is not registered
    """
    if name not in _BLUEPRINT_REGISTRY:
        available = list(_BLUEPRINT_REGISTRY.keys())
        raise KeyError(
            f"Blueprint '{name}' not registered. " f"Available blueprints: {available}"
        )

    return _BLUEPRINT_REGISTRY[name]


def list_blueprints() -> List[str]:
    """List all registered blueprint names.

    Returns:
        list: List of registered blueprint names
    """
    return list(_BLUEPRINT_REGISTRY.keys())


def get_blueprint_info() -> Dict[str, Dict[str, Any]]:
    """Get information about all registered blueprints.

    Returns:
        dict: Blueprint information keyed by blueprint name
    """
    info = {}

    for name, blueprint in _BLUEPRINT_REGISTRY.items():
        info[name] = {
            "name": blueprint.name,
            "url_prefix": blueprint.url_prefix,
            "subdomain": blueprint.subdomain,
            "static_folder": blueprint.static_folder,
            "template_folder": blueprint.template_folder,
            "root_path": blueprint.root_path,
        }

    return info


def register_blueprints(app: Flask) -> None:
    """Register all blueprints with the Flask application.

    This function automatically discovers and registers all blueprints
    in the blueprints package.

    Args:
        app: Flask application instance
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting blueprint registration process")

    # Import and register core blueprints
    blueprint_modules = [
        "health",  # Health check endpoints
        "api",  # Core API endpoints
        "auth",  # Authentication endpoints
        "examples",  # Example endpoints
        # 'ml',       # Uncomment when implemented
        # 'data',     # Uncomment when implemented
        # 'user',     # Uncomment when implemented
        # 'admin',    # Uncomment when implemented
    ]

    registered_count = 0

    for module_name in blueprint_modules:
        logger.info(f"Attempting to register blueprint: {module_name}")
        try:
            # Import the blueprint module
            logger.info(f"Importing module: app.blueprints.{module_name}")
            module = __import__(f"app.blueprints.{module_name}", fromlist=["blueprint"])
            logger.info(f"Successfully imported module: {module_name}")

            if hasattr(module, "blueprint"):
                blueprint = module.blueprint
                logger.info(f"Found blueprint object in module: {module_name}")
                logger.info(
                    f"Blueprint name: {blueprint.name}, url_prefix: {blueprint.url_prefix}"
                )

                # Register with Flask app (blueprint already has url_prefix set)
                app.register_blueprint(blueprint)
                logger.info(f"Registered blueprint with Flask app: {module_name}")

                # Register in our registry
                register_blueprint(blueprint, module_name)
                logger.info(f"Registered blueprint in registry: {module_name}")

                registered_count += 1
                logger.info(
                    f"Successfully registered blueprint '{module_name}' with prefix '{blueprint.url_prefix}'"
                )

            else:
                logger.warning(
                    f"Blueprint module '{module_name}' does not export 'blueprint'"
                )

        except ImportError as e:
            logger.warning(f"Could not import blueprint '{module_name}': {str(e)}")
        except Exception as e:
            logger.error(f"Failed to register blueprint '{module_name}': {str(e)}")

    logger.info(f"Registered {registered_count} blueprints")

    # Log blueprint information
    if logger.isEnabledFor(logging.DEBUG):
        for name, info in get_blueprint_info().items():
            logger.debug(f"Blueprint '{name}': {info}")


# Export public interface
__all__ = [
    "register_blueprint",
    "get_blueprint",
    "list_blueprints",
    "get_blueprint_info",
    "register_blueprints",
]
