"""Service layer template following the project style guide.

This template provides a standard structure for creating service classes
that handle business logic and data operations while maintaining separation
of concerns.

Example:
    from ai_templates.flask_service import BaseServiceTemplate

    class UserService(BaseServiceTemplate):
        model_class = User

        def create_user(self, data: Dict[str, Any]) -> User:
            # Custom user creation logic
            pass
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional, Type

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

# Note: In actual implementation, import from your app's database instance
# from app.extensions import db
# from app.models import BaseModel


class ServiceException(Exception):
    """Base exception for service layer errors.

    This exception should be raised when business logic validation fails
    or when service-specific errors occur.

    Attributes:
        message: Human-readable error message
        code: Optional error code for programmatic handling
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize service exception.

        Args:
            message: Human-readable error message
            code: Optional error code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class ValidationException(ServiceException):
    """Exception raised when data validation fails.

    This exception should be raised when input data doesn't meet
    business rules or validation requirements.
    """


class NotFoundException(ServiceException):
    """Exception raised when requested resource is not found.

    This exception should be raised when a requested entity
    doesn't exist in the database.
    """


class DuplicateException(ServiceException):
    """Exception raised when attempting to create duplicate resource.

    This exception should be raised when trying to create a resource
    that violates uniqueness constraints.
    """


class BaseServiceTemplate(ABC):
    """Abstract base service template with common CRUD operations.

    This abstract base class provides common functionality that should be
    inherited by all service classes in the application.

    Attributes:
        model_class: The SQLAlchemy model class this service manages
        session: Database session for operations
    """

    model_class: Type = None

    def __init__(self, session: Optional[Session] = None) -> None:
        """Initialize the service.

        Args:
            session: Database session (defaults to current session)
        """
        # Note: In actual implementation, get session from app context
        # self.session = session or db.session
        self.session = session

        if not self.model_class:
            raise ValueError("model_class must be defined in subclass")

    def create(self, data: Dict[str, Any]) -> Any:
        """Create a new entity.

        Args:
            data: Dictionary containing entity data

        Returns:
            Created entity instance

        Raises:
            ValidationException: If data validation fails
            DuplicateException: If entity already exists
            ServiceException: If creation fails
        """
        try:
            # Validate input data
            validated_data = self._validate_create_data(data)

            # Create new instance
            entity = self.model_class(**validated_data)

            # Add to session and commit
            self.session.add(entity)
            self.session.commit()

            return entity

        except IntegrityError as e:
            self.session.rollback()
            raise DuplicateException(
                "Entity already exists",
                code="DUPLICATE_ENTITY",
                details={"error": str(e)},
            )
        except ValidationException:
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            raise ServiceException(
                f"Failed to create entity: {str(e)}", code="CREATE_FAILED"
            )

    def get_by_id(self, entity_id: int) -> Any:
        """Get entity by ID.

        Args:
            entity_id: The entity ID

        Returns:
            Entity instance

        Raises:
            NotFoundException: If entity doesn't exist
            ValidationException: If ID is invalid
        """
        if not isinstance(entity_id, int) or entity_id <= 0:
            raise ValidationException(
                "Entity ID must be a positive integer", code="INVALID_ID"
            )

        entity = (
            self.session.query(self.model_class)
            .filter(
                self.model_class.id == entity_id, self.model_class.is_active == True
            )
            .first()
        )

        if not entity:
            raise NotFoundException(
                f"Entity with ID {entity_id} not found",
                code="ENTITY_NOT_FOUND",
                details={"entity_id": entity_id},
            )

        return entity

    def get_all(
        self,
        page: int = 1,
        per_page: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get all entities with pagination and filtering.

        Args:
            page: Page number (1-based)
            per_page: Number of items per page
            filters: Optional filters to apply
            order_by: Optional field to order by

        Returns:
            Dictionary containing entities and pagination info

        Raises:
            ValidationException: If pagination parameters are invalid
        """
        # Validate pagination parameters
        if page < 1 or per_page < 1 or per_page > 100:
            raise ValidationException(
                "Invalid pagination parameters", code="INVALID_PAGINATION"
            )

        # Build base query
        query = self.session.query(self.model_class).filter(
            self.model_class.is_active == True
        )

        # Apply filters
        if filters:
            query = self._apply_filters(query, filters)

        # Apply ordering
        if order_by:
            query = self._apply_ordering(query, order_by)

        # Get total count
        total = query.count()

        # Apply pagination
        entities = query.offset((page - 1) * per_page).limit(per_page).all()

        return {
            "entities": entities,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page,
            },
        }

    def update(self, entity_id: int, data: Dict[str, Any]) -> Any:
        """Update an existing entity.

        Args:
            entity_id: The entity ID
            data: Dictionary containing update data

        Returns:
            Updated entity instance

        Raises:
            NotFoundException: If entity doesn't exist
            ValidationException: If data validation fails
            ServiceException: If update fails
        """
        try:
            # Get existing entity
            entity = self.get_by_id(entity_id)

            # Validate update data
            validated_data = self._validate_update_data(data, entity)

            # Update entity
            for key, value in validated_data.items():
                setattr(entity, key, value)

            entity.updated_at = datetime.utcnow()

            # Commit changes
            self.session.commit()

            return entity

        except (NotFoundException, ValidationException):
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            raise ServiceException(
                f"Failed to update entity: {str(e)}", code="UPDATE_FAILED"
            )

    def delete(self, entity_id: int, soft_delete: bool = True) -> bool:
        """Delete an entity.

        Args:
            entity_id: The entity ID
            soft_delete: Whether to perform soft delete (default: True)

        Returns:
            True if deletion was successful

        Raises:
            NotFoundException: If entity doesn't exist
            ServiceException: If deletion fails
        """
        try:
            # Get existing entity
            entity = self.get_by_id(entity_id)

            if soft_delete:
                # Perform soft delete
                entity.soft_delete()
            else:
                # Perform hard delete
                self.session.delete(entity)

            # Commit changes
            self.session.commit()

            return True

        except NotFoundException:
            raise
        except Exception as e:
            self.session.rollback()
            raise ServiceException(
                f"Failed to delete entity: {str(e)}", code="DELETE_FAILED"
            )

    @abstractmethod
    def _validate_create_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data for entity creation.

        Args:
            data: Raw input data

        Returns:
            Validated and sanitized data

        Raises:
            ValidationException: If validation fails
        """

    @abstractmethod
    def _validate_update_data(
        self, data: Dict[str, Any], entity: Any
    ) -> Dict[str, Any]:
        """Validate data for entity update.

        Args:
            data: Raw input data
            entity: Existing entity instance

        Returns:
            Validated and sanitized data

        Raises:
            ValidationException: If validation fails
        """

    def _apply_filters(self, query, filters: Dict[str, Any]):
        """Apply filters to query.

        Args:
            query: SQLAlchemy query object
            filters: Dictionary of filters to apply

        Returns:
            Modified query object
        """
        # TODO: Implement filter logic based on model fields
        return query

    def _apply_ordering(self, query, order_by: str):
        """Apply ordering to query.

        Args:
            query: SQLAlchemy query object
            order_by: Field name to order by (prefix with '-' for descending)

        Returns:
            Modified query object
        """
        # TODO: Implement ordering logic
        return query


class UserServiceTemplate(BaseServiceTemplate):
    """User service template with authentication and user management.

    This template provides user-specific business logic including
    registration, authentication, and profile management.
    """

    # Note: Set this to your actual User model class
    # model_class = User

    def register_user(
        self,
        email: str,
        username: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> Any:
        """Register a new user.

        Args:
            email: User's email address
            username: User's username
            password: User's password
            first_name: User's first name
            last_name: User's last name

        Returns:
            Created user instance

        Raises:
            ValidationException: If registration data is invalid
            DuplicateException: If user already exists
        """
        # Check if user already exists
        existing_user = (
            self.session.query(self.model_class)
            .filter(
                (self.model_class.email == email.lower())
                | (self.model_class.username == username.lower())
            )
            .first()
        )

        if existing_user:
            raise DuplicateException(
                "User with this email or username already exists", code="USER_EXISTS"
            )

        # Create user data
        user_data = {
            "email": email,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
        }

        # Create user
        user = self.create(user_data)

        # Set password
        user.set_password(password)
        self.session.commit()

        return user

    def authenticate_user(self, identifier: str, password: str) -> Any:
        """Authenticate user by email/username and password.

        Args:
            identifier: Email or username
            password: User's password

        Returns:
            User instance if authentication successful

        Raises:
            NotFoundException: If user doesn't exist
            ValidationException: If credentials are invalid
        """
        # Find user by email or username
        user = (
            self.session.query(self.model_class)
            .filter(
                (
                    (self.model_class.email == identifier.lower())
                    | (self.model_class.username == identifier.lower())
                )
                & (self.model_class.is_active == True)
            )
            .first()
        )

        if not user:
            raise NotFoundException("User not found", code="USER_NOT_FOUND")

        if not user.check_password(password):
            raise ValidationException("Invalid credentials", code="INVALID_CREDENTIALS")

        return user

    def change_password(
        self, user_id: int, current_password: str, new_password: str
    ) -> bool:
        """Change user's password.

        Args:
            user_id: User's ID
            current_password: Current password
            new_password: New password

        Returns:
            True if password change was successful

        Raises:
            NotFoundException: If user doesn't exist
            ValidationException: If current password is invalid
        """
        user = self.get_by_id(user_id)

        if not user.check_password(current_password):
            raise ValidationException(
                "Current password is incorrect", code="INVALID_CURRENT_PASSWORD"
            )

        user.set_password(new_password)
        self.session.commit()

        return True

    def _validate_create_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user creation data.

        Args:
            data: Raw user data

        Returns:
            Validated user data

        Raises:
            ValidationException: If validation fails
        """
        required_fields = ["email", "username"]

        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationException(
                    f"Field '{field}' is required",
                    code="MISSING_REQUIRED_FIELD",
                    details={"field": field},
                )

        # Additional validation logic here
        return data

    def _validate_update_data(
        self, data: Dict[str, Any], entity: Any
    ) -> Dict[str, Any]:
        """Validate user update data.

        Args:
            data: Raw update data
            entity: Existing user instance

        Returns:
            Validated update data

        Raises:
            ValidationException: If validation fails
        """
        # Remove fields that shouldn't be updated directly
        forbidden_fields = ["id", "created_at", "password_hash"]

        for field in forbidden_fields:
            data.pop(field, None)

        # Additional validation logic here
        return data
