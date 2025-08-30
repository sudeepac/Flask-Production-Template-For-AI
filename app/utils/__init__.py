"""Utilities Package.

This package contains utility functions and classes that are used
across the application. Utilities are organized by functionality.

Utility Modules:
- helpers: General helper functions
- validators: Data validation utilities
- decorators: Custom decorators
- formatters: Data formatting utilities
- security: Security-related utilities
- ml_utils: Machine learning utilities
- api_utils: API-specific utilities

Usage:
    from app.utils import helpers, validators
    from app.utils.decorators import require_api_key
    from app.utils.security import hash_password

See AI_INSTRUCTIONS.md §6 for utility implementation guidelines.
"""

import hashlib
import json
import logging
import secrets
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Dict, List

# Flask imports removed - not used in this module

logger = logging.getLogger(__name__)


# Common utility functions that are used frequently


def get_timestamp() -> str:
    """Get current UTC timestamp in ISO format.

    Returns:
        str: ISO formatted timestamp
    """
    return datetime.now(timezone.utc).isoformat()


def generate_id(prefix: str = "", length: int = 16) -> str:
    """Generate a random ID with optional prefix.

    Args:
        prefix: Optional prefix for the ID
        length: Length of the random part

    Returns:
        str: Generated ID
    """
    random_part = secrets.token_hex(length // 2)
    return f"{prefix}{random_part}" if prefix else random_part


def safe_json_loads(data: str, default: Any = None) -> Any:
    """Safely parse JSON string.

    Args:
        data: JSON string to parse
        default: Default value if parsing fails

    Returns:
        Parsed JSON data or default value
    """
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(data: Any, default: str = "{}") -> str:
    """Safely serialize data to JSON string.

    Args:
        data: Data to serialize
        default: Default value if serialization fails

    Returns:
        JSON string or default value
    """
    try:
        return json.dumps(data, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        return default


def hash_string(data: str, algorithm: str = "sha256") -> str:
    """Hash a string using the specified algorithm.

    Args:
        data: String to hash
        algorithm: Hash algorithm to use

    Returns:
        str: Hexadecimal hash digest
    """
    hasher = hashlib.new(algorithm)
    hasher.update(data.encode("utf-8"))
    return hasher.hexdigest()


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate a string to a maximum length.

    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        str: Truncated string
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def flatten_dict(
    data: Dict[str, Any], separator: str = ".", prefix: str = ""
) -> Dict[str, Any]:
    """Flatten a nested dictionary.

    Args:
        data: Dictionary to flatten
        separator: Separator for nested keys
        prefix: Prefix for keys

    Returns:
        dict: Flattened dictionary
    """
    result = {}

    for key, value in data.items():
        new_key = f"{prefix}{separator}{key}" if prefix else key

        if isinstance(value, dict):
            result.update(flatten_dict(value, separator, new_key))
        else:
            result[new_key] = value

    return result


def chunk_list(data: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size.

    Args:
        data: List to chunk
        chunk_size: Size of each chunk

    Returns:
        list: List of chunks
    """
    return [data[i : i + chunk_size] for i in range(0, len(data), chunk_size)]


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries.

    Args:
        *dicts: Dictionaries to merge

    Returns:
        dict: Merged dictionary
    """
    result = {}
    for d in dicts:
        if isinstance(d, dict):
            result.update(d)
    return result


def get_nested_value(
    data: Dict[str, Any], key_path: str, separator: str = ".", default: Any = None
) -> Any:
    """Get value from nested dictionary using dot notation.

    Args:
        data: Dictionary to search
        key_path: Dot-separated key path
        separator: Key separator
        default: Default value if key not found

    Returns:
        Value at key path or default
    """
    keys = key_path.split(separator)
    current = data

    try:
        for key in keys:
            current = current[key]
        return current
    except (KeyError, TypeError):
        return default


def set_nested_value(
    data: Dict[str, Any], key_path: str, value: Any, separator: str = "."
) -> None:
    """Set value in nested dictionary using dot notation.

    Args:
        data: Dictionary to modify
        key_path: Dot-separated key path
        value: Value to set
        separator: Key separator
    """
    keys = key_path.split(separator)
    current = data

    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]

    current[keys[-1]] = value


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by removing/replacing invalid characters.

    Args:
        filename: Original filename

    Returns:
        str: Sanitized filename
    """
    import re

    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)

    # Remove leading/trailing whitespace and dots
    filename = filename.strip(" .")

    # Ensure filename is not empty
    if not filename:
        filename = "unnamed_file"

    return filename


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        str: Formatted size string
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math

    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)

    return f"{s} {size_names[i]}"


def is_valid_email(email: str) -> bool:
    """Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        bool: True if valid email format
    """
    import re

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def is_valid_url(url: str) -> bool:
    """Validate URL format.

    Args:
        url: URL to validate

    Returns:
        bool: True if valid URL format
    """
    import re

    pattern = (
        r"^https?://(?:[-\w.])+(?:[:\d]+)?"
        r"(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$"
    )
    return bool(re.match(pattern, url))


def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """Mask sensitive data like API keys, passwords, etc.

    Args:
        data: Sensitive data to mask
        mask_char: Character to use for masking
        visible_chars: Number of characters to keep visible at the end

    Returns:
        str: Masked data
    """
    if len(data) <= visible_chars:
        return mask_char * len(data)

    masked_length = len(data) - visible_chars
    return mask_char * masked_length + data[-visible_chars:]


def retry_on_exception(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """Decorator to retry function on specified exceptions.

    Args:
        max_retries: Maximum number of retries
        delay: Initial delay between retries
        backoff: Backoff multiplier for delay
        exceptions: Tuple of exceptions to catch

    Returns:
        Decorated function
    """

    def decorator(func):
        """Decorator function for utility operations."""

        @wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapper function for decorated operations."""
            import time

            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        raise e

                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. Retrying in {current_delay}s..."
                    )

                    time.sleep(current_delay)
                    current_delay *= backoff

        return wrapper

    return decorator


# Export commonly used utilities
__all__ = [
    "get_timestamp",
    "generate_id",
    "safe_json_loads",
    "safe_json_dumps",
    "hash_string",
    "truncate_string",
    "flatten_dict",
    "chunk_list",
    "merge_dicts",
    "get_nested_value",
    "set_nested_value",
    "sanitize_filename",
    "format_file_size",
    "is_valid_email",
    "is_valid_url",
    "mask_sensitive_data",
    "retry_on_exception",
]
