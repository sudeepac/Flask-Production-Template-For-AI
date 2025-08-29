"""Health Check Routes.

This module contains health check endpoints for monitoring
application status and system health.
"""

import time
import psutil
from datetime import datetime
from flask import jsonify, current_app
from sqlalchemy import text
from app.extensions import db
from . import blueprint


@blueprint.route('/', methods=['GET'])
@blueprint.route('/basic', methods=['GET'])
def health_check():
    """Basic health check endpoint.
    
    Returns:
        JSON response indicating application is running
        
    Example:
        GET /health
        
        Response:
        {
            "status": "healthy",
            "timestamp": "2024-01-01T12:00:00Z",
            "version": "1.0.0"
        }
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'version': getattr(current_app, 'version', '1.0.0')
    }), 200


@blueprint.route('/detailed', methods=['GET'])
def detailed_health_check():
    """Detailed health check with system information.
    
    Returns:
        JSON response with detailed system status
        
    Example:
        GET /health/detailed
        
        Response:
        {
            "status": "healthy",
            "timestamp": "2024-01-01T12:00:00Z",
            "version": "1.0.0",
            "database": {
                "status": "connected",
                "response_time_ms": 5.2
            },
            "system": {
                "cpu_percent": 25.5,
                "memory_percent": 45.2,
                "disk_percent": 60.1
            }
        }
    """
    health_data = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'version': getattr(current_app, 'version', '1.0.0'),
        'database': _check_database(),
        'system': _get_system_info()
    }
    
    # Determine overall status
    if health_data['database']['status'] != 'connected':
        health_data['status'] = 'unhealthy'
        return jsonify(health_data), 503
    
    return jsonify(health_data), 200


@blueprint.route('/ready', methods=['GET'])
def readiness_probe():
    """Kubernetes readiness probe.
    
    Checks if the application is ready to receive traffic.
    
    Returns:
        JSON response indicating readiness status
    """
    try:
        # Check database connectivity
        db_status = _check_database()
        
        if db_status['status'] == 'connected':
            return jsonify({
                'status': 'ready',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 200
        else:
            return jsonify({
                'status': 'not_ready',
                'reason': 'database_unavailable',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 503
            
    except Exception as e:
        return jsonify({
            'status': 'not_ready',
            'reason': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503


@blueprint.route('/live', methods=['GET'])
def liveness_probe():
    """Kubernetes liveness probe.
    
    Checks if the application is alive and should not be restarted.
    
    Returns:
        JSON response indicating liveness status
    """
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200


def _check_database():
    """Check database connectivity and response time.
    
    Returns:
        dict: Database status information
    """
    try:
        start_time = time.time()
        
        # Simple database query to check connectivity
        with db.engine.connect() as connection:
            connection.execute(text('SELECT 1'))
        
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return {
            'status': 'connected',
            'response_time_ms': round(response_time, 2)
        }
        
    except Exception as e:
        return {
            'status': 'disconnected',
            'error': str(e)
        }


def _get_system_info():
    """Get system resource information.
    
    Returns:
        dict: System resource usage
    """
    try:
        return {
            'cpu_percent': round(psutil.cpu_percent(interval=1), 1),
            'memory_percent': round(psutil.virtual_memory().percent, 1),
            'disk_percent': round(psutil.disk_usage('/').percent, 1)
        }
    except Exception:
        return {
            'cpu_percent': 'unavailable',
            'memory_percent': 'unavailable',
            'disk_percent': 'unavailable'
        }