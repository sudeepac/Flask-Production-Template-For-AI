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
from typing import Any, Dict, List, Optional
from uuid import uuid4

from marshmallow import Schema, ValidationError, fields
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

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


class ExampleService:
    """Example service demonstrating error handling and logging best practices."""

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
            try:
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
                    user = self._get_user_or_raise(user_id)
                    self.logger.debug(
                        f"User {user_id} found for post creation",
                        extra={"context": {"operation_id": operation_id}},
                    )

                # Check for slug conflicts
                slug = self._generate_slug(validated_data["title"])
                if self._slug_exists(slug):
                    self.logger.warning(
                        f"Slug conflict detected: {slug}",
                        extra={"context": {"operation_id": operation_id, "slug": slug}},
                    )
                    raise ConflictAPIError(
                        f"Post with slug '{slug}' already exists",
                        {
                            "slug": slug,
                            "suggested_slug": f"{slug}-{int(datetime.utcnow().timestamp())}",
                        },
                    )

                # Create post with transaction
                post = self._create_post_transaction(validated_data, slug, user_id)

                # Log success
                self.logger.info(
                    f"Post created successfully: {post.id}",
                    extra={
                        "context": {
                            "operation_id": operation_id,
                            "post_id": post.id,
                            "slug": post.slug,
                        }
                    },
                )

                # Log security event for content creation
                log_security_event(
                    "content_creation",
                    f"New post created: {post.id}",
                    {
                        "post_id": post.id,
                        "user_id": user_id,
                        "operation_id": operation_id,
                    },
                    logging.INFO,
                )

                return self._serialize_post(post)

            except ValidationAPIError:
                # Re-raise validation errors as-is
                raise
            except (NotFoundAPIError, ConflictAPIError):
                # Re-raise known API errors as-is
                raise
            except IntegrityError as e:
                db.session.rollback()
                self.logger.error(
                    f"Database integrity error in create_post: {str(e)}",
                    extra={"context": {"operation_id": operation_id}},
                    exc_info=True,
                )
                raise ConflictAPIError(
                    "Data integrity constraint violation",
                    {"constraint_type": "database_constraint"},
                )
            except SQLAlchemyError as e:
                db.session.rollback()
                self.logger.error(
                    f"Database error in create_post: {str(e)}",
                    extra={"context": {"operation_id": operation_id}},
                    exc_info=True,
                )
                raise APIError("Database operation failed", 500)
            except Exception as e:
                db.session.rollback()
                self.logger.error(
                    f"Unexpected error in create_post: {str(e)}",
                    extra={"context": {"operation_id": operation_id}},
                    exc_info=True,
                )
                raise APIError("An unexpected error occurred", 500)

    def get_post(self, post_id: int) -> Dict[str, Any]:
        """Get a post by ID with error handling.

        Args:
            post_id: ID of the post to retrieve

        Returns:
            Post data dictionary

        Raises:
            NotFoundAPIError: If post not found
            APIError: For other service errors
        """
        try:
            self.logger.debug(
                f"Retrieving post {post_id}", extra={"context": {"post_id": post_id}}
            )

            post = db.session.query(Post).filter_by(id=post_id).first()
            if not post:
                self.logger.warning(
                    f"Post not found: {post_id}",
                    extra={"context": {"post_id": post_id}},
                )
                raise NotFoundAPIError(f"Post with ID {post_id} not found", "post")

            self.logger.info(
                f"Post retrieved successfully: {post_id}",
                extra={"context": {"post_id": post_id, "slug": post.slug}},
            )

            return self._serialize_post(post)

        except NotFoundAPIError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(
                f"Database error retrieving post {post_id}: {str(e)}",
                extra={"context": {"post_id": post_id}},
                exc_info=True,
            )
            raise APIError("Database operation failed", 500)
        except Exception as e:
            self.logger.error(
                f"Unexpected error retrieving post {post_id}: {str(e)}",
                extra={"context": {"post_id": post_id}},
                exc_info=True,
            )
            raise APIError("An unexpected error occurred", 500)

    def list_posts(
        self, page: int = 1, per_page: int = 10, filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """List posts with pagination and filtering.

        Args:
            page: Page number (1-based)
            per_page: Items per page
            filters: Optional filters

        Returns:
            Paginated posts data

        Raises:
            ValidationAPIError: If pagination parameters are invalid
            APIError: For other service errors
        """
        try:
            # Validate pagination parameters
            if page < 1:
                raise ValidationAPIError(
                    "Page number must be positive", {"page": "Must be >= 1"}
                )

            if per_page < 1 or per_page > 100:
                raise ValidationAPIError(
                    "Per page must be between 1 and 100",
                    {"per_page": "Must be between 1 and 100"},
                )

            self.logger.debug(
                f"Listing posts - page: {page}, per_page: {per_page}",
                extra={
                    "context": {
                        "page": page,
                        "per_page": per_page,
                        "filters": filters or {},
                    }
                },
            )

            # Build query
            query = db.session.query(Post)

            # Apply filters
            if filters:
                query = self._apply_post_filters(query, filters)

            # Get paginated results
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)

            posts_data = [self._serialize_post(post) for post in pagination.items]

            result = {
                "data": posts_data,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": pagination.total,
                    "pages": pagination.pages,
                    "has_next": pagination.has_next,
                    "has_prev": pagination.has_prev,
                },
            }

            self.logger.info(
                f"Posts listed successfully - {len(posts_data)} items",
                extra={
                    "context": {
                        "page": page,
                        "per_page": per_page,
                        "total_items": pagination.total,
                        "returned_items": len(posts_data),
                    }
                },
            )

            return result

        except ValidationAPIError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(
                f"Database error listing posts: {str(e)}",
                extra={"context": {"page": page, "per_page": per_page}},
                exc_info=True,
            )
            raise APIError("Database operation failed", 500)
        except Exception as e:
            self.logger.error(
                f"Unexpected error listing posts: {str(e)}",
                extra={"context": {"page": page, "per_page": per_page}},
                exc_info=True,
            )
            raise APIError("An unexpected error occurred", 500)

    def health_check(self) -> Dict[str, Any]:
        """Perform service health check.

        Returns:
            Health status data

        Raises:
            ServiceUnavailableAPIError: If service is unhealthy
        """
        try:
            self.logger.debug("Performing service health check")

            # Check database connectivity
            db.session.execute("SELECT 1")

            # Check if we can query posts table
            post_count = db.session.query(Post).count()

            health_data = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "checks": {"database": "ok", "posts_table": "ok"},
                "metrics": {"total_posts": post_count},
            }

            self.logger.info(
                "Service health check passed",
                extra={"context": {"post_count": post_count}},
            )

            return health_data

        except SQLAlchemyError as e:
            self.logger.error(f"Database health check failed: {str(e)}", exc_info=True)
            raise ServiceUnavailableAPIError("Database connectivity issues detected")
        except Exception as e:
            self.logger.error(f"Service health check failed: {str(e)}", exc_info=True)
            raise ServiceUnavailableAPIError("Service health check failed")

    # Private helper methods

    def _validate_post_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate post data.

        Args:
            data: Raw post data

        Returns:
            Validated post data

        Raises:
            ValidationAPIError: If validation fails
        """

        class PostSchema(Schema):
            title = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
            content = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
            excerpt = fields.Str(missing="")
            category = fields.Str(missing="general")
            tags = fields.List(fields.Str(), missing=[])
            status = fields.Str(
                missing="draft", validate=lambda x: x in ["draft", "published"]
            )

        schema = PostSchema()
        try:
            return schema.load(data)
        except ValidationError as e:
            self.logger.warning(
                f"Post data validation failed: {e.messages}",
                extra={"context": {"validation_errors": e.messages}},
            )
            raise ValidationAPIError("Invalid post data", {"field_errors": e.messages})

    def _get_user_or_raise(self, user_id: int) -> User:
        """Get user by ID or raise NotFoundAPIError.

        Args:
            user_id: User ID

        Returns:
            User instance

        Raises:
            NotFoundAPIError: If user not found
        """
        user = db.session.query(User).filter_by(id=user_id).first()
        if not user:
            raise NotFoundAPIError(f"User with ID {user_id} not found", "user")
        return user

    def _generate_slug(self, title: str) -> str:
        """Generate URL slug from title.

        Args:
            title: Post title

        Returns:
            URL slug
        """
        import re

        slug = re.sub(r"[^\w\s-]", "", title.lower())
        slug = re.sub(r"[-\s]+", "-", slug)
        return slug.strip("-")

    def _slug_exists(self, slug: str) -> bool:
        """Check if slug already exists.

        Args:
            slug: URL slug to check

        Returns:
            True if slug exists
        """
        return db.session.query(Post).filter_by(slug=slug).first() is not None

    def _create_post_transaction(
        self, data: Dict[str, Any], slug: str, user_id: Optional[int]
    ) -> Post:
        """Create post within database transaction.

        Args:
            data: Validated post data
            slug: Generated slug
            user_id: User ID

        Returns:
            Created post instance
        """
        post = Post(
            title=data["title"],
            content=data["content"],
            excerpt=data.get("excerpt", ""),
            slug=slug,
            category=data.get("category", "general"),
            tags=",".join(data.get("tags", [])),
            status=data.get("status", "draft"),
            user_id=user_id,
            view_count=0,
            like_count=0,
            comment_count=0,
        )

        if data.get("status") == "published":
            post.published_at = datetime.utcnow()

        db.session.add(post)
        db.session.commit()

        return post

    def _apply_post_filters(self, query, filters: Dict[str, Any]):
        """Apply filters to post query.

        Args:
            query: SQLAlchemy query
            filters: Filter dictionary

        Returns:
            Filtered query
        """
        if "status" in filters:
            query = query.filter(Post.status == filters["status"])

        if "category" in filters:
            query = query.filter(Post.category == filters["category"])

        if "user_id" in filters:
            query = query.filter(Post.user_id == filters["user_id"])

        return query

    def _serialize_post(self, post: Post) -> Dict[str, Any]:
        """Serialize post to dictionary.

        Args:
            post: Post instance

        Returns:
            Post data dictionary
        """
        return {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "excerpt": post.excerpt,
            "slug": post.slug,
            "category": post.category,
            "tags": post.tag_list,
            "status": post.status,
            "is_published": post.is_published,
            "user_id": post.user_id,
            "view_count": post.view_count,
            "like_count": post.like_count,
            "comment_count": post.comment_count,
            "created_at": (
                post.created_at.isoformat() + "Z" if post.created_at else None
            ),
            "updated_at": (
                post.updated_at.isoformat() + "Z" if post.updated_at else None
            ),
            "published_at": (
                post.published_at.isoformat() + "Z" if post.published_at else None
            ),
        }
