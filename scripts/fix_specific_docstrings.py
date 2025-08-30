#!/usr/bin/env python3
"""
Specific Docstring Fixer

This script fixes the specific docstring issues identified by the style compliance checker.
"""

from pathlib import Path


def fix_config_manager():
    """Fix DynamicConfig class docstring."""
    file_path = Path("app/config_manager.py")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the DynamicConfig class and add docstring
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if "class DynamicConfig:" in line:
            # Insert docstring after the class definition
            lines.insert(
                i + 1, '        """Dynamic configuration class generated at runtime."""'
            )
            break

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Fixed DynamicConfig class docstring in {file_path}")


def fix_schemas_v2_base():
    """Fix schemas/v2/base.py docstrings."""
    file_path = Path("app/schemas/v2/base.py")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")

    # Fix ResponseSchema class
    for i, line in enumerate(lines):
        if "class ResponseSchema(" in line:
            # Check if next line is not a docstring
            if i + 1 < len(lines) and not lines[i + 1].strip().startswith('"""'):
                lines.insert(
                    i + 1, '    """Base response schema with common fields."""'
                )
            break

    # Fix ListSchema class
    for i, line in enumerate(lines):
        if "class ListSchema(" in line:
            # Check if next line is not a docstring
            if i + 1 < len(lines) and not lines[i + 1].strip().startswith('"""'):
                lines.insert(i + 1, '    """Schema for paginated list responses."""')
            break

    # Fix add_count function
    for i, line in enumerate(lines):
        if "def add_count(" in line:
            # Check if next line is not a docstring
            if i + 1 < len(lines) and not lines[i + 1].strip().startswith('"""'):
                lines.insert(i + 1, '        """Add count field to the schema."""')
            break

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Fixed docstrings in {file_path}")


def fix_example_service():
    """Fix services/example_service.py docstrings."""
    file_path = Path("app/services/example_service.py")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")

    # Fix PostSchema class
    for i, line in enumerate(lines):
        if "class PostSchema(" in line:
            # Check if next line is not a docstring
            if i + 1 < len(lines) and not lines[i + 1].strip().startswith('"""'):
                lines.insert(i + 1, '    """Schema for post data validation."""')
            break

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Fixed PostSchema docstring in {file_path}")


def fix_logging_config():
    """Fix utils/logging_config.py wrapper function docstring."""
    file_path = Path("app/utils/logging_config.py")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")

    # Find the wrapper function around line 382
    for i in range(375, min(390, len(lines))):
        if "def wrapper(" in lines[i]:
            # Check if next line is not a docstring
            if i + 1 < len(lines) and not lines[i + 1].strip().startswith('"""'):
                # Get indentation
                indent = len(lines[i]) - len(lines[i].lstrip()) + 4
                docstring = (
                    " " * indent + '"""Wrapper function for logging decorator."""'
                )
                lines.insert(i + 1, docstring)
            break

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Fixed wrapper function docstring in {file_path}")


def fix_security():
    """Fix utils/security.py decorated_function docstring."""
    file_path = Path("app/utils/security.py")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")

    # Find decorated_function around line 135
    for i in range(130, min(140, len(lines))):
        if "def decorated_function(" in lines[i]:
            # Check if next line is not a docstring
            if i + 1 < len(lines) and not lines[i + 1].strip().startswith('"""'):
                # Get indentation
                indent = len(lines[i]) - len(lines[i].lstrip()) + 4
                docstring = (
                    " " * indent + '"""Decorated function with API key validation."""'
                )
                lines.insert(i + 1, docstring)
            break

    # Find another decorated_function around line 173
    for i in range(168, min(180, len(lines))):
        if "def decorated_function(" in lines[i]:
            # Check if next line is not a docstring
            if i + 1 < len(lines) and not lines[i + 1].strip().startswith('"""'):
                # Get indentation
                indent = len(lines[i]) - len(lines[i].lstrip()) + 4
                docstring = (
                    " " * indent
                    + '"""Decorated function with role-based access control."""'
                )
                lines.insert(i + 1, docstring)
            break

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Fixed decorated_function docstrings in {file_path}")


def fix_utils_init():
    """Fix utils/__init__.py decorator and wrapper function docstrings."""
    file_path = Path("app/utils/__init__.py")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")

    # Find decorator function around line 340
    for i in range(335, min(345, len(lines))):
        if "def decorator(" in lines[i]:
            # Check if next line is not a docstring
            if i + 1 < len(lines) and not lines[i + 1].strip().startswith('"""'):
                # Get indentation
                indent = len(lines[i]) - len(lines[i].lstrip()) + 4
                docstring = (
                    " " * indent + '"""Decorator function for utility operations."""'
                )
                lines.insert(i + 1, docstring)
            break

    # Find wrapper function around line 342
    for i in range(337, min(347, len(lines))):
        if "def wrapper(" in lines[i]:
            # Check if next line is not a docstring
            if i + 1 < len(lines) and not lines[i + 1].strip().startswith('"""'):
                # Get indentation
                indent = len(lines[i]) - len(lines[i].lstrip()) + 4
                docstring = (
                    " " * indent + '"""Wrapper function for decorated operations."""'
                )
                lines.insert(i + 1, docstring)
            break

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Fixed decorator and wrapper function docstrings in {file_path}")


def main():
    """Main function to fix all specific docstring issues."""
    print("Fixing specific docstring issues...")

    try:
        fix_config_manager()
        fix_schemas_v2_base()
        fix_example_service()
        fix_logging_config()
        fix_security()
        fix_utils_init()

        print("\nAll specific docstring issues have been fixed!")
        print("Run the style compliance check again to verify.")

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
