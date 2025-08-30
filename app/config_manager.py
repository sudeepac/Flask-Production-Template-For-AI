"""Simplified Configuration Manager.

This module provides a simplified interface for managing application
configuration with better validation, documentation, and ease of use.
"""

import os
import logging
from typing import Dict, Any, Optional, Union
from datetime import timedelta
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    url: str = 'sqlite:///app.db'
    track_modifications: bool = False
    record_queries: bool = False
    pool_size: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    
    @classmethod
    def from_env(cls, env: str = 'development') -> 'DatabaseConfig':
        """Create database config from environment variables."""
        if env == 'testing':
            return cls(url='sqlite:///:memory:')
        
        url = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
        return cls(
            url=url,
            track_modifications=False,
            record_queries=env == 'development',
            pool_size=int(os.environ.get('DB_POOL_SIZE', '10')),
            pool_timeout=int(os.environ.get('DB_POOL_TIMEOUT', '30')),
            pool_recycle=int(os.environ.get('DB_POOL_RECYCLE', '3600'))
        )


@dataclass
class CacheConfig:
    """Cache configuration settings."""
    type: str = 'simple'
    redis_url: str = 'redis://localhost:6379/0'
    default_timeout: int = 300
    key_prefix: str = 'flask_app'
    
    @classmethod
    def from_env(cls) -> 'CacheConfig':
        """Create cache config from environment variables."""
        redis_url = os.environ.get('REDIS_URL')
        cache_type = 'redis' if redis_url else 'simple'
        
        return cls(
            type=cache_type,
            redis_url=redis_url or 'redis://localhost:6379/0',
            default_timeout=int(os.environ.get('CACHE_DEFAULT_TIMEOUT', '300')),
            key_prefix=os.environ.get('CACHE_KEY_PREFIX', 'flask_app')
        )


@dataclass
class SecurityConfig:
    """Security configuration settings."""
    secret_key: str = 'dev-secret-key-change-in-production'
    jwt_secret_key: Optional[str] = None
    jwt_access_token_expires: timedelta = field(default_factory=lambda: timedelta(hours=1))
    jwt_refresh_token_expires: timedelta = field(default_factory=lambda: timedelta(days=30))
    force_https: bool = False
    csrf_enabled: bool = True
    
    def __post_init__(self):
        """Set JWT secret key to secret key if not provided."""
        if self.jwt_secret_key is None:
            self.jwt_secret_key = self.secret_key
    
    @classmethod
    def from_env(cls, env: str = 'development') -> 'SecurityConfig':
        """Create security config from environment variables."""
        secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
        jwt_secret_key = os.environ.get('JWT_SECRET_KEY')
        
        # Validate secret keys
        cls._validate_secret_key(secret_key, env, 'SECRET_KEY')
        if jwt_secret_key:
            cls._validate_secret_key(jwt_secret_key, env, 'JWT_SECRET_KEY')
        
        return cls(
            secret_key=secret_key,
            jwt_secret_key=jwt_secret_key,
            jwt_access_token_expires=timedelta(
                seconds=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', '3600'))
            ),
            jwt_refresh_token_expires=timedelta(
                days=int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', '30'))
            ),
            force_https=os.environ.get('FORCE_HTTPS', 'False').lower() == 'true',
            csrf_enabled=os.environ.get('WTF_CSRF_ENABLED', 'True').lower() == 'true'
        )
    
    @staticmethod
    def _validate_secret_key(key: str, env: str, key_name: str) -> None:
        """Validate secret key strength."""
        # Check for development defaults
        weak_defaults = [
            'dev-secret-key-change-in-production',
            'development-key',
            'dev-key',
            'secret',
            'password',
            '123456',
            'changeme'
        ]
        
        if env == 'production':
            if key in weak_defaults:
                raise ValueError(f"{key_name} cannot use weak default value in production")
            
            if len(key) < 32:
                raise ValueError(f"{key_name} must be at least 32 characters long in production")
            
            # Check for common weak patterns
            if key.lower() in ['secret', 'password', 'key'] or key.isdigit():
                raise ValueError(f"{key_name} is too weak for production use")
        
        elif env == 'development' and len(key) < 16:
            import logging
            logging.warning(f"{key_name} is shorter than recommended (16+ characters)")


@dataclass
class APIConfig:
    """API configuration settings."""
    version: str = 'v2'
    rate_limit: str = '100 per hour'
    docs_enabled: bool = True
    cors_origins: list = field(default_factory=list)
    max_content_length: int = 16 * 1024 * 1024  # 16MB
    
    @classmethod
    def from_env(cls) -> 'APIConfig':
        """Create API config from environment variables."""
        cors_origins = os.environ.get('CORS_ORIGINS', '')
        origins = [origin.strip() for origin in cors_origins.split(',') if origin.strip()]
        
        return cls(
            version=os.environ.get('API_VERSION', 'v2'),
            rate_limit=os.environ.get('API_RATE_LIMIT', '100 per hour'),
            docs_enabled=os.environ.get('API_DOCS_ENABLED', 'True').lower() == 'true',
            cors_origins=origins,
            max_content_length=int(os.environ.get('MAX_CONTENT_LENGTH', str(16 * 1024 * 1024)))
        )


@dataclass
class LoggingConfig:
    """Logging configuration settings."""
    level: str = 'INFO'
    format: str = '%(asctime)s %(levelname)s %(name)s: %(message)s'
    file_path: Optional[str] = None
    structured: bool = False
    
    @classmethod
    def from_env(cls, env: str = 'development') -> 'LoggingConfig':
        """Create logging config from environment variables."""
        level_map = {
            'development': 'DEBUG',
            'testing': 'WARNING',
            'production': 'WARNING'
        }
        
        default_level = level_map.get(env, 'INFO')
        
        return cls(
            level=os.environ.get('LOG_LEVEL', default_level),
            format=os.environ.get('LOG_FORMAT', '%(asctime)s %(levelname)s %(name)s: %(message)s'),
            file_path=os.environ.get('LOG_FILE'),
            structured=os.environ.get('STRUCTURED_LOGGING', 'False').lower() == 'true'
        )


class ConfigManager:
    """Simplified configuration manager.
    
    This class provides a clean interface for managing all application
    configuration with proper validation and environment-specific defaults.
    """
    
    def __init__(self, env: str = None):
        """Initialize configuration manager.
        
        Args:
            env: Environment name (development, testing, production)
        """
        self.env = env or os.environ.get('FLASK_ENV', 'development')
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment and defaults."""
        # Load component configurations
        database = DatabaseConfig.from_env(self.env)
        cache = CacheConfig.from_env()
        security = SecurityConfig.from_env(self.env)
        api = APIConfig.from_env()
        logging_config = LoggingConfig.from_env(self.env)
        
        # Build Flask configuration dictionary
        config = {
            # Flask core
            'SECRET_KEY': security.secret_key,
            'DEBUG': self.env == 'development',
            'TESTING': self.env == 'testing',
            
            # Database
            'SQLALCHEMY_DATABASE_URI': database.url,
            'SQLALCHEMY_TRACK_MODIFICATIONS': database.track_modifications,
            'SQLALCHEMY_RECORD_QUERIES': database.record_queries,
            'SQLALCHEMY_ENGINE_OPTIONS': {
                'pool_size': database.pool_size,
                'pool_timeout': database.pool_timeout,
                'pool_recycle': database.pool_recycle,
            },
            
            # Cache
            'CACHE_TYPE': cache.type,
            'CACHE_REDIS_URL': cache.redis_url,
            'CACHE_DEFAULT_TIMEOUT': cache.default_timeout,
            'CACHE_KEY_PREFIX': cache.key_prefix,
            
            # JWT
            'JWT_SECRET_KEY': security.jwt_secret_key,
            'JWT_ACCESS_TOKEN_EXPIRES': security.jwt_access_token_expires,
            'JWT_REFRESH_TOKEN_EXPIRES': security.jwt_refresh_token_expires,
            
            # Security
            'FORCE_HTTPS': security.force_https,
            'WTF_CSRF_ENABLED': security.csrf_enabled,
            
            # API
            'API_VERSION': api.version,
            'API_RATE_LIMIT': api.rate_limit,
            'API_DOCS_ENABLED': api.docs_enabled,
            'CORS_ORIGINS': api.cors_origins,
            'MAX_CONTENT_LENGTH': api.max_content_length,
            
            # Logging
            'LOG_LEVEL': logging_config.level,
            'LOG_FORMAT': logging_config.format,
            'LOG_FILE': logging_config.file_path,
            'STRUCTURED_LOGGING': logging_config.structured,
            
            # File uploads
            'UPLOAD_FOLDER': os.environ.get('UPLOAD_FOLDER', 'uploads/'),
            'ALLOWED_EXTENSIONS': set(
                os.environ.get('ALLOWED_EXTENSIONS', 'txt,pdf,png,jpg,jpeg,gif,csv,json').split(',')
            ),
            
            # Security headers
            'SECURITY_HEADERS': {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY',
                'X-XSS-Protection': '1; mode=block'
            }
        }
        
        return config
    
    def get_config(self) -> Dict[str, Any]:
        """Get the complete configuration dictionary."""
        return self._config.copy()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)
    
    def validate(self) -> None:
        """Validate configuration for current environment."""
        if self.env == 'production':
            self._validate_production()
        elif self.env == 'testing':
            self._validate_testing()
    
    def _validate_production(self) -> None:
        """Validate production configuration."""
        required_vars = {
            'SECRET_KEY': 'Production secret key is required',
            'DATABASE_URL': 'Production database URL is required'
        }
        
        errors = []
        
        for var, message in required_vars.items():
            if not os.environ.get(var):
                errors.append(f"{var}: {message}")
        
        # Check for development defaults in production
        if self._config['SECRET_KEY'] == 'dev-secret-key-change-in-production':
            errors.append("SECRET_KEY: Cannot use development default in production")
        
        if self._config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:'):
            logging.warning("Using SQLite in production is not recommended")
        
        if errors:
            raise ValueError(f"Production configuration errors:\n" + "\n".join(errors))
    
    def _validate_testing(self) -> None:
        """Validate testing configuration."""
        # Ensure testing uses in-memory database
        if not self._config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:///:memory:'):
            logging.warning("Testing should use in-memory SQLite database")
    
    def print_summary(self) -> None:
        """Print configuration summary for debugging."""
        print(f"\n=== Configuration Summary ({self.env}) ===")
        print(f"Database: {self._config['SQLALCHEMY_DATABASE_URI']}")
        print(f"Cache: {self._config['CACHE_TYPE']}")
        print(f"Debug: {self._config['DEBUG']}")
        print(f"API Version: {self._config['API_VERSION']}")
        print(f"Log Level: {self._config['LOG_LEVEL']}")
        print(f"CORS Origins: {self._config['CORS_ORIGINS']}")
        print("=" * 40)


# Convenience functions for backward compatibility
def get_config(env: str = None) -> Dict[str, Any]:
    """Get configuration dictionary for the specified environment.
    
    Args:
        env: Environment name (development, testing, production)
        
    Returns:
        Configuration dictionary
    """
    manager = ConfigManager(env)
    manager.validate()
    return manager.get_config()


def create_config_class(env: str = None):
    """Create a Flask configuration class for the specified environment.
    
    Args:
        env: Environment name (development, testing, production)
        
    Returns:
        Configuration class compatible with Flask
    """
    config_dict = get_config(env)
    
    class DynamicConfig:
        pass
    
    # Set all configuration values as class attributes
    for key, value in config_dict.items():
        setattr(DynamicConfig, key, value)
    
    return DynamicConfig