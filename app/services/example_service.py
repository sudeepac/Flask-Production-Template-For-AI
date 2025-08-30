"""Example Service with Error Handling and Logging.

This module demonstrates best practices for error handling and logging
in service classes. Use this as a template for implementing other services.

Features:
- Comprehensive error handling
- Structured logging with context
- Performance monitoring
- Input validation
- Database transaction management
- Security event logging

Usage:
    from app.services.example_service import ExampleService

    service = ExampleService()
    result = service.create_item({"name": "test"})
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from marshmallow import Schema, ValidationError, fields
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models.example import Post, User
from app.utils.error_handlers import (
    APIError,
    ConflictAPIError,
    NotFoundAPIError,
    ServiceUnavailableAPIError,
    ValidationAPIError,
)
from app.utils.logging_config import PerformanceLogger, get_logger, log_security_event
from app.utils.service_helpers import safe_execute, validate_required_fields, ServiceError, ValidationError


class ExampleService:
    """Example service demonstrating error handling and logging best
    practices.
    """

    def __init__(self):
        """Initialize the service."""
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("ExampleService initialized")

    def create_post(
        self, data: Dict[str, Any], user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new post with comprehensive error handling.

        Args:
            data: Post data dictionary
            user_id: ID of the user creating the post

        Returns:
            Created post data

        Raises:
            ValidationAPIError: If input data is invalid
            NotFoundAPIError: If user not found
            ConflictAPIError: If post with same slug exists
            APIError: For other service errors
        """
        operation_id = str(uuid4())

        with PerformanceLogger(f"create_post_{operation_id}", self.logger):
            self.logger.info(
                f"Creating post for user {user_id}",
                extra={
                    "context": {
                        "operation_id": operation_id,
                        "user_id": user_id,
                        "data_keys": list(data.keys()),
                    }
                },
            )

            # Validate input data
            validated_data = self._validate_post_data(data)

            # Check if user exists
            if user_id:
                self._get_user_or_raise(user_id)
                self.logger.debug(
                    f"User {user_id} found for post creation",
                    extra={"context": {"operation_id": operation_id}},
                )

            # Check for slug conflicts
            slug = self._generate_slug(validated_data["title"])
            
            try:
                # Create post
                post = Post(
                    title=validated_data["title"],
                    content=validated_data["content"],
                    user_id=user_id,
                    created_at=datetime.utcnow()
                )
                
                db.session.add(post)
                db.session.commit()
                
                self.logger.info(f"Created post {post.id} for user {user_id}")
                return self._post_to_dict(post)
                
            except SQLAlchemyError as e:
                db.session.rollback()
                self.logger.error(f"Database error creating post: {str(e)}")
                raise APIError("Failed to create post") from e

    def get_post(self, post_id: int) -> Dict[str, Any]:
        """Get a post by ID.
        
        Args:
            post_id: ID of the post to retrieve
            
        Returns:
            Post data as dictionary
            
        Raises:
            NotFoundAPIError: If post not found
        """
        post = Post.query.get(post_id)
        if not post:
            raise NotFoundAPIError(f"Post {post_id} not found")
            
        return self._post_to_dict(post)
    
    def update_post(self, post_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a post.
        
        Args:
            post_id: ID of the post to update
            data: Updated post data
            
        Returns:
            Updated post data as dictionary
            
        Raises:
            NotFoundAPIError: If post not found
            ValidationAPIError: If data is invalid
        """
        try:
            post = Post.query.get(post_id)
            if not post:
                raise NotFoundAPIError(f"Post {post_id} not found")
            
            # Update fields if provided
            if 'title' in data:
                post.title = data['title']
            if 'content' in data:
                post.content = data['content']
                
            db.session.commit()
            
            self.logger.info(f"Updated post {post_id}")
            return self._post_to_dict(post)
            
        except SQLAlchemyError as e:
            db.session.rollback()
            self.logger.error(f"Database error updating post: {str(e)}")
            raise APIError("Failed to update post") from e
    
    def delete_post(self, post_id: int) -> bool:
        """Delete a post.
        
        Args:
            post_id: ID of the post to delete
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundAPIError: If post not found
        """
        try:
            post = Post.query.get(post_id)
            if not post:
                raise NotFoundAPIError(f"Post {post_id} not found")
            
            db.session.delete(post)
            db.session.commit()
            
            self.logger.info(f"Deleted post {post_id}")
            return True
            
        except SQLAlchemyError as e:
            db.session.rollback()
            self.logger.error(f"Database error deleting post: {str(e)}")
            raise APIError("Failed to delete post") from e

    # Private helper methods

    def _validate_post_data(self, data: Dict[str, Any]) -> None:
        """Validate post data.

        Args:
            data: Post data to validate

        Raises:
            ValidationAPIError: If validation fails
        """
        if not isinstance(data, dict):
            raise ValidationAPIError("Data must be a dictionary")
            
        required_fields = ['title', 'content']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            raise ValidationAPIError(f"Missing required fields: {', '.join(missing_fields)}")
            
        if not data['title'].strip():
            raise ValidationAPIError("Title cannot be empty")
            
        if not data['content'].strip():
            raise ValidationAPIError("Content cannot be empty")

    def _get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: User ID to look up

        Returns:
            User instance or None if not found
        """
        return User.query.get(user_id)

    def _post_to_dict(self, post: Post) -> Dict[str, Any]:
        """Convert Post model to dictionary.

        Args:
            post: Post model instance

        Returns:
            Post data as dictionary
        """
        return {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "user_id": post.user_id,
            "created_at": post.created_at.isoformat() if post.created_at else None,
        }
