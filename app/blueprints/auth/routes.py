"""Authentication routes.

Handles user authentication including registration, login, logout,
and JWT token management.
"""

from datetime import timedelta

from flask import current_app, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from marshmallow import ValidationError

from app.extensions import db
from app.models.example import User
from app.utils.error_handlers import handle_validation_error
from app.utils.logging_config import log_security_event
from app.utils.security import validate_password_strength

from . import blueprint

# Token blacklist for logout functionality
blacklisted_tokens = set()


@blueprint.route("/register", methods=["POST"])
def register():
    """Register a new user.

    Expected JSON payload:
    {
        "username": "string",
        "email": "string",
        "password": "string"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        username = data.get("username", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        # Validate required fields
        if not all([username, email, password]):
            return jsonify({"error": "Username, email, and password are required"}), 400

        # Validate password strength
        password_validation = validate_password_strength(password)
        if not password_validation["valid"]:
            return (
                jsonify(
                    {
                        "error": "Password does not meet requirements",
                        "requirements": password_validation["requirements"],
                    }
                ),
                400,
            )

        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already exists"}), 409

        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 409

        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        # Log security event
        log_security_event(
            "user_registration",
            user_id=user.id,
            username=username,
            email=email,
            ip_address=request.remote_addr,
        )

        return (
            jsonify(
                {
                    "message": "User registered successfully",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                    },
                }
            ),
            201,
        )

    except Exception as e:
        current_app.logger.error(f"Registration error: {str(e)}")
        return jsonify({"error": "Registration failed"}), 500


@blueprint.route("/login", methods=["POST"])
def login():
    """Authenticate user and return JWT tokens.

    Expected JSON payload:
    {
        "username": "string",  # or email
        "password": "string"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        username_or_email = data.get("username", "").strip()
        password = data.get("password", "")

        if not all([username_or_email, password]):
            return jsonify({"error": "Username/email and password are required"}), 400

        # Find user by username or email
        user = User.query.filter(
            (User.username == username_or_email)
            | (User.email == username_or_email.lower())
        ).first()

        if not user or not user.check_password(password):
            # Log failed login attempt
            log_security_event(
                "failed_login_attempt",
                username=username_or_email,
                ip_address=request.remote_addr,
            )
            return jsonify({"error": "Invalid credentials"}), 401

        # Update last login
        user.update_last_login()
        db.session.commit()

        # Create JWT tokens
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(hours=1),
            additional_claims={"username": user.username, "token_type": "access"},
        )
        refresh_token = create_refresh_token(
            identity=user.id,
            expires_delta=timedelta(days=30),
            additional_claims={"username": user.username, "token_type": "refresh"},
        )

        # Log successful login
        log_security_event(
            "user_login",
            user_id=user.id,
            username=user.username,
            ip_address=request.remote_addr,
        )

        return (
            jsonify(
                {
                    "message": "Login successful",
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
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({"error": "Login failed"}), 500


@blueprint.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """Logout user by blacklisting the JWT token."""
    try:
        jti = get_jwt()["jti"]  # JWT ID
        user_id = get_jwt_identity()

        # Add token to blacklist
        blacklisted_tokens.add(jti)

        # Log logout event
        log_security_event(
            "user_logout", user_id=user_id, ip_address=request.remote_addr
        )

        return jsonify({"message": "Successfully logged out"}), 200

    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
        return jsonify({"error": "Logout failed"}), 500


@blueprint.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        # Create new access token
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(hours=1),
            additional_claims={"username": user.username, "token_type": "access"},
        )

        return jsonify({"access_token": access_token}), 200

    except Exception as e:
        current_app.logger.error(f"Token refresh error: {str(e)}")
        return jsonify({"error": "Token refresh failed"}), 500


@blueprint.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    """Get current authenticated user information."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        return (
            jsonify(
                {
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "created_at": user.created_at.isoformat(),
                        "last_login": (
                            user.last_login.isoformat() if user.last_login else None
                        ),
                    }
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Get current user error: {str(e)}")
        return jsonify({"error": "Failed to get user information"}), 500


# JWT token blacklist checker
@blueprint.before_app_request
def check_if_token_revoked():
    """Check if JWT token is blacklisted before processing requests."""
    try:
        if request.endpoint and "auth" in request.endpoint:
            # Get JWT from request headers
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                from flask_jwt_extended import decode_token

                token = auth_header.split(" ")[1]
                try:
                    decoded_token = decode_token(token)
                    jti = decoded_token["jti"]
                    if jti in blacklisted_tokens:
                        return jsonify({"error": "Token has been revoked"}), 401
                except Exception:
                    # Invalid token format, let JWT extension handle it
                    pass
    except Exception:
        # Don't block requests if token checking fails
        pass
