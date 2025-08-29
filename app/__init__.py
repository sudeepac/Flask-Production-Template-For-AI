"""Flask Application Factory.

This module contains the application factory pattern implementation
for creating Flask app instances with proper configuration and
extension initialization.

See CONTRIBUTING.md §5 for style guidelines.
"""

import logging
import time
from flask import Flask, jsonify
from datetime import datetime
from app.config_manager import ConfigManager
from app.api_docs import APIDocumentation
from app.extensions import db, migrate, jwt, cache


def create_app(config_name='development'):
    """Create and configure Flask application instance.
    
    This factory function creates a Flask app with:
    - Configuration loading
    - Extension initialization
    - Blueprint registration
    - Error handlers setup
    
    Args:
        config_name: Configuration environment name (defaults to 'development')
        
    Returns:
        Flask: Configured Flask application instance
        
    Example:
        app = create_app()
        app.run(debug=True)
    """
    app = Flask(__name__)
    
    # Load configuration using simplified config manager
    config_manager = ConfigManager(config_name)
    config_manager.validate()
    app.config.update(config_manager.get_config())
    
    # Print config summary in development
    if config_name == 'development':
        config_manager.print_summary()
    
    # Track application start time for uptime calculations
    app._start_time = time.time()
    app.version = '1.0.0'
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cache.init_app(app)
    
    # Initialize API documentation
    _setup_api_docs(app)
    
    # Import models to register them with SQLAlchemy
    from app import models
    
    # Register blueprints
    _register_blueprints(app)
    
    # Setup enhanced logging
    _setup_logging(app)
    
    # Register enhanced error handlers
    _register_error_handlers(app)
    
    # Add root route
    _register_root_route(app)
    
    return app


def _setup_api_docs(app):
    """Initialize API documentation.
    
    Args:
        app: Flask application instance
    """
    from app.api_docs import api_docs
    api_docs.init_app(app)


def _register_blueprints(app):
    """Register all application blueprints.
    
    Args:
        app: Flask application instance
    """
    # Import and register blueprints using the centralized system
    from app.blueprints import register_blueprints
    register_blueprints(app)


def _setup_logging(app):
    """Configure application logging.
    
    Args:
        app: Flask application instance
    """
    from app.extensions import _configure_logging
    _configure_logging(app)


def _register_error_handlers(app):
    """Register enhanced global error handlers.
    
    Args:
        app: Flask application instance
    """
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)


def _register_root_route(app):
    """Register the root route for the application.
    
    Args:
        app: Flask application instance
    """
    @app.route('/')
    def index():
        """Application root endpoint - provides overview of available services."""
        return jsonify({
            'message': 'Flask Production Template - Production Ready',
            'description': 'A comprehensive Flask application with ML capabilities, proper error handling, and production-ready features.',
            'version': getattr(app, 'version', '1.0.0'),
            'environment': app.config.get('FLASK_ENV', 'development'),
            'available_endpoints': {
                '/': 'This index page',
                '/health/': 'Health check endpoints',
                '/api/': 'Core API endpoints',
                '/examples/': 'Example endpoints demonstrating best practices'
            },
            'features': {
                'authentication': 'JWT-based authentication',
                'database': 'SQLAlchemy with migrations',
                'caching': 'Redis/Simple caching support',
                'rate_limiting': 'Request rate limiting',
                'cors': 'Cross-origin resource sharing',
                'logging': 'Structured logging with performance monitoring',
                'error_handling': 'Comprehensive error handling with custom exceptions'
            },
            'documentation': {
                'api_docs': 'Available at /docs/ (Swagger UI)',
                'openapi_spec': 'Available at /swagger.json',
                'health_checks': 'Available at /health/',
                'examples': 'Available at /examples/'
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200