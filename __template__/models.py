"""Template Blueprint Models.

This module contains database models for the template blueprint.
Models define the structure and relationships of data entities.

Model Types:
- Entity models: Core business objects
- Association models: Many-to-many relationships
- Mixin models: Reusable model components

See AI_INSTRUCTIONS.md §4 for model implementation guidelines.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

from app.extensions import db
from app.utils import generate_uuid


class TimestampMixin:
    """Mixin for adding timestamp fields to models.

    This mixin provides created_at and updated_at fields
    that are automatically managed.
    """

    created_at = Column(
        DateTime,
        nullable=False,
        default=func.now(),
        server_default=func.now(),
        comment="Record creation timestamp",
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Record last update timestamp",
    )


class UUIDMixin:
    """Mixin for adding UUID field to models.

    This mixin provides a UUID field for external references
    and API exposure while keeping internal integer IDs.
    """

    uuid = Column(
        String(36),
        nullable=False,
        unique=True,
        default=generate_uuid,
        comment="External UUID identifier",
    )


class Template(db.Model, TimestampMixin, UUIDMixin):
    """Template model.

    Represents a template entity in the system.
    Templates are reusable components or configurations
    that can be applied to various contexts.
    """

    __tablename__ = "templates"
    __table_args__ = {"comment": "Template entities for reusable components"}

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True, comment="Template ID")

    # Core fields
    name = Column(
        String(100), nullable=False, unique=True, index=True, comment="Template name"
    )

    description = Column(Text, nullable=True, comment="Template description")

    category = Column(
        String(50),
        nullable=True,
        index=True,
        default="general",
        comment="Template category",
    )

    # Status and configuration
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether template is active",
    )

    is_public = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="Whether template is publicly accessible",
    )

    # Usage tracking
    usage_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of times template has been used",
    )

    last_used_at = Column(
        DateTime, nullable=True, comment="Last time template was used"
    )

    # Flexible data storage
    tags = Column(JSON, nullable=True, comment="Template tags as JSON array")

    metadata = Column(
        JSON, nullable=True, comment="Additional template metadata as JSON"
    )

    configuration = Column(
        JSON, nullable=True, comment="Template configuration as JSON"
    )

    # Relationships
    # Add relationships here as needed
    # Example: template_items = relationship('TemplateItem', back_populates='template')

    def __init__(self, **kwargs):
        """Initialize template instance.

        Args:
            **kwargs: Template attributes
        """
        super().__init__(**kwargs)

        # Initialize default values
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
        if self.configuration is None:
            self.configuration = {}

    def __repr__(self) -> str:
        """String representation of template.

        Returns:
            str: Template representation
        """
        return f"<Template {self.id}: {self.name}>"

    def __str__(self) -> str:
        """Human-readable string representation.

        Returns:
            str: Template string
        """
        return self.name

    @validates("name")
    def validate_name(self, key: str, value: str) -> str:
        """Validate template name.

        Args:
            key: Field name
            value: Field value

        Returns:
            str: Validated name

        Raises:
            ValueError: If name is invalid
        """
        if not value or not value.strip():
            raise ValueError("Template name cannot be empty")

        # Check length
        if len(value.strip()) > 100:
            raise ValueError("Template name cannot exceed 100 characters")

        # Check for reserved names
        reserved_names = ["admin", "api", "system", "default", "root"]
        if value.lower().strip() in reserved_names:
            raise ValueError(f'Template name "{value}" is reserved')

        return value.strip()

    @validates("category")
    def validate_category(self, key: str, value: str) -> str:
        """Validate template category.

        Args:
            key: Field name
            value: Field value

        Returns:
            str: Validated category

        Raises:
            ValueError: If category is invalid
        """
        if value is None:
            return "general"

        valid_categories = ["general", "specific", "custom", "system"]
        if value.lower() not in valid_categories:
            raise ValueError(
                f'Invalid category "{value}". '
                f'Must be one of: {", ".join(valid_categories)}'
            )

        return value.lower()

    @validates("tags")
    def validate_tags(self, key: str, value: List[str]) -> List[str]:
        """Validate template tags.

        Args:
            key: Field name
            value: Field value

        Returns:
            List[str]: Validated tags

        Raises:
            ValueError: If tags are invalid
        """
        if value is None:
            return []

        if not isinstance(value, list):
            raise ValueError("Tags must be a list")

        # Validate each tag
        validated_tags = []
        for tag in value:
            if not isinstance(tag, str):
                raise ValueError("Each tag must be a string")

            tag = tag.strip().lower()
            if not tag:
                continue

            if len(tag) > 50:
                raise ValueError("Tag cannot exceed 50 characters")

            # Check for valid characters
            if not tag.replace("-", "").replace("_", "").isalnum():
                raise ValueError(
                    f'Tag "{tag}" contains invalid characters. '
                    "Only alphanumeric characters, hyphens, and underscores are allowed."
                )

            if tag not in validated_tags:
                validated_tags.append(tag)

        # Limit number of tags
        if len(validated_tags) > 10:
            raise ValueError("Cannot have more than 10 tags")

        return validated_tags

    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """Convert template to dictionary.

        Args:
            include_relationships: Whether to include relationship data

        Returns:
            Dict[str, Any]: Template data as dictionary
        """
        data = {
            "id": self.id,
            "uuid": self.uuid,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "is_active": self.is_active,
            "is_public": self.is_public,
            "usage_count": self.usage_count,
            "last_used_at": self.last_used_at.isoformat()
            if self.last_used_at
            else None,
            "tags": self.tags or [],
            "metadata": self.metadata or {},
            "configuration": self.configuration or {},
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

        if include_relationships:
            # Add relationship data here as needed
            pass

        return data

    def increment_usage(self) -> None:
        """Increment template usage count.

        Updates the usage count and last used timestamp.
        """
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()

    def add_tag(self, tag: str) -> bool:
        """Add a tag to the template.

        Args:
            tag: Tag to add

        Returns:
            bool: True if tag was added, False if already exists
        """
        if self.tags is None:
            self.tags = []

        tag = tag.strip().lower()
        if tag and tag not in self.tags:
            self.tags.append(tag)
            return True
        return False

    def remove_tag(self, tag: str) -> bool:
        """Remove a tag from the template.

        Args:
            tag: Tag to remove

        Returns:
            bool: True if tag was removed, False if not found
        """
        if self.tags is None:
            return False

        tag = tag.strip().lower()
        if tag in self.tags:
            self.tags.remove(tag)
            return True
        return False

    def has_tag(self, tag: str) -> bool:
        """Check if template has a specific tag.

        Args:
            tag: Tag to check

        Returns:
            bool: True if template has the tag
        """
        if self.tags is None:
            return False

        return tag.strip().lower() in self.tags

    def update_metadata(self, key: str, value: Any) -> None:
        """Update a metadata field.

        Args:
            key: Metadata key
            value: Metadata value
        """
        if self.metadata is None:
            self.metadata = {}

        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get a metadata field value.

        Args:
            key: Metadata key
            default: Default value if key not found

        Returns:
            Any: Metadata value
        """
        if self.metadata is None:
            return default

        return self.metadata.get(key, default)

    @classmethod
    def find_by_name(cls, name: str) -> Optional["Template"]:
        """Find template by name.

        Args:
            name: Template name

        Returns:
            Optional[Template]: Template if found, None otherwise
        """
        return cls.query.filter_by(name=name).first()

    @classmethod
    def find_by_uuid(cls, uuid: str) -> Optional["Template"]:
        """Find template by UUID.

        Args:
            uuid: Template UUID

        Returns:
            Optional[Template]: Template if found, None otherwise
        """
        return cls.query.filter_by(uuid=uuid).first()

    @classmethod
    def find_active(cls) -> List["Template"]:
        """Find all active templates.

        Returns:
            List[Template]: List of active templates
        """
        return cls.query.filter_by(is_active=True).all()

    @classmethod
    def find_by_category(cls, category: str) -> List["Template"]:
        """Find templates by category.

        Args:
            category: Template category

        Returns:
            List[Template]: List of templates in category
        """
        return cls.query.filter_by(category=category).all()

    @classmethod
    def find_by_tag(cls, tag: str) -> List["Template"]:
        """Find templates by tag.

        Args:
            tag: Tag to search for

        Returns:
            List[Template]: List of templates with the tag
        """
        return cls.query.filter(cls.tags.contains([tag])).all()

    @classmethod
    def search(
        cls,
        query: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_active: Optional[bool] = None,
    ) -> List["Template"]:
        """Search templates.

        Args:
            query: Search query for name/description
            category: Filter by category
            tags: Filter by tags
            is_active: Filter by active status

        Returns:
            List[Template]: List of matching templates
        """
        q = cls.query

        if query:
            search_filter = f"%{query}%"
            q = q.filter(
                db.or_(
                    cls.name.ilike(search_filter), cls.description.ilike(search_filter)
                )
            )

        if category:
            q = q.filter_by(category=category)

        if tags:
            for tag in tags:
                q = q.filter(cls.tags.contains([tag]))

        if is_active is not None:
            q = q.filter_by(is_active=is_active)

        return q.all()


# Example of an association model for many-to-many relationships
# Uncomment and modify as needed

# class TemplateItem(db.Model, TimestampMixin):
#     """Template item association model.
#
#     Represents items or components that belong to a template.
#     This is an example of how to create association models.
#     """
#
#     __tablename__ = 'template_items'
#     __table_args__ = {
#         'comment': 'Items associated with templates'
#     }
#
#     # Primary key
#     id = Column(
#         Integer,
#         primary_key=True,
#         autoincrement=True,
#         comment='Template item ID'
#     )
#
#     # Foreign keys
#     template_id = Column(
#         Integer,
#         db.ForeignKey('templates.id', ondelete='CASCADE'),
#         nullable=False,
#         index=True,
#         comment='Template ID'
#     )
#
#     # Item fields
#     name = Column(
#         String(100),
#         nullable=False,
#         comment='Item name'
#     )
#
#     value = Column(
#         Text,
#         nullable=True,
#         comment='Item value'
#     )
#
#     order = Column(
#         Integer,
#         nullable=False,
#         default=0,
#         comment='Item order'
#     )
#
#     # Relationships
#     template = relationship('Template', back_populates='template_items')
#
#     def __repr__(self) -> str:
#         return f'<TemplateItem {self.id}: {self.name}>'
