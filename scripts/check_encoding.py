#!/usr/bin/env python3
"""
Python Encoding Checker

Checks that all Python files have proper UTF-8 encoding declaration
when needed (for files containing non-ASCII characters).
"""

import os
import sys
from pathlib import Path


def has_non_ascii_chars(file_path):
    """Check if file contains non-ASCII characters."""
    try:
        with open(file_path, "rb") as f:
            content = f.read()
            # Try to decode as ASCII
            content.decode("ascii")
            return False
    except UnicodeDecodeError:
        return True
    except Exception:
        return False


def has_encoding_declaration(file_path):
    """Check if file has encoding declaration in first or second line."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [f.readline().strip(), f.readline().strip()]

        for line in lines:
            if "coding:" in line or "coding=" in line:
                return True

        return False
    except Exception:
        return False


def check_python_encoding():
    """Check Python files for proper encoding declarations."""
    errors = []
    warnings = []
    checked_files = 0

    # Find all Python files
    for root, dirs, files in os.walk("."):
        # Skip certain directories
        dirs[:] = [
            d
            for d in dirs
            if not d.startswith(".")
            and d not in ["__pycache__", "node_modules", "venv", "env", "migrations"]
        ]

        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                checked_files += 1

                # Check if file has non-ASCII characters
                if has_non_ascii_chars(file_path):
                    if not has_encoding_declaration(file_path):
                        errors.append(
                            f"File '{file_path}' contains non-ASCII characters but lacks encoding declaration"
                        )

                # Check for common encoding issues
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Check for BOM (Byte Order Mark)
                    if content.startswith("\ufeff"):
                        warnings.append(
                            f"File '{file_path}' contains UTF-8 BOM, consider removing it"
                        )

                except UnicodeDecodeError:
                    errors.append(f"File '{file_path}' cannot be decoded as UTF-8")
                except Exception as e:
                    warnings.append(f"Could not check file '{file_path}': {e}")

    # Report results
    if errors:
        print("[ERROR] Python encoding errors found:")
        for error in errors:
            print(f"  - {error}")
        print("\nTo fix: Add '# -*- coding: utf-8 -*-' to the first or second line")
        return False

    if warnings:
        print("[WARNING] Python encoding warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    if not errors and not warnings:
        print(f"[OK] All {checked_files} Python files have proper encoding")
    elif not errors:
        print(
            f"[OK] All {checked_files} Python files have valid encoding (with warnings)"
        )

    return True  # Only fail on errors, not warnings


if __name__ == "__main__":
    success = check_python_encoding()
    sys.exit(0 if success else 1)
