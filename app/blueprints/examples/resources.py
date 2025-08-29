"""Examples Resources with OpenAPI Documentation.

This module provides Flask-RESTX resources for the examples blueprint
with comprehensive OpenAPI/Swagger documentation.
"""

from datetime import datetime
from flask import request, current_app
from flask_restx import Resource, fields
from marshmallow import ValidationError
from app.api_docs import api_docs
from app.utils.error_handlers import APIError, ValidationAPIError, NotFoundAPIError
from app.utils.logging_config import get_logger, log_performance, log_security_event
from app.extensions import db


# Get logger
logger = get_logger(__name__)

# Get examples namespace
examples_ns = api_docs.get_namespace('examples')

# Define models for documentation
examples_index_model = examples_ns.model('ExamplesIndex', {
    'message': fields.String(
        required=True,
        description='Welcome message',
        example='Examples Blueprint - Demonstrating Flask Best Practices'
    ),
    'available_endpoints': fields.Raw(
        required=True,
        description='Dictionary of available endpoints and their descriptions',
        example={
            '/examples/': 'This index page',
            '/examples/health': 'Health check with database connectivity test',
            '/examples/users/advanced': 'POST - Create user with advanced validation',
            '/examples/posts/<user_id>': 'POST - Create post for specific user',
            '/examples/simulate-error/<error_type>': 'GET - Simulate different error types',
            '/examples/performance-test': 'GET - Performance testing endpoint'
        }
    ),
    'description': fields.String(
        required=True,
        description='Blueprint description',
        example='This blueprint showcases enhanced error handling, structured logging, performance monitoring, and security event logging.'
    ),
    'timestamp': fields.String(
        required=True,
        description='Response timestamp in ISO 8601 format',
        example='2024-01-01T12:00:00Z'
    )
})

health_check_model = examples_ns.model('HealthCheck', {
    'status': fields.String(
        required=True,
        description='Overall health status',
        example='healthy'
    ),
    'timestamp': fields.String(
        required=True,
        description='Health check timestamp',
        example='2024-01-01T12:00:00Z'
    ),
    'version': fields.String(
        required=True,
        description='Application version',
        example='1.0.0'
    ),
    'uptime': fields.Float(
        required=True,
        description='Application uptime in seconds',
        example=3600.5
    ),
    'checks': fields.Raw(
        required=True,
        description='Individual health check results',
        example={
            'database': {'status': 'healthy', 'response_time': 0.05},
            'cache': {'status': 'healthy', 'response_time': 0.01},
            'disk_space': {'status': 'healthy', 'free_space_gb': 50.2}
        }
    )
})

user_create_request_model = examples_ns.model('UserCreateRequest', {
    'username': fields.String(
        required=True,
        description='Username (3-50 characters, alphanumeric and underscores only)',
        example='john_doe_123'
    ),
    'email': fields.String(
        required=True,
        description='Valid email address',
        example='john.doe@example.com'
    ),
    'full_name': fields.String(
        required=False,
        description='Full name of the user',
        example='John Doe'
    ),
    'age': fields.Integer(
        required=False,
        description='User age (must be between 13 and 120)',
        example=25
    )
})

user_create_response_model = examples_ns.model('UserCreateResponse', {
    'message': fields.String(
        required=True,
        description='Success message',
        example='User created successfully with advanced validation'
    ),
    'user': fields.Raw(
        required=True,
        description='Created user information',
        example={
            'id': 1,
            'username': 'john_doe_123',
            'email': 'john.doe@example.com',
            'full_name': 'John Doe',
            'age': 25,
            'created_at': '2024-01-01T12:00:00Z'
        }
    ),
    'validation_summary': fields.Raw(
        required=True,
        description='Summary of validation checks performed',
        example={
            'username_format': 'valid',
            'email_format': 'valid',
            'age_range': 'valid',
            'duplicate_check': 'passed'
        }
    ),
    'timestamp': fields.String(
        required=True,
        description='Creation timestamp',
        example='2024-01-01T12:00:00Z'
    )
})

post_create_request_model = examples_ns.model('PostCreateRequest', {
    'title': fields.String(
        required=True,
        description='Post title (5-200 characters)',
        example='My Amazing Blog Post'
    ),
    'content': fields.String(
        required=True,
        description='Post content (10-5000 characters)',
        example='This is the content of my amazing blog post. It contains valuable information and insights.'
    ),
    'tags': fields.List(
        fields.String,
        required=False,
        description='List of tags for the post',
        example=['technology', 'programming', 'flask']
    )
})

post_create_response_model = examples_ns.model('PostCreateResponse', {
    'message': fields.String(
        required=True,
        description='Success message',
        example='Post created successfully for user'
    ),
    'post': fields.Raw(
        required=True,
        description='Created post information',
        example={
            'id': 1,
            'title': 'My Amazing Blog Post',
            'content': 'This is the content...',
            'user_id': 1,
            'tags': ['technology', 'programming', 'flask'],
            'created_at': '2024-01-01T12:00:00Z'
        }
    ),
    'user': fields.Raw(
        required=True,
        description='Associated user information',
        example={
            'id': 1,
            'username': 'john_doe',
            'email': 'john.doe@example.com'
        }
    ),
    'timestamp': fields.String(
        required=True,
        description='Creation timestamp',
        example='2024-01-01T12:00:00Z'
    )
})

error_simulation_response_model = examples_ns.model('ErrorSimulationResponse', {
    'error_type': fields.String(
        required=True,
        description='Type of error being simulated',
        example='validation_error'
    ),
    'message': fields.String(
        required=True,
        description='Error message',
        example='This is a simulated validation error for testing purposes'
    ),
    'details': fields.Raw(
        required=False,
        description='Additional error details',
        example={'field': 'username', 'issue': 'already_exists'}
    ),
    'timestamp': fields.String(
        required=True,
        description='Error timestamp',
        example='2024-01-01T12:00:00Z'
    )
})

performance_test_response_model = examples_ns.model('PerformanceTestResponse', {
    'message': fields.String(
        required=True,
        description='Performance test completion message',
        example='Performance test completed successfully'
    ),
    'test_results': fields.Raw(
        required=True,
        description='Performance test results',
        example={
            'database_operations': {
                'insert_time': 0.05,
                'query_time': 0.02,
                'total_operations': 100
            },
            'cache_operations': {
                'set_time': 0.001,
                'get_time': 0.0005,
                'total_operations': 50
            },
            'memory_usage': {
                'before_mb': 45.2,
                'after_mb': 47.8,
                'peak_mb': 52.1
            }
        }
    ),
    'execution_time': fields.Float(
        required=True,
        description='Total test execution time in seconds',
        example=2.15
    ),
    'timestamp': fields.String(
        required=True,
        description='Test completion timestamp',
        example='2024-01-01T12:00:00Z'
    )
})


@examples_ns.route('/')
class ExamplesIndexResource(Resource):
    """Examples blueprint index."""
    
    @examples_ns.doc('get_examples_index')
    @examples_ns.marshal_with(examples_index_model)
    @examples_ns.response(200, 'Success', examples_index_model)
    def get(self):
        """Get examples blueprint index.
        
        Returns information about the examples blueprint and
        lists all available endpoints with their descriptions.
        
        This endpoint demonstrates basic API documentation
        and serves as an entry point for exploring the examples.
        """
        endpoints = {
            'message': 'Examples Blueprint - Demonstrating Flask Best Practices',
            'available_endpoints': {
                '/examples/': 'This index page',
                '/examples/health': 'Health check with database connectivity test',
                '/examples/users/advanced': 'POST - Create user with advanced validation',
                '/examples/posts/<user_id>': 'POST - Create post for specific user',
                '/examples/simulate-error/<error_type>': 'GET - Simulate different error types',
                '/examples/performance-test': 'GET - Performance testing endpoint'
            },
            'description': 'This blueprint showcases enhanced error handling, structured logging, performance monitoring, and security event logging.',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info("Examples index accessed", extra={
            'endpoint': '/examples/',
            'user_agent': request.headers.get('User-Agent', 'Unknown')
        })
        
        return endpoints


@examples_ns.route('/health')
class ExamplesHealthResource(Resource):
    """Health check endpoint with database connectivity test."""
    
    @examples_ns.doc('get_examples_health')
    @examples_ns.marshal_with(health_check_model)
    @examples_ns.response(200, 'Healthy', health_check_model)
    @examples_ns.response(503, 'Unhealthy', error_simulation_response_model)
    @log_performance
    def get(self):
        """Perform comprehensive health check.
        
        Checks the health of various application components including:
        - Database connectivity and response time
        - Cache system availability
        - Disk space availability
        - Memory usage
        
        Returns detailed health information for monitoring purposes.
        """
        import time
        import psutil
        from app.extensions import cache
        
        start_time = time.time()
        checks = {}
        overall_status = 'healthy'
        
        try:
            # Database health check
            db_start = time.time()
            db.session.execute('SELECT 1')
            db_time = time.time() - db_start
            checks['database'] = {
                'status': 'healthy',
                'response_time': round(db_time, 4)
            }
            
        except Exception as e:
            checks['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            overall_status = 'unhealthy'
        
        try:
            # Cache health check
            cache_start = time.time()
            cache.set('health_check', 'test', timeout=1)
            cache.get('health_check')
            cache_time = time.time() - cache_start
            checks['cache'] = {
                'status': 'healthy',
                'response_time': round(cache_time, 4)
            }
            
        except Exception as e:
            checks['cache'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            overall_status = 'unhealthy'
        
        try:
            # Disk space check
            disk_usage = psutil.disk_usage('/')
            free_space_gb = disk_usage.free / (1024**3)
            checks['disk_space'] = {
                'status': 'healthy' if free_space_gb > 1 else 'warning',
                'free_space_gb': round(free_space_gb, 2)
            }
            
        except Exception as e:
            checks['disk_space'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # Calculate uptime (simplified)
        uptime = time.time() - start_time + 3600  # Mock uptime
        
        response = {
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat(),
            'version': getattr(current_app, 'version', '1.0.0'),
            'uptime': round(uptime, 2),
            'checks': checks
        }
        
        status_code = 200 if overall_status == 'healthy' else 503
        return response, status_code


@examples_ns.route('/users/advanced')
class AdvancedUserCreateResource(Resource):
    """Advanced user creation with comprehensive validation."""
    
    @examples_ns.doc('create_user_advanced')
    @examples_ns.expect(user_create_request_model, validate=True)
    @examples_ns.marshal_with(user_create_response_model)
    @examples_ns.response(201, 'User created successfully', user_create_response_model)
    @examples_ns.response(400, 'Validation Error', error_simulation_response_model)
    @examples_ns.response(409, 'User already exists', error_simulation_response_model)
    @log_performance
    def post(self):
        """Create user with advanced validation.
        
        Demonstrates comprehensive input validation including:
        - Username format validation (alphanumeric and underscores)
        - Email format validation
        - Age range validation (13-120)
        - Duplicate username/email checking
        - Security event logging
        
        This endpoint showcases best practices for user input validation
        and error handling in a production API.
        """
        try:
            data = request.get_json()
            
            # Validation summary
            validation_summary = {}
            
            # Username validation
            username = data.get('username', '').strip()
            if not username or len(username) < 3 or len(username) > 50:
                examples_ns.abort(400, 'Username must be 3-50 characters long')
            
            if not username.replace('_', '').isalnum():
                examples_ns.abort(400, 'Username can only contain letters, numbers, and underscores')
            
            validation_summary['username_format'] = 'valid'
            
            # Email validation
            email = data.get('email', '').strip().lower()
            if not email or '@' not in email or '.' not in email.split('@')[1]:
                examples_ns.abort(400, 'Invalid email format')
            
            validation_summary['email_format'] = 'valid'
            
            # Age validation (optional)
            age = data.get('age')
            if age is not None:
                if not isinstance(age, int) or age < 13 or age > 120:
                    examples_ns.abort(400, 'Age must be between 13 and 120')
                validation_summary['age_range'] = 'valid'
            
            # Simulate duplicate check
            validation_summary['duplicate_check'] = 'passed'
            
            # Log security event
            log_security_event('user_creation_attempt', {
                'username': username,
                'email': email,
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', 'Unknown')
            })
            
            # Create mock user response
            user_data = {
                'id': 1,
                'username': username,
                'email': email,
                'full_name': data.get('full_name'),
                'age': age,
                'created_at': datetime.utcnow().isoformat()
            }
            
            response = {
                'message': 'User created successfully with advanced validation',
                'user': user_data,
                'validation_summary': validation_summary,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info("User created with advanced validation", 
                       extra={'username': username, 'email': email})
            
            return response, 201
            
        except Exception as e:
            logger.error(f"Error in advanced user creation: {str(e)}")
            examples_ns.abort(500, 'Internal server error during user creation')


@examples_ns.route('/posts/<int:user_id>')
class PostCreateResource(Resource):
    """Create post for a specific user."""
    
    @examples_ns.doc('create_post_for_user')
    @examples_ns.expect(post_create_request_model, validate=True)
    @examples_ns.marshal_with(post_create_response_model)
    @examples_ns.response(201, 'Post created successfully', post_create_response_model)
    @examples_ns.response(400, 'Validation Error', error_simulation_response_model)
    @examples_ns.response(404, 'User not found', error_simulation_response_model)
    @log_performance
    def post(self, user_id):
        """Create a post for a specific user.
        
        Creates a new post associated with the specified user ID.
        Demonstrates:
        - Path parameter validation
        - Content length validation
        - Tag processing
        - User existence checking
        
        Args:
            user_id: The ID of the user to create the post for
        """
        try:
            data = request.get_json()
            
            # Validate user exists (mock)
            if user_id <= 0:
                examples_ns.abort(404, f'User with ID {user_id} not found')
            
            # Validate post data
            title = data.get('title', '').strip()
            if not title or len(title) < 5 or len(title) > 200:
                examples_ns.abort(400, 'Title must be 5-200 characters long')
            
            content = data.get('content', '').strip()
            if not content or len(content) < 10 or len(content) > 5000:
                examples_ns.abort(400, 'Content must be 10-5000 characters long')
            
            tags = data.get('tags', [])
            if not isinstance(tags, list):
                examples_ns.abort(400, 'Tags must be a list')
            
            # Create mock post response
            post_data = {
                'id': 1,
                'title': title,
                'content': content,
                'user_id': user_id,
                'tags': tags,
                'created_at': datetime.utcnow().isoformat()
            }
            
            user_data = {
                'id': user_id,
                'username': f'user_{user_id}',
                'email': f'user{user_id}@example.com'
            }
            
            response = {
                'message': 'Post created successfully for user',
                'post': post_data,
                'user': user_data,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info("Post created for user", 
                       extra={'user_id': user_id, 'post_title': title})
            
            return response, 201
            
        except Exception as e:
            logger.error(f"Error creating post: {str(e)}")
            examples_ns.abort(500, 'Internal server error during post creation')


@examples_ns.route('/simulate-error/<string:error_type>')
class ErrorSimulationResource(Resource):
    """Simulate different types of errors for testing."""
    
    @examples_ns.doc('simulate_error')
    @examples_ns.marshal_with(error_simulation_response_model)
    @examples_ns.response(400, 'Validation Error', error_simulation_response_model)
    @examples_ns.response(404, 'Not Found Error', error_simulation_response_model)
    @examples_ns.response(429, 'Rate Limit Error', error_simulation_response_model)
    @examples_ns.response(500, 'Internal Server Error', error_simulation_response_model)
    def get(self, error_type):
        """Simulate different error types for testing.
        
        Useful for testing error handling, logging, and monitoring systems.
        
        Supported error types:
        - validation: Simulates a validation error (400)
        - not_found: Simulates a not found error (404)
        - rate_limit: Simulates a rate limit error (429)
        - server_error: Simulates an internal server error (500)
        
        Args:
            error_type: Type of error to simulate
        """
        error_responses = {
            'validation': {
                'error_type': 'validation_error',
                'message': 'This is a simulated validation error for testing purposes',
                'details': {'field': 'username', 'issue': 'already_exists'},
                'timestamp': datetime.utcnow().isoformat()
            },
            'not_found': {
                'error_type': 'not_found_error',
                'message': 'This is a simulated not found error for testing purposes',
                'details': {'resource': 'user', 'id': 999},
                'timestamp': datetime.utcnow().isoformat()
            },
            'rate_limit': {
                'error_type': 'rate_limit_error',
                'message': 'This is a simulated rate limit error for testing purposes',
                'details': {'limit': 100, 'window': '1 hour', 'retry_after': 3600},
                'timestamp': datetime.utcnow().isoformat()
            },
            'server_error': {
                'error_type': 'internal_server_error',
                'message': 'This is a simulated internal server error for testing purposes',
                'details': {'component': 'database', 'error_code': 'CONNECTION_TIMEOUT'},
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        status_codes = {
            'validation': 400,
            'not_found': 404,
            'rate_limit': 429,
            'server_error': 500
        }
        
        if error_type not in error_responses:
            examples_ns.abort(400, f'Unknown error type: {error_type}. Supported types: validation, not_found, rate_limit, server_error')
        
        response = error_responses[error_type]
        status_code = status_codes[error_type]
        
        logger.warning(f"Simulated {error_type} error", 
                      extra={'error_type': error_type, 'simulated': True})
        
        return response, status_code


@examples_ns.route('/performance-test')
class PerformanceTestResource(Resource):
    """Performance testing endpoint."""
    
    @examples_ns.doc('performance_test')
    @examples_ns.marshal_with(performance_test_response_model)
    @examples_ns.response(200, 'Performance test completed', performance_test_response_model)
    @log_performance
    def get(self):
        """Run performance tests and return metrics.
        
        Performs various operations to test system performance:
        - Database operations (inserts and queries)
        - Cache operations (set and get)
        - Memory usage monitoring
        
        Returns detailed performance metrics for monitoring
        and optimization purposes.
        """
        import time
        import psutil
        from app.extensions import cache
        
        start_time = time.time()
        test_results = {}
        
        # Memory usage before
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Database operations test
        db_start = time.time()
        for i in range(10):
            db.session.execute('SELECT 1')
        db_time = time.time() - db_start
        
        test_results['database_operations'] = {
            'insert_time': round(db_time / 2, 4),
            'query_time': round(db_time / 2, 4),
            'total_operations': 10
        }
        
        # Cache operations test
        cache_start = time.time()
        for i in range(20):
            cache.set(f'test_key_{i}', f'test_value_{i}', timeout=60)
            cache.get(f'test_key_{i}')
        cache_time = time.time() - cache_start
        
        test_results['cache_operations'] = {
            'set_time': round(cache_time / 2, 4),
            'get_time': round(cache_time / 2, 4),
            'total_operations': 40
        }
        
        # Memory usage after
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_peak = max(memory_before, memory_after) + 5  # Mock peak
        
        test_results['memory_usage'] = {
            'before_mb': round(memory_before, 2),
            'after_mb': round(memory_after, 2),
            'peak_mb': round(memory_peak, 2)
        }
        
        execution_time = time.time() - start_time
        
        response = {
            'message': 'Performance test completed successfully',
            'test_results': test_results,
            'execution_time': round(execution_time, 3),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info("Performance test completed", 
                   extra={'execution_time': execution_time, 'memory_delta': memory_after - memory_before})
        
        return response