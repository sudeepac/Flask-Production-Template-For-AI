# Error Handling and Logging Guide

This guide demonstrates the enhanced error handling and logging implementation in the Flask Production Template.

## Overview

The boilerplate includes a comprehensive error handling and logging system that provides:

- **Structured Error Handling**: Custom exception classes with consistent error responses
- **Enhanced Logging**: JSON-structured logging with request correlation and performance metrics
- **Security Event Logging**: Dedicated logging for security-related events
- **Performance Monitoring**: Automatic performance tracking for endpoints
- **Request Correlation**: Unique request IDs for tracing requests across services

## Error Handling

### Custom Exception Classes

The system provides several custom exception classes in `app/utils/error_handlers.py`:

```python
# Base API error
class APIError(Exception):
    """Base API error with structured response"""
    
# Specific error types
class ValidationError(APIError):
    """Input validation errors"""
    
class NotFoundError(APIError):
    """Resource not found errors"""
    
class DatabaseError(APIError):
    """Database operation errors"""
    
class AuthenticationError(APIError):
    """Authentication/authorization errors"""
    
class RateLimitError(APIError):
    """Rate limiting errors"""
```

### Usage in Routes

```python
from app.utils.error_handlers import ValidationError, NotFoundError

@blueprint.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError(f"User with ID {user_id} not found")
    
    return jsonify(user.to_dict())
```

### Error Response Format

All errors return a consistent JSON structure:

```json
{
    "error": {
        "type": "validation_error",
        "message": "Invalid input data",
        "details": {
            "username": ["Username must be at least 3 characters"]
        },
        "request_id": "req_123456789",
        "timestamp": "2024-01-20T10:30:00Z"
    }
}
```

## Logging System

### Logger Configuration

The logging system is configured in `app/utils/logging_config.py` and provides:

- **Development**: Console logging with colored output
- **Production**: JSON-structured logging with file rotation
- **Request Correlation**: Automatic request ID generation and tracking
- **Performance Metrics**: Automatic timing for decorated endpoints

### Getting a Logger

```python
from app.utils.logging_config import get_logger

logger = get_logger(__name__)
```

### Structured Logging

```python
# Basic logging
logger.info("User created successfully")

# Structured logging with extra context
logger.info("User created successfully", extra={
    'user_id': user.id,
    'username': username,
    'ip_address': request.remote_addr
})

# Error logging with context
logger.error("Database error occurred", extra={
    'error_type': type(e).__name__,
    'operation': 'user_creation',
    'user_data': {'username': username}
})
```

### Performance Logging

Use the `@log_performance` decorator to automatically track endpoint performance:

```python
from app.utils.logging_config import log_performance

@blueprint.route('/users', methods=['GET'])
@log_performance
def get_users():
    # Endpoint logic here
    pass
```

This automatically logs:
- Request start time
- Request duration
- Response status code
- Request method and path

### Security Event Logging

```python
from app.utils.logging_config import log_security_event

# Log security events
log_security_event('user_login', {
    'user_id': user.id,
    'ip_address': request.remote_addr,
    'user_agent': request.headers.get('User-Agent'),
    'success': True
})

log_security_event('failed_login_attempt', {
    'username': username,
    'ip_address': request.remote_addr,
    'reason': 'invalid_password'
})
```

## Example Service Implementation

The `app/services/example_service.py` demonstrates best practices:

```python
class ExampleService:
    def create_user_with_posts(self, username: str, email: str, post_titles: List[str]):
        """Create user with posts using proper error handling and logging."""
        
        # Input validation
        self._validate_user_input(username, email)
        
        try:
            # Database operations with transaction
            user = User(username=username, email=email)
            db.session.add(user)
            db.session.flush()  # Get ID without committing
            
            # Create posts
            for title in post_titles:
                post = Post(title=title, user_id=user.id)
                db.session.add(post)
            
            db.session.commit()
            
            # Log success
            logger.info("User and posts created", extra={
                'user_id': user.id,
                'post_count': len(post_titles)
            })
            
            return self._format_response(user, posts)
            
        except ValidationError:
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Database error: {e}", extra={
                'operation': 'create_user_with_posts',
                'error_type': type(e).__name__
            })
            raise DatabaseError("Failed to create user with posts")
```

## Example Endpoints

The `/examples` blueprint provides comprehensive examples:

### Health Check with Error Handling

```bash
GET /examples/health
```

Returns system health status with database connectivity check.

### Advanced User Creation

```bash
POST /examples/users/advanced
Content-Type: application/json

{
    "username": "john_doe",
    "email": "john@example.com",
    "bio": "Software developer"
}
```

Demonstrates:
- Schema validation with Marshmallow
- Business logic validation
- Database transaction management
- Security event logging
- Comprehensive error handling

### Post Creation with User Validation

```bash
POST /examples/posts/1
Content-Type: application/json

{
    "title": "My First Post",
    "content": "This is the content of my first post.",
    "tags": ["introduction", "first-post"]
}
```

### Error Simulation

```bash
GET /examples/simulate-error/validation
GET /examples/simulate-error/not_found
GET /examples/simulate-error/database
GET /examples/simulate-error/auth
GET /examples/simulate-error/unexpected
```

These endpoints simulate different error types for testing error handling.

### Performance Testing

```bash
GET /examples/performance-test
```

Demonstrates performance logging with simulated work.

## Best Practices

### 1. Always Use Structured Logging

```python
# Good
logger.info("User operation completed", extra={
    'user_id': user.id,
    'operation': 'update_profile',
    'duration_ms': duration
})

# Avoid
logger.info(f"User {user.id} updated profile in {duration}ms")
```

### 2. Handle Exceptions at the Right Level

```python
# Service layer - convert to domain exceptions
try:
    db.session.commit()
except SQLAlchemyError as e:
    db.session.rollback()
    logger.error("Database error", extra={'error': str(e)})
    raise DatabaseError("Failed to save user")

# Route layer - let error handlers manage the response
try:
    result = service.create_user(data)
    return jsonify(result), 201
except ValidationError:
    raise  # Let error handler format response
```

### 3. Use Request Correlation IDs

Request IDs are automatically generated and available in `g.request_id`:

```python
logger.info("Processing request", extra={
    'request_id': g.request_id,
    'operation': 'user_creation'
})
```

### 4. Log Security Events

```python
# Always log security-relevant events
log_security_event('password_change', {
    'user_id': user.id,
    'ip_address': request.remote_addr,
    'timestamp': datetime.utcnow().isoformat()
})
```

### 5. Use Performance Decorators

```python
@blueprint.route('/expensive-operation', methods=['POST'])
@log_performance  # Automatically tracks timing
def expensive_operation():
    # Your logic here
    pass
```

## Configuration

### Environment Variables

```bash
# Logging configuration
LOG_LEVEL=INFO
LOG_FORMAT=json  # or 'console' for development
LOG_FILE=logs/app.log
LOG_MAX_BYTES=10485760  # 10MB
LOG_BACKUP_COUNT=5

# Error handling
DEBUG=False  # Set to True for development
```

### Development vs Production

- **Development**: Console logging with colors, detailed error messages
- **Production**: JSON logging to files, sanitized error responses

## Testing Error Handling

Test your error handling with the simulation endpoints:

```bash
# Test validation error
curl -X GET http://localhost:5000/examples/simulate-error/validation

# Test not found error
curl -X GET http://localhost:5000/examples/simulate-error/not_found

# Test database error
curl -X GET http://localhost:5000/examples/simulate-error/database
```

Each will return a properly formatted error response with appropriate HTTP status codes.

## Monitoring and Alerting

The structured logging format makes it easy to:

1. **Parse logs** with tools like ELK stack, Fluentd, or Datadog
2. **Set up alerts** based on error rates or specific error types
3. **Track performance** metrics across endpoints
4. **Monitor security** events and suspicious activities
5. **Debug issues** using request correlation IDs

Example log parsing query (for ELK):

```json
{
  "query": {
    "bool": {
      "must": [
        {"match": {"level": "ERROR"}},
        {"range": {"timestamp": {"gte": "now-1h"}}}
      ]
    }
  }
}
```

This comprehensive error handling and logging system provides a solid foundation for production Flask applications with proper observability and debugging capabilities.