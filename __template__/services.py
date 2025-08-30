"""Template Blueprint Services.

This module contains business logic services for the template blueprint.
Services handle complex operations, data processing, and business rules.

Service Types:
- CRUD services: Basic create, read, update, delete operations
- Business services: Complex business logic and workflows
- Integration services: External API and system integrations
- Utility services: Helper functions and data processing

See AI_INSTRUCTIONS.md §5 for service implementation guidelines.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, asc, desc, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.extensions import db
from app.utils import generate_uuid, sanitize_string, validate_email

from .models import Template
from .schemas import TemplateRequestSchema, TemplateSearchSchema


class TemplateService:
    """Service class for template operations.

    This service handles all business logic related to templates,
    including CRUD operations, search, validation, and business rules.
    """

    def __init__(self, session: Optional[Session] = None):
        """Initialize template service.

        Args:
            session: Database session (optional, uses default if not provided)
        """
        self.session = session or db.session

    def create_template(self, data: Dict[str, Any]) -> Template:
        """Create a new template.

        Args:
            data: Template data dictionary

        Returns:
            Template: Created template instance

        Raises:
            ValueError: If data is invalid
            IntegrityError: If template name already exists
        """
        # Validate input data
        schema = TemplateRequestSchema()
        validated_data = schema.load(data)

        # Check if template name already exists
        existing = self.get_template_by_name(validated_data["name"])
        if existing:
            raise ValueError(
                f"Template with name '{validated_data['name']}' already exists"
            )

        # Create template instance
        template = Template(**validated_data)

        try:
            self.session.add(template)
            self.session.commit()
            return template
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Failed to create template: {str(e)}")

    def get_template(self, template_id: int) -> Optional[Template]:
        """Get template by ID.

        Args:
            template_id: Template ID

        Returns:
            Optional[Template]: Template if found, None otherwise
        """
        return self.session.query(Template).filter_by(id=template_id).first()

    def get_template_by_uuid(self, uuid: str) -> Optional[Template]:
        """Get template by UUID.

        Args:
            uuid: Template UUID

        Returns:
            Optional[Template]: Template if found, None otherwise
        """
        return self.session.query(Template).filter_by(uuid=uuid).first()

    def get_template_by_name(self, name: str) -> Optional[Template]:
        """Get template by name.

        Args:
            name: Template name

        Returns:
            Optional[Template]: Template if found, None otherwise
        """
        return self.session.query(Template).filter_by(name=name).first()

    def update_template(
        self, template_id: int, data: Dict[str, Any]
    ) -> Optional[Template]:
        """Update an existing template.

        Args:
            template_id: Template ID
            data: Updated template data

        Returns:
            Optional[Template]: Updated template if found, None otherwise

        Raises:
            ValueError: If data is invalid
        """
        template = self.get_template(template_id)
        if not template:
            return None

        # Validate input data
        schema = TemplateRequestSchema(partial=True)
        validated_data = schema.load(data)

        # Check if name is being changed and already exists
        if "name" in validated_data and validated_data["name"] != template.name:
            existing = self.get_template_by_name(validated_data["name"])
            if existing:
                raise ValueError(
                    f"Template with name '{validated_data['name']}' already exists"
                )

        # Update template fields
        for key, value in validated_data.items():
            setattr(template, key, value)

        try:
            self.session.commit()
            return template
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Failed to update template: {str(e)}")

    def delete_template(self, template_id: int) -> bool:
        """Delete a template.

        Args:
            template_id: Template ID

        Returns:
            bool: True if deleted, False if not found
        """
        template = self.get_template(template_id)
        if not template:
            return False

        try:
            self.session.delete(template)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Failed to delete template: {str(e)}")

    def list_templates(
        self,
        page: int = 1,
        per_page: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Template], int]:
        """List templates with pagination and filtering.

        Args:
            page: Page number (1-based)
            per_page: Items per page
            filters: Optional filters dictionary

        Returns:
            Tuple[List[Template], int]: List of templates and total count
        """
        query = self.session.query(Template)

        # Apply filters
        if filters:
            if filters.get("is_active") is not None:
                query = query.filter_by(is_active=filters["is_active"])

            if filters.get("category"):
                query = query.filter_by(category=filters["category"])

            if filters.get("is_public") is not None:
                query = query.filter_by(is_public=filters["is_public"])

            if filters.get("tags"):
                for tag in filters["tags"]:
                    query = query.filter(Template.tags.contains([tag]))

            if filters.get("search"):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        Template.name.ilike(search_term),
                        Template.description.ilike(search_term),
                    )
                )

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * per_page
        templates = query.offset(offset).limit(per_page).all()

        return templates, total

    def search_templates(
        self, search_params: Dict[str, Any]
    ) -> Tuple[List[Template], int]:
        """Search templates with advanced parameters.

        Args:
            search_params: Search parameters dictionary

        Returns:
            Tuple[List[Template], int]: List of matching templates and total count
        """
        # Validate search parameters
        schema = TemplateSearchSchema()
        validated_params = schema.load(search_params)

        query = self.session.query(Template)

        # Apply search filters
        if validated_params.get("query"):
            search_term = f"%{validated_params['query']}%"
            query = query.filter(
                or_(
                    Template.name.ilike(search_term),
                    Template.description.ilike(search_term),
                )
            )

        if validated_params.get("category"):
            query = query.filter_by(category=validated_params["category"])

        if validated_params.get("tags"):
            for tag in validated_params["tags"]:
                query = query.filter(Template.tags.contains([tag]))

        if validated_params.get("is_active") is not None:
            query = query.filter_by(is_active=validated_params["is_active"])

        # Apply sorting
        sort_field = validated_params.get("sort_by", "created_at")
        sort_order = validated_params.get("sort_order", "desc")

        if hasattr(Template, sort_field):
            order_func = desc if sort_order == "desc" else asc
            query = query.order_by(order_func(getattr(Template, sort_field)))

        # Get total count
        total = query.count()

        # Apply pagination
        page = validated_params.get("page", 1)
        per_page = validated_params.get("per_page", 10)
        offset = (page - 1) * per_page

        templates = query.offset(offset).limit(per_page).all()

        return templates, total

    def activate_template(self, template_id: int) -> Optional[Template]:
        """Activate a template.

        Args:
            template_id: Template ID

        Returns:
            Optional[Template]: Updated template if found, None otherwise
        """
        return self.update_template(template_id, {"is_active": True})

    def deactivate_template(self, template_id: int) -> Optional[Template]:
        """Deactivate a template.

        Args:
            template_id: Template ID

        Returns:
            Optional[Template]: Updated template if found, None otherwise
        """
        return self.update_template(template_id, {"is_active": False})

    def increment_usage(self, template_id: int) -> Optional[Template]:
        """Increment template usage count.

        Args:
            template_id: Template ID

        Returns:
            Optional[Template]: Updated template if found, None otherwise
        """
        template = self.get_template(template_id)
        if not template:
            return None

        template.increment_usage()

        try:
            self.session.commit()
            return template
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Failed to increment usage: {str(e)}")

    def bulk_action(self, action: str, template_ids: List[int]) -> Dict[str, Any]:
        """Perform bulk action on multiple templates.

        Args:
            action: Action to perform ('activate', 'deactivate', 'delete')
            template_ids: List of template IDs

        Returns:
            Dict[str, Any]: Results of bulk operation
        """
        results = {
            "action": action,
            "total": len(template_ids),
            "successful": 0,
            "failed": 0,
            "errors": [],
        }

        for template_id in template_ids:
            try:
                if action == "activate":
                    result = self.activate_template(template_id)
                elif action == "deactivate":
                    result = self.deactivate_template(template_id)
                elif action == "delete":
                    result = self.delete_template(template_id)
                else:
                    raise ValueError(f"Unknown action: {action}")

                if result or action == "delete":
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(
                        {"template_id": template_id, "error": "Template not found"}
                    )

            except Exception as e:
                results["failed"] += 1
                results["errors"].append({"template_id": template_id, "error": str(e)})

        return results

    def get_template_stats(self) -> Dict[str, Any]:
        """Get template statistics.

        Returns:
            Dict[str, Any]: Template statistics
        """
        total_templates = self.session.query(Template).count()
        active_templates = (
            self.session.query(Template).filter_by(is_active=True).count()
        )
        inactive_templates = total_templates - active_templates

        # Category statistics
        category_stats = {}
        categories = self.session.query(Template.category).distinct().all()
        for (category,) in categories:
            if category:
                count = (
                    self.session.query(Template).filter_by(category=category).count()
                )
                category_stats[category] = count

        # Popular tags (this is a simplified version)
        # In a real implementation, you might want to use a more efficient query
        all_templates = self.session.query(Template).all()
        tag_counts = {}
        for template in all_templates:
            if template.tags:
                for tag in template.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

        popular_tags = [
            {"tag": tag, "count": count}
            for tag, count in sorted(
                tag_counts.items(), key=lambda x: x[1], reverse=True
            )[:10]
        ]

        # Usage statistics
        total_usage = sum(template.usage_count for template in all_templates)
        avg_usage = total_usage / total_templates if total_templates > 0 else 0

        # Most used templates
        most_used = (
            self.session.query(Template)
            .order_by(desc(Template.usage_count))
            .limit(5)
            .all()
        )

        return {
            "total_templates": total_templates,
            "active_templates": active_templates,
            "inactive_templates": inactive_templates,
            "categories": category_stats,
            "popular_tags": popular_tags,
            "usage_stats": {
                "total_usage": total_usage,
                "average_usage": round(avg_usage, 2),
                "most_used": [
                    {"id": t.id, "name": t.name, "usage_count": t.usage_count}
                    for t in most_used
                ],
            },
        }

    def duplicate_template(self, template_id: int, new_name: str) -> Optional[Template]:
        """Duplicate an existing template.

        Args:
            template_id: Template ID to duplicate
            new_name: Name for the new template

        Returns:
            Optional[Template]: New template if successful, None if original not found

        Raises:
            ValueError: If new name already exists or is invalid
        """
        original = self.get_template(template_id)
        if not original:
            return None

        # Check if new name already exists
        if self.get_template_by_name(new_name):
            raise ValueError(f"Template with name '{new_name}' already exists")

        # Create duplicate data
        duplicate_data = {
            "name": new_name,
            "description": f"Copy of {original.description}"
            if original.description
            else None,
            "category": original.category,
            "is_active": False,  # Start as inactive
            "is_public": False,  # Start as private
            "tags": original.tags.copy() if original.tags else [],
            "metadata": original.metadata.copy() if original.metadata else {},
            "configuration": original.configuration.copy()
            if original.configuration
            else {},
        }

        return self.create_template(duplicate_data)

    def export_template(self, template_id: int) -> Optional[Dict[str, Any]]:
        """Export template data for backup or transfer.

        Args:
            template_id: Template ID to export

        Returns:
            Optional[Dict[str, Any]]: Template export data if found, None otherwise
        """
        template = self.get_template(template_id)
        if not template:
            return None

        export_data = template.to_dict(include_relationships=True)

        # Add export metadata
        export_data["export_info"] = {
            "exported_at": datetime.utcnow().isoformat(),
            "version": "1.0",
            "format": "template_export",
        }

        return export_data

    def import_template(self, import_data: Dict[str, Any]) -> Template:
        """Import template from export data.

        Args:
            import_data: Template import data

        Returns:
            Template: Imported template

        Raises:
            ValueError: If import data is invalid
        """
        # Validate import data structure
        if "export_info" not in import_data:
            raise ValueError("Invalid import data: missing export_info")

        # Extract template data (exclude system fields)
        template_data = {
            key: value
            for key, value in import_data.items()
            if key
            not in [
                "id",
                "uuid",
                "created_at",
                "updated_at",
                "export_info",
                "usage_count",
                "last_used_at",
            ]
        }

        # Ensure unique name
        original_name = template_data.get("name", "Imported Template")
        name = original_name
        counter = 1

        while self.get_template_by_name(name):
            name = f"{original_name} ({counter})"
            counter += 1

        template_data["name"] = name

        return self.create_template(template_data)


# Example of a specialized service class
class TemplateAnalyticsService:
    """Service for template analytics and reporting.

    This service provides advanced analytics and reporting
    capabilities for templates.
    """

    def __init__(self, session: Optional[Session] = None):
        """Initialize analytics service.

        Args:
            session: Database session (optional)
        """
        self.session = session or db.session

    def get_usage_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get template usage trends over time.

        Args:
            days: Number of days to analyze

        Returns:
            Dict[str, Any]: Usage trend data
        """
        # This is a simplified implementation
        # In a real system, you'd want to track usage events in a separate table

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get templates used in the period
        templates = (
            self.session.query(Template)
            .filter(
                and_(
                    Template.last_used_at >= start_date,
                    Template.last_used_at <= end_date,
                )
            )
            .all()
        )

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days,
            },
            "templates_used": len(templates),
            "total_usage": sum(t.usage_count for t in templates),
            "most_active": [
                {
                    "id": t.id,
                    "name": t.name,
                    "usage_count": t.usage_count,
                    "last_used_at": t.last_used_at.isoformat()
                    if t.last_used_at
                    else None,
                }
                for t in sorted(templates, key=lambda x: x.usage_count, reverse=True)[
                    :5
                ]
            ],
        }

    def get_category_analysis(self) -> Dict[str, Any]:
        """Analyze template distribution by category.

        Returns:
            Dict[str, Any]: Category analysis data
        """
        categories = self.session.query(Template.category).distinct().all()
        analysis = {}

        for (category,) in categories:
            if category:
                templates = (
                    self.session.query(Template).filter_by(category=category).all()
                )
                analysis[category] = {
                    "count": len(templates),
                    "active_count": len([t for t in templates if t.is_active]),
                    "total_usage": sum(t.usage_count for t in templates),
                    "avg_usage": sum(t.usage_count for t in templates) / len(templates)
                    if templates
                    else 0,
                }

        return analysis
