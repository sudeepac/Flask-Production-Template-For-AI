"""SQLAlchemy model template following the project style guide.

This template provides a standard structure for creating SQLAlchemy models
that comply with the project's coding standards and best practices.

Example:
    from ai_templates.flask_model import BaseModelTemplate

    class User(BaseModelTemplate):
        __tablename__ = 'users'

        email = db.Column(db.String(255), unique=True, nullable=False)
        username = db.Column(db.String(80), unique=True, nullable=False)
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import validates
from werkzeug.security import check_password_hash, generate_password_hash

# Note: In actual implementation, import from your app's database instance
# from app.extensions import db

# For template purposes, using declarative_base
Base = declarative_base()


class BaseModelTemplate(Base):
    """Base model template with common fields and methods.

    This abstract base class provides common functionality that should be
    inherited by all model classes in the application.

    Attributes:
        id: Primary key identifier
        created_at: Timestamp when the record was created
        updated_at: Timestamp when the record was last updated
        is_active: Soft delete flag
    """

    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    is_active = Column(Boolean, default=True, nullable=False)

    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """Convert model instance to dictionary.

        Args:
            include_relationships: Whether to include relationship data

        Returns:
            Dictionary representation of the model instance
        """
        result = {}

        for column in self.__table__.columns:
            value = getattr(self, column.name)

            # Handle datetime serialization
            if isinstance(value, datetime):
                value = value.isoformat()

            result[column.name] = value

        if include_relationships:
            # TODO: Add relationship serialization logic
            pass

        return result

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update model instance from dictionary.

        Args:
            data: Dictionary containing field updates

        Raises:
            ValueError: If data contains invalid fields
        """
        for key, value in data.items():
            if hasattr(self, key) and key not in ["id", "created_at"]:
                setattr(self, key, value)
            elif key not in ["id", "created_at"]:
                raise ValueError(f"Invalid field: {key}")

    def soft_delete(self) -> None:
        """Perform soft delete by setting is_active to False."""
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def restore(self) -> None:
        """Restore soft deleted record by setting is_active to True."""
        self.is_active = True
        self.updated_at = datetime.utcnow()

    @classmethod
    def get_active_query(cls):
        """Get query for active (non-deleted) records.

        Returns:
            SQLAlchemy query object filtered for active records
        """
        # Note: In actual implementation, use session.query(cls)
        # return session.query(cls).filter(cls.is_active == True)

    def __repr__(self) -> str:
        """String representation of the model instance.

        Returns:
            String representation showing class name and ID
        """
        return f"<{self.__class__.__name__}(id={self.id})>"


class UserModelTemplate(BaseModelTemplate):
    """User model template with authentication capabilities.

    This template provides a standard user model with common fields
    and authentication methods.

    Attributes:
        email: User's email address (unique)
        username: User's username (unique)
        password_hash: Hashed password
        first_name: User's first name
        last_name: User's last name
        is_verified: Email verification status
        is_admin: Admin privileges flag
    """

    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    @validates("email")
    def validate_email(self, key: str, email: str) -> str:
        """Validate email format.

        Args:
            key: The field name being validated
            email: The email value to validate

        Returns:
            The validated email address

        Raises:
            ValueError: If email format is invalid
        """
        import re

        if not email or not isinstance(email, str):
            raise ValueError("Email must be a non-empty string")

        email = email.lower().strip()

        # Basic email validation regex
        email_pattern = r"^[a-z_a-Z0-9._%+-]+@[a-z_a-Z0-9.-]+\.[a-z_a-Z]{2,}$"

        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")

        return email

    @validates("username")
    def validate_username(self, key: str, username: str) -> str:
        """Validate username format.

        Args:
            key: The field name being validated
            username: The username value to validate

        Returns:
            The validated username

        Raises:
            ValueError: If username format is invalid
        """
        if not username or not isinstance(username, str):
            raise ValueError("Username must be a non-empty string")

        username = username.strip()

        if len(username) < 3 or len(username) > 80:
            raise ValueError("Username must be between 3 and 80 characters")

        # Allow alphanumeric characters, underscores, and hyphens
        import re

        if not re.match(r"^[a-z_a-Z0-9_-]+$", username):
            raise ValueError(
                "Username can only contain letters, numbers, underscores, and hyphens"
            )

        return username

    def set_password(self, password: str) -> None:
        """Set user password with proper hashing.

        Args:
            password: Plain text password to hash and store

        Raises:
            ValueError: If password doesn't meet requirements
        """
        if not password or not isinstance(password, str):
            raise ValueError("Password must be a non-empty string")

        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check if provided password matches stored hash.

        Args:
            password: Plain text password to verify

        Returns:
            True if password matches, False otherwise
        """
        if not password or not self.password_hash:
            return False

        return check_password_hash(self.password_hash, password)

    def get_full_name(self) -> str:
        """Get user's full name.

        Returns:
            Concatenated first and last name, or username if names not available
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.username

    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """Convert user model to dictionary (excluding sensitive data).

        Args:
            include_relationships: Whether to include relationship data

        Returns:
            Dictionary representation excluding password_hash
        """
        result = super().to_dict(include_relationships)

        # Remove sensitive information
        result.pop("password_hash", None)

        # Add computed fields
        result["full_name"] = self.get_full_name()

        return result


class AuditLogModelTemplate(BaseModelTemplate):
    """Audit log model template for tracking changes.

    This template provides a standard audit log model for tracking
    user actions and system changes.

    Attributes:
        user_id: ID of the user who performed the action
        action: Type of action performed
        resource_type: Type of resource affected
        resource_id: ID of the affected resource
        details: Additional details about the action
        ip_address: IP address of the user
        user_agent: User agent string
    """

    __tablename__ = "audit_logs"

    user_id = Column(Integer, nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(100), nullable=True, index=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)

    @validates("action")
    def validate_action(self, key: str, action: str) -> str:
        """Validate action type.

        Args:
            key: The field name being validated
            action: The action value to validate

        Returns:
            The validated action

        Raises:
            ValueError: If action is invalid
        """
        valid_actions = [
            "CREATE",
            "READ",
            "UPDATE",
            "DELETE",
            "LOGIN",
            "LOGOUT",
            "REGISTER",
            "PASSWORD_CHANGE",
        ]

        if not action or action.upper() not in valid_actions:
            raise ValueError(f"Action must be one of: {', '.join(valid_actions)}")

        return action.upper()

    @classmethod
    def log_action(
        cls,
        user_id: Optional[int],
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> "AuditLogModelTemplate":
        """Create a new audit log entry.

        Args:
            user_id: ID of the user performing the action
            action: Type of action being performed
            resource_type: Type of resource being affected
            resource_id: ID of the affected resource
            details: Additional details about the action
            ip_address: IP address of the user
            user_agent: User agent string

        Returns:
            New audit log instance
        """
        log_entry = cls(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return log_entry