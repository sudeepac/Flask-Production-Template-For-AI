"""Example models for demonstration purposes.

These models serve as examples of how to structure database models
using the base model class and SQLAlchemy relationships.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.extensions import db
from .base import BaseModel


class User(BaseModel):
    """User model for authentication and user management.
    
    This is an example model that demonstrates:
    - Basic fields with validation
    - Relationships to other models
    - Custom methods
    - Serialization
    """
    
    # Basic user information
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    
    # Authentication
    password_hash = Column(String(255), nullable=True)  # In real app, this would be required
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    
    # Profile information
    bio = Column(Text, nullable=True)
    location = Column(String(100), nullable=True)
    website = Column(String(200), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # Timestamps
    last_login = Column(DateTime, nullable=True)
    email_verified_at = Column(DateTime, nullable=True)
    
    # Relationships
    posts = relationship('Post', back_populates='author', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        """Initialize user with default values."""
        super().__init__(**kwargs)
        
        # Set default values
        if not self.is_active:
            self.is_active = True
        if not self.is_admin:
            self.is_admin = False
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username
    
    @property
    def post_count(self) -> int:
        """Get number of posts by this user."""
        return self.posts.count()
    
    def set_password(self, password: str) -> None:
        """Set user password (placeholder - implement proper hashing).
        
        Args:
            password: Plain text password
        """
        # In a real application, use proper password hashing
        # from werkzeug.security import generate_password_hash
        # self.password_hash = generate_password_hash(password)
        self.password_hash = f"hashed_{password}"  # Placeholder
    
    def check_password(self, password: str) -> bool:
        """Check if provided password is correct.
        
        Args:
            password: Plain text password to check
            
        Returns:
            True if password is correct
        """
        # In a real application, use proper password verification
        # from werkzeug.security import check_password_hash
        # return check_password_hash(self.password_hash, password)
        return self.password_hash == f"hashed_{password}"  # Placeholder
    
    def update_last_login(self) -> None:
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self, include_relationships: bool = False, include_sensitive: bool = False) -> dict:
        """Convert user to dictionary with privacy controls.
        
        Args:
            include_relationships: Whether to include related data
            include_sensitive: Whether to include sensitive fields
            
        Returns:
            Dictionary representation
        """
        result = super().to_dict(include_relationships=include_relationships)
        
        # Remove sensitive fields unless explicitly requested
        if not include_sensitive:
            result.pop('password_hash', None)
            result.pop('email', None)  # In some cases, email might be sensitive
        
        # Add computed fields
        result['full_name'] = self.full_name
        result['post_count'] = self.post_count
        
        return result
    
    @classmethod
    def get_by_username(cls, username: str) -> Optional['User']:
        """Get user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            User instance or None
        """
        return cls.query.filter_by(username=username).first()
    
    @classmethod
    def get_by_email(cls, email: str) -> Optional['User']:
        """Get user by email.
        
        Args:
            email: Email to search for
            
        Returns:
            User instance or None
        """
        return cls.query.filter_by(email=email).first()
    
    @classmethod
    def get_active_users(cls) -> list:
        """Get all active users.
        
        Returns:
            List of active users
        """
        return cls.query.filter_by(is_active=True).all()
    
    @classmethod
    def get_admins(cls) -> list:
        """Get all admin users.
        
        Returns:
            List of admin users
        """
        return cls.query.filter_by(is_admin=True).all()
    
    def __repr__(self) -> str:
        """String representation of user."""
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class Post(BaseModel):
    """Blog post model for content management.
    
    This is an example model that demonstrates:
    - Foreign key relationships
    - Text content handling
    - Status management
    - Search and filtering
    """
    
    # Content fields
    title = Column(String(200), nullable=False, index=True)
    slug = Column(String(250), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    excerpt = Column(Text, nullable=True)
    
    # Metadata
    category = Column(String(50), nullable=True, index=True)
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    status = Column(String(20), default='draft', nullable=False, index=True)
    
    # Engagement metrics
    view_count = Column(Integer, default=0, nullable=False)
    like_count = Column(Integer, default=0, nullable=False)
    comment_count = Column(Integer, default=0, nullable=False)
    
    # Flags
    is_featured = Column(Boolean, default=False, nullable=False)
    is_pinned = Column(Boolean, default=False, nullable=False)
    
    # Publishing
    published_at = Column(DateTime, nullable=True)
    
    # Relationships
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    author = relationship('User', back_populates='posts')
    
    def __init__(self, **kwargs):
        """Initialize post with default values."""
        super().__init__(**kwargs)
        
        # Set default values
        if not self.status:
            self.status = 'draft'
        if self.view_count is None:
            self.view_count = 0
        if self.like_count is None:
            self.like_count = 0
        if self.comment_count is None:
            self.comment_count = 0
    
    @property
    def is_published(self) -> bool:
        """Check if post is published."""
        return self.status == 'published' and self.published_at is not None
    
    @property
    def tag_list(self) -> list:
        """Get tags as a list."""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
    
    @tag_list.setter
    def tag_list(self, tags: list) -> None:
        """Set tags from a list."""
        self.tags = ', '.join(tags) if tags else None
    
    @property
    def reading_time(self) -> int:
        """Estimate reading time in minutes."""
        if not self.content:
            return 0
        
        # Rough estimate: 200 words per minute
        word_count = len(self.content.split())
        return max(1, round(word_count / 200))
    
    def publish(self) -> None:
        """Publish the post."""
        self.status = 'published'
        self.published_at = datetime.utcnow()
        db.session.commit()
    
    def unpublish(self) -> None:
        """Unpublish the post."""
        self.status = 'draft'
        self.published_at = None
        db.session.commit()
    
    def increment_views(self) -> None:
        """Increment view count."""
        self.view_count += 1
        db.session.commit()
    
    def increment_likes(self) -> None:
        """Increment like count."""
        self.like_count += 1
        db.session.commit()
    
    def to_dict(self, include_relationships: bool = False) -> dict:
        """Convert post to dictionary with computed fields.
        
        Args:
            include_relationships: Whether to include related data
            
        Returns:
            Dictionary representation
        """
        result = super().to_dict(include_relationships=include_relationships)
        
        # Add computed fields
        result['is_published'] = self.is_published
        result['tag_list'] = self.tag_list
        result['reading_time'] = self.reading_time
        
        return result
    
    @classmethod
    def get_published(cls) -> list:
        """Get all published posts.
        
        Returns:
            List of published posts
        """
        return cls.query.filter_by(status='published').order_by(cls.published_at.desc()).all()
    
    @classmethod
    def get_by_slug(cls, slug: str) -> Optional['Post']:
        """Get post by slug.
        
        Args:
            slug: Post slug
            
        Returns:
            Post instance or None
        """
        return cls.query.filter_by(slug=slug).first()
    
    @classmethod
    def get_by_category(cls, category: str) -> list:
        """Get posts by category.
        
        Args:
            category: Category name
            
        Returns:
            List of posts in category
        """
        return cls.query.filter_by(category=category).all()
    
    @classmethod
    def get_featured(cls) -> list:
        """Get featured posts.
        
        Returns:
            List of featured posts
        """
        return cls.query.filter_by(is_featured=True).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def search(cls, query: str) -> list:
        """Search posts by title and content.
        
        Args:
            query: Search query
            
        Returns:
            List of matching posts
        """
        search_term = f"%{query}%"
        return cls.query.filter(
            db.or_(
                cls.title.ilike(search_term),
                cls.content.ilike(search_term)
            )
        ).all()
    
    def __repr__(self) -> str:
        """String representation of post."""
        return f"<Post(id={self.id}, title='{self.title}', status='{self.status}')>"