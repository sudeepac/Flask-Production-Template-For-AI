# Python Style Guide for Flask Production Template

This document provides comprehensive Python coding standards and style guidelines for the Flask Production Template for AI project. Following these guidelines ensures code consistency, readability, and maintainability across the entire codebase.

## 📋 Table of Contents

- [Overview](#overview)
- [Code Formatting](#code-formatting)
- [Naming Conventions](#naming-conventions)
- [Import Organization](#import-organization)
- [Documentation Standards](#documentation-standards)
- [Type Hints](#type-hints)
- [Error Handling](#error-handling)
- [Testing Standards](#testing-standards)
- [Security Guidelines](#security-guidelines)
- [Performance Guidelines](#performance-guidelines)
- [Tool Configuration](#tool-configuration)
- [Pre-commit Hooks](#pre-commit-hooks)
- [Examples](#examples)

## 🎯 Overview

We follow **PEP 8** as our base standard with specific modifications and enhancements tailored for this Flask application. Our style guide emphasizes:

- **Consistency**: Uniform code style across all modules
- **Readability**: Clear, self-documenting code
- **Maintainability**: Easy to modify and extend
- **Security**: Secure coding practices
- **Performance**: Efficient and scalable code

### Key Principles

1. **Code should be written for humans first, computers second**
2. **Explicit is better than implicit**
3. **Simple is better than complex**
4. **Consistency within the project trumps external consistency**

## 🎨 Code Formatting

### Line Length

- **Maximum line length**: 88 characters (Black default)
- **Docstring line length**: 72 characters
- **Comments**: 72 characters

### Indentation

- **Use 4 spaces** for indentation (no tabs)
- **Continuation lines**: Align with opening delimiter or use hanging indent

```python
# Good: Aligned with opening delimiter
foo = long_function_name(var_one, var_two,
                         var_three, var_four)

# Good: Hanging indent
foo = long_function_name(
    var_one, var_two,
    var_three, var_four
)
```

### Blank Lines

- **2 blank lines** around top-level class and function definitions
- **1 blank line** around method definitions inside classes
- **1 blank line** to separate logical sections within functions

### Quotes

- **Use double quotes** for strings by default
- **Use single quotes** for string literals within f-strings
- **Use triple double quotes** for docstrings

```python
# Good
message = "Hello, world!"
formatted = f"User {user['name']} logged in"

# Docstring
def function():
    """This is a docstring."""
    pass
```

## 📝 Naming Conventions

### Variables and Functions

- **snake_case** for variables, functions, and methods
- Use descriptive names that clearly indicate purpose

```python
# Good
user_count = 0
def calculate_total_price():
    pass

# Bad
n = 0
def calc():
    pass
```

### Classes

- **PascalCase** for class names
- Use nouns that describe what the class represents

```python
# Good
class UserService:
    pass

class DatabaseConnection:
    pass

# Bad
class userservice:
    pass
```

### Constants

- **UPPER_SNAKE_CASE** for constants
- Define at module level

```python
# Good
MAX_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT = 30
API_BASE_URL = "https://api.example.com"
```

### Files and Modules

- **snake_case** for file and module names
- Use descriptive names that indicate module purpose

```python
# Good
user_service.py
auth_middleware.py
ml_model_trainer.py

# Bad
UserService.py
auth.py
ml.py
```

### Packages

- **lowercase** for package names
- Avoid underscores if possible

```python
# Good
app/
utils/
services/

# Acceptable if needed for clarity
ml_models/
```

### Private Members

- **Single leading underscore** for internal use
- **Double leading underscore** for name mangling (rare)

```python
class UserService:
    def __init__(self):
        self.public_attr = "public"
        self._internal_attr = "internal"
        self.__private_attr = "private"  # Name mangled

    def public_method(self):
        pass

    def _internal_method(self):
        pass
```

## 📦 Import Organization

Imports should be organized in the following order with blank lines between groups:

1. **Standard library imports**
2. **Third-party library imports**
3. **Local application imports**

```python
# Standard library
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Third-party
import flask
from flask import Flask, request, jsonify
from sqlalchemy import Column, Integer, String

# Local application
from app.models import User
from app.services.user_service import UserService
from app.utils.security import hash_password
```

### Import Guidelines

- **Use absolute imports** for clarity
- **Avoid wildcard imports** (`from module import *`)
- **Group related imports** together
- **Use `as` for long module names** when needed

```python
# Good
from app.services.machine_learning import ModelTrainer as MLTrainer

# Bad
from app.services.machine_learning import *
```

## 📚 Documentation Standards

### Docstrings

Use **Google-style docstrings** for all public modules, classes, and functions:

```python
def calculate_user_score(user_id: int, include_bonus: bool = False) -> float:
    """Calculate the total score for a user.

    This function calculates the user's score based on their activities
    and optionally includes bonus points from special events.

    Args:
        user_id: The unique identifier for the user.
        include_bonus: Whether to include bonus points in calculation.
            Defaults to False.

    Returns:
        The calculated score as a floating-point number.

    Raises:
        ValueError: If user_id is not positive.
        UserNotFoundError: If user doesn't exist in the database.

    Example:
        >>> score = calculate_user_score(123, include_bonus=True)
        >>> print(f"User score: {score}")
        User score: 85.5
    """
    if user_id <= 0:
        raise ValueError("User ID must be positive")

    # Implementation here
    return 0.0
```

### Module Docstrings

Every module should have a docstring explaining its purpose:

```python
"""User authentication and authorization services.

This module provides comprehensive user authentication functionality
including login, logout, password management, and JWT token handling.

Classes:
    AuthService: Main authentication service class.
    TokenManager: JWT token management utilities.

Functions:
    authenticate_user: Authenticate user credentials.
    generate_token: Generate JWT access tokens.

Example:
    from app.services.auth_service import AuthService

    auth = AuthService()
    user = auth.authenticate_user("user@example.com", "password")
"""
```

### Comments

- **Explain WHY, not WHAT** the code does
- **Use inline comments** sparingly for complex logic
- **Keep comments up-to-date** with code changes

```python
# Good: Explains the reasoning
# Use exponential backoff to avoid overwhelming the API
time.sleep(2 ** attempt)

# Bad: States the obvious
# Increment counter by 1
counter += 1
```

## 🏷️ Type Hints

Use type hints for all function signatures and complex variables:

```python
from typing import Dict, List, Optional, Union, Any
from datetime import datetime

def process_user_data(
    users: List[Dict[str, Any]],
    active_only: bool = True
) -> Dict[str, Union[int, List[str]]]:
    """Process user data and return summary statistics."""
    result: Dict[str, Union[int, List[str]]] = {
        "total_users": 0,
        "active_users": [],
    }

    for user in users:
        if active_only and not user.get("is_active", False):
            continue

        result["total_users"] += 1
        result["active_users"].append(user["name"])

    return result
```

### Type Hint Guidelines

- **Use built-in types** when possible (Python 3.9+)
- **Import from typing** for complex types
- **Use Optional** for nullable values
- **Use Union** sparingly, prefer specific types

```python
# Python 3.9+ style (preferred)
def process_items(items: list[dict[str, any]]) -> dict[str, int]:
    pass

# Legacy style (for compatibility)
from typing import List, Dict, Any
def process_items(items: List[Dict[str, Any]]) -> Dict[str, int]:
    pass
```

## ⚠️ Error Handling

### Exception Handling

- **Use specific exception types** rather than bare `except:`
- **Handle exceptions at the appropriate level**
- **Provide meaningful error messages**
- **Use custom exceptions** for application-specific errors

```python
# Good
try:
    user = User.query.get(user_id)
    if not user:
        raise UserNotFoundError(f"User {user_id} not found")
except SQLAlchemyError as e:
    logger.error(f"Database error while fetching user {user_id}: {e}")
    raise DatabaseError("Failed to retrieve user") from e
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise

# Bad
try:
    user = User.query.get(user_id)
except:
    pass  # Silent failure
```

### Custom Exceptions

Define custom exceptions for application-specific errors:

```python
class AppError(Exception):
    """Base exception for application errors."""
    pass

class ValidationError(AppError):
    """Raised when input validation fails."""
    pass

class AuthenticationError(AppError):
    """Raised when authentication fails."""
    pass
```

## 🧪 Testing Standards

### Test Naming

- **Use descriptive test names** that explain what is being tested
- **Follow the pattern**: `test_<what>_<when>_<expected>`

```python
def test_user_creation_with_valid_data_creates_user():
    """Test that user creation with valid data successfully creates a user."""
    pass

def test_user_login_with_invalid_password_raises_authentication_error():
    """Test that login with invalid password raises AuthenticationError."""
    pass
```

### Test Structure

Use the **Arrange-Act-Assert** pattern:

```python
def test_calculate_total_price_with_discount():
    """Test price calculation with discount applied."""
    # Arrange
    items = [Item("laptop", 1000), Item("mouse", 50)]
    discount_rate = 0.1

    # Act
    total = calculate_total_price(items, discount_rate)

    # Assert
    assert total == 945.0  # (1000 + 50) * 0.9
```

## 🔒 Security Guidelines

### Input Validation

- **Validate all user inputs**
- **Use parameterized queries** for database operations
- **Sanitize data** before processing

```python
# Good
def get_user_by_email(email: str) -> Optional[User]:
    if not email or "@" not in email:
        raise ValidationError("Invalid email format")

    # Use parameterized query
    return User.query.filter(User.email == email).first()

# Bad
def get_user_by_email(email: str) -> Optional[User]:
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE email = '{email}'"
    return db.execute(query)
```

### Sensitive Data

- **Never log sensitive information**
- **Use environment variables** for secrets
- **Mask sensitive data** in logs

```python
# Good
logger.info(f"User {user.id} logged in successfully")
password_hash = hash_password(password)  # Don't log the password

# Bad
logger.info(f"User {user.email} logged in with password {password}")
```

## ⚡ Performance Guidelines

### Database Operations

- **Use lazy loading** appropriately
- **Optimize queries** with proper indexing
- **Use bulk operations** for multiple records

```python
# Good: Bulk operation
users_to_update = User.query.filter(User.is_active == False).all()
for user in users_to_update:
    user.last_login = None
db.session.bulk_save_objects(users_to_update)
db.session.commit()

# Bad: Individual operations
for user in User.query.filter(User.is_active == False).all():
    user.last_login = None
    db.session.commit()  # Commits for each user
```

### Memory Management

- **Use generators** for large datasets
- **Close resources** properly
- **Avoid memory leaks** in long-running processes

```python
# Good: Generator for memory efficiency
def process_large_dataset(filename: str):
    with open(filename, 'r') as file:
        for line in file:
            yield process_line(line)

# Bad: Loading everything into memory
def process_large_dataset(filename: str):
    with open(filename, 'r') as file:
        lines = file.readlines()  # Loads entire file
        return [process_line(line) for line in lines]
```

## 🔧 Tool Configuration

### Black (Code Formatting)

```toml
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py310']
include = '\.pyi?$'
extend-exclude = '''
(
  /(
      \.eggs
    | \.git
    | \.venv
    | migrations
  )/
)
'''
```

### isort (Import Sorting)

```toml
# pyproject.toml
[tool.isort]
profile = "black"
line_length = 88
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
skip_glob = ["migrations/*"]
known_first_party = ["app"]
```

### Flake8 (Linting)

```ini
# .flake8 or setup.cfg
[flake8]
max-line-length = 88
extend-ignore = E203, E501, W503
exclude = .git,__pycache__,.venv,migrations
per-file-ignores =
    __init__.py:F401
    tests/*:S101
```

### MyPy (Type Checking)

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
check_untyped_defs = true
no_implicit_optional = true
strict_equality = true
```

## 🪝 Pre-commit Hooks

The project uses pre-commit hooks to enforce code quality:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### Configured Hooks

- **trailing-whitespace**: Remove trailing whitespace
- **end-of-file-fixer**: Ensure files end with newline
- **black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **bandit**: Security linting

## 📋 Examples

### Complete Class Example

```python
"""User service module for handling user operations."""

from typing import List, Optional
from datetime import datetime

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from app.models import User, db
from app.utils.security import hash_password, verify_password
from app.utils.exceptions import ValidationError, UserNotFoundError


class UserService:
    """Service class for user-related operations.

    This class provides methods for user management including
    creation, authentication, and profile updates.

    Attributes:
        logger: Logger instance for this service.

    Example:
        >>> service = UserService()
        >>> user = service.create_user("john@example.com", "password123")
        >>> print(f"Created user: {user.email}")
    """

    def __init__(self) -> None:
        """Initialize the user service."""
        self.logger = current_app.logger

    def create_user(self, email: str, password: str, name: str = None) -> User:
        """Create a new user account.

        Args:
            email: User's email address.
            password: Plain text password (will be hashed).
            name: Optional user's full name.

        Returns:
            The created User instance.

        Raises:
            ValidationError: If email format is invalid or password is weak.
            SQLAlchemyError: If database operation fails.

        Example:
            >>> user = service.create_user("john@example.com", "secure123")
            >>> print(user.id)
            1
        """
        # Validate input
        if not self._is_valid_email(email):
            raise ValidationError("Invalid email format")

        if not self._is_strong_password(password):
            raise ValidationError("Password does not meet requirements")

        try:
            # Create user with hashed password
            user = User(
                email=email.lower().strip(),
                password_hash=hash_password(password),
                name=name.strip() if name else None,
                created_at=datetime.utcnow()
            )

            db.session.add(user)
            db.session.commit()

            self.logger.info(f"Created user account for {email}")
            return user

        except SQLAlchemyError as e:
            db.session.rollback()
            self.logger.error(f"Failed to create user {email}: {e}")
            raise

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user credentials.

        Args:
            email: User's email address.
            password: Plain text password.

        Returns:
            User instance if authentication successful, None otherwise.

        Example:
            >>> user = service.authenticate_user("john@example.com", "password")
            >>> if user:
            ...     print(f"Welcome, {user.name}!")
        """
        if not email or not password:
            return None

        user = User.query.filter(User.email == email.lower()).first()
        if user and verify_password(password, user.password_hash):
            # Update last login timestamp
            user.last_login = datetime.utcnow()
            db.session.commit()

            self.logger.info(f"User {email} authenticated successfully")
            return user

        self.logger.warning(f"Failed authentication attempt for {email}")
        return None

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format.

        Args:
            email: Email address to validate.

        Returns:
            True if email format is valid, False otherwise.
        """
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _is_strong_password(self, password: str) -> bool:
        """Check if password meets strength requirements.

        Args:
            password: Password to validate.

        Returns:
            True if password is strong enough, False otherwise.
        """
        # Minimum 8 characters, at least one letter and one number
        if len(password) < 8:
            return False

        has_letter = any(c.isalpha() for c in password)
        has_number = any(c.isdigit() for c in password)

        return has_letter and has_number
```

### Function Example

```python
def calculate_pagination_info(
    total_items: int,
    page: int = 1,
    per_page: int = 20
) -> Dict[str, Union[int, bool]]:
    """Calculate pagination information for API responses.

    Args:
        total_items: Total number of items in the dataset.
        page: Current page number (1-indexed).
        per_page: Number of items per page.

    Returns:
        Dictionary containing pagination metadata:
        - page: Current page number
        - per_page: Items per page
        - total: Total number of items
        - pages: Total number of pages
        - has_prev: Whether there's a previous page
        - has_next: Whether there's a next page
        - prev_num: Previous page number (None if no previous)
        - next_num: Next page number (None if no next)

    Raises:
        ValueError: If page or per_page is not positive.

    Example:
        >>> info = calculate_pagination_info(100, page=2, per_page=10)
        >>> print(info['pages'])
        10
        >>> print(info['has_next'])
        True
    """
    if page < 1:
        raise ValueError("Page number must be positive")
    if per_page < 1:
        raise ValueError("Items per page must be positive")

    total_pages = (total_items + per_page - 1) // per_page  # Ceiling division

    return {
        "page": page,
        "per_page": per_page,
        "total": total_items,
        "pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
        "prev_num": page - 1 if page > 1 else None,
        "next_num": page + 1 if page < total_pages else None,
    }
```

## 🚀 Quick Commands

```bash
# Format code
black .

# Sort imports
isort .

# Check style
flake8 .

# Type checking
mypy app/

# Run all quality checks
pre-commit run --all-files

# Run tests with coverage
pytest --cov=app --cov-report=html

# Security check
bandit -r app/
```

---

**Remember**: Consistency is key. When in doubt, follow the existing patterns in the codebase and refer to this guide. If you need to deviate from these guidelines, document the reason and discuss with the team.

**Tools**: This style guide is enforced by automated tools (Black, isort, Flake8, MyPy) configured in the project. The pre-commit hooks ensure compliance before code is committed.

**Updates**: This style guide is a living document. As the project evolves, update this guide to reflect new standards and best practices.
