"""Template Blueprint Utilities.

This module contains utility functions and helpers specific to the template blueprint.
Utilities provide reusable functionality for common operations.

Utility Types:
- Data processing utilities
- Validation helpers
- Formatting functions
- Helper decorators
- Common algorithms

See AI_INSTRUCTIONS.md §6 for utility implementation guidelines.
"""

import hashlib
import json
import re
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urljoin, urlparse

from flask import current_app, request, url_for
from marshmallow import ValidationError


def validate_template_name(name: str) -> bool:
    """Validate template name format.

    Args:
        name: Template name to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not name or not isinstance(name, str):
        return False

    # Check length
    if len(name.strip()) < 1 or len(name.strip()) > 100:
        return False

    # Check for valid characters (alphanumeric, spaces, hyphens, underscores)
    pattern = r"^[a-zA-Z0-9\s\-_]+$"
    if not re.match(pattern, name.strip()):
        return False

    # Check for reserved names
    reserved_names = ["admin", "api", "system", "default", "root", "test"]
    if name.lower().strip() in reserved_names:
        return False

    return True


def sanitize_template_name(name: str) -> str:
    """Sanitize template name for safe usage.

    Args:
        name: Template name to sanitize

    Returns:
        str: Sanitized template name
    """
    if not name:
        return ""

    # Remove extra whitespace and convert to string
    sanitized = str(name).strip()

    # Replace multiple spaces with single space
    sanitized = re.sub(r"\s+", " ", sanitized)

    # Remove invalid characters
    sanitized = re.sub(r"[^a-zA-Z0-9\s\-_]", "", sanitized)

    # Limit length
    if len(sanitized) > 100:
        sanitized = sanitized[:100].strip()

    return sanitized


def validate_template_tags(tags: List[str]) -> List[str]:
    """Validate and sanitize template tags.

    Args:
        tags: List of tags to validate

    Returns:
        List[str]: List of valid, sanitized tags

    Raises:
        ValidationError: If tags are invalid
    """
    if not tags:
        return []

    if not isinstance(tags, list):
        raise ValidationError("Tags must be a list")

    validated_tags = []

    for tag in tags:
        if not isinstance(tag, str):
            continue

        # Sanitize tag
        sanitized_tag = tag.strip().lower()

        # Skip empty tags
        if not sanitized_tag:
            continue

        # Validate tag format
        if not re.match(r"^[a-zA-Z0-9\-_]+$", sanitized_tag):
            raise ValidationError(f'Tag "{tag}" contains invalid characters')

        # Check tag length
        if len(sanitized_tag) > 50:
            raise ValidationError(f'Tag "{tag}" is too long (max 50 characters)')

        # Add unique tags only
        if sanitized_tag not in validated_tags:
            validated_tags.append(sanitized_tag)

    # Limit number of tags
    if len(validated_tags) > 10:
        raise ValidationError("Cannot have more than 10 tags")

    return validated_tags


def generate_template_slug(name: str) -> str:
    """Generate URL-friendly slug from template name.

    Args:
        name: Template name

    Returns:
        str: URL-friendly slug
    """
    if not name:
        return ""

    # Convert to lowercase and replace spaces with hyphens
    slug = name.lower().strip()
    slug = re.sub(r"\s+", "-", slug)

    # Remove invalid characters
    slug = re.sub(r"[^a-z0-9\-_]", "", slug)

    # Remove multiple consecutive hyphens
    slug = re.sub(r"-+", "-", slug)

    # Remove leading/trailing hyphens
    slug = slug.strip("-")

    return slug


def calculate_template_hash(template_data: Dict[str, Any]) -> str:
    """Calculate hash for template data.

    Args:
        template_data: Template data dictionary

    Returns:
        str: SHA-256 hash of template data
    """
    # Create a normalized representation of the data
    normalized_data = {
        "name": template_data.get("name", ""),
        "description": template_data.get("description", ""),
        "category": template_data.get("category", ""),
        "tags": sorted(template_data.get("tags", [])),
        "configuration": template_data.get("configuration", {}),
    }

    # Convert to JSON string with sorted keys
    json_string = json.dumps(normalized_data, sort_keys=True, separators=(",", ":"))

    # Calculate SHA-256 hash
    return hashlib.sha256(json_string.encode("utf-8")).hexdigest()


def format_template_size(size_bytes: int) -> str:
    """Format template size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        str: Formatted size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def parse_template_filters(request_args: Dict[str, Any]) -> Dict[str, Any]:
    """Parse and validate template filter parameters from request.

    Args:
        request_args: Request arguments dictionary

    Returns:
        Dict[str, Any]: Parsed and validated filters
    """
    filters = {}

    # Parse boolean filters
    if "is_active" in request_args:
        value = request_args["is_active"]
        if isinstance(value, str):
            filters["is_active"] = value.lower() in ("true", "1", "yes", "on")
        else:
            filters["is_active"] = bool(value)

    if "is_public" in request_args:
        value = request_args["is_public"]
        if isinstance(value, str):
            filters["is_public"] = value.lower() in ("true", "1", "yes", "on")
        else:
            filters["is_public"] = bool(value)

    # Parse string filters
    if "category" in request_args and request_args["category"]:
        filters["category"] = str(request_args["category"]).strip()

    if "search" in request_args and request_args["search"]:
        filters["search"] = str(request_args["search"]).strip()

    # Parse tags filter
    if "tags" in request_args:
        tags = request_args["tags"]
        if isinstance(tags, str):
            # Split comma-separated tags
            filters["tags"] = [tag.strip() for tag in tags.split(",") if tag.strip()]
        elif isinstance(tags, list):
            filters["tags"] = [str(tag).strip() for tag in tags if str(tag).strip()]

    # Parse date filters
    if "created_after" in request_args:
        try:
            filters["created_after"] = datetime.fromisoformat(
                request_args["created_after"]
            )
        except (ValueError, TypeError):
            pass

    if "created_before" in request_args:
        try:
            filters["created_before"] = datetime.fromisoformat(
                request_args["created_before"]
            )
        except (ValueError, TypeError):
            pass

    return filters


def build_template_url(template_id: int, action: str = "view", **kwargs) -> str:
    """Build URL for template-related actions.

    Args:
        template_id: Template ID
        action: Action type ('view', 'edit', 'delete', etc.)
        **kwargs: Additional URL parameters

    Returns:
        str: Built URL
    """
    endpoint_map = {
        "view": "template.get_template",
        "edit": "template.update_template",
        "delete": "template.delete_template",
        "duplicate": "template.duplicate_template",
        "export": "template.export_template",
    }

    endpoint = endpoint_map.get(action, "template.get_template")

    try:
        return url_for(endpoint, template_id=template_id, **kwargs)
    except Exception:
        # Fallback to basic URL
        return f"/api/templates/{template_id}"


def paginate_results(
    query_result: List[Any], page: int = 1, per_page: int = 10
) -> Dict[str, Any]:
    """Paginate query results.

    Args:
        query_result: List of query results
        page: Page number (1-based)
        per_page: Items per page

    Returns:
        Dict[str, Any]: Pagination information and data
    """
    total = len(query_result)

    # Calculate pagination values
    total_pages = (total + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages

    # Calculate slice indices
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    # Get page data
    page_data = query_result[start_idx:end_idx]

    return {
        "data": page_data,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_prev": has_prev,
            "has_next": has_next,
            "prev_page": page - 1 if has_prev else None,
            "next_page": page + 1 if has_next else None,
        },
    }


def cache_key_for_template(template_id: int, action: str = "get") -> str:
    """Generate cache key for template operations.

    Args:
        template_id: Template ID
        action: Action type

    Returns:
        str: Cache key
    """
    return f"template:{action}:{template_id}"


def cache_key_for_template_list(
    filters: Optional[Dict[str, Any]] = None, page: int = 1, per_page: int = 10
) -> str:
    """Generate cache key for template list operations.

    Args:
        filters: Filter parameters
        page: Page number
        per_page: Items per page

    Returns:
        str: Cache key
    """
    # Create a normalized representation of filters
    filter_str = ""
    if filters:
        sorted_filters = sorted(filters.items())
        filter_str = json.dumps(sorted_filters, sort_keys=True, separators=(",", ":"))

    # Create hash of the filter string for shorter cache keys
    filter_hash = hashlib.md5(filter_str.encode("utf-8")).hexdigest()[:8]

    return f"template:list:{filter_hash}:{page}:{per_page}"


def require_template_permission(permission: str):
    """Decorator to require specific template permissions.

    Args:
        permission: Required permission ('read', 'write', 'delete', 'admin')

    Returns:
        Callable: Decorator function
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # This is a placeholder implementation
            # In a real application, you would check user permissions here

            # Example permission check (implement based on your auth system)
            # if not current_user.has_permission(f'template:{permission}'):
            #     abort(403, description='Insufficient permissions')

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def log_template_action(
    action: str,
    template_id: Optional[int] = None,
    user_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
):
    """Log template-related actions for audit purposes.

    Args:
        action: Action performed
        template_id: Template ID (if applicable)
        user_id: User ID (if applicable)
        details: Additional action details
    """
    # This is a placeholder implementation
    # In a real application, you would log to your audit system

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "template_id": template_id,
        "user_id": user_id,
        "details": details or {},
        "ip_address": request.remote_addr if request else None,
        "user_agent": request.headers.get("User-Agent") if request else None,
    }

    # Log to application logger
    current_app.logger.info(f"Template action: {json.dumps(log_entry)}")


def validate_template_configuration(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate template configuration data.

    Args:
        config: Configuration dictionary to validate

    Returns:
        Dict[str, Any]: Validated configuration

    Raises:
        ValidationError: If configuration is invalid
    """
    if not isinstance(config, dict):
        raise ValidationError("Configuration must be a dictionary")

    validated_config = {}

    # Define allowed configuration keys and their types
    allowed_keys = {
        "version": str,
        "schema": str,
        "settings": dict,
        "parameters": dict,
        "metadata": dict,
    }

    for key, value in config.items():
        if key in allowed_keys:
            expected_type = allowed_keys[key]
            if not isinstance(value, expected_type):
                raise ValidationError(
                    f'Configuration key "{key}" must be of type {expected_type.__name__}'
                )
            validated_config[key] = value
        else:
            # Allow unknown keys but log a warning
            current_app.logger.warning(f"Unknown configuration key: {key}")
            validated_config[key] = value

    return validated_config


def merge_template_metadata(
    base_metadata: Dict[str, Any], new_metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """Merge template metadata dictionaries.

    Args:
        base_metadata: Base metadata dictionary
        new_metadata: New metadata to merge

    Returns:
        Dict[str, Any]: Merged metadata
    """
    if not base_metadata:
        return new_metadata.copy() if new_metadata else {}

    if not new_metadata:
        return base_metadata.copy()

    merged = base_metadata.copy()

    for key, value in new_metadata.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            merged[key] = merge_template_metadata(merged[key], value)
        else:
            # Overwrite with new value
            merged[key] = value

    return merged


def extract_template_dependencies(config: Dict[str, Any]) -> List[str]:
    """Extract dependencies from template configuration.

    Args:
        config: Template configuration

    Returns:
        List[str]: List of dependency identifiers
    """
    dependencies = []

    # Look for dependencies in various configuration sections
    if "dependencies" in config:
        deps = config["dependencies"]
        if isinstance(deps, list):
            dependencies.extend(deps)
        elif isinstance(deps, dict):
            dependencies.extend(deps.keys())

    if "requires" in config:
        requires = config["requires"]
        if isinstance(requires, list):
            dependencies.extend(requires)

    if "imports" in config:
        imports = config["imports"]
        if isinstance(imports, list):
            dependencies.extend(imports)

    # Remove duplicates and return
    return list(set(dependencies))


def validate_url(url: str) -> bool:
    """Validate URL format.

    Args:
        url: URL to validate

    Returns:
        bool: True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def safe_join_url(base: str, path: str) -> str:
    """Safely join base URL with path.

    Args:
        base: Base URL
        path: Path to join

    Returns:
        str: Joined URL
    """
    try:
        return urljoin(base.rstrip("/") + "/", path.lstrip("/"))
    except Exception:
        return base


class TemplateProcessor:
    """Utility class for processing template data.

    This class provides methods for complex template data processing
    that don't fit into simple utility functions.
    """

    def __init__(self, template_data: Dict[str, Any]):
        """Initialize processor with template data.

        Args:
            template_data: Template data to process
        """
        self.template_data = template_data.copy()
        self.processed_data = {}
        self.errors = []

    def validate(self) -> bool:
        """Validate template data.

        Returns:
            bool: True if valid, False otherwise
        """
        self.errors = []

        # Validate required fields
        required_fields = ["name"]
        for field in required_fields:
            if field not in self.template_data or not self.template_data[field]:
                self.errors.append(f"Missing required field: {field}")

        # Validate name
        if "name" in self.template_data:
            if not validate_template_name(self.template_data["name"]):
                self.errors.append("Invalid template name")

        # Validate tags
        if "tags" in self.template_data:
            try:
                validate_template_tags(self.template_data["tags"])
            except ValidationError as e:
                self.errors.append(f"Invalid tags: {str(e)}")

        # Validate configuration
        if "configuration" in self.template_data:
            try:
                validate_template_configuration(self.template_data["configuration"])
            except ValidationError as e:
                self.errors.append(f"Invalid configuration: {str(e)}")

        return len(self.errors) == 0

    def process(self) -> Dict[str, Any]:
        """Process template data.

        Returns:
            Dict[str, Any]: Processed template data

        Raises:
            ValueError: If validation fails
        """
        if not self.validate():
            raise ValueError(f"Validation failed: {', '.join(self.errors)}")

        self.processed_data = self.template_data.copy()

        # Sanitize name
        if "name" in self.processed_data:
            self.processed_data["name"] = sanitize_template_name(
                self.processed_data["name"]
            )

        # Process tags
        if "tags" in self.processed_data:
            self.processed_data["tags"] = validate_template_tags(
                self.processed_data["tags"]
            )

        # Generate slug
        if "name" in self.processed_data:
            self.processed_data["slug"] = generate_template_slug(
                self.processed_data["name"]
            )

        # Calculate hash
        self.processed_data["content_hash"] = calculate_template_hash(
            self.processed_data
        )

        # Add processing metadata
        self.processed_data["processed_at"] = datetime.utcnow().isoformat()

        return self.processed_data

    def get_errors(self) -> List[str]:
        """Get validation errors.

        Returns:
            List[str]: List of validation errors
        """
        return self.errors.copy()
