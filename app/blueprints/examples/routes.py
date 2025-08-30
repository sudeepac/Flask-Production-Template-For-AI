"""Example routes demonstrating best practices for error handling and logging.

This module provides comprehensive examples of:
- Structured error handling with custom exceptions
- Performance logging and monitoring
- Security event logging
- Input validation patterns
- Database transaction management
- Request correlation tracking
"""

import time
from datetime import datetime

from marshmallow import Schema

from app.models.example import Post, User
from app.utils.common_imports import (
    APIError,
    CommonFields,
    NotFoundAPIError,
    ValidationAPIError,
    db,
    error_response,
    fields,
    get_jwt_identity,
    get_module_logger,
    handle_api_errors,
    handle_common_exceptions,
    jsonify,
    jwt_required,
    limiter,
    log_endpoint_access,
    log_performance,
    log_security_event,
    request,
    success_response,
    validate_json_input,
)
from app.utils.error_handlers import RateLimitAPIError, UnauthorizedAPIError

from . import blueprint

# Logger instance
logger = get_module_logger(__name__)


# Validation schemas
class UserCreateSchema(Schema):
    """Schema for user creation validation."""

    username = CommonFields.username
    email = CommonFields.email
    bio = fields.Str(validate=fields.Length(max=500))


class PostCreateSchema(Schema):
    """Schema for post creation validation."""

    title = CommonFields.title
    content = fields.Str(
        required=True,
        description="Post content",
        validate=fields.Length(min=1, max=5000),
    )
    tags = fields.List(fields.Str(), load_default=[])


user_create_schema = UserCreateSchema()
post_create_schema = PostCreateSchema()


@blueprint.route("/", methods=["GET"])
@handle_common_exceptions
def index():
    """Examples blueprint index - lists available endpoints."""
    endpoints = {
        "message": "Examples Blueprint - Demonstrating Flask Best Practices",
        "available_endpoints": {
            "/examples/": "This index page",
            "/examples/health": "Health check with database connectivity test",
            "/examples/users/advanced": ("POST - Create user with advanced validation"),
            "/examples/posts/<user_id>": (
                "POST - Create post for specific user (JWT required)"
            ),
            "/examples/profile": ("GET - Get current user profile (JWT required)"),
            "/examples/simulate-error/<error_type>": (
                "GET - Simulate different error types"
            ),
            "/examples/performance-test": "GET - Performance testing endpoint",
        },
        "description": (
            "This blueprint showcases enhanced error handling, "
            "structured logging, "
            "performance monitoring, and security event logging."
        ),
        "timestamp": datetime.utcnow().isoformat(),
    }

    logger.info(
        "Examples index accessed",
        extra={
            "endpoint": "/examples/",
            "user_agent": request.headers.get("User-Agent", "Unknown"),
        },
    )

    return success_response(endpoints)


@blueprint.route("/health", methods=["GET"])
@log_performance
@handle_common_exceptions
def health_check():
    """Health check endpoint with comprehensive status reporting."""
    start_time = time.time()

    # Check database connectivity
    db_status = "healthy"
    try:
        db.session.execute("SELECT 1")
        db_latency = round((time.time() - start_time) * 1000, 2)
    except Exception as e:
        db_status = "unhealthy"
        db_latency = None
        logger.error(
            f"Database health check failed: {e}",
            extra={"error_type": type(e).__name__},
        )

    # System status
    status = {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "database": {"status": db_status, "latency_ms": db_latency},
        "uptime_seconds": round(time.time() - start_time, 2),
    }

    logger.info(
        "Health check completed",
        extra={
            "db_status": db_status,
            "db_latency_ms": db_latency,
            "overall_status": status["status"],
        },
    )

    if status["status"] == "healthy":
        return success_response(data=status, message="Service is healthy")
    else:
        return error_response(
            message="Service is unhealthy", data=status, status_code=503
        )


@blueprint.route("/users/advanced", methods=["POST"])
@limiter.limit("5 per minute")
@log_performance
@handle_api_errors
@validate_json_input(UserCreateSchema)
@log_endpoint_access
def create_user_advanced(validated_data):
    """Advanced user creation with comprehensive error handling.

    This endpoint demonstrates:
    - Input validation with detailed error messages
    - Business logic validation
    - Database transaction management
    - Comprehensive logging and monitoring
    - Security event logging
    - Rate limiting

    Returns:
        201: User created successfully
        400: Validation error
        409: User already exists
        429: Rate limit exceeded
        500: Internal server error
    """
    # Business logic validation
    username = validated_data["username"].strip()
    email = validated_data["email"].strip().lower()
    bio = validated_data.get("bio", "").strip()

    # Check for existing user
    existing_user = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()

    if existing_user:
        conflict_field = "username" if existing_user.username == username else "email"
        logger.warning(
            f"User creation conflict: {conflict_field} already exists",
            extra={
                "conflict_field": conflict_field,
                "attempted_username": username,
                "attempted_email": email,
            },
        )
        raise ValidationAPIError(f"{conflict_field.title()} already exists")

    # Create user with transaction
    try:
        user = User(username=username, email=email)
        if bio:
            # Assuming User model has a bio field
            setattr(user, "bio", bio)

        db.session.add(user)
        db.session.commit()

        # Log successful creation
        logger.info(
            "User created successfully",
            extra={
                "user_id": user.id,
                "username": username,
                "email": email,
                "has_bio": bool(bio),
            },
        )

        # Log security event
        log_security_event(
            "user_registration",
            {
                "user_id": user.id,
                "username": username,
                "ip_address": request.remote_addr,
                "user_agent": request.headers.get("User-Agent", "unknown"),
            },
        )

        response_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.isoformat(),
        }

        if bio:
            response_data["bio"] = bio

        return success_response(
            data=response_data, message="User created successfully", status_code=201
        )

    except Exception as e:
        db.session.rollback()
        logger.error(
            f"Database error during user creation: {e}",
            extra={
                "username": username,
                "email": email,
                "error_type": type(e).__name__,
            },
        )
        raise APIError("Failed to create user")


@blueprint.route("/posts/<int:user_id>", methods=["POST"])
@jwt_required()
@limiter.limit("10 per minute")
@handle_api_errors
@validate_json_input(post_create_schema)
@log_endpoint_access
@log_performance
def create_post_for_user(user_id: int, validated_data):
    """Create a post for a specific user with comprehensive error handling."""
    # Get authenticated user ID from JWT
    current_user_id = get_jwt_identity()

    # Check if user is trying to create post for themselves
    if current_user_id != user_id:
        logger.warning(
            "User attempted to create post for another user",
            extra={
                "current_user_id": current_user_id,
                "target_user_id": user_id,
                "ip_address": request.remote_addr,
            },
        )
        raise UnauthorizedAPIError("You can only create posts for yourself")

    # Validate user exists
    user = User.query.get(user_id)
    if not user:
        logger.warning(
            "Attempted to create post for non-existent user",
            extra={"user_id": user_id, "ip_address": request.remote_addr},
        )
        raise NotFoundAPIError(f"User with ID {user_id} not found")

        # Create post
    try:
        post = Post(
            title=validated_data["title"].strip(),
            content=validated_data["content"].strip(),
            user_id=user_id,
        )

        db.session.add(post)
        db.session.commit()

        logger.info(
            "Post created successfully",
            extra={
                "post_id": post.id,
                "user_id": user_id,
                "title": post.title,
                "content_length": len(post.content),
            },
        )

        # Log security event
        log_security_event(
            "post_created",
            {
                "post_id": post.id,
                "user_id": user_id,
                "title": post.title,
                "ip_address": request.remote_addr,
            },
        )

        response_data = {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "user_id": post.user_id,
            "created_at": post.created_at.isoformat(),
        }

        return success_response(
            data=response_data, message="Post created successfully", status_code=201
        )

    except Exception as e:
        db.session.rollback()
        logger.error(
            f"Database error creating post: {e}",
            extra={"user_id": user_id, "error_type": type(e).__name__},
        )
        raise APIError("Failed to create post")


@blueprint.route("/simulate-error/<error_type>", methods=["GET"])
@log_performance
def simulate_error(error_type: str):
    """Simulate different types of errors for testing error handling."""
    logger.info(
        f"Simulating error type: {error_type}",
        extra={"error_type": error_type, "ip_address": request.remote_addr},
    )

    if error_type == "validation":
        raise ValidationAPIError("This is a simulated validation error")
    elif error_type == "not_found":
        raise NotFoundAPIError("This is a simulated not found error")
    elif error_type == "database":
        raise APIError("This is a simulated database error")
    elif error_type == "auth":
        raise UnauthorizedAPIError("This is a simulated authentication error")
    elif error_type == "rate_limit":
        raise RateLimitAPIError("This is a simulated rate limit error")
    elif error_type == "unexpected":
        raise Exception("This is a simulated unexpected error")
    else:
        raise ValidationAPIError(f"Unknown error type: {error_type}")


@blueprint.route("/performance-test", methods=["GET"])
@log_performance
def performance_test():
    """Endpoint for testing performance logging."""
    # Simulate some work
    import time

    time.sleep(0.1)  # 100ms delay

    # Simulate database query
    user_count = User.query.count()
    post_count = Post.query.count()

    logger.info(
        "Performance test completed",
        extra={
            "user_count": user_count,
            "post_count": post_count,
            "simulated_delay_ms": 100,
        },
    )

    return jsonify(
        {
            "message": "Performance test completed",
            "stats": {"users": user_count, "posts": post_count, "delay_ms": 100},
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@blueprint.route("/profile", methods=["GET"])
@jwt_required()
@log_performance
def get_user_profile():
    """Get current authenticated user's profile.

    Demonstrates JWT protection.
    """
    try:
        # Get authenticated user ID from JWT
        current_user_id = get_jwt_identity()

        logger.info(
            "User profile requested",
            extra={
                "user_id": current_user_id,
                "endpoint": "get_user_profile",
                "ip_address": request.remote_addr,
            },
        )

        # Get user from database
        user = User.query.get(current_user_id)
        if not user:
            logger.error(
                "JWT token contains invalid user ID",
                extra={"user_id": current_user_id, "ip_address": request.remote_addr},
            )
            raise NotFoundAPIError("User not found")

        # Get user's posts count
        posts_count = Post.query.filter_by(user_id=current_user_id).count()

        # Log security event
        log_security_event(
            "profile_accessed",
            {
                "user_id": current_user_id,
                "username": user.username,
                "ip_address": request.remote_addr,
            },
        )

        profile_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.isoformat(),
            "last_login": (user.last_login.isoformat() if user.last_login else None),
            "posts_count": posts_count,
            "profile_accessed_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            "User profile retrieved successfully",
            extra={"user_id": current_user_id, "posts_count": posts_count},
        )

        return success_response(
            data=profile_data, message="User profile retrieved successfully"
        )

    except NotFoundAPIError:
        raise  # Re-raise not found errors
    except Exception as e:
        logger.error(
            f"Error retrieving user profile: {e}",
            extra={
                "user_id": (
                    current_user_id if "current_user_id" in locals() else "unknown"
                ),
                "error_type": type(e).__name__,
                "ip_address": request.remote_addr,
            },
        )
        raise APIError("Failed to retrieve user profile")
