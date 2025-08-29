"""Data fixtures for testing.

This module contains fixtures that provide sample data,
mock objects, and test data for various test scenarios.
"""

import pytest
import json
import datetime
from unittest.mock import Mock, MagicMock
from werkzeug.datastructures import FileStorage
import io


@pytest.fixture(scope='function')
def sample_user_data():
    """Sample user data for testing."""
    return {
        'id': 1,
        'username': 'testuser',
        'email': 'test@example.com',
        'first_name': 'Test',
        'last_name': 'User',
        'is_active': True,
        'is_admin': False,
        'created_at': datetime.datetime.utcnow(),
        'updated_at': datetime.datetime.utcnow()
    }


@pytest.fixture(scope='function')
def sample_admin_data():
    """Sample admin user data for testing."""
    return {
        'id': 2,
        'username': 'admin',
        'email': 'admin@example.com',
        'first_name': 'Admin',
        'last_name': 'User',
        'is_active': True,
        'is_admin': True,
        'created_at': datetime.datetime.utcnow(),
        'updated_at': datetime.datetime.utcnow()
    }


@pytest.fixture(scope='function')
def sample_ml_data():
    """Sample ML data for testing."""
    return {
        'features': {
            'numerical': [1.0, 2.5, 3.7, 4.2, 5.1],
            'categorical': ['A', 'B', 'A', 'C', 'B'],
            'text': ['sample text 1', 'sample text 2', 'sample text 3']
        },
        'labels': [0, 1, 0, 1, 1],
        'metadata': {
            'dataset_name': 'test_dataset',
            'version': '1.0',
            'created_at': datetime.datetime.utcnow().isoformat()
        }
    }


@pytest.fixture(scope='function')
def sample_api_responses():
    """Sample API response data for testing."""
    return {
        'success_response': {
            'status': 'success',
            'data': {'id': 123, 'name': 'Test Item'},
            'message': 'Operation completed successfully'
        },
        'error_response': {
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Invalid input data',
                'details': ['Field "name" is required']
            }
        },
        'paginated_response': {
            'status': 'success',
            'data': [
                {'id': 1, 'name': 'Item 1'},
                {'id': 2, 'name': 'Item 2'},
                {'id': 3, 'name': 'Item 3'}
            ],
            'pagination': {
                'page': 1,
                'per_page': 10,
                'total': 25,
                'pages': 3
            }
        }
    }


@pytest.fixture(scope='function')
def mock_file_upload():
    """Mock file upload for testing."""
    def create_mock_file(filename='test.txt', content='test content', content_type='text/plain'):
        return FileStorage(
            stream=io.BytesIO(content.encode('utf-8')),
            filename=filename,
            content_type=content_type
        )
    
    return create_mock_file


@pytest.fixture(scope='function')
def mock_image_upload():
    """Mock image upload for testing."""
    def create_mock_image(filename='test.jpg', content_type='image/jpeg'):
        # Create minimal JPEG header
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb'
        
        return FileStorage(
            stream=io.BytesIO(jpeg_header + b'\x00' * 100),  # Minimal JPEG data
            filename=filename,
            content_type=content_type
        )
    
    return create_mock_image


@pytest.fixture(scope='function')
def mock_database_session():
    """Mock database session for testing."""
    session = Mock()
    
    # Mock common session methods
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    session.close = Mock()
    session.flush = Mock()
    session.query = Mock()
    session.execute = Mock()
    session.scalar = Mock()
    
    # Mock query builder
    query_mock = Mock()
    query_mock.filter = Mock(return_value=query_mock)
    query_mock.filter_by = Mock(return_value=query_mock)
    query_mock.order_by = Mock(return_value=query_mock)
    query_mock.limit = Mock(return_value=query_mock)
    query_mock.offset = Mock(return_value=query_mock)
    query_mock.first = Mock(return_value=None)
    query_mock.all = Mock(return_value=[])
    query_mock.count = Mock(return_value=0)
    
    session.query.return_value = query_mock
    
    return session


@pytest.fixture(scope='function')
def mock_cache_service():
    """Mock cache service for testing."""
    cache_data = {}
    
    class MockCache:
        def get(self, key):
            return cache_data.get(key)
        
        def set(self, key, value, timeout=None):
            cache_data[key] = value
            return True
        
        def delete(self, key):
            return cache_data.pop(key, None) is not None
        
        def clear(self):
            cache_data.clear()
            return True
        
        def get_many(self, *keys):
            return [cache_data.get(key) for key in keys]
        
        def set_many(self, mapping, timeout=None):
            cache_data.update(mapping)
            return True
        
        def delete_many(self, *keys):
            deleted = 0
            for key in keys:
                if cache_data.pop(key, None) is not None:
                    deleted += 1
            return deleted
        
        def has(self, key):
            return key in cache_data
        
        @property
        def data(self):
            return cache_data.copy()
    
    return MockCache()


@pytest.fixture(scope='function')
def mock_ml_model():
    """Mock ML model for testing."""
    class MockMLModel:
        def __init__(self, model_name='test_model'):
            self.model_name = model_name
            self.is_trained = True
            self.version = '1.0.0'
            self.features = ['feature1', 'feature2', 'feature3']
        
        def predict(self, data):
            # Return mock predictions
            if isinstance(data, list):
                return [0.8, 0.6, 0.9][:len(data)]
            return 0.75
        
        def predict_proba(self, data):
            # Return mock probabilities
            if isinstance(data, list):
                return [[0.2, 0.8], [0.4, 0.6], [0.1, 0.9]][:len(data)]
            return [0.25, 0.75]
        
        def fit(self, X, y):
            self.is_trained = True
            return self
        
        def score(self, X, y):
            return 0.85
        
        def get_feature_importance(self):
            return {
                'feature1': 0.4,
                'feature2': 0.35,
                'feature3': 0.25
            }
        
        def save(self, path):
            return True
        
        def load(self, path):
            return self
    
    return MockMLModel()


@pytest.fixture(scope='function')
def sample_json_data():
    """Sample JSON data for testing."""
    return {
        'simple_object': {
            'name': 'Test Object',
            'value': 42,
            'active': True
        },
        'nested_object': {
            'user': {
                'id': 1,
                'profile': {
                    'name': 'John Doe',
                    'settings': {
                        'theme': 'dark',
                        'notifications': True
                    }
                }
            }
        },
        'array_data': {
            'items': [
                {'id': 1, 'name': 'Item 1'},
                {'id': 2, 'name': 'Item 2'},
                {'id': 3, 'name': 'Item 3'}
            ],
            'metadata': {
                'total': 3,
                'type': 'test_items'
            }
        },
        'complex_data': {
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'coordinates': [40.7128, -74.0060],
            'tags': ['test', 'sample', 'data'],
            'config': {
                'enabled': True,
                'max_retries': 3,
                'timeout': 30.0
            }
        }
    }


@pytest.fixture(scope='function')
def mock_external_service():
    """Mock external service for testing."""
    class MockExternalService:
        def __init__(self):
            self.call_count = 0
            self.last_request = None
            self.responses = {
                'default': {'status': 'success', 'data': 'mock response'}
            }
        
        def call_api(self, endpoint, method='GET', data=None, headers=None):
            self.call_count += 1
            self.last_request = {
                'endpoint': endpoint,
                'method': method,
                'data': data,
                'headers': headers
            }
            
            # Return appropriate mock response
            if endpoint in self.responses:
                return self.responses[endpoint]
            return self.responses['default']
        
        def set_response(self, endpoint, response):
            self.responses[endpoint] = response
        
        def reset(self):
            self.call_count = 0
            self.last_request = None
            self.responses = {
                'default': {'status': 'success', 'data': 'mock response'}
            }
    
    return MockExternalService()


@pytest.fixture(scope='function')
def sample_form_data():
    """Sample form data for testing."""
    return {
        'login_form': {
            'username': 'testuser',
            'password': 'testpassword123',
            'remember_me': True
        },
        'registration_form': {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'confirm_password': 'newpassword123',
            'first_name': 'New',
            'last_name': 'User',
            'terms_accepted': True
        },
        'profile_form': {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com',
            'bio': 'This is an updated bio.',
            'website': 'https://example.com',
            'location': 'New York, NY'
        },
        'search_form': {
            'query': 'test search query',
            'category': 'all',
            'sort_by': 'relevance',
            'page': 1,
            'per_page': 10
        }
    }


@pytest.fixture(scope='function')
def mock_datetime():
    """Mock datetime for consistent testing."""
    class MockDateTime:
        def __init__(self):
            self.fixed_time = datetime.datetime(2024, 1, 15, 12, 0, 0)
        
        def utcnow(self):
            return self.fixed_time
        
        def now(self, tz=None):
            if tz:
                return self.fixed_time.replace(tzinfo=tz)
            return self.fixed_time
        
        def set_time(self, new_time):
            self.fixed_time = new_time
        
        def advance_time(self, **kwargs):
            self.fixed_time += datetime.timedelta(**kwargs)
    
    return MockDateTime()


@pytest.fixture(scope='function')
def sample_error_scenarios():
    """Sample error scenarios for testing."""
    return {
        'validation_errors': {
            'required_field_missing': {
                'field': 'email',
                'message': 'Email is required'
            },
            'invalid_format': {
                'field': 'email',
                'message': 'Invalid email format'
            },
            'value_too_long': {
                'field': 'username',
                'message': 'Username must be less than 50 characters'
            }
        },
        'authentication_errors': {
            'invalid_credentials': {
                'code': 'AUTH_001',
                'message': 'Invalid username or password'
            },
            'account_locked': {
                'code': 'AUTH_002',
                'message': 'Account is temporarily locked'
            },
            'token_expired': {
                'code': 'AUTH_003',
                'message': 'Authentication token has expired'
            }
        },
        'permission_errors': {
            'access_denied': {
                'code': 'PERM_001',
                'message': 'Access denied for this resource'
            },
            'insufficient_privileges': {
                'code': 'PERM_002',
                'message': 'Insufficient privileges to perform this action'
            }
        },
        'system_errors': {
            'database_error': {
                'code': 'SYS_001',
                'message': 'Database connection failed'
            },
            'external_service_error': {
                'code': 'SYS_002',
                'message': 'External service unavailable'
            },
            'rate_limit_exceeded': {
                'code': 'SYS_003',
                'message': 'Rate limit exceeded, please try again later'
            }
        }
    }


@pytest.fixture(scope='function')
def performance_test_data():
    """Performance test data for load testing."""
    return {
        'small_dataset': {
            'size': 100,
            'data': [{'id': i, 'value': f'item_{i}'} for i in range(100)]
        },
        'medium_dataset': {
            'size': 1000,
            'data': [{'id': i, 'value': f'item_{i}'} for i in range(1000)]
        },
        'large_dataset': {
            'size': 10000,
            'data': [{'id': i, 'value': f'item_{i}'} for i in range(10000)]
        },
        'concurrent_users': {
            'light_load': 10,
            'medium_load': 50,
            'heavy_load': 100
        },
        'request_patterns': {
            'burst': {'requests': 100, 'duration': 1},
            'sustained': {'requests': 1000, 'duration': 60},
            'gradual': {'requests': 500, 'duration': 30}
        }
    }