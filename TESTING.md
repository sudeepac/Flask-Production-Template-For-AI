# Testing Guide for Flask Production Template for AI

This guide provides comprehensive information about testing the Flask Production Template for AI application, including setup, running tests, and best practices.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Setup](#setup)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Writing Tests](#writing-tests)
- [Fixtures and Utilities](#fixtures-and-utilities)
- [Coverage and Reporting](#coverage-and-reporting)
- [CI/CD Integration](#cicd-integration)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The Flask Production Template for AI testing framework is built using pytest and provides comprehensive test coverage for:

- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **API Tests**: REST API endpoint testing
- **ML Tests**: Machine learning functionality testing
- **Performance Tests**: Load and performance testing

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Shared pytest configuration and fixtures
├── pytest.ini                 # Pytest configuration
├── unit/                       # Unit tests
│   ├── test_app.py            # Application factory tests
│   └── test_extensions.py     # Flask extensions tests
├── integration/                # Integration tests
│   └── test_app_integration.py # Full application integration tests
├── api/                        # API tests
│   └── test_examples_api.py   # API endpoint tests
├── ml/                         # Machine learning tests
│   └── test_ml_services.py    # ML services and model tests
├── performance/                # Performance tests
│   └── test_performance.py    # Load and performance tests
└── fixtures/                   # Test fixtures and utilities
    ├── app_fixtures.py        # Application-specific fixtures
    ├── data_fixtures.py       # Data and mock fixtures
    └── ml_fixtures.py         # ML-specific fixtures
```

## Setup

### Prerequisites

1. **Python 3.8+** installed
2. **Virtual environment** activated
3. **Application dependencies** installed

### Install Test Dependencies

```bash
# Using the test runner (recommended)
python run_tests.py --setup

# Or manually install
pip install pytest pytest-cov pytest-mock pytest-xdist pytest-benchmark pytest-html
pip install coverage factory-boy faker responses freezegun psutil
```

### Environment Setup

```bash
# Set environment variables for testing
export FLASK_ENV=testing
export DATABASE_URL=sqlite:///test.db
export SECRET_KEY=test-secret-key
```

## Running Tests

### Using the Test Runner (Recommended)

The `run_tests.py` script provides a convenient interface for running tests:

```bash
# Run all tests
python run_tests.py --all

# Run specific test categories
python run_tests.py --unit
python run_tests.py --integration
python run_tests.py --api
python run_tests.py --ml
python run_tests.py --performance

# Run with coverage
python run_tests.py --all --coverage

# Run in parallel
python run_tests.py --all --parallel

# Run with specific markers
python run_tests.py --all --markers "not slow"

# Generate comprehensive report
python run_tests.py --report
```

### Using Pytest Directly

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_app.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run with specific markers
pytest -m "unit and not slow"

# Run in parallel
pytest -n auto

# Verbose output
pytest -v
```

## Test Categories

### Unit Tests

Test individual components in isolation:

```bash
# Run unit tests
python run_tests.py --unit

# Or with pytest
pytest tests/unit/ -v
```

**Markers**: `unit`, `fast`

### Integration Tests

Test component interactions and full application flow:

```bash
# Run integration tests
python run_tests.py --integration

# Or with pytest
pytest tests/integration/ -v
```

**Markers**: `integration`, `database`, `cache`

### API Tests

Test REST API endpoints and responses:

```bash
# Run API tests
python run_tests.py --api

# Or with pytest
pytest tests/api/ -v
```

**Markers**: `api`, `auth`, `external`

### ML Tests

Test machine learning functionality:

```bash
# Run ML tests
python run_tests.py --ml

# Or with pytest
pytest tests/ml/ -v
```

**Markers**: `ml`, `slow`

### Performance Tests

Test application performance and load handling:

```bash
# Run performance tests
python run_tests.py --performance

# Run with benchmarking
python run_tests.py --performance --benchmark

# Or with pytest
pytest tests/performance/ -v -m performance
```

**Markers**: `performance`, `slow`, `benchmark`

### Smoke Tests

Quick tests to verify basic functionality:

```bash
# Run smoke tests
python run_tests.py --smoke

# Or with pytest
pytest -m smoke
```

**Markers**: `smoke`

## Writing Tests

### Basic Test Structure

```python
import pytest
from app import create_app

class TestExample:
    """Test class for example functionality."""
    
    def test_basic_functionality(self, app, client):
        """Test basic functionality."""
        response = client.get('/')
        assert response.status_code == 200
    
    @pytest.mark.slow
    def test_slow_operation(self, app):
        """Test that takes longer to run."""
        # Slow test implementation
        pass
    
    @pytest.mark.parametrize("input_data,expected", [
        ("test1", "result1"),
        ("test2", "result2"),
    ])
    def test_parametrized(self, input_data, expected):
        """Parametrized test example."""
        result = some_function(input_data)
        assert result == expected
```

### Using Fixtures

```python
def test_with_fixtures(self, app, client, sample_user_data, mock_database_session):
    """Test using multiple fixtures."""
    # Use fixtures in your test
    user_data = sample_user_data
    response = client.post('/api/users', json=user_data)
    assert response.status_code == 201
```

### Mocking External Services

```python
def test_external_api(self, client, mock_external_api):
    """Test with mocked external API."""
    response = client.get('/api/external-data')
    assert response.status_code == 200
    assert mock_external_api['get'].called
```

## Fixtures and Utilities

### Application Fixtures

- `app`: Flask application instance
- `client`: Test client for HTTP requests
- `db`: Database session
- `auth_headers`: Authentication headers
- `authenticated_client`: Pre-authenticated test client

### Data Fixtures

- `sample_user_data`: Sample user data
- `sample_ml_data`: Sample ML datasets
- `sample_api_responses`: Mock API responses
- `mock_file_upload`: File upload simulation
- `performance_test_data`: Performance testing datasets

### ML Fixtures

- `sample_training_data`: ML training datasets
- `mock_sklearn_model`: Mock scikit-learn model
- `mock_model_registry`: Mock model registry
- `mock_experiment_tracker`: Mock experiment tracking

### Utility Fixtures

- `temp_file`: Temporary file creation
- `temp_directory`: Temporary directory creation
- `mock_datetime`: Fixed datetime for testing
- `performance_monitor`: Performance monitoring
- `capture_logs`: Enhanced log capturing

## Coverage and Reporting

### Generate Coverage Report

```bash
# HTML coverage report
python run_tests.py --all --coverage

# Or with pytest
pytest --cov=app --cov-report=html --cov-report=term-missing
```

### Generate Test Reports

```bash
# Comprehensive test report
python run_tests.py --report

# HTML test report
pytest --html=reports/test_report.html --self-contained-html

# JSON test report
pytest --json-report --json-report-file=reports/test_report.json
```

### View Reports

- **Coverage Report**: `reports/coverage/index.html`
- **Test Report**: `reports/test_report.html`
- **JSON Report**: `reports/test_report.json`

## CI/CD Integration

### GitHub Actions

The project includes GitHub Actions workflows:

- **`.github/workflows/ci.yml`**: Main CI pipeline
- **`.github/workflows/security.yml`**: Security scanning

### Running in CI

```yaml
# Example CI step
- name: Run Tests
  run: |
    python run_tests.py --all --coverage --parallel
    python run_tests.py --lint --security
```

### Docker Testing

```bash
# Run tests in Docker
docker-compose -f docker-compose.test.yml up --build

# Or using development environment
./docker-dev.ps1 test
```

## Best Practices

### Test Organization

1. **Group related tests** in classes
2. **Use descriptive test names** that explain what is being tested
3. **Follow the AAA pattern**: Arrange, Act, Assert
4. **Keep tests independent** and isolated
5. **Use appropriate markers** for test categorization

### Test Data

1. **Use fixtures** for reusable test data
2. **Create minimal test data** that covers the test case
3. **Use factories** for generating test data variations
4. **Mock external dependencies** to ensure test isolation

### Performance

1. **Mark slow tests** with `@pytest.mark.slow`
2. **Use parallel execution** for faster test runs
3. **Profile test performance** and optimize bottlenecks
4. **Separate performance tests** from regular test suite

### Maintenance

1. **Keep tests up to date** with code changes
2. **Remove obsolete tests** when features are removed
3. **Refactor test code** to reduce duplication
4. **Document complex test scenarios**

## Troubleshooting

### Common Issues

#### Database Connection Errors

```bash
# Ensure test database is properly configured
export DATABASE_URL=sqlite:///test.db

# Or use in-memory database
export DATABASE_URL=sqlite:///:memory:
```

#### Import Errors

```bash
# Ensure PYTHONPATH includes the application directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or install the application in development mode
pip install -e .
```

#### Fixture Not Found

```python
# Ensure fixtures are properly imported in conftest.py
from tests.fixtures.app_fixtures import *
from tests.fixtures.data_fixtures import *
from tests.fixtures.ml_fixtures import *
```

#### Slow Test Performance

```bash
# Run tests in parallel
pytest -n auto

# Skip slow tests during development
pytest -m "not slow"

# Use faster test database
export DATABASE_URL=sqlite:///:memory:
```

### Debug Mode

```bash
# Run tests with debugging
pytest --pdb

# Capture print statements
pytest -s

# Show local variables on failure
pytest --tb=long
```

### Clean Test Environment

```bash
# Clean test artifacts
python run_tests.py --clean

# Or manually
rm -rf .pytest_cache __pycache__ .coverage htmlcov reports
```

## Advanced Features

### Custom Markers

Define custom markers in `pytest.ini`:

```ini
markers =
    integration: marks tests as integration tests
    slow: marks tests as slow running
    external: marks tests that require external services
```

### Test Configuration

Customize test behavior in `conftest.py`:

```python
def pytest_configure(config):
    """Configure pytest settings."""
    config.addinivalue_line(
        "markers", "custom: mark test as custom category"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    for item in items:
        # Add markers based on test location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
```

### Performance Monitoring

```python
def test_with_performance_monitoring(self, performance_monitor):
    """Test with performance monitoring."""
    performance_monitor.start()
    
    # Your test code here
    result = expensive_operation()
    
    stats = performance_monitor.stop()
    assert stats['duration'] < 1.0  # Should complete in under 1 second
    assert result is not None
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Flask Testing Documentation](https://flask.palletsprojects.com/en/2.3.x/testing/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Factory Boy Documentation](https://factoryboy.readthedocs.io/)
- [Responses Documentation](https://github.com/getsentry/responses)

---

For questions or issues with testing, please refer to the project documentation or create an issue in the repository.