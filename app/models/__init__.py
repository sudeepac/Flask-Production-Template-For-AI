"""Database models package.

This package contains all database models for the application.
Models are organized by domain/feature for better maintainability.
"""

from .base import BaseModel
from .example import User, Post

# Export all models for easy importing
__all__ = [
    'BaseModel',
    'User', 
    'Post'
]