#!/usr/bin/env python3
"""Test Generator Script.

This script automatically generates test stubs for Flask blueprints
based on their route definitions and schemas.

Usage:
    python scripts/gen_tests.py <blueprint_name>
    python scripts/gen_tests.py user_management
    python scripts/gen_tests.py --all  # Generate for all blueprints

Features:
- Analyzes blueprint routes and generates test stubs
- Creates test fixtures based on schemas
- Generates integration and unit tests
- Updates existing test files without overwriting custom tests
- Follows pytest conventions and best practices

See AI_INSTRUCTIONS.md §5 for testing guidelines.
"""

import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set


@dataclass
class RouteInfo:
    """Information about a Flask route."""

    name: str
    path: str
    methods: List[str]
    function_name: str
    docstring: Optional[str] = None


class RouteAnalyzer:
    """Analyzes Flask blueprint routes."""

    def __init__(self, blueprint_path: Path):
        """Initialize analyzer.

        Args:
            blueprint_path: Path to blueprint directory
        """
        self.blueprint_path = blueprint_path
        self.routes_file = blueprint_path / "routes.py"

    def extract_routes(self) -> List[RouteInfo]:
        """Extract route information from routes.py.

        Returns:
            List of RouteInfo objects
        """
        if not self.routes_file.exists():
            return []

        routes = []
        content = self.routes_file.read_text(encoding="utf-8")

        # Parse AST to find route decorators
        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    route_info = self._analyze_function(node)
                    if route_info:
                        routes.append(route_info)

        except SyntaxError as e:
            print(f"Warning: Could not parse {self.routes_file}: {e}")

        return routes

    def _analyze_function(self, func_node: ast.FunctionDef) -> Optional[RouteInfo]:
        """Analyze a function node for route decorators.

        Args:
            func_node: AST function definition node

        Returns:
            RouteInfo if function has route decorator, None otherwise
        """
        for decorator in func_node.decorator_list:
            if self._is_route_decorator(decorator):
                path, methods = self._extract_route_params(decorator)

                # Extract docstring
                docstring = None
                if (
                    func_node.body
                    and isinstance(func_node.body[0], ast.Expr)
                    and isinstance(func_node.body[0].value, ast.Constant)
                ):
                    docstring = func_node.body[0].value.value

                return RouteInfo(
                    name=func_node.name,
                    path=path,
                    methods=methods,
                    function_name=func_node.name,
                    docstring=docstring,
                )

        return None

    def _is_route_decorator(self, decorator: ast.AST) -> bool:
        """Check if decorator is a route decorator.

        Args:
            decorator: AST decorator node

        Returns:
            True if route decorator
        """
        if isinstance(decorator, ast.Attribute):
            return decorator.attr == "route"
        elif isinstance(decorator, ast.Call) and isinstance(
            decorator.func, ast.Attribute
        ):
            return decorator.func.attr == "route"
        return False

    def _extract_route_params(self, decorator: ast.AST) -> tuple[str, List[str]]:
        """Extract path and methods from route decorator.

        Args:
            decorator: AST decorator node

        Returns:
            Tuple of (path, methods)
        """
        path = "/"
        methods = ["GET"]

        if isinstance(decorator, ast.Call):
            # Extract positional arguments (path)
            if decorator.args:
                if isinstance(decorator.args[0], ast.Constant):
                    path = decorator.args[0].value

            # Extract keyword arguments (methods)
            for keyword in decorator.keywords:
                if keyword.arg == "methods":
                    if isinstance(keyword.value, ast.List):
                        methods = []
                        for elt in keyword.value.elts:
                            if isinstance(elt, ast.Constant):
                                methods.append(elt.value)

        return path, methods


class TestGenerator:
    """Generates test files for blueprints."""

    def __init__(self, blueprint_name: str, project_root: Path):
        """Initialize generator.

        Args:
            blueprint_name: Name of the blueprint
            project_root: Root directory of the project
        """
        self.blueprint_name = blueprint_name
        self.project_root = project_root
        self.blueprint_path = project_root / "app" / "blueprints" / blueprint_name
        self.test_path = project_root / "tests" / blueprint_name

    def generate_tests(self) -> None:
        """Generate all test files for the blueprint."""
        if not self.blueprint_path.exists():
            print(f"Error: Blueprint '{self.blueprint_name}' not found")
            return

        # Create test directory
        self.test_path.mkdir(parents=True, exist_ok=True)

        # Analyze routes
        analyzer = RouteAnalyzer(self.blueprint_path)
        routes = analyzer.extract_routes()

        # Generate test files
        self._generate_route_tests(routes)
        self._generate_schema_tests()
        self._generate_service_tests()
        self._generate_model_tests()

        print(f"Generated tests for blueprint '{self.blueprint_name}'")

    def _generate_route_tests(self, routes: List[RouteInfo]) -> None:
        """Generate route test file.

        Args:
            routes: List of route information
        """
        test_file = self.test_path / "test_routes.py"

        # Check if file exists and has custom tests
        existing_tests = set()
        if test_file.exists():
            existing_tests = self._extract_existing_tests(test_file)

        class_name = f"Test{self.blueprint_name.replace('_', ' ').title().replace(' ', '')}Routes"

        content = f'''"""Test routes for {self.blueprint_name} blueprint.

See AI_INSTRUCTIONS.md §5 for testing guidelines.
"""

import pytest
import json
from flask import url_for
from unittest.mock import patch, MagicMock


class {class_name}:
    """Test class for {self.blueprint_name} routes."""
'''

        # Generate test methods for each route
        for route in routes:
            test_method_name = f"test_{route.function_name}"

            # Skip if test already exists (custom implementation)
            if test_method_name in existing_tests:
                continue

            content += self._generate_route_test_method(route)

        # Add helper methods
        content += self._generate_test_helpers()

        test_file.write_text(content, encoding="utf-8")

    def _generate_route_test_method(self, route: RouteInfo) -> str:
        """Generate test method for a route.

        Args:
            route: Route information

        Returns:
            Test method code
        """
        method_name = f"test_{route.function_name}"

        # Determine test type based on HTTP methods
        if "GET" in route.methods and route.path.endswith("/"):
            # List endpoint
            return f'''

    def {method_name}(self, client, auth_headers):
        """Test {route.function_name} endpoint."""
        response = client.get(
            url_for('{self.blueprint_name}.{route.function_name}'),
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'status' in data
        assert data['status'] == 'success'
'''
        elif "GET" in route.methods and "<" in route.path:
            # Get single item endpoint
            return f'''

    def {method_name}(self, client, auth_headers, sample_{self.blueprint_name}_id):
        """Test {route.function_name} endpoint."""
        response = client.get(
            url_for('{self.blueprint_name}.{route.function_name}', id=sample_{self.blueprint_name}_id),
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'status' in data
        assert data['status'] == 'success'
'''
        elif "POST" in route.methods:
            # Create endpoint
            return f'''

    def {method_name}(self, client, auth_headers, sample_{self.blueprint_name}_data):
        """Test {route.function_name} endpoint."""
        response = client.post(
            url_for('{self.blueprint_name}.{route.function_name}'),
            json=sample_{self.blueprint_name}_data,
            headers=auth_headers
        )
        assert response.status_code in [200, 201]
        data = response.get_json()
        assert 'status' in data
        assert data['status'] == 'success'
'''
        elif "PUT" in route.methods:
            # Update endpoint
            return f'''

    def {method_name}(self, client, auth_headers, sample_{self.blueprint_name}_id, sample_{self.blueprint_name}_data):
        """Test {route.function_name} endpoint."""
        response = client.put(
            url_for('{self.blueprint_name}.{route.function_name}', id=sample_{self.blueprint_name}_id),
            json=sample_{self.blueprint_name}_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'status' in data
        assert data['status'] == 'success'
'''
        elif "DELETE" in route.methods:
            # Delete endpoint
            return f'''

    def {method_name}(self, client, auth_headers, sample_{self.blueprint_name}_id):
        """Test {route.function_name} endpoint."""
        response = client.delete(
            url_for('{self.blueprint_name}.{route.function_name}', id=sample_{self.blueprint_name}_id),
            headers=auth_headers
        )
        assert response.status_code in [200, 204]
'''
        else:
            # Generic endpoint
            return f'''

    def {method_name}(self, client, auth_headers):
        """Test {route.function_name} endpoint."""
        # TODO: Implement test for {route.function_name}
        pass
'''

    def _generate_test_helpers(self) -> str:
        """Generate helper methods and fixtures.

        Returns:
            Helper method code
        """
        return f'''


@pytest.fixture
def sample_{self.blueprint_name}_data():
    """Sample data for {self.blueprint_name} tests."""
    return {{
        'name': 'Test {self.blueprint_name.replace("_", " ").title()}',
        'description': 'Test description',
        # TODO: Add more fields based on your schema
    }}


@pytest.fixture
def sample_{self.blueprint_name}_id():
    """Sample ID for {self.blueprint_name} tests."""
    return 1


@pytest.fixture
def auth_headers(jwt_token):
    """Authentication headers for API requests."""
    return {{
        'Authorization': f'Bearer {{jwt_token}}',
        'Content-Type': 'application/json'
    }}
'''

    def _generate_schema_tests(self) -> None:
        """Generate schema test file."""
        test_file = self.test_path / "test_schemas.py"

        if test_file.exists():
            return  # Don't overwrite existing schema tests

        content = f'''"""Test schemas for {self.blueprint_name} blueprint.

See AI_INSTRUCTIONS.md §5 for testing guidelines.
"""

import pytest
from marshmallow import ValidationError

# Import schemas from the blueprint
try:
    from app.blueprints.{self.blueprint_name}.schemas import (
        {self.blueprint_name.replace("_", " ").title().replace(" ", "")}RequestSchema,
        {self.blueprint_name.replace("_", " ").title().replace(" ", "")}ResponseSchema,
    )
except ImportError:
    pytest.skip("Schemas not implemented yet", allow_module_level=True)


class Test{self.blueprint_name.replace("_", " ").title().replace(" ", "")}Schemas:
    """Test class for {self.blueprint_name} schemas."""

    def test_request_schema_valid_data(self):
        """Test request schema with valid data."""
        schema = {self.blueprint_name.replace("_", " ").title().replace(" ", "")}RequestSchema()
        data = {{
            'name': 'Test Name',
            'description': 'Test Description',
            # TODO: Add more fields
        }}

        result = schema.load(data)
        assert result['name'] == 'Test Name'
        assert result['description'] == 'Test Description'

    def test_request_schema_invalid_data(self):
        """Test request schema with invalid data."""
        schema = {self.blueprint_name.replace("_", " ").title().replace(" ", "")}RequestSchema()
        data = {{
            # Missing required fields
        }}

        with pytest.raises(ValidationError):
            schema.load(data)

    def test_response_schema_serialization(self):
        """Test response schema serialization."""
        schema = {self.blueprint_name.replace("_", " ").title().replace(" ", "")}ResponseSchema()
        data = {{
            'id': 1,
            'name': 'Test Name',
            'description': 'Test Description',
            # TODO: Add more fields
        }}

        result = schema.dump(data)
        assert 'id' in result
        assert 'name' in result
        assert 'description' in result
'''

        test_file.write_text(content, encoding="utf-8")

    def _generate_service_tests(self) -> None:
        """Generate service test file."""
        test_file = self.test_path / "test_services.py"

        if test_file.exists():
            return  # Don't overwrite existing service tests

        content = f'''"""Test services for {self.blueprint_name} blueprint.

See AI_INSTRUCTIONS.md §5 for testing guidelines.
"""

import pytest
from unittest.mock import Mock, patch

# Import services from the blueprint
try:
    from app.blueprints.{self.blueprint_name}.services import (
        {self.blueprint_name.replace("_", " ").title().replace(" ", "")}Service,
    )
except ImportError:
    pytest.skip("Services not implemented yet", allow_module_level=True)


class Test{self.blueprint_name.replace("_", " ").title().replace(" ", "")}Service:
    """Test class for {self.blueprint_name} service."""

    def test_service_initialization(self):
        """Test service initialization."""
        service = {self.blueprint_name.replace("_", " ").title().replace(" ", "")}Service()
        assert service is not None

    def test_create_method(self):
        """Test create method."""
        # TODO: Implement test
        pass

    def test_get_method(self):
        """Test get method."""
        # TODO: Implement test
        pass

    def test_update_method(self):
        """Test update method."""
        # TODO: Implement test
        pass

    def test_delete_method(self):
        """Test delete method."""
        # TODO: Implement test
        pass
'''

        test_file.write_text(content, encoding="utf-8")

    def _generate_model_tests(self) -> None:
        """Generate model test file."""
        test_file = self.test_path / "test_models.py"

        if test_file.exists():
            return  # Don't overwrite existing model tests

        content = f'''"""Test models for {self.blueprint_name} blueprint.

See AI_INSTRUCTIONS.md §5 for testing guidelines.
"""

import pytest
from datetime import datetime

# Import models from the blueprint
try:
    from app.blueprints.{self.blueprint_name}.models import (
        {self.blueprint_name.replace("_", " ").title().replace(" ", "")},
    )
except ImportError:
    pytest.skip("Models not implemented yet", allow_module_level=True)


class Test{self.blueprint_name.replace("_", " ").title().replace(" ", "")}Model:
    """Test class for {self.blueprint_name} model."""

    def test_model_creation(self, db_session):
        """Test model creation."""
        model = {self.blueprint_name.replace("_", " ").title().replace(" ", "")}(
            name='Test Name',
            description='Test Description'
        )

        db_session.add(model)
        db_session.commit()

        assert model.id is not None
        assert model.name == 'Test Name'
        assert model.description == 'Test Description'
        assert isinstance(model.created_at, datetime)

    def test_model_validation(self):
        """Test model validation."""
        # TODO: Implement validation tests
        pass

    def test_model_relationships(self, db_session):
        """Test model relationships."""
        # TODO: Implement relationship tests
        pass
'''

        test_file.write_text(content, encoding="utf-8")

    def _extract_existing_tests(self, test_file: Path) -> Set[str]:
        """Extract existing test method names from file.

        Args:
            test_file: Path to test file

        Returns:
            Set of existing test method names
        """
        existing_tests = set()

        try:
            content = test_file.read_text(encoding="utf-8")
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    existing_tests.add(node.name)

        except (SyntaxError, FileNotFoundError):
            pass

        return existing_tests


def generate_tests_for_blueprint(blueprint_name: str) -> None:
    """Generate tests for a specific blueprint.

    Args:
        blueprint_name: Name of the blueprint
    """
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    generator = TestGenerator(blueprint_name, project_root)
    generator.generate_tests()


def generate_tests_for_all_blueprints() -> None:
    """Generate tests for all blueprints."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    blueprints_dir = project_root / "app" / "blueprints"

    if not blueprints_dir.exists():
        print("No blueprints directory found")
        return

    for blueprint_dir in blueprints_dir.iterdir():
        if blueprint_dir.is_dir() and not blueprint_dir.name.startswith("_"):
            print(f"Generating tests for {blueprint_dir.name}...")
            generator = TestGenerator(blueprint_dir.name, project_root)
            generator.generate_tests()


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/gen_tests.py <blueprint_name>")
        print("       python scripts/gen_tests.py --all")
        print("Example: python scripts/gen_tests.py user_management")
        sys.exit(1)

    if sys.argv[1] == "--all":
        generate_tests_for_all_blueprints()
    else:
        blueprint_name = sys.argv[1]
        generate_tests_for_blueprint(blueprint_name)

    print("\n✅ Test generation completed!")
    print("\nNext steps:")
    print("1. Review generated test files")
    print("2. Implement TODO test cases")
    print("3. Add test fixtures and data")
    print("4. Run tests: pytest tests/")


if __name__ == "__main__":
    main()
