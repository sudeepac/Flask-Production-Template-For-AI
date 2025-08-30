#!/usr/bin/env python3
"""Blueprint Generator Script.

This script automates the creation of new Flask blueprints by copying
the __template__ directory and customizing it for the new blueprint.

Usage:
    python scripts/make_blueprint.py <blueprint_name>
    python scripts/make_blueprint.py user_management
    python scripts/make_blueprint.py fraud_detector

Features:
- Copies __template__ to app/blueprints/<name>
- Updates blueprint name and imports
- Registers URL prefix in app/urls.py
- Creates test directory structure
- Validates naming conventions

See AI_INSTRUCTIONS.md §2 for blueprint creation guidelines.
"""

import re
import shutil
import sys
from pathlib import Path


def validate_blueprint_name(name: str) -> bool:
    """Validate blueprint name follows conventions.

    Args:
        name: Blueprint name to validate

    Returns:
        bool: True if valid, False otherwise
    """
    # Must be valid Python identifier
    if not name.isidentifier():
        return False

    # Must be lowercase with underscores
    if not re.match(r"^[a-z][a-z0-9_]*$", name):
        return False

    # Must not be reserved words
    reserved = {"app", "test", "tests", "template", "blueprint", "blueprints"}
    if name in reserved:
        return False

    return True


def update_file_content(file_path: Path, blueprint_name: str) -> None:
    """Update file content with blueprint-specific values.

    Args:
        file_path: Path to file to update
        blueprint_name: Name of the blueprint
    """
    if not file_path.exists():
        return

    content = file_path.read_text(encoding="utf-8")

    # Replace template placeholders
    replacements = {
        "template": blueprint_name,
        "Template": blueprint_name.replace("_", " ").title().replace(" ", ""),
        "TEMPLATE": blueprint_name.upper(),
        "__template__": f"__{blueprint_name}__",
    }

    for old, new in replacements.items():
        content = content.replace(old, new)

    # Update specific patterns
    content = re.sub(
        r"BLUEPRINT_NAME = 'template'", f"BLUEPRINT_NAME = '{blueprint_name}'", content
    )

    content = re.sub(
        r"logger = get_logger\('app\.blueprints\.template'\)",
        f"logger = get_logger('app.blueprints.{blueprint_name}')",
        content,
    )

    file_path.write_text(content, encoding="utf-8")


def update_urls_file(blueprint_name: str, project_root: Path) -> None:
    """Add blueprint URL prefix to app/urls.py.

    Args:
        blueprint_name: Name of the blueprint
        project_root: Root directory of the project
    """
    urls_file = project_root / "app" / "urls.py"

    if not urls_file.exists():
        print(f"Warning: {urls_file} not found")
        return

    content = urls_file.read_text(encoding="utf-8")

    # Check if already exists
    if f"'{blueprint_name}'" in content:
        print(f"URL prefix for '{blueprint_name}' already exists in urls.py")
        return

    # Find URL_PREFIX dictionary and add new entry
    pattern = r"(URL_PREFIX\s*=\s*{[^}]*)(})"
    match = re.search(pattern, content, re.DOTALL)

    if match:
        # Add new entry before closing brace
        new_entry = f"    '{blueprint_name}': '/{blueprint_name}',\n"
        updated_content = content[: match.end(1)] + new_entry + match.group(2)
        urls_file.write_text(updated_content, encoding="utf-8")
        print(f"Added URL prefix for '{blueprint_name}' to urls.py")
    else:
        print("Warning: Could not find URL_PREFIX dictionary in urls.py")


def create_test_structure(blueprint_name: str, project_root: Path) -> None:
    """Create test directory structure for the blueprint.

    Args:
        blueprint_name: Name of the blueprint
        project_root: Root directory of the project
    """
    test_dir = project_root / "tests" / blueprint_name
    test_dir.mkdir(parents=True, exist_ok=True)

    # Create __init__.py
    init_file = test_dir / "__init__.py"
    init_content = f'"""Tests for {blueprint_name} blueprint."""\n'
    init_file.write_text(init_content, encoding="utf-8")

    # Create test_routes.py stub
    routes_test = test_dir / "test_routes.py"
    routes_content = f'''"""Test routes for {blueprint_name} blueprint.

See AI_INSTRUCTIONS.md §5 for testing guidelines.
"""

import pytest
from flask import url_for


class Test{blueprint_name.replace('_', ' ').title().replace(' ', '')}Routes:
    """Test class for {blueprint_name} routes."""

    def test_list_{blueprint_name}(self, client):
        """Test listing {blueprint_name} resources."""
        response = client.get(url_for('{blueprint_name}.list_{blueprint_name}s'))
        assert response.status_code == 200

    def test_get_{blueprint_name}(self, client):
        """Test getting specific {blueprint_name} resource."""
        # TODO: Implement test
        pass

    def test_create_{blueprint_name}(self, client):
        """Test creating {blueprint_name} resource."""
        # TODO: Implement test
        pass

    def test_update_{blueprint_name}(self, client):
        """Test updating {blueprint_name} resource."""
        # TODO: Implement test
        pass

    def test_delete_{blueprint_name}(self, client):
        """Test deleting {blueprint_name} resource."""
        # TODO: Implement test
        pass
'''
    routes_test.write_text(routes_content, encoding="utf-8")

    print(f"Created test structure in tests/{blueprint_name}/")


def create_blueprint(blueprint_name: str) -> None:
    """Create a new blueprint from template.

    Args:
        blueprint_name: Name of the new blueprint
    """
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Validate name
    if not validate_blueprint_name(blueprint_name):
        print(f"Error: Invalid blueprint name '{blueprint_name}'")
        print("Blueprint names must:")
        print("- Be valid Python identifiers")
        print("- Use lowercase with underscores")
        print("- Not be reserved words")
        sys.exit(1)

    # Check if blueprint already exists
    blueprint_dir = project_root / "app" / "blueprints" / blueprint_name
    if blueprint_dir.exists():
        print(f"Error: Blueprint '{blueprint_name}' already exists")
        sys.exit(1)

    # Check if template exists
    template_dir = project_root / "__template__"
    if not template_dir.exists():
        print("Error: __template__ directory not found")
        sys.exit(1)

    print(f"Creating blueprint '{blueprint_name}'...")

    # Copy template to new blueprint directory
    shutil.copytree(template_dir, blueprint_dir)
    print(f"Copied template to app/blueprints/{blueprint_name}/")

    # Update file contents
    for file_path in blueprint_dir.rglob("*.py"):
        update_file_content(file_path, blueprint_name)

    print(f"Updated blueprint files with '{blueprint_name}' specifics")

    # Update URLs file
    update_urls_file(blueprint_name, project_root)

    # Create test structure
    create_test_structure(blueprint_name, project_root)

    print(f"\n✅ Blueprint '{blueprint_name}' created successfully!")
    print("\nNext steps:")
    print(f"1. Implement your routes in app/blueprints/{blueprint_name}/routes.py")
    print(f"2. Define schemas in app/blueprints/{blueprint_name}/schemas.py")
    print(f"3. Add models in app/blueprints/{blueprint_name}/models.py")
    print(f"4. Implement services in app/blueprints/{blueprint_name}/services.py")
    print(f"5. Write tests in tests/{blueprint_name}/")
    print(f"6. Run: python scripts/gen_tests.py {blueprint_name}")


def main() -> None:
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python scripts/make_blueprint.py <blueprint_name>")
        print("Example: python scripts/make_blueprint.py user_management")
        sys.exit(1)

    blueprint_name = sys.argv[1]
    create_blueprint(blueprint_name)


if __name__ == "__main__":
    main()
