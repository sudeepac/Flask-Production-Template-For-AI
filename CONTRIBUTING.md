# Contributing to Flask Production Template for AI

Thank you for your interest in contributing to Flask Production Template for AI! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Code Style](#code-style)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Community](#community)

## 🤝 Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Positive behavior includes:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behavior includes:**
- The use of sexualized language or imagery
- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git 2.0 or higher
- Basic understanding of Flask and REST APIs
- Familiarity with machine learning concepts (for ML-related contributions)

### First-time Contributors

1. **Fork the Repository**
   ```bash
   # Click the "Fork" button on GitHub
   git clone https://github.com/YOUR_USERNAME/flask-production-template.git
cd flask-production-template
   ```

2. **Set Up Remote**
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/flask-production-template.git
   ```

3. **Run Quick Start**
   ```bash
   # Windows
   .\scripts\quickstart.ps1
   
   # Unix/Linux/macOS
   ./scripts/quickstart.sh
   ```

### 🤖 AI-Assisted Development

If you're using AI coding assistants (GitHub Copilot, Cursor, Claude, etc.), please ensure they read the project guidelines first:

1. **Point your AI assistant to [`AI_INSTRUCTIONS.md`](./AI_INSTRUCTIONS.md)** - This contains essential project architecture, coding standards, and templates
2. **Review AI-generated code** - Always validate that generated code follows our patterns and standards
3. **Test thoroughly** - AI-generated code should pass all existing tests and maintain code quality

**Example prompt for AI assistants:**
```
Before writing any code for this Flask project, please read and follow the guidelines in AI_INSTRUCTIONS.md. 
This file contains the project architecture, coding standards, directory structure rules, and code generation templates.
```

## 🛠️ Development Setup

### Environment Setup

1. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

3. **Install Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

4. **Set Up Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env with your local configuration
   ```

5. **Initialize Database**
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

### Development Tools

- **Linting**: `flake8`, `pylint`
- **Formatting**: `black`, `isort`
- **Type Checking**: `mypy`
- **Testing**: `pytest`, `coverage`
- **Pre-commit**: Automated code quality checks

## 📝 Contributing Guidelines

### Types of Contributions

1. **Bug Fixes**
   - Fix existing issues
   - Improve error handling
   - Performance optimizations

2. **New Features**
   - New API endpoints
   - ML service implementations
   - Utility functions
   - Documentation improvements

3. **Documentation**
   - API documentation
   - Code comments
   - README updates
   - Tutorial content

4. **Testing**
   - Unit tests
   - Integration tests
   - Performance tests
   - Test coverage improvements

### Contribution Workflow

1. **Check Existing Issues**
   - Look for existing issues or feature requests
   - Comment on issues you'd like to work on
   - Ask questions if requirements are unclear

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b bugfix/issue-number
   ```

3. **Make Changes**
   - Follow code style guidelines
   - Add tests for new functionality
   - Update documentation as needed
   - Keep commits focused and atomic

4. **Test Your Changes**
   ```bash
   # Run tests
   pytest
   
   # Check coverage
   pytest --cov=app
   
   # Run linting
   pre-commit run --all-files
   ```

5. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add new ML service for text classification"
   ```

6. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create pull request on GitHub
   ```

## 🎨 Code Style

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line Length**: 88 characters (Black default)
- **Imports**: Use `isort` for import sorting
- **Docstrings**: Google-style docstrings
- **Type Hints**: Use type hints for function signatures

### Code Formatting

```bash
# Format code
black .

# Sort imports
isort .

# Check style
flake8 .
```

### Naming Conventions

- **Variables/Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Files/Modules**: `snake_case`
- **Packages**: `lowercase`

### Example Code Style

```python
from typing import Dict, List, Optional

from flask import Blueprint, request
from marshmallow import ValidationError

from app.schemas.v2.common import ErrorSchema, SuccessSchema
from app.services import get_service
from app.utils import generate_id, get_current_timestamp


class MLPredictionService:
    """Service for handling ML predictions.
    
    This service provides methods for making predictions using
    registered ML models with caching and error handling.
    
    Attributes:
        model_name: Name of the ML model to use
        cache_enabled: Whether to enable prediction caching
    """
    
    def __init__(self, model_name: str, cache_enabled: bool = True) -> None:
        """Initialize the prediction service.
        
        Args:
            model_name: Name of the ML model
            cache_enabled: Enable caching for predictions
        """
        self.model_name = model_name
        self.cache_enabled = cache_enabled
        self._model = None
    
    def predict(self, data: Dict) -> Dict:
        """Make a prediction using the loaded model.
        
        Args:
            data: Input data for prediction
            
        Returns:
            Dictionary containing prediction results
            
        Raises:
            ValueError: If input data is invalid
            RuntimeError: If model is not loaded
        """
        if not self._model:
            raise RuntimeError(f"Model {self.model_name} not loaded")
        
        # Validate input data
        if not isinstance(data, dict):
            raise ValueError("Input data must be a dictionary")
        
        # Make prediction
        result = self._model.predict(data)
        
        return {
            "prediction_id": generate_id(),
            "model_name": self.model_name,
            "result": result,
            "timestamp": get_current_timestamp(),
        }
```

## 🧪 Testing

### Testing Guidelines

1. **Write Tests First**: Follow TDD when possible
2. **Test Coverage**: Aim for >90% code coverage
3. **Test Types**: Unit, integration, and end-to-end tests
4. **Mock External Dependencies**: Use mocks for external services

### Test Structure

```
tests/
├── unit/                    # Unit tests
│   ├── test_services.py
│   ├── test_utils.py
│   └── test_schemas.py
├── integration/             # Integration tests
│   ├── test_api.py
│   └── test_database.py
├── e2e/                     # End-to-end tests
│   └── test_workflows.py
└── fixtures/                # Test data
    ├── models/
    └── data/
```

### Writing Tests

```python
import pytest
from unittest.mock import Mock, patch

from app.services.base import BaseMLService
from app.utils import generate_id


class TestBaseMLService:
    """Test cases for BaseMLService."""
    
    def test_service_initialization(self):
        """Test service initialization."""
        service = BaseMLService("test_model")
        assert service.model_name == "test_model"
        assert service.model is None
    
    @patch('app.services.base.load_model')
    def test_load_model_success(self, mock_load_model):
        """Test successful model loading."""
        mock_model = Mock()
        mock_load_model.return_value = mock_model
        
        service = BaseMLService("test_model")
        service.load_model()
        
        assert service.model == mock_model
        mock_load_model.assert_called_once()
    
    def test_predict_without_model(self):
        """Test prediction without loaded model."""
        service = BaseMLService("test_model")
        
        with pytest.raises(RuntimeError, match="Model not loaded"):
            service.predict({"input": "test"})
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_services.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run with verbose output
pytest -v

# Run only failed tests
pytest --lf
```

## 📚 Documentation

### Documentation Types

1. **Code Documentation**
   - Docstrings for all public functions/classes
   - Inline comments for complex logic
   - Type hints for function signatures

2. **API Documentation**
   - OpenAPI/Swagger specifications
   - Endpoint descriptions
   - Request/response examples

3. **User Documentation**
   - README updates
   - Tutorial content
   - Configuration guides

### Docstring Format

Use Google-style docstrings:

```python
def predict_batch(self, data_list: List[Dict]) -> List[Dict]:
    """Make predictions for multiple data points.
    
    This method processes a list of input data and returns
    predictions for each item using the loaded ML model.
    
    Args:
        data_list: List of dictionaries containing input data
            for prediction. Each dictionary should contain
            the required features for the model.
    
    Returns:
        List of dictionaries containing prediction results.
        Each result includes prediction_id, model_name,
        result, and timestamp.
    
    Raises:
        ValueError: If data_list is empty or contains invalid data
        RuntimeError: If model is not loaded
        
    Example:
        >>> service = MLPredictionService("text_classifier")
        >>> service.load_model()
        >>> data = [{"text": "Hello world"}, {"text": "Goodbye"}]
        >>> results = service.predict_batch(data)
        >>> len(results)
        2
    """
```

## 🔄 Pull Request Process

### Before Submitting

1. **Update Documentation**
   - Update README if needed
   - Add/update docstrings
   - Update API documentation

2. **Run Quality Checks**
   ```bash
   # Run all tests
   pytest
   
   # Check code style
   pre-commit run --all-files
   
   # Check type hints
   mypy app/
   ```

3. **Update Dependencies**
   ```bash
   # If you added new dependencies
   pip freeze > requirements.txt
   ```

### PR Template

Use this template for pull requests:

```markdown
## Description

Brief description of changes made.

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing

- [ ] Tests pass locally
- [ ] Added tests for new functionality
- [ ] Updated existing tests if needed

## Checklist

- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings introduced
- [ ] Tests added/updated
- [ ] All checks pass

## Related Issues

Fixes #(issue number)

## Screenshots (if applicable)

## Additional Notes

Any additional information or context.
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs tests and quality checks
2. **Code Review**: Maintainers review code for quality and style
3. **Testing**: Reviewers test functionality if needed
4. **Approval**: At least one maintainer approval required
5. **Merge**: Squash and merge to main branch

## 🐛 Issue Reporting

### Bug Reports

Use this template for bug reports:

```markdown
## Bug Description

A clear description of the bug.

## Steps to Reproduce

1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

## Expected Behavior

What you expected to happen.

## Actual Behavior

What actually happened.

## Environment

- OS: [e.g., Windows 10, Ubuntu 20.04]
- Python Version: [e.g., 3.9.7]
- Flask Version: [e.g., 2.0.1]
- Browser: [if applicable]

## Additional Context

Any other context about the problem.

## Logs

```
Paste relevant logs here
```
```

### Feature Requests

Use this template for feature requests:

```markdown
## Feature Description

A clear description of the feature you'd like to see.

## Problem Statement

What problem does this feature solve?

## Proposed Solution

Describe your proposed solution.

## Alternatives Considered

Describe alternatives you've considered.

## Additional Context

Any other context or screenshots.
```

## 👥 Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Pull Requests**: Code contributions

### Getting Help

1. **Check Documentation**: README and code comments
2. **Search Issues**: Look for existing solutions
3. **Ask Questions**: Create a discussion or issue
4. **Join Community**: Participate in discussions

### Recognition

Contributors are recognized in:
- GitHub contributors list
- Release notes
- Project documentation
- Community highlights

## 📄 License

By contributing to Flask Production Template for AI, you agree that your contributions will be licensed under the same license as the project (MIT License).

## 🙏 Thank You

Thank you for contributing to Flask Production Template for AI! Your efforts help make this project better for everyone.

---

**Questions?** Feel free to ask in GitHub Discussions or create an issue.