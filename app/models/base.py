"""Base model class with common functionality.

This module provides a base model class that includes:
- Common fields (id, created_at, updated_at)
- Utility methods for serialization
- Query helpers
- Audit trail functionality
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.ext.declarative import declared_attr

from app.extensions import db


class BaseModel(db.Model):
    """Base model class with common functionality.

    Provides:
    - Primary key (id)
    - Timestamps (created_at, updated_at)
    - Serialization methods
    - Query helpers
    """

    __abstract__ = True

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    @declared_attr
    def __tablename__(cls):
        """Generate table name from class name.

        Converts CamelCase to snake_case and pluralizes.
        Example: UserProfile -> user_profiles
        """
        import re

        # Convert CamelCase to snake_case
        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", cls.__name__)
        name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()

        # Simple pluralization (add 's' or 'es')
        if name.endswith(("s", "sh", "ch", "x", "z")):
            return name + "es"
        elif name.endswith("y"):
            return name[:-1] + "ies"
        else:
            return name + "s"

    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """Convert model instance to dictionary.

        Args:
            include_relationships: Whether to include relationship data

        Returns:
            Dictionary representation of the model
        """
        result = {}

        # Include column data
        for column in self.__table__.columns:
            value = getattr(self, column.name)

            # Handle datetime serialization
            if isinstance(value, datetime):
                value = value.isoformat() + "Z"

            result[column.name] = value

        # Include relationships if requested
        if include_relationships:
            for relationship in self.__mapper__.relationships:
                rel_value = getattr(self, relationship.key)

                if rel_value is None:
                    result[relationship.key] = None
                elif hasattr(rel_value, "__iter__") and not isinstance(rel_value, str):
                    # Collection relationship
                    result[relationship.key] = [
                        (item.to_dict() if hasattr(item, "to_dict") else str(item))
                        for item in rel_value
                    ]
                else:
                    # Single relationship
                    result[relationship.key] = (
                        rel_value.to_dict()
                        if hasattr(rel_value, "to_dict")
                        else str(rel_value)
                    )

        return result

    def update(self, **kwargs) -> "BaseModel":
        """Update model instance with provided data.

        Args:
            **kwargs: Fields to update

        Returns:
            Updated model instance
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        self.updated_at = datetime.utcnow()
        return self

    def save(self) -> "BaseModel":
        """Save model instance to database.

        Returns:
            Saved model instance
        """
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self) -> None:
        """Delete model instance from database."""
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def create(cls, **kwargs) -> "BaseModel":
        """Create and save new model instance.

        Args:
            **kwargs: Model fields

        Returns:
            Created model instance
        """
        instance = cls(**kwargs)
        return instance.save()

    @classmethod
    def get_by_id(cls, id: int) -> Optional["BaseModel"]:
        """Get model instance by ID.

        Args:
            id: Model ID

        Returns:
            Model instance or None
        """
        return cls.query.get(id)

    @classmethod
    def get_or_404(cls, id: int) -> "BaseModel":
        """Get model instance by ID or raise 404.

        Args:
            id: Model ID

        Returns:
            Model instance

        Raises:
            404 error if not found
        """
        return cls.query.get_or_404(id)

    @classmethod
    def get_all(cls, limit: Optional[int] = None, offset: Optional[int] = None) -> list:
        """Get all model instances with optional pagination.

        Args:
            limit: Maximum number of records
            offset: Number of records to skip

        Returns:
            List of model instances
        """
        query = cls.query

        if offset:
            query = query.offset(offset)

        if limit:
            query = query.limit(limit)

        return query.all()

    @classmethod
    def count(cls) -> int:
        """Get total count of model instances.

        Returns:
            Total count
        """
        return cls.query.count()

    def __repr__(self) -> str:
        """String representation of model instance."""
        return f"<{self.__class__.__name__}(id={self.id})>"
