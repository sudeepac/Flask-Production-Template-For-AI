"""Tests for security utilities."""

from unittest.mock import patch

import pytest
from flask import Flask

from app.utils.security import (
    check_password,
    generate_api_key,
    generate_secure_token,
    hash_password,
    is_safe_url,
    require_api_key,
    require_auth,
    sanitize_input,
    validate_password_strength,
)


class TestPasswordHashing:
    """Test password hashing functions."""

    def test_hash_password_success(self):
        """Test successful password hashing."""
        password = "test_password_123"
        hashed = hash_password(password)

        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != password
        # Verify it's a valid bcrypt hash
        assert hashed.startswith("$2b$")

    def test_hash_password_empty_raises_error(self):
        """Test that empty password raises ValueError."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            hash_password("")

        with pytest.raises(ValueError, match="Password cannot be empty"):
            hash_password(None)

    def test_hash_password_different_each_time(self):
        """Test that same password produces different hashes."""
        password = "same_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Different salts should produce different hashes

    def test_check_password_valid(self):
        """Test password verification with valid password."""
        password = "test_password_123"
        hashed = hash_password(password)

        assert check_password(password, hashed) is True

    def test_check_password_invalid(self):
        """Test password verification with invalid password."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = hash_password(password)

        assert check_password(wrong_password, hashed) is False

    def test_check_password_empty_inputs(self):
        """Test password verification with empty inputs."""
        assert check_password("", "some_hash") is False
        assert check_password("password", "") is False
        assert check_password("", "") is False
        assert check_password(None, "some_hash") is False
        assert check_password("password", None) is False

    def test_check_password_invalid_hash_format(self):
        """Test password verification with invalid hash format."""
        password = "test_password"
        invalid_hash = "not_a_valid_hash"

        assert check_password(password, invalid_hash) is False

    @patch("bcrypt.checkpw")
    def test_check_password_bcrypt_exception(self, mock_checkpw):
        """Test password verification when bcrypt raises exception."""
        mock_checkpw.side_effect = ValueError("Invalid hash")

        result = check_password("password", "hash")
        assert result is False


class TestTokenGeneration:
    """Test token generation functions."""

    def test_generate_secure_token_default_length(self):
        """Test secure token generation with default length."""
        token = generate_secure_token()

        assert isinstance(token, str)
        assert len(token) > 0
        # URL-safe base64 encoding typically produces longer strings
        assert len(token) >= 32

    def test_generate_secure_token_custom_length(self):
        """Test secure token generation with custom length."""
        length = 16
        token = generate_secure_token(length)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_generate_secure_token_uniqueness(self):
        """Test that generated tokens are unique."""
        token1 = generate_secure_token()
        token2 = generate_secure_token()

        assert token1 != token2

    def test_generate_api_key_default(self):
        """Test API key generation with default parameters."""
        api_key = generate_api_key()

        assert isinstance(api_key, str)
        assert api_key.startswith("ak_")
        assert len(api_key) > 3  # prefix + underscore + random part

    def test_generate_api_key_custom_prefix(self):
        """Test API key generation with custom prefix."""
        prefix = "test"
        api_key = generate_api_key(prefix=prefix)

        assert api_key.startswith(f"{prefix}_")

    def test_generate_api_key_custom_length(self):
        """Test API key generation with custom length."""
        length = 16
        api_key = generate_api_key(length=length)

        assert isinstance(api_key, str)
        assert api_key.startswith("ak_")

    def test_generate_api_key_uniqueness(self):
        """Test that generated API keys are unique."""
        key1 = generate_api_key()
        key2 = generate_api_key()

        assert key1 != key2


class TestInputSanitization:
    """Test input sanitization functions."""

    def test_sanitize_input_normal_text(self):
        """Test sanitization of normal text."""
        text = "Hello, World! This is normal text."
        result = sanitize_input(text)

        assert result == text

    def test_sanitize_input_empty_string(self):
        """Test sanitization of empty string."""
        assert sanitize_input("") == ""
        assert sanitize_input(None) == ""

    def test_sanitize_input_with_control_characters(self):
        """Test sanitization removes control characters."""
        text = "Hello\x00World\x01Test\x1f"
        result = sanitize_input(text)

        assert "\x00" not in result
        assert "\x01" not in result
        assert "\x1f" not in result
        assert result == "HelloWorldTest"

    def test_sanitize_input_preserves_allowed_whitespace(self):
        """Test that allowed whitespace characters are preserved."""
        text = "Hello\nWorld\r\nTest\tTab"
        result = sanitize_input(text)

        assert "\n" in result
        assert "\r" in result
        assert "\t" in result

    def test_sanitize_input_max_length(self):
        """Test that input is truncated to max length."""
        text = "a" * 2000
        max_length = 100
        result = sanitize_input(text, max_length=max_length)

        assert len(result) == max_length
        assert result == "a" * max_length

    def test_sanitize_input_default_max_length(self):
        """Test default max length truncation."""
        text = "a" * 2000
        result = sanitize_input(text)

        assert len(result) == 1000  # Default max length


class TestRequireApiKey:
    """Test require_api_key decorator."""

    def test_require_api_key_missing_header(self):
        """Test API key requirement when header is missing."""
        app = Flask(__name__)

        @require_api_key
        def test_endpoint():
            return {"message": "success"}

        with app.test_request_context("/", headers={}):
            response, status_code = test_endpoint()

        assert status_code == 401
        response_data = response.get_json()
        assert response_data["error"] == "API key required"
        assert "X-API-Key" in response_data["message"]

    def test_require_api_key_with_valid_header(self):
        """Test API key requirement when header is present."""
        app = Flask(__name__)

        @require_api_key
        def test_endpoint():
            return {"message": "success"}

        with app.test_request_context("/", headers={"X-API-Key": "valid_key"}):
            result = test_endpoint()

        assert result == {"message": "success"}

    def test_require_api_key_empty_header(self):
        """Test API key requirement when header is empty."""
        app = Flask(__name__)

        @require_api_key
        def test_endpoint():
            return {"message": "success"}

        with app.test_request_context("/", headers={"X-API-Key": ""}):
            response, status_code = test_endpoint()

        assert status_code == 401


class TestRequireAuth:
    """Test require_auth decorator."""

    @patch("app.utils.security.jwt_required")
    def test_require_auth_decorator_applied(self, mock_jwt_required):
        """Test that require_auth applies jwt_required decorator."""
        mock_jwt_required.return_value = lambda f: f  # Mock decorator

        @require_auth
        def test_endpoint():
            return {"message": "success"}

        # Verify jwt_required was called
        mock_jwt_required.assert_called_once()

    @patch("app.utils.security.jwt_required")
    def test_require_auth_function_execution(self, mock_jwt_required):
        """Test that decorated function executes properly."""
        mock_jwt_required.return_value = lambda f: f  # Mock decorator

        @require_auth
        def test_endpoint():
            return {"message": "authenticated"}

        result = test_endpoint()
        assert result == {"message": "authenticated"}


class TestPasswordValidation:
    """Test password strength validation."""

    def test_validate_strong_password(self):
        """Test validation of a strong password."""
        password = "StrongP@ssw0rd!"
        is_valid, errors = validate_password_strength(password)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_weak_password_too_short(self):
        """Test validation of password that's too short."""
        password = "Weak1!"
        is_valid, errors = validate_password_strength(password)

        assert is_valid is False
        assert "at least 8 characters long" in errors[0]

    def test_validate_password_missing_uppercase(self):
        """Test validation of password missing uppercase letter."""
        password = "weakpassword1!"
        is_valid, errors = validate_password_strength(password)

        assert is_valid is False
        assert any("uppercase letter" in error for error in errors)

    def test_validate_password_missing_lowercase(self):
        """Test validation of password missing lowercase letter."""
        password = "WEAKPASSWORD1!"
        is_valid, errors = validate_password_strength(password)

        assert is_valid is False
        assert any("lowercase letter" in error for error in errors)

    def test_validate_password_missing_digit(self):
        """Test validation of password missing digit."""
        password = "WeakPassword!"
        is_valid, errors = validate_password_strength(password)

        assert is_valid is False
        assert any("digit" in error for error in errors)

    def test_validate_password_missing_special_char(self):
        """Test validation of password missing special character."""
        password = "WeakPassword1"
        is_valid, errors = validate_password_strength(password)

        assert is_valid is False
        assert any("special character" in error for error in errors)

    def test_validate_password_multiple_errors(self):
        """Test validation of password with multiple issues."""
        password = "weak"
        is_valid, errors = validate_password_strength(password)

        assert is_valid is False
        assert len(errors) > 1
        assert any("8 characters" in error for error in errors)
        assert any("uppercase" in error for error in errors)
        assert any("digit" in error for error in errors)
        assert any("special character" in error for error in errors)


class TestUrlSafety:
    """Test URL safety validation."""

    def test_is_safe_url_valid_http(self):
        """Test validation of safe HTTP URL."""
        url = "http://example.com/path"
        assert is_safe_url(url) is True

    def test_is_safe_url_valid_https(self):
        """Test validation of safe HTTPS URL."""
        url = "https://example.com/path"
        assert is_safe_url(url) is True

    def test_is_safe_url_relative_path(self):
        """Test validation of relative path."""
        url = "/relative/path"
        assert is_safe_url(url) is True

    def test_is_safe_url_empty_string(self):
        """Test validation of empty URL."""
        assert is_safe_url("") is False
        assert is_safe_url(None) is False

    def test_is_safe_url_javascript_scheme(self):
        """Test validation rejects javascript: URLs."""
        url = "javascript:alert('xss')"
        assert is_safe_url(url) is False

    def test_is_safe_url_data_scheme(self):
        """Test validation rejects data: URLs."""
        url = "data:text/html,<script>alert('xss')</script>"
        assert is_safe_url(url) is False

    def test_is_safe_url_vbscript_scheme(self):
        """Test validation rejects vbscript: URLs."""
        url = "vbscript:msgbox('xss')"
        assert is_safe_url(url) is False

    def test_is_safe_url_case_insensitive(self):
        """Test validation is case insensitive for dangerous schemes."""
        urls = [
            "JAVASCRIPT:alert('xss')",
            "JavaScript:alert('xss')",
            "DATA:text/html,<script>",
            "VBScript:msgbox('xss')",
        ]

        for url in urls:
            assert is_safe_url(url) is False

    def test_is_safe_url_with_whitespace(self):
        """Test validation handles URLs with whitespace."""
        url = "  javascript:alert('xss')  "
        assert is_safe_url(url) is False
