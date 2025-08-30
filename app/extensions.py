"""Flask Extensions Initialization.

This module contains all Flask extension instances that are shared
across the application. Extensions are initialized here and then
bound to the Flask app in the application factory.

See CONTRIBUTING.md §5 for style guidelines.
"""

import logging

from flask_caching import Cache
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# Database ORM
db = SQLAlchemy()

# Database migrations
migrate = Migrate()

# JWT token management
jwt = JWTManager()

# Caching (Redis/Simple)
cache = Cache()

# Cross-Origin Resource Sharing
cors = CORS()

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address, default_limits=["200 per day", "50 per hour"]
)

# Application logger
logger = logging.getLogger("app")


def init_extensions(app):
    """Initialize all Flask extensions with the app.

    This function is called from the application factory to bind
    all extensions to the Flask app instance with proper configuration.

    Args:
        app: Flask application instance

    Example:
        app = Flask(__name__)
        init_extensions(app)
    """
    # Initialize database
    db.init_app(app)
    migrate.init_app(app, db)

    # Initialize authentication
    jwt.init_app(app)
    _configure_jwt(app)

    # Initialize caching
    cache.init_app(app)

    # Initialize CORS
    cors_origins = app.config.get("CORS_ORIGINS", [])
    # Fallback to localhost for development if no origins configured
    if not cors_origins and app.config.get("DEBUG", False):
        cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

    cors.init_app(
        app,
        resources={
            r"/api/*": {
                "origins": cors_origins,
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
            }
        },
    )

    # Initialize rate limiting
    limiter.init_app(app)

    # Configure logging
    _configure_logging(app)


def _configure_jwt(app):
    """Configure JWT extension with custom handlers.

    Sets up JWT token validation, error handlers, and custom claims.

    Args:
        app: Flask application instance
    """

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """Handle expired JWT tokens."""
        return {"error": "Token has expired", "message": "Please log in again"}, 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        """Handle invalid JWT tokens."""
        return {
            "error": "Invalid token",
            "message": "Token signature verification failed",
        }, 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        """Handle missing JWT tokens."""
        return {
            "error": "Authorization token required",
            "message": "Please provide a valid token",
        }, 401

    @jwt.additional_claims_loader
    def add_claims_to_access_token(identity):
        """Add custom claims to JWT tokens.

        Args:
            identity: User identity (usually user ID)

        Returns:
            dict: Additional claims to include in token
        """
        # Add custom claims here (e.g., user roles, permissions)
        return {"user_id": identity, "token_type": "access"}


def _configure_logging(app):
    """Configure application logging.

    Sets up structured logging with appropriate levels and formatters
    based on the application environment.

    Args:
        app: Flask application instance
    """
    log_level = getattr(logging, app.config.get("LOG_LEVEL", "INFO"))
    log_format = app.config.get(
        "LOG_FORMAT", "%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    # Configure root logger
    logging.basicConfig(level=log_level, format=log_format, datefmt="%Y-%m-%d %H:%M:%S")

    # Configure app logger
    logger.setLevel(log_level)

    # Suppress noisy third-party loggers in production
    if not app.debug:
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)


# Utility functions for extensions
def get_db():
    """Get database instance.

    Returns:
        SQLAlchemy: Database instance

    Example:
        db = get_db()
        users = db.session.query(User).all()
    """
    return db


def get_cache():
    """Get cache instance.

    Returns:
        Cache: Cache instance

    Example:
        cache = get_cache()
        cache.set('key', 'value', timeout=300)
    """
    return cache


def get_logger(name=None):
    """Get application logger.

    Args:
        name: Logger name (defaults to 'app')

    Returns:
        Logger: Configured logger instance

    Example:
        logger = get_logger('app.blueprints.auth')
        logger.info('User logged in')
    """
    return logging.getLogger(name or "app")
