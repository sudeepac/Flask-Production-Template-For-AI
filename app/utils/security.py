"""Security Utilities.

This module provides security-related utility functions including
password hashing, token generation, and security validation.

Features:
- Secure password hashing with bcrypt
- Token generation and validation
- Security decorators
- Input sanitization

Usage:
    from app.utils.security import hash_password, check_password

    # Hash a password
    hashed = hash_password('my_password')

    # Verify a password
    is_valid = check_password('my_password', hashed)
"""

import secrets
import string
from functools import wraps
from typing import Optional

import bcrypt
from flask import current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password to hash

    Returns:
        str: Hashed password

    Example:
        hashed = hash_password('my_secure_password')
    """
    if not password:
        raise ValueError("Password cannot be empty")

    # Use bcrypt for secure password hashing
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def check_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    Args:
        password: Plain text password to verify
        hashed_password: Hashed password to check against

    Returns:
        bool: True if password matches, False otherwise

    Example:
        is_valid = check_password('my_password', stored_hash)
    """
    if not password or not hashed_password:
        return False

    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token.

    Args:
        length: Length of the token

    Returns:
        str: Secure random token
    """
    return secrets.token_urlsafe(length)


def generate_api_key(prefix: str = "ak", length: int = 32) -> str:
    """Generate an API key with a prefix.

    Args:
        prefix: Prefix for the API key
        length: Length of the random part

    Returns:
        str: Generated API key
    """
    random_part = secrets.token_urlsafe(length)
    return f"{prefix}_{random_part}"


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input by removing potentially dangerous characters.

    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length

    Returns:
        str: Sanitized text
    """
    if not text:
        return ""

    # Remove null bytes and control characters
    sanitized = "".join(char for char in text if ord(char) >= 32 or char in "\n\r\t")

    # Truncate to max length
    return sanitized[:max_length]


def require_api_key(f):
    """Decorator to require API key authentication.

    Checks for API key in X-API-Key header.

    Usage:
        @blueprint.route('/protected')
        @require_api_key
        def protected_endpoint():
            return {'message': 'Access granted'}
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        """Decorated function with API key validation."""
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            return (
                jsonify(
                    {
                        "error": "API key required",
                        "message": "Please provide X-API-Key header",
                    }
                ),
                401,
            )

        # Here you would validate the API key against your database
        # For now, we'll just check if it's not empty
        # TODO: Implement proper API key validation

        return f(*args, **kwargs)

    return decorated_function


def require_auth(f):
    """Decorator to require JWT authentication.

    Combines @jwt_required with additional security checks.

    Usage:
        @blueprint.route('/protected')
        @require_auth
        def protected_endpoint():
            user_id = get_jwt_identity()
            return {'user_id': user_id}
    """

    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        """Decorated function with role-based access control."""
        # Additional security checks can be added here
        # For example: check if user is active, not banned, etc.

        return f(*args, **kwargs)

    return decorated_function


def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """Validate password strength.

    Args:
        password: Password to validate

    Returns:
        tuple: (is_valid, list_of_errors)
    """
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")

    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")

    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")

    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")

    if not any(c in string.punctuation for c in password):
        errors.append("Password must contain at least one special character")

    return len(errors) == 0, errors


def is_safe_url(target: str) -> bool:
    """Check if a URL is safe for redirects.

    Args:
        target: URL to check

    Returns:
        bool: True if URL is safe, False otherwise
    """
    if not target:
        return False

    # Basic checks for safe URLs
    # In a real application, you'd want more sophisticated validation
    dangerous_schemes = ["javascript:", "data:", "vbscript:"]

    target_lower = target.lower().strip()

    for scheme in dangerous_schemes:
        if target_lower.startswith(scheme):
            return False

    return True
