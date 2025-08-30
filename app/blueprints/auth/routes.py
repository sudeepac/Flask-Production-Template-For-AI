"""Authentication routes.

Handles user authentication including registration, login, logout,
and JWT token management.
"""

from datetime import timedelta

from flask import request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

from app.extensions import db, jwt
from app.models.example import User
from app.utils.logging_config import log_security_event
from app.utils.response_helpers import (
    already_exists_error,
    error_response,
    handle_common_exceptions,
    invalid_credentials_error,
    missing_fields_error,
    no_data_provided_error,
    success_response,
    token_revoked_error,
    user_not_found_error,
)
from app.utils.security import validate_password_strength

from . import blueprint

# Token blacklist for logout functionality
blacklisted_tokens = set()


@blueprint.route("/register", methods=["POST"])
@handle_common_exceptions
def register():
    """Register a new user.

    Expected JSON payload:
    {
        "username": "string",
        "email": "string",
        "password": "string"
    }
    """
    data = request.get_json()

    if not data:
        return no_data_provided_error()

    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # Validate required fields
    if not all([username, email, password]):
        return missing_fields_error(["username", "email", "password"])

    # Validate password strength
    is_valid, validation_errors = validate_password_strength(password)
    if not is_valid:
        return error_response(
            "Password does not meet requirements",
            400,
            "weak_password",
            {"requirements": validation_errors},
        )

    # Check if user already exists
    if User.query.filter_by(username=username).first():
        return already_exists_error("Username")

    if User.query.filter_by(email=email).first():
        return already_exists_error("Email")

    # Create new user
    user = User(username=username, email=email)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    # Log security event
    log_security_event(
        "user_registration",
        f"User {username} registered successfully",
        {
            "user_id": user.id,
            "username": username,
            "email": email,
            "ip_address": request.remote_addr,
        },
    )

    # Create tokens
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"username": user.username, "token_type": "access"},
    )
    refresh_token = create_refresh_token(
        identity=str(user.id),
        additional_claims={"username": user.username, "token_type": "refresh"},
    )

    return success_response(
        message="User registered successfully",
        data={
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            },
            "access_token": access_token,
            "refresh_token": refresh_token,
        },
        status_code=201,
        flatten_data=True,
    )


@blueprint.route("/login", methods=["POST"])
@handle_common_exceptions
def login():
    """Authenticate user and return JWT tokens.

    Expected JSON payload:
    {
        "username": "string",  # or email
        "password": "string"
    }
    """
    data = request.get_json()

    if not data:
        return no_data_provided_error()

    username_or_email = data.get("username", "").strip()
    password = data.get("password", "")

    if not all([username_or_email, password]):
        return missing_fields_error(["username", "password"])

    # Find user by username or email
    user = User.query.filter(
        (User.username == username_or_email) | (User.email == username_or_email.lower())
    ).first()

    if not user or not user.check_password(password):
        # Log failed login attempt
        log_security_event(
            "failed_login_attempt",
            f"Failed login attempt for {username_or_email}",
            {
                "username": username_or_email,
                "ip_address": request.remote_addr,
            },
        )
        return invalid_credentials_error()

    # Update last login
    user.update_last_login()
    db.session.commit()

    # Create JWT tokens
    access_token = create_access_token(
        identity=str(user.id),
        expires_delta=timedelta(hours=1),
        additional_claims={"username": user.username, "token_type": "access"},
    )
    refresh_token = create_refresh_token(
        identity=str(user.id),
        expires_delta=timedelta(days=30),
        additional_claims={"username": user.username, "token_type": "refresh"},
    )

    # Log successful login
    log_security_event(
        "user_login",
        f"User {user.username} logged in successfully",
        {
            "user_id": user.id,
            "username": user.username,
            "ip_address": request.remote_addr,
        },
    )

    return success_response(
        message="Login successful",
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "last_login": (
                    user.last_login.isoformat() if user.last_login else None
                ),
            },
        },
        flatten_data=True,
    )


@blueprint.route("/logout", methods=["POST"])
@jwt_required()
@handle_common_exceptions
def logout():
    """Logout user by blacklisting the JWT token."""
    jti = get_jwt()["jti"]  # JWT ID
    user_id = get_jwt_identity()

    # Add token to blacklist
    blacklisted_tokens.add(jti)

    # Log logout event
    log_security_event(
        "user_logout",
        f"User {user_id} logged out successfully",
        {
            "user_id": int(user_id),
            "ip_address": request.remote_addr,
        },
    )

    return success_response(message="Successfully logged out")


@blueprint.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
@handle_common_exceptions
def refresh():
    """Refresh access token using refresh token."""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))

    if not user:
        return user_not_found_error()

    # Create new access token
    access_token = create_access_token(
        identity=str(user.id),
        expires_delta=timedelta(hours=1),
        additional_claims={"username": user.username, "token_type": "access"},
    )

    return success_response(
        message="Token refreshed successfully",
        data={"access_token": access_token},
        flatten_data=True,
    )


@blueprint.route("/me", methods=["GET"])
@jwt_required()
@handle_common_exceptions
def get_current_user():
    """Get current authenticated user information."""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))

    if not user:
        return user_not_found_error()

    return success_response(
        message="User information retrieved successfully",
        data={
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "created_at": user.created_at.isoformat(),
                "last_login": (
                    user.last_login.isoformat() if user.last_login else None
                ),
            }
        },
        flatten_data=True,
    )


# JWT token blacklist checker


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    """Check if a JWT token has been revoked.

    This function is called automatically by Flask-JWT-Extended
    whenever a protected route is accessed.
    """
    jti = jwt_payload["jti"]
    return jti in blacklisted_tokens


# Error handler for revoked tokens
@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    """Handle requests with revoked tokens."""
    return token_revoked_error()
