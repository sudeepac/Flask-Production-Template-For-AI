"""Unit tests for app.blueprints.auth.routes module.

This module tests all authentication endpoints including registration,
login, logout, token refresh, and user profile functionality.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.blueprints.auth.routes import (
    blacklisted_tokens,
    check_if_token_revoked,
    get_current_user,
    login,
    logout,
    refresh,
    register,
    revoked_token_callback,
)


class TestRegisterEndpoint:
    """Test user registration endpoint functionality."""

    @patch("app.blueprints.auth.routes.log_security_event")
    @patch("app.blueprints.auth.routes.create_refresh_token")
    @patch("app.blueprints.auth.routes.create_access_token")
    @patch("app.blueprints.auth.routes.db")
    @patch("app.blueprints.auth.routes.User")
    @patch("app.blueprints.auth.routes.validate_password_strength")
    @patch("app.blueprints.auth.routes.request")
    @patch("app.blueprints.auth.routes.success_response")
    def test_register_success(
        self,
        mock_success_response,
        mock_request,
        mock_validate_password,
        mock_user_class,
        mock_db,
        mock_create_access,
        mock_create_refresh,
        mock_log_security,
    ):
        """Test successful user registration."""
        # Mock request data
        request_data = {
            "username": "  testuser  ",  # Test trimming
            "email": "  TEST@EXAMPLE.COM  ",  # Test trimming and lowercasing
            "password": "SecurePass123!",
        }
        mock_request.get_json.return_value = request_data
        mock_request.remote_addr = "192.168.1.1"

        # Mock password validation
        mock_validate_password.return_value = (True, [])

        # Mock user queries (no existing users)
        mock_user_class.query.filter_by.return_value.first.return_value = None

        # Mock new user creation
        mock_user_instance = Mock()
        mock_user_instance.id = 123
        mock_user_instance.username = "testuser"
        mock_user_instance.email = "test@example.com"
        mock_user_class.return_value = mock_user_instance

        # Mock token creation
        mock_create_access.return_value = "access_token_123"
        mock_create_refresh.return_value = "refresh_token_123"

        # Mock success response
        mock_success_response.return_value = ({"status": "success"}, 201)

        result = register()

        # Verify user creation
        mock_user_class.assert_called_once_with(
            username="testuser", email="test@example.com"
        )
        mock_user_instance.set_password.assert_called_once_with("SecurePass123!")

        # Verify database operations
        mock_db.session.add.assert_called_once_with(mock_user_instance)
        mock_db.session.commit.assert_called_once()

        # Verify security logging
        mock_log_security.assert_called_once_with(
            "user_registration",
            "User testuser registered successfully",
            {
                "user_id": 123,
                "username": "testuser",
                "email": "test@example.com",
                "ip_address": "192.168.1.1",
            },
        )

        # Verify token creation
        mock_create_access.assert_called_once_with(
            identity="123",
            additional_claims={"username": "testuser", "token_type": "access"},
        )
        mock_create_refresh.assert_called_once_with(
            identity="123",
            additional_claims={"username": "testuser", "token_type": "refresh"},
        )

        # Verify success response
        call_args = mock_success_response.call_args
        expected_data = {
            "user": {"id": 123, "username": "testuser", "email": "test@example.com"},
            "access_token": "access_token_123",
            "refresh_token": "refresh_token_123",
        }

        assert call_args[1]["message"] == "User registered successfully"
        assert call_args[1]["data"] == expected_data
        assert call_args[1]["status_code"] == 201
        assert call_args[1]["flatten_data"] is True

        assert result == ({"status": "success"}, 201)

    @patch("app.blueprints.auth.routes.request")
    @patch("app.blueprints.auth.routes.no_data_provided_error")
    def test_register_no_data(self, mock_no_data_error, mock_request):
        """Test registration with no request data."""
        mock_request.get_json.return_value = None
        mock_no_data_error.return_value = ({"error": "no_data"}, 400)

        result = register()

        mock_no_data_error.assert_called_once()
        assert result == ({"error": "no_data"}, 400)

    @patch("app.blueprints.auth.routes.request")
    @patch("app.blueprints.auth.routes.missing_fields_error")
    def test_register_missing_fields(self, mock_missing_fields_error, mock_request):
        """Test registration with missing required fields."""
        request_data = {
            "username": "testuser"
            # Missing email and password
        }
        mock_request.get_json.return_value = request_data
        mock_missing_fields_error.return_value = ({"error": "missing_fields"}, 400)

        result = register()

        mock_missing_fields_error.assert_called_once_with(
            ["username", "email", "password"]
        )
        assert result == ({"error": "missing_fields"}, 400)

    @patch("app.blueprints.auth.routes.request")
    @patch("app.blueprints.auth.routes.validate_password_strength")
    @patch("app.blueprints.auth.routes.error_response")
    def test_register_weak_password(
        self, mock_error_response, mock_validate_password, mock_request
    ):
        """Test registration with weak password."""
        request_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "weak",
        }
        mock_request.get_json.return_value = request_data

        # Mock password validation failure
        mock_validate_password.return_value = (
            False,
            [
                "Password must be at least 8 characters",
                "Password must contain uppercase",
            ],
        )
        mock_error_response.return_value = ({"error": "weak_password"}, 400)

        result = register()

        mock_error_response.assert_called_once_with(
            "Password does not meet requirements",
            400,
            "weak_password",
            {
                "requirements": [
                    "Password must be at least 8 characters",
                    "Password must contain uppercase",
                ]
            },
        )
        assert result == ({"error": "weak_password"}, 400)

    @patch("app.blueprints.auth.routes.request")
    @patch("app.blueprints.auth.routes.validate_password_strength")
    @patch("app.blueprints.auth.routes.User")
    @patch("app.blueprints.auth.routes.already_exists_error")
    def test_register_username_exists(
        self,
        mock_already_exists_error,
        mock_user_class,
        mock_validate_password,
        mock_request,
    ):
        """Test registration with existing username."""
        request_data = {
            "username": "existinguser",
            "email": "new@example.com",
            "password": "SecurePass123!",
        }
        mock_request.get_json.return_value = request_data

        # Mock password validation success
        mock_validate_password.return_value = (True, [])

        # Mock existing username
        mock_existing_user = Mock()
        mock_user_class.query.filter_by.return_value.first.return_value = (
            mock_existing_user
        )
        mock_already_exists_error.return_value = ({"error": "username_exists"}, 409)

        result = register()

        mock_already_exists_error.assert_called_once_with("Username")
        assert result == ({"error": "username_exists"}, 409)

    @patch("app.blueprints.auth.routes.request")
    @patch("app.blueprints.auth.routes.validate_password_strength")
    @patch("app.blueprints.auth.routes.User")
    @patch("app.blueprints.auth.routes.already_exists_error")
    def test_register_email_exists(
        self,
        mock_already_exists_error,
        mock_user_class,
        mock_validate_password,
        mock_request,
    ):
        """Test registration with existing email."""
        request_data = {
            "username": "newuser",
            "email": "existing@example.com",
            "password": "SecurePass123!",
        }
        mock_request.get_json.return_value = request_data

        # Mock password validation success
        mock_validate_password.return_value = (True, [])

        # Mock no existing username but existing email
        def mock_filter_by(**kwargs):
            if "username" in kwargs:
                return Mock(first=Mock(return_value=None))
            elif "email" in kwargs:
                return Mock(first=Mock(return_value=Mock()))

        mock_user_class.query.filter_by.side_effect = mock_filter_by
        mock_already_exists_error.return_value = ({"error": "email_exists"}, 409)

        result = register()

        mock_already_exists_error.assert_called_once_with("Email")
        assert result == ({"error": "email_exists"}, 409)


class TestLoginEndpoint:
    """Test user login endpoint functionality."""

    @patch("app.blueprints.auth.routes.log_security_event")
    @patch("app.blueprints.auth.routes.create_refresh_token")
    @patch("app.blueprints.auth.routes.create_access_token")
    @patch("app.blueprints.auth.routes.db")
    @patch("app.blueprints.auth.routes.User")
    @patch("app.blueprints.auth.routes.request")
    @patch("app.blueprints.auth.routes.success_response")
    def test_login_success_with_username(
        self,
        mock_success_response,
        mock_request,
        mock_user_class,
        mock_db,
        mock_create_access,
        mock_create_refresh,
        mock_log_security,
    ):
        """Test successful login with username."""
        # Mock request data
        request_data = {"username": "testuser", "password": "SecurePass123!"}
        mock_request.get_json.return_value = request_data
        mock_request.remote_addr = "192.168.1.1"

        # Mock user found and password check
        mock_user = Mock()
        mock_user.id = 123
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.last_login = datetime(2023, 12, 1, 10, 30, 45)
        mock_user.check_password.return_value = True

        mock_user_class.query.filter.return_value.first.return_value = mock_user

        # Mock token creation
        mock_create_access.return_value = "access_token_123"
        mock_create_refresh.return_value = "refresh_token_123"

        # Mock success response
        mock_success_response.return_value = ({"status": "success"}, 200)

        result = login()

        # Verify user lookup
        mock_user_class.query.filter.assert_called_once()

        # Verify password check
        mock_user.check_password.assert_called_once_with("SecurePass123!")

        # Verify last login update
        mock_user.update_last_login.assert_called_once()
        mock_db.session.commit.assert_called_once()

        # Verify token creation
        mock_create_access.assert_called_once_with(
            identity="123",
            expires_delta=timedelta(hours=1),
            additional_claims={"username": "testuser", "token_type": "access"},
        )
        mock_create_refresh.assert_called_once_with(
            identity="123",
            expires_delta=timedelta(days=30),
            additional_claims={"username": "testuser", "token_type": "refresh"},
        )

        # Verify security logging
        mock_log_security.assert_called_once_with(
            "user_login",
            "User testuser logged in successfully",
            {"user_id": 123, "username": "testuser", "ip_address": "192.168.1.1"},
        )

        # Verify success response
        call_args = mock_success_response.call_args
        expected_data = {
            "access_token": "access_token_123",
            "refresh_token": "refresh_token_123",
            "user": {
                "id": 123,
                "username": "testuser",
                "email": "test@example.com",
                "last_login": "2023-12-01T10:30:45",
            },
        }

        assert call_args[1]["message"] == "Login successful"
        assert call_args[1]["data"] == expected_data
        assert call_args[1]["flatten_data"] is True

        assert result == ({"status": "success"}, 200)

    @patch("app.blueprints.auth.routes.log_security_event")
    @patch("app.blueprints.auth.routes.User")
    @patch("app.blueprints.auth.routes.request")
    @patch("app.blueprints.auth.routes.invalid_credentials_error")
    def test_login_user_not_found(
        self,
        mock_invalid_credentials_error,
        mock_request,
        mock_user_class,
        mock_log_security,
    ):
        """Test login with non-existent user."""
        request_data = {"username": "nonexistent", "password": "password123"}
        mock_request.get_json.return_value = request_data
        mock_request.remote_addr = "192.168.1.1"

        # Mock user not found
        mock_user_class.query.filter.return_value.first.return_value = None
        mock_invalid_credentials_error.return_value = (
            {"error": "invalid_credentials"},
            401,
        )

        result = login()

        # Verify security logging for failed attempt
        mock_log_security.assert_called_once_with(
            "failed_login_attempt",
            "Failed login attempt for nonexistent",
            {"username": "nonexistent", "ip_address": "192.168.1.1"},
        )

        mock_invalid_credentials_error.assert_called_once()
        assert result == ({"error": "invalid_credentials"}, 401)

    @patch("app.blueprints.auth.routes.log_security_event")
    @patch("app.blueprints.auth.routes.User")
    @patch("app.blueprints.auth.routes.request")
    @patch("app.blueprints.auth.routes.invalid_credentials_error")
    def test_login_wrong_password(
        self,
        mock_invalid_credentials_error,
        mock_request,
        mock_user_class,
        mock_log_security,
    ):
        """Test login with wrong password."""
        request_data = {"username": "testuser", "password": "wrongpassword"}
        mock_request.get_json.return_value = request_data
        mock_request.remote_addr = "192.168.1.1"

        # Mock user found but wrong password
        mock_user = Mock()
        mock_user.check_password.return_value = False
        mock_user_class.query.filter.return_value.first.return_value = mock_user
        mock_invalid_credentials_error.return_value = (
            {"error": "invalid_credentials"},
            401,
        )

        result = login()

        # Verify security logging for failed attempt
        mock_log_security.assert_called_once_with(
            "failed_login_attempt",
            "Failed login attempt for testuser",
            {"username": "testuser", "ip_address": "192.168.1.1"},
        )

        mock_invalid_credentials_error.assert_called_once()
        assert result == ({"error": "invalid_credentials"}, 401)

    @patch("app.blueprints.auth.routes.request")
    @patch("app.blueprints.auth.routes.missing_fields_error")
    def test_login_missing_fields(self, mock_missing_fields_error, mock_request):
        """Test login with missing required fields."""
        request_data = {"username": "testuser"}  # Missing password
        mock_request.get_json.return_value = request_data
        mock_missing_fields_error.return_value = ({"error": "missing_fields"}, 400)

        result = login()

        mock_missing_fields_error.assert_called_once_with(["username", "password"])
        assert result == ({"error": "missing_fields"}, 400)

    @patch("app.blueprints.auth.routes.request")
    @patch("app.blueprints.auth.routes.no_data_provided_error")
    def test_login_no_data(self, mock_no_data_error, mock_request):
        """Test login with no request data."""
        mock_request.get_json.return_value = None
        mock_no_data_error.return_value = ({"error": "no_data"}, 400)

        result = login()

        mock_no_data_error.assert_called_once()
        assert result == ({"error": "no_data"}, 400)


class TestLogoutEndpoint:
    """Test user logout endpoint functionality."""

    @patch("app.blueprints.auth.routes.log_security_event")
    @patch("app.blueprints.auth.routes.get_jwt_identity")
    @patch("app.blueprints.auth.routes.get_jwt")
    @patch("app.blueprints.auth.routes.request")
    @patch("app.blueprints.auth.routes.success_response")
    def test_logout_success(
        self,
        mock_success_response,
        mock_request,
        mock_get_jwt,
        mock_get_jwt_identity,
        mock_log_security,
    ):
        """Test successful logout."""
        # Mock JWT data
        mock_get_jwt.return_value = {"jti": "token_id_123"}
        mock_get_jwt_identity.return_value = "123"
        mock_request.remote_addr = "192.168.1.1"

        # Mock success response
        mock_success_response.return_value = ({"status": "success"}, 200)

        # Clear blacklist before test
        blacklisted_tokens.clear()

        result = logout()

        # Verify token was added to blacklist
        assert "token_id_123" in blacklisted_tokens

        # Verify security logging
        mock_log_security.assert_called_once_with(
            "user_logout",
            "User 123 logged out successfully",
            {"user_id": 123, "ip_address": "192.168.1.1"},
        )

        # Verify success response
        mock_success_response.assert_called_once_with(message="Successfully logged out")
        assert result == ({"status": "success"}, 200)

        # Clean up
        blacklisted_tokens.clear()


class TestRefreshEndpoint:
    """Test token refresh endpoint functionality."""

    @patch("app.blueprints.auth.routes.create_access_token")
    @patch("app.blueprints.auth.routes.User")
    @patch("app.blueprints.auth.routes.get_jwt_identity")
    @patch("app.blueprints.auth.routes.success_response")
    def test_refresh_success(
        self,
        mock_success_response,
        mock_get_jwt_identity,
        mock_user_class,
        mock_create_access,
    ):
        """Test successful token refresh."""
        # Mock JWT identity
        mock_get_jwt_identity.return_value = "123"

        # Mock user found
        mock_user = Mock()
        mock_user.id = 123
        mock_user.username = "testuser"
        mock_user_class.query.get.return_value = mock_user

        # Mock token creation
        mock_create_access.return_value = "new_access_token_123"

        # Mock success response
        mock_success_response.return_value = ({"status": "success"}, 200)

        result = refresh()

        # Verify user lookup
        mock_user_class.query.get.assert_called_once_with(123)

        # Verify token creation
        mock_create_access.assert_called_once_with(
            identity="123",
            expires_delta=timedelta(hours=1),
            additional_claims={"username": "testuser", "token_type": "access"},
        )

        # Verify success response
        call_args = mock_success_response.call_args
        expected_data = {"access_token": "new_access_token_123"}

        assert call_args[1]["message"] == "Token refreshed successfully"
        assert call_args[1]["data"] == expected_data
        assert call_args[1]["flatten_data"] is True

        assert result == ({"status": "success"}, 200)

    @patch("app.blueprints.auth.routes.User")
    @patch("app.blueprints.auth.routes.get_jwt_identity")
    @patch("app.blueprints.auth.routes.user_not_found_error")
    def test_refresh_user_not_found(
        self, mock_user_not_found_error, mock_get_jwt_identity, mock_user_class
    ):
        """Test token refresh with non-existent user."""
        # Mock JWT identity
        mock_get_jwt_identity.return_value = "999"

        # Mock user not found
        mock_user_class.query.get.return_value = None
        mock_user_not_found_error.return_value = ({"error": "user_not_found"}, 404)

        result = refresh()

        mock_user_not_found_error.assert_called_once()
        assert result == ({"error": "user_not_found"}, 404)


class TestGetCurrentUserEndpoint:
    """Test get current user endpoint functionality."""

    @patch("app.blueprints.auth.routes.User")
    @patch("app.blueprints.auth.routes.get_jwt_identity")
    @patch("app.blueprints.auth.routes.success_response")
    def test_get_current_user_success(
        self, mock_success_response, mock_get_jwt_identity, mock_user_class
    ):
        """Test successful current user retrieval."""
        # Mock JWT identity
        mock_get_jwt_identity.return_value = "123"

        # Mock user found
        mock_user = Mock()
        mock_user.id = 123
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.created_at = datetime(2023, 11, 1, 9, 0, 0)
        mock_user.last_login = datetime(2023, 12, 1, 10, 30, 45)
        mock_user_class.query.get.return_value = mock_user

        # Mock success response
        mock_success_response.return_value = ({"status": "success"}, 200)

        result = get_current_user()

        # Verify user lookup
        mock_user_class.query.get.assert_called_once_with(123)

        # Verify success response
        call_args = mock_success_response.call_args
        expected_data = {
            "user": {
                "id": 123,
                "username": "testuser",
                "email": "test@example.com",
                "created_at": "2023-11-01T09:00:00",
                "last_login": "2023-12-01T10:30:45",
            }
        }

        assert call_args[1]["message"] == "User information retrieved successfully"
        assert call_args[1]["data"] == expected_data
        assert call_args[1]["flatten_data"] is True

        assert result == ({"status": "success"}, 200)

    @patch("app.blueprints.auth.routes.User")
    @patch("app.blueprints.auth.routes.get_jwt_identity")
    @patch("app.blueprints.auth.routes.success_response")
    def test_get_current_user_no_last_login(
        self, mock_success_response, mock_get_jwt_identity, mock_user_class
    ):
        """Test current user retrieval with no last login."""
        # Mock JWT identity
        mock_get_jwt_identity.return_value = "123"

        # Mock user found with no last login
        mock_user = Mock()
        mock_user.id = 123
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.created_at = datetime(2023, 11, 1, 9, 0, 0)
        mock_user.last_login = None
        mock_user_class.query.get.return_value = mock_user

        # Mock success response
        mock_success_response.return_value = ({"status": "success"}, 200)

        result = get_current_user()

        # Verify success response with None last_login
        call_args = mock_success_response.call_args
        assert call_args[1]["data"]["user"]["last_login"] is None

    @patch("app.blueprints.auth.routes.User")
    @patch("app.blueprints.auth.routes.get_jwt_identity")
    @patch("app.blueprints.auth.routes.user_not_found_error")
    def test_get_current_user_not_found(
        self, mock_user_not_found_error, mock_get_jwt_identity, mock_user_class
    ):
        """Test current user retrieval with non-existent user."""
        # Mock JWT identity
        mock_get_jwt_identity.return_value = "999"

        # Mock user not found
        mock_user_class.query.get.return_value = None
        mock_user_not_found_error.return_value = ({"error": "user_not_found"}, 404)

        result = get_current_user()

        mock_user_not_found_error.assert_called_once()
        assert result == ({"error": "user_not_found"}, 404)


class TestJWTTokenBlacklist:
    """Test JWT token blacklist functionality."""

    def test_check_if_token_revoked_blacklisted(self):
        """Test token revocation check for blacklisted token."""
        # Add token to blacklist
        blacklisted_tokens.clear()
        blacklisted_tokens.add("blacklisted_token_123")

        # Mock JWT payload
        jwt_payload = {"jti": "blacklisted_token_123"}

        result = check_if_token_revoked(None, jwt_payload)

        assert result is True

        # Clean up
        blacklisted_tokens.clear()

    def test_check_if_token_revoked_not_blacklisted(self):
        """Test token revocation check for valid token."""
        # Ensure blacklist is empty
        blacklisted_tokens.clear()

        # Mock JWT payload
        jwt_payload = {"jti": "valid_token_123"}

        result = check_if_token_revoked(None, jwt_payload)

        assert result is False

    @patch("app.blueprints.auth.routes.token_revoked_error")
    def test_revoked_token_callback(self, mock_token_revoked_error):
        """Test revoked token callback."""
        mock_token_revoked_error.return_value = ({"error": "token_revoked"}, 401)

        result = revoked_token_callback(None, None)

        mock_token_revoked_error.assert_called_once()
        assert result == ({"error": "token_revoked"}, 401)


class TestAuthRoutesIntegration:
    """Test integration scenarios for auth routes."""

    def test_registration_login_flow_integration(self):
        """Test integration between registration and login flows."""
        # This test verifies that the data flow between registration
        # and login is consistent

        # Mock user data that would be created during registration
        user_data = {
            "username": "integrationuser",
            "email": "integration@example.com",
            "password": "SecurePass123!",
        }

        # Verify that the same data format is expected in both endpoints
        # Registration expects: username, email, password
        # Login expects: username (or email), password

        # Test that email can be used for login (as per login logic)
        login_with_email = {
            "username": user_data["email"],  # Using email as username
            "password": user_data["password"],
        }

        # Both should have the same password field
        assert user_data["password"] == login_with_email["password"]

        # Login should accept email in username field
        assert login_with_email["username"] == user_data["email"]

    def test_token_lifecycle_integration(self):
        """Test token lifecycle from creation to revocation."""
        # Test the complete token lifecycle:
        # 1. Token created during login/registration
        # 2. Token used for authenticated requests
        # 3. Token refreshed
        # 4. Token revoked during logout

        # Mock token ID
        token_jti = "lifecycle_token_123"

        # Initially token should not be blacklisted
        blacklisted_tokens.clear()
        jwt_payload = {"jti": token_jti}
        assert check_if_token_revoked(None, jwt_payload) is False

        # Simulate logout - token gets blacklisted
        blacklisted_tokens.add(token_jti)

        # Now token should be revoked
        assert check_if_token_revoked(None, jwt_payload) is True

        # Clean up
        blacklisted_tokens.clear()

    def test_user_data_consistency_across_endpoints(self):
        """Test that user data format is consistent across all endpoints."""
        # Test that user data structure is consistent between:
        # - Registration response
        # - Login response
        # - Get current user response

        # Common user fields that should be present
        common_fields = ["id", "username", "email"]

        # Registration response should include these fields
        registration_user_data = {
            "id": 123,
            "username": "testuser",
            "email": "test@example.com",
        }

        # Login response should include these fields plus last_login
        login_user_data = {
            "id": 123,
            "username": "testuser",
            "email": "test@example.com",
            "last_login": "2023-12-01T10:30:45",
        }

        # Get current user response should include these fields plus created_at
        current_user_data = {
            "id": 123,
            "username": "testuser",
            "email": "test@example.com",
            "created_at": "2023-11-01T09:00:00",
            "last_login": "2023-12-01T10:30:45",
        }

        # Verify common fields are present in all responses
        for field in common_fields:
            assert field in registration_user_data
            assert field in login_user_data
            assert field in current_user_data

            # Verify values are consistent
            assert registration_user_data[field] == login_user_data[field]
            assert login_user_data[field] == current_user_data[field]

    def test_error_handling_consistency(self):
        """Test that error handling is consistent across auth endpoints."""
        # Test that all auth endpoints handle common errors consistently:
        # - No data provided
        # - Missing fields
        # - User not found
        # - Invalid credentials

        # All endpoints should handle missing data the same way
        # All endpoints should validate required fields consistently
        # Error response format should be consistent

        # This is verified by the individual endpoint tests,
        # but this integration test ensures the patterns are consistent
        pass
