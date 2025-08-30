# Configuration Guide

This Flask application uses a simplified configuration management system that's easy to understand and use.

## Quick Start

The application automatically detects your environment and loads appropriate defaults:

```bash
# Development (default)
flask run

# Testing
FLASK_ENV=testing flask run

# Production
FLASK_ENV=production flask run
```

## Environment Variables

Create a `.env` file in your project root (copy from `.env.example`) and customize these key settings:

### Essential Settings

```bash
# Security (REQUIRED in production)
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite:///app.db  # Development default
# DATABASE_URL=postgresql://user:pass@localhost/dbname  # Production

# Environment
FLASK_ENV=development  # development, testing, production
DEBUG=True  # Auto-set based on environment
```

### Optional Settings

```bash
# Cache (Redis)
REDIS_URL=redis://localhost:6379/0

# JWT Tokens
JWT_ACCESS_TOKEN_EXPIRES=3600  # 1 hour in seconds
JWT_REFRESH_TOKEN_EXPIRES=30   # 30 days

# API Configuration
API_VERSION=v2
API_RATE_LIMIT=100 per hour
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# File Uploads
UPLOAD_FOLDER=uploads/
MAX_CONTENT_LENGTH=16777216  # 16MB in bytes
ALLOWED_EXTENSIONS=txt,pdf,png,jpg,jpeg,gif,csv,json

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
LOG_FILE=/path/to/logfile.log  # Optional file logging
```

## Environment-Specific Defaults

### Development

- Debug mode enabled
- SQLite database
- Detailed logging (DEBUG level)
- API documentation enabled
- CSRF protection enabled

### Testing

- In-memory SQLite database
- Minimal logging (WARNING level)
- Debug mode disabled
- Fast test execution

### Production

- Debug mode disabled
- Requires SECRET_KEY and DATABASE_URL
- Warning-level logging
- Security headers enabled
- HTTPS enforcement (if configured)

## Configuration Components

The system is organized into logical components:

### DatabaseConfig

- Connection settings
- Pool configuration
- Query recording

### CacheConfig

- Redis or simple cache
- Timeout settings
- Key prefixes

### SecurityConfig

- Secret keys
- JWT settings
- CSRF protection
- HTTPS enforcement

### APIConfig

- Versioning
- Rate limiting
- CORS settings
- Documentation

### LoggingConfig

- Log levels
- Output formats
- File logging

## Usage Examples

### Basic Usage

```python
from app import create_app

# Use default development config
app = create_app()

# Specify environment
app = create_app('production')
```

### Advanced Configuration

```python
from app.config_manager import ConfigManager

# Get configuration manager
config = ConfigManager('production')
config.validate()  # Validate settings

# Get specific values
db_url = config.get('SQLALCHEMY_DATABASE_URI')
api_version = config.get('API_VERSION', 'v1')

# Print configuration summary
config.print_summary()
```

### Custom Configuration

```python
from app.config_manager import create_config_class

# Create Flask-compatible config class
CustomConfig = create_config_class('development')

# Use with Flask
app = Flask(__name__)
app.config.from_object(CustomConfig)
```

## Validation

The configuration system automatically validates settings:

- **Production**: Ensures required environment variables are set
- **Testing**: Warns about non-optimal settings
- **Development**: Provides helpful defaults

## Migration from Old Config

If you're upgrading from the old `config.py` system:

1. **Environment Variables**: Most variables remain the same
2. **Class-based Config**: Replace with `ConfigManager`
3. **Custom Settings**: Use environment variables or extend `ConfigManager`

### Before (Old System)

```python
from app.config import ProductionConfig
app.config.from_object(ProductionConfig)
```

### After (New System)

```python
from app.config_manager import ConfigManager
config_manager = ConfigManager('production')
app.config.update(config_manager.get_config())
```

## Troubleshooting

### Common Issues

1. **Missing SECRET_KEY in Production**

   ```
   ValueError: SECRET_KEY: Production secret key is required
   ```

   Solution: Set `SECRET_KEY` environment variable

2. **Database Connection Errors**

   ```
   sqlalchemy.exc.OperationalError
   ```

   Solution: Check `DATABASE_URL` format and database availability

3. **Redis Connection Issues**

   ```
   redis.exceptions.ConnectionError
   ```

   Solution: Verify `REDIS_URL` or use simple cache (`CACHE_TYPE=simple`)

### Debug Configuration

```python
# Print all configuration values
from app.config_manager import ConfigManager
config = ConfigManager()
config.print_summary()

# Check specific values
print(f"Database: {config.get('SQLALCHEMY_DATABASE_URI')}")
print(f"Debug: {config.get('DEBUG')}")
```

## Best Practices

1. **Use Environment Variables**: Never hardcode secrets in code
2. **Validate Early**: Call `config.validate()` on startup
3. **Environment-Specific**: Use different `.env` files for each environment
4. **Security**: Use strong, unique secret keys in production
5. **Monitoring**: Enable structured logging in production

## Security Considerations

- **SECRET_KEY**: Must be cryptographically secure in production
- **Database URLs**: Don't expose credentials in logs
- **HTTPS**: Enable `FORCE_HTTPS=True` in production
- **CORS**: Restrict `CORS_ORIGINS` to trusted domains
- **File Uploads**: Limit `MAX_CONTENT_LENGTH` and `ALLOWED_EXTENSIONS`

For more details, see the `.env.example` file for all available configuration options.
