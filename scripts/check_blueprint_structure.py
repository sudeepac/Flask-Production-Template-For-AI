#!/usr/bin/env python3
"""
Blueprint Structure Checker

Checks that all blueprints follow the required structure:
- __init__.py
- routes.py
- resources.py (for API blueprints)
"""

import os
import sys
from pathlib import Path


def check_blueprint_structure():
    """Check that all blueprints have required files."""
    blueprints_dir = Path("app/blueprints")

    if not blueprints_dir.exists():
        print("[OK] No blueprints directory found, skipping check")
        return True

    errors = []

    for blueprint_dir in blueprints_dir.iterdir():
        if (
            not blueprint_dir.is_dir()
            or blueprint_dir.name.startswith(".")
            or blueprint_dir.name == "__pycache__"
        ):
            continue

        # Check for required files
        init_file = blueprint_dir / "__init__.py"
        routes_file = blueprint_dir / "routes.py"

        if not init_file.exists():
            errors.append(f"Missing __init__.py in {blueprint_dir.name}")

        if not routes_file.exists():
            errors.append(f"Missing routes.py in {blueprint_dir.name}")

        # Check if it's an API blueprint (should have resources.py)
        if blueprint_dir.name == "api" or "api" in blueprint_dir.name:
            resources_file = blueprint_dir / "resources.py"
            if not resources_file.exists():
                errors.append(
                    f"Missing resources.py in API blueprint {blueprint_dir.name}"
                )

    if errors:
        print("[ERROR] Blueprint structure errors found:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("[OK] All blueprints have proper structure")
        return True


if __name__ == "__main__":
    success = check_blueprint_structure()
    sys.exit(0 if success else 1)
