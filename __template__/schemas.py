"""Template Blueprint Schemas.

This module contains Marshmallow schemas for request/response validation
and serialization for the template blueprint.

Schema Types:
- Request schemas: Validate incoming request data
- Response schemas: Serialize outgoing response data
- Nested schemas: Reusable schema components

See AI_INSTRUCTIONS.md §3 for schema implementation guidelines.
"""

from marshmallow import ValidationError, fields, validate, validates

from app.schemas.v2.base import BaseSchema, TimestampMixin
from app.schemas.v2.common import DataResponseSchema, PaginatedResponseSchema


class TemplateRequestSchema(BaseSchema):
    """Schema for template creation/update requests.

    This schema validates incoming request data for creating
    or updating template resources.
    """

    name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=100),
        metadata={"description": "Template name"},
    )

    description = fields.Str(
        required=False,
        validate=validate.Length(max=500),
        metadata={"description": "Template description"},
    )

    category = fields.Str(
        required=False,
        validate=validate.OneOf(["general", "specific", "custom"]),
        metadata={"description": "Template category"},
    )

    tags = fields.List(
        fields.Str(validate=validate.Length(min=1, max=50)),
        required=False,
        validate=validate.Length(max=10),
        metadata={"description": "Template tags"},
    )

    is_active = fields.Bool(
        required=False,
        default=True,
        metadata={"description": "Whether template is active"},
    )

    metadata = fields.Dict(
        required=False, metadata={"description": "Additional template metadata"}
    )

    @validates("name")
    def validate_name(self, value):
        """Validate template name.

        Args:
            value: Template name to validate

        Raises:
            ValidationError: If name is invalid
        """
        if not value.strip():
            raise ValidationError("Template name cannot be empty")

        # Check for reserved names
        reserved_names = ["admin", "api", "system", "default"]
        if value.lower() in reserved_names:
            raise ValidationError(f'Template name "{value}" is reserved')

    @validates("tags")
    def validate_tags(self, value):
        """Validate template tags.

        Args:
            value: List of tags to validate

        Raises:
            ValidationError: If tags are invalid
        """
        if value:
            # Check for duplicate tags
            if len(value) != len(set(value)):
                raise ValidationError("Duplicate tags are not allowed")

            # Check for invalid characters
            for tag in value:
                if not tag.replace("-", "").replace("_", "").isalnum():
                    raise ValidationError(
                        f'Tag "{tag}" contains invalid characters. '
                        "Only alphanumeric characters, hyphens, and underscores are allowed."
                    )


class TemplateSchema(BaseSchema, TimestampMixin):
    """Schema for template resource representation.

    This schema defines the structure of template resources
    in API responses.
    """

    id = fields.Int(required=True, metadata={"description": "Template ID"})

    name = fields.Str(required=True, metadata={"description": "Template name"})

    description = fields.Str(
        required=False,
        allow_none=True,
        metadata={"description": "Template description"},
    )

    category = fields.Str(
        required=False, allow_none=True, metadata={"description": "Template category"}
    )

    tags = fields.List(
        fields.Str(), required=False, metadata={"description": "Template tags"}
    )

    is_active = fields.Bool(
        required=True, metadata={"description": "Whether template is active"}
    )

    usage_count = fields.Int(
        required=False,
        metadata={"description": "Number of times template has been used"},
    )

    metadata = fields.Dict(
        required=False,
        allow_none=True,
        metadata={"description": "Additional template metadata"},
    )

    # Computed fields
    url = fields.Method("get_url", metadata={"description": "Template URL"})

    def get_url(self, obj):
        """Generate URL for the template.

        Args:
            obj: Template object

        Returns:
            str: Template URL
        """
        from flask import url_for

        return url_for(
            "template.get_template", template_id=obj.get("id"), _external=True
        )


class TemplateResponseSchema(DataResponseSchema):
    """Schema for single template responses.

    This schema wraps a single template resource in the
    standard API response format.
    """

    data = fields.Nested(
        TemplateSchema, required=True, metadata={"description": "Template data"}
    )


class TemplateListResponseSchema(PaginatedResponseSchema):
    """Schema for template list responses.

    This schema wraps a list of template resources with
    pagination information in the standard API response format.
    """

    data = fields.List(
        fields.Nested(TemplateSchema),
        required=True,
        metadata={"description": "List of templates"},
    )


class TemplateSearchSchema(BaseSchema):
    """Schema for template search requests.

    This schema validates search parameters for finding templates.
    """

    query = fields.Str(
        required=False,
        validate=validate.Length(min=1, max=100),
        metadata={"description": "Search query"},
    )

    category = fields.Str(
        required=False,
        validate=validate.OneOf(["general", "specific", "custom"]),
        metadata={"description": "Filter by category"},
    )

    tags = fields.List(
        fields.Str(), required=False, metadata={"description": "Filter by tags"}
    )

    is_active = fields.Bool(
        required=False, metadata={"description": "Filter by active status"}
    )

    sort_by = fields.Str(
        required=False,
        validate=validate.OneOf(["name", "created_at", "updated_at", "usage_count"]),
        default="created_at",
        metadata={"description": "Sort field"},
    )

    sort_order = fields.Str(
        required=False,
        validate=validate.OneOf(["asc", "desc"]),
        default="desc",
        metadata={"description": "Sort order"},
    )

    page = fields.Int(
        required=False,
        validate=validate.Range(min=1),
        default=1,
        metadata={"description": "Page number"},
    )

    per_page = fields.Int(
        required=False,
        validate=validate.Range(min=1, max=100),
        default=10,
        metadata={"description": "Items per page"},
    )


class TemplateBulkActionSchema(BaseSchema):
    """Schema for bulk actions on templates.

    This schema validates requests for performing bulk operations
    on multiple templates.
    """

    action = fields.Str(
        required=True,
        validate=validate.OneOf(["activate", "deactivate", "delete"]),
        metadata={"description": "Bulk action to perform"},
    )

    template_ids = fields.List(
        fields.Int(validate=validate.Range(min=1)),
        required=True,
        validate=validate.Length(min=1, max=100),
        metadata={"description": "List of template IDs"},
    )

    @validates("template_ids")
    def validate_template_ids(self, value):
        """Validate template IDs.

        Args:
            value: List of template IDs to validate

        Raises:
            ValidationError: If IDs are invalid
        """
        if len(value) != len(set(value)):
            raise ValidationError("Duplicate template IDs are not allowed")


class TemplateBulkActionResponseSchema(DataResponseSchema):
    """Schema for bulk action responses.

    This schema defines the response format for bulk operations.
    """

    data = fields.Dict(required=True, metadata={"description": "Bulk action results"})

    # The data dict should contain:
    # - action: str - The action performed
    # - total: int - Total number of items processed
    # - successful: int - Number of successful operations
    # - failed: int - Number of failed operations
    # - errors: list - List of error details for failed operations


class TemplateStatsSchema(BaseSchema):
    """Schema for template statistics.

    This schema defines the structure for template usage statistics.
    """

    total_templates = fields.Int(
        required=True, metadata={"description": "Total number of templates"}
    )

    active_templates = fields.Int(
        required=True, metadata={"description": "Number of active templates"}
    )

    inactive_templates = fields.Int(
        required=True, metadata={"description": "Number of inactive templates"}
    )

    categories = fields.Dict(
        required=True, metadata={"description": "Template count by category"}
    )

    popular_tags = fields.List(
        fields.Dict(),
        required=True,
        metadata={"description": "Most popular tags with usage counts"},
    )

    usage_stats = fields.Dict(
        required=True, metadata={"description": "Template usage statistics"}
    )


class TemplateStatsResponseSchema(DataResponseSchema):
    """Schema for template statistics responses.

    This schema wraps template statistics in the standard API response format.
    """

    data = fields.Nested(
        TemplateStatsSchema,
        required=True,
        metadata={"description": "Template statistics"},
    )
