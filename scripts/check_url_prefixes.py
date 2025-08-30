#!/usr/bin/env python3
"""
URL Prefix Consistency Checker

Checks that URL prefixes are consistent between blueprint registration
and route definitions.
"""

import os
import re
import sys
from pathlib import Path


def extract_url_prefixes_from_urls():
    """Extract URL prefixes from app/urls.py."""
    urls_file = Path("app/urls.py")

    if not urls_file.exists():
        return {}

    prefixes = {}

    try:
        with open(urls_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Look for blueprint registration patterns
        # app.register_blueprint(blueprint, url_prefix='/prefix')
        pattern = r'app\.register_blueprint\(([^,]+),\s*url_prefix=["\']([^"\']+)["\']'
        matches = re.findall(pattern, content)

        for blueprint_var, prefix in matches:
            # Extract blueprint name from variable
            blueprint_name = blueprint_var.strip()
            prefixes[blueprint_name] = prefix

    except Exception as e:
        print(f"Warning: Could not parse urls.py: {e}")

    return prefixes


def extract_routes_from_blueprint(blueprint_path):
    """Extract route patterns from a blueprint routes.py file."""
    routes_file = blueprint_path / "routes.py"

    if not routes_file.exists():
        return []

    routes = []

    try:
        with open(routes_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Look for route decorators
        # @bp.route('/path') or @blueprint.route('/path')
        pattern = r'@\w+\.route\(["\']([^"\']+)["\']'
        matches = re.findall(pattern, content)
        routes.extend(matches)

    except Exception as e:
        print(f"Warning: Could not parse {routes_file}: {e}")

    return routes


def check_url_prefix_consistency():
    """Check URL prefix consistency across blueprints."""
    blueprints_dir = Path("app/blueprints")

    if not blueprints_dir.exists():
        print("[OK] No blueprints directory found, skipping check")
        return True

    # Get registered prefixes
    registered_prefixes = extract_url_prefixes_from_urls()

    errors = []
    warnings = []

    for blueprint_dir in blueprints_dir.iterdir():
        if not blueprint_dir.is_dir() or blueprint_dir.name.startswith("."):
            continue

        blueprint_name = blueprint_dir.name
        routes = extract_routes_from_blueprint(blueprint_dir)

        if not routes:
            continue

        # Check if blueprint has a registered prefix
        expected_prefix = None
        for var_name, prefix in registered_prefixes.items():
            if blueprint_name in var_name.lower():
                expected_prefix = prefix
                break

        if expected_prefix:
            # Check if routes are consistent with prefix
            for route in routes:
                if route.startswith("/"):
                    # Route should not duplicate the prefix
                    if route.startswith(expected_prefix):
                        warnings.append(
                            f"Route '{route}' in {blueprint_name} duplicates prefix '{expected_prefix}'"
                        )
        else:
            # Blueprint not found in registration, might be an issue
            if blueprint_name not in [
                "health"
            ]:  # health is often registered without prefix
                warnings.append(
                    f"Blueprint '{blueprint_name}' not found in URL registration"
                )

    if errors:
        print("[ERROR] URL prefix errors found:")
        for error in errors:
            print(f"  - {error}")
        return False

    if warnings:
        print("[WARNING] URL prefix warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    if not errors and not warnings:
        print("[OK] URL prefixes are consistent")

    return True  # Only fail on errors, not warnings


if __name__ == "__main__":
    success = check_url_prefix_consistency()
    sys.exit(0 if success else 1)
