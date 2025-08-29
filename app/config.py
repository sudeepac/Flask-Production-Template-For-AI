"""Central Configuration Module.

This module contains all Flask, database, ML, and feature configurations
in a single source of truth. Environment-specific settings are handled
through environment variables with sensible defaults.

See CONTRIBUTING.md §5 for style guidelines.
"""

import os
from datetime import timedelta


class Config:
    """Base configuration class with common settings.
    
    This class contains all configuration variables used across
    the application. Environment variables override defaults.
    
    Environment Variables:
        SECRET_KEY: Flask secret key for sessions/JWT
        DATABASE_URL: Database connection string
        REDIS_URL: Redis connection for caching
        ML_MODEL_PATH: Path to ML model files
        DEBUG: Enable debug mode (default: False)
        
    Example:
        app.config.from_object(Config)
    """
    
    # Flask Core Settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    TESTING = False
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = DEBUG
    
    # JWT Configuration
    JWT_SECRET_KEY = SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Cache Configuration (Redis)
    CACHE_TYPE = 'redis' if os.environ.get('REDIS_URL') else 'simple'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # ML Model Configuration
    ML_MODEL_PATH = os.environ.get('ML_MODEL_PATH', 'models/')
    ML_MODEL_CACHE_TTL = int(os.environ.get('ML_MODEL_CACHE_TTL', '3600'))  # 1 hour
    ML_BATCH_SIZE = int(os.environ.get('ML_BATCH_SIZE', '32'))
    ML_MAX_WORKERS = int(os.environ.get('ML_MAX_WORKERS', '4'))
    
    # API Configuration
    API_RATE_LIMIT = os.environ.get('API_RATE_LIMIT', '100 per hour')
    API_VERSION = 'v2'  # Current active API version
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads/')
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'csv', 'json'}
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s %(levelname)s %(name)s: %(message)s'
    
    # Security Headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block'
    }


class DevelopmentConfig(Config):
    """Development environment configuration.
    
    Extends base Config with development-specific settings:
    - Debug mode enabled
    - Verbose logging
    - Local database
    """
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///dev.db'
    LOG_LEVEL = 'DEBUG'


class TestingConfig(Config):
    """Testing environment configuration.
    
    Extends base Config with testing-specific settings:
    - Testing mode enabled
    - In-memory database
    - Disabled CSRF protection
    """
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)


class ProductionConfig(Config):
    """Production environment configuration.
    
    Extends base Config with production-specific settings:
    - Strict security settings
    - Performance optimizations
    - External services required
    """
    DEBUG = False
    SQLALCHEMY_RECORD_QUERIES = False
    LOG_LEVEL = 'WARNING'
    
    # Production requires these environment variables
    @classmethod
    def validate_production_config(cls):
        """Validate required production environment variables.
        
        Raises:
            ValueError: If required production variables are missing
        """
        required_vars = ['SECRET_KEY', 'DATABASE_URL', 'REDIS_URL']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            raise ValueError(
                f"Missing required production environment variables: {missing_vars}"
            )


# Configuration mapping for easy selection
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}