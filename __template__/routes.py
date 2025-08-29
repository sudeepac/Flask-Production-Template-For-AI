"""Template Blueprint Routes.

This module contains route definitions for the template blueprint.
All routes should follow RESTful conventions and include proper
documentation, validation, and error handling.

Route Patterns:
- GET /: List resources
- GET /<id>: Get specific resource
- POST /: Create new resource
- PUT /<id>: Update specific resource
- DELETE /<id>: Delete specific resource

See AI_INSTRUCTIONS.md §4 for route implementation guidelines.
"""

from flask import request, jsonify, current_app
from marshmallow import ValidationError
from app.extensions import get_logger
from app.schemas.v2.common import ErrorSchema, SuccessSchema
from . import blueprint
from .schemas import (
    TemplateRequestSchema,
    TemplateResponseSchema,
    TemplateListResponseSchema
)

logger = get_logger('app.blueprints.template')

# Schema instances
template_request_schema = TemplateRequestSchema()
template_response_schema = TemplateResponseSchema()
template_list_response_schema = TemplateListResponseSchema()
error_schema = ErrorSchema()
success_schema = SuccessSchema()


@blueprint.route('/', methods=['GET'])
def list_templates():
    """List all template resources.
    
    Returns:
        JSON response with list of template resources
        
    Example:
        GET /api/v2/template/
        
        Response:
        {
            "status": "success",
            "data": [
                {
                    "id": 1,
                    "name": "Template 1",
                    "description": "Sample template",
                    "created_at": "2024-01-01T00:00:00Z"
                }
            ],
            "pagination": {
                "page": 1,
                "per_page": 10,
                "total": 1,
                "pages": 1
            }
        }
    """
    try:
        # TODO: Implement actual data retrieval logic
        # Example: templates = TemplateService.get_all()
        
        # Mock data for template
        templates = [
            {
                'id': 1,
                'name': 'Sample Template',
                'description': 'This is a sample template',
                'created_at': '2024-01-01T00:00:00Z'
            }
        ]
        
        # Serialize response
        result = template_list_response_schema.dump({
            'data': templates,
            'pagination': {
                'page': 1,
                'per_page': 10,
                'total': len(templates),
                'pages': 1
            }
        })
        
        logger.info(f"Retrieved {len(templates)} template resources")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Failed to list templates: {str(e)}")
        error_response = error_schema.dump({
            'error': 'internal_server_error',
            'message': 'Failed to retrieve templates'
        })
        return jsonify(error_response), 500


@blueprint.route('/<int:template_id>', methods=['GET'])
def get_template(template_id):
    """Get a specific template resource.
    
    Args:
        template_id: ID of the template to retrieve
        
    Returns:
        JSON response with template resource
        
    Example:
        GET /api/v2/template/1
        
        Response:
        {
            "status": "success",
            "data": {
                "id": 1,
                "name": "Template 1",
                "description": "Sample template",
                "created_at": "2024-01-01T00:00:00Z"
            }
        }
    """
    try:
        # TODO: Implement actual data retrieval logic
        # Example: template = TemplateService.get_by_id(template_id)
        
        # Mock data for template
        if template_id == 1:
            template = {
                'id': 1,
                'name': 'Sample Template',
                'description': 'This is a sample template',
                'created_at': '2024-01-01T00:00:00Z'
            }
        else:
            error_response = error_schema.dump({
                'error': 'not_found',
                'message': f'Template with ID {template_id} not found'
            })
            return jsonify(error_response), 404
        
        # Serialize response
        result = template_response_schema.dump({'data': template})
        
        logger.info(f"Retrieved template {template_id}")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Failed to get template {template_id}: {str(e)}")
        error_response = error_schema.dump({
            'error': 'internal_server_error',
            'message': 'Failed to retrieve template'
        })
        return jsonify(error_response), 500


@blueprint.route('/', methods=['POST'])
def create_template():
    """Create a new template resource.
    
    Returns:
        JSON response with created template resource
        
    Example:
        POST /api/v2/template/
        
        Request:
        {
            "name": "New Template",
            "description": "A new template"
        }
        
        Response:
        {
            "status": "success",
            "data": {
                "id": 2,
                "name": "New Template",
                "description": "A new template",
                "created_at": "2024-01-01T00:00:00Z"
            },
            "message": "Template created successfully"
        }
    """
    try:
        # Validate request data
        request_data = template_request_schema.load(request.json)
        
        # TODO: Implement actual creation logic
        # Example: template = TemplateService.create(request_data)
        
        # Mock creation for template
        template = {
            'id': 2,
            'name': request_data['name'],
            'description': request_data.get('description', ''),
            'created_at': '2024-01-01T00:00:00Z'
        }
        
        # Serialize response
        result = template_response_schema.dump({
            'data': template,
            'message': 'Template created successfully'
        })
        
        logger.info(f"Created template: {template['name']}")
        return jsonify(result), 201
        
    except ValidationError as e:
        logger.warning(f"Validation error creating template: {e.messages}")
        error_response = error_schema.dump({
            'error': 'validation_error',
            'message': 'Invalid request data',
            'details': e.messages
        })
        return jsonify(error_response), 400
        
    except Exception as e:
        logger.error(f"Failed to create template: {str(e)}")
        error_response = error_schema.dump({
            'error': 'internal_server_error',
            'message': 'Failed to create template'
        })
        return jsonify(error_response), 500


@blueprint.route('/<int:template_id>', methods=['PUT'])
def update_template(template_id):
    """Update a specific template resource.
    
    Args:
        template_id: ID of the template to update
        
    Returns:
        JSON response with updated template resource
        
    Example:
        PUT /api/v2/template/1
        
        Request:
        {
            "name": "Updated Template",
            "description": "Updated description"
        }
        
        Response:
        {
            "status": "success",
            "data": {
                "id": 1,
                "name": "Updated Template",
                "description": "Updated description",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T01:00:00Z"
            },
            "message": "Template updated successfully"
        }
    """
    try:
        # Validate request data
        request_data = template_request_schema.load(request.json)
        
        # TODO: Implement actual update logic
        # Example: template = TemplateService.update(template_id, request_data)
        
        # Mock update for template
        if template_id == 1:
            template = {
                'id': template_id,
                'name': request_data['name'],
                'description': request_data.get('description', ''),
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-01T01:00:00Z'
            }
        else:
            error_response = error_schema.dump({
                'error': 'not_found',
                'message': f'Template with ID {template_id} not found'
            })
            return jsonify(error_response), 404
        
        # Serialize response
        result = template_response_schema.dump({
            'data': template,
            'message': 'Template updated successfully'
        })
        
        logger.info(f"Updated template {template_id}")
        return jsonify(result), 200
        
    except ValidationError as e:
        logger.warning(f"Validation error updating template {template_id}: {e.messages}")
        error_response = error_schema.dump({
            'error': 'validation_error',
            'message': 'Invalid request data',
            'details': e.messages
        })
        return jsonify(error_response), 400
        
    except Exception as e:
        logger.error(f"Failed to update template {template_id}: {str(e)}")
        error_response = error_schema.dump({
            'error': 'internal_server_error',
            'message': 'Failed to update template'
        })
        return jsonify(error_response), 500


@blueprint.route('/<int:template_id>', methods=['DELETE'])
def delete_template(template_id):
    """Delete a specific template resource.
    
    Args:
        template_id: ID of the template to delete
        
    Returns:
        JSON response confirming deletion
        
    Example:
        DELETE /api/v2/template/1
        
        Response:
        {
            "status": "success",
            "message": "Template deleted successfully"
        }
    """
    try:
        # TODO: Implement actual deletion logic
        # Example: TemplateService.delete(template_id)
        
        # Mock deletion for template
        if template_id != 1:
            error_response = error_schema.dump({
                'error': 'not_found',
                'message': f'Template with ID {template_id} not found'
            })
            return jsonify(error_response), 404
        
        # Serialize response
        result = success_schema.dump({
            'message': 'Template deleted successfully'
        })
        
        logger.info(f"Deleted template {template_id}")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Failed to delete template {template_id}: {str(e)}")
        error_response = error_schema.dump({
            'error': 'internal_server_error',
            'message': 'Failed to delete template'
        })
        return jsonify(error_response), 500


@blueprint.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for the template blueprint.
    
    Returns:
        JSON response with health status
        
    Example:
        GET /api/v2/template/health
        
        Response:
        {
            "status": "success",
            "data": {
                "service": "template",
                "status": "healthy",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
    """
    try:
        from app.utils import get_timestamp
        
        health_data = {
            'service': 'template',
            'status': 'healthy',
            'timestamp': get_timestamp()
        }
        
        result = success_schema.dump({'data': health_data})
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        error_response = error_schema.dump({
            'error': 'service_unavailable',
            'message': 'Service health check failed'
        })
        return jsonify(error_response), 503