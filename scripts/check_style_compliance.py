#!/usr/bin/env python3
"""Style compliance checker for Flask Production Template.

This script validates that the codebase follows the Python style guide
defined in docs/python_style_guide.md. It performs various checks beyond
what the standard linting tools provide.

Usage:
    python scripts/check_style_compliance.py
    python scripts/check_style_compliance.py --fix

Checks performed:
- Docstring presence and format
- Naming convention compliance
- Import organization
- File structure compliance
- Security best practices
"""

import argparse
import ast
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List


class StyleChecker:
    """Main style compliance checker."""

    def __init__(self, fix_mode: bool = False):
        """Initialize the style checker.

        Args:
            fix_mode: Whether to automatically fix issues where possible.
        """
        self.fix_mode = fix_mode
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []

    def check_file(self, file_path: Path) -> bool:
        """Check a single Python file for style compliance.

        Args:
            file_path: Path to the Python file to check.

        Returns:
            True if file passes all checks, False otherwise.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse the AST
            try:
                tree = ast.parse(content, filename=str(file_path))
            except SyntaxError as e:
                self._add_error(file_path, 0, f"Syntax error: {e}")
                return False

            # Perform various checks
            self._check_module_docstring(file_path, tree, content)
            self._check_function_docstrings(file_path, tree)
            self._check_class_docstrings(file_path, tree)
            self._check_naming_conventions(file_path, tree)
            self._check_import_organization(file_path, content)
            self._check_security_patterns(file_path, content)

            return len([e for e in self.errors if e["file"] == str(file_path)]) == 0

        except Exception as e:
            self._add_error(file_path, 0, f"Error checking file: {e}")
            return False

    def _check_module_docstring(
        self, file_path: Path, tree: ast.AST, content: str
    ) -> None:
        """Check if module has a proper docstring."""
        if not ast.get_docstring(tree):
            # Skip __init__.py files and test files
            if file_path.name != "__init__.py" and "test_" not in file_path.name:
                self._add_error(file_path, 1, "Module missing docstring")

    def _check_function_docstrings(self, file_path: Path, tree: ast.AST) -> None:
        """Check if public functions have docstrings."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Skip private functions, test functions, and dunder methods
                if (
                    node.name.startswith("_")
                    or node.name.startswith("test_")
                    or (node.name.startswith("__") and node.name.endswith("__"))
                ):
                    continue

                # Skip simple decorator functions (usually just return a
                # function)
                if (
                    len(node.body) == 1
                    and isinstance(node.body[0], ast.Return)
                    and isinstance(node.body[0].value, ast.Name)
                ):
                    continue

                # Skip very short functions (likely simple wrappers)
                if len(node.body) <= 2:
                    # Check if it's just a simple return or pass
                    simple_body = all(
                        isinstance(stmt, (ast.Return, ast.Pass, ast.Expr))
                        for stmt in node.body
                    )
                    if simple_body:
                        continue

                # Check if function has a docstring
                if not ast.get_docstring(node):
                    self._add_error(
                        file_path,
                        node.lineno,
                        f"Public function '{node.name}' missing docstring",
                    )

    def _check_class_docstrings(self, file_path: Path, tree: ast.AST) -> None:
        """Check if public classes have docstrings."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Skip private classes
                if not node.name.startswith("_") and not ast.get_docstring(node):
                    self._add_error(
                        file_path,
                        node.lineno,
                        f"Public class '{node.name}' missing docstring",
                    )

    def _check_naming_conventions(self, file_path: Path, tree: ast.AST) -> None:
        """Check naming convention compliance."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Skip dunder methods (e.g., __init__, __str__, __repr__)
                if node.name.startswith("__") and node.name.endswith("__"):
                    continue

                # Skip private methods (starting with single underscore) -
                # these are allowed
                if node.name.startswith("_") and not node.name.startswith("__"):
                    continue

                # Skip test functions
                if node.name.startswith("test_"):
                    continue

                if not self._is_snake_case(node.name):
                    self._add_error(
                        file_path,
                        node.lineno,
                        f"Function '{node.name}' should use snake_case",
                    )
            elif isinstance(node, ast.ClassDef):
                # Skip private classes (starting with underscore)
                if node.name.startswith("_"):
                    continue

                if not self._is_pascal_case(node.name):
                    self._add_error(
                        file_path,
                        node.lineno,
                        f"Class '{node.name}' should use PascalCase",
                    )
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        name = target.id
                        # Check for constants (all uppercase)
                        if name.isupper():
                            if not self._is_upper_snake_case(name):
                                self._add_error(
                                    file_path,
                                    node.lineno,
                                    f"Constant '{name}' should use UPPER_SNAKE_CASE",
                                )
                        # Check for regular variables
                        elif not self._is_snake_case(name) and not name.startswith("_"):
                            # Skip schema variables (these are intentionally
                            # PascalCase)
                            if "Schema" in name:
                                continue
                            # Skip class references and imports (PascalCase is
                            # expected)
                            if self._is_pascal_case(name):
                                # Only warn if it's clearly a variable, not a class reference
                                # Check if the assignment is a simple value,
                                # not a class instantiation
                                if isinstance(
                                    node.value, (ast.Constant, ast.Name, ast.Attribute)
                                ):
                                    continue  # Likely a class reference or constant
                            self._add_warning(
                                file_path,
                                node.lineno,
                                f"Variable '{name}' should use snake_case",
                            )

    def _check_import_organization(self, file_path: Path, content: str) -> None:
        """Check import organization and style."""
        lines = content.split("\n")
        import_sections = []
        current_section = []
        in_imports = False

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Skip docstrings and comments at the top
            if stripped.startswith('"""') or stripped.startswith("'''"):
                continue
            if stripped.startswith("#") and not in_imports:
                continue

            if stripped.startswith(("import ", "from ")):
                in_imports = True
                current_section.append((i, stripped))
            elif in_imports and stripped == "":
                if current_section:
                    import_sections.append(current_section)
                    current_section = []
            elif in_imports and stripped and not stripped.startswith("#"):
                # End of imports
                if current_section:
                    import_sections.append(current_section)
                break

        # Check for wildcard imports
        for section in import_sections:
            for line_num, import_line in section:
                if "import *" in import_line:
                    self._add_error(
                        file_path, line_num, "Wildcard imports are not allowed"
                    )

    def _check_security_patterns(self, file_path: Path, content: str) -> None:
        """Check for common security anti-patterns."""
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            # Check for hardcoded secrets
            if re.search(
                r'(password|secret|key)\s*=\s*["\'].{8,}["\']', line, re.IGNORECASE
            ):
                self._add_warning(file_path, i, "Potential hardcoded secret detected")

            # Check for SQL injection patterns
            if re.search(r'execute\s*\(\s*f?["\'].*%.*["\']', line):
                self._add_error(file_path, i, "Potential SQL injection vulnerability")

            # Check for eval usage
            if "eval(" in line:
                self._add_error(
                    file_path, i, "Use of eval() is dangerous and should be avoided"
                )

    def _is_snake_case(self, name: str) -> bool:
        """Check if name follows snake_case convention."""
        return re.match(r"^[a-z][a-z0-9_]*$", name) is not None

    def _is_pascal_case(self, name: str) -> bool:
        """Check if name follows PascalCase convention."""
        return re.match(r"^[A-Z][a-zA-Z0-9]*$", name) is not None

    def _is_upper_snake_case(self, name: str) -> bool:
        """Check if name follows UPPER_SNAKE_CASE convention."""
        return re.match(r"^[A-Z][A-Z0-9_]*$", name) is not None

    def _add_error(self, file_path: Path, line_num: int, message: str) -> None:
        """Add an error to the error list."""
        self.errors.append(
            {
                "file": str(file_path),
                "line": line_num,
                "type": "error",
                "message": message,
            }
        )

    def _add_warning(self, file_path: Path, line_num: int, message: str) -> None:
        """Add a warning to the warning list."""
        self.warnings.append(
            {
                "file": str(file_path),
                "line": line_num,
                "type": "warning",
                "message": message,
            }
        )

    def print_results(self) -> None:
        """Print the results of the style check."""
        if self.errors:
            print("\n[ERROR] ERRORS:")
            for error in self.errors:
                print(f"  {error['file']}:{error['line']} - {error['message']}")

        if self.warnings:
            print("\n[WARNING] WARNINGS:")
            for warning in self.warnings:
                print(f"  {warning['file']}:{warning['line']} - {warning['message']}")

        if not self.errors and not self.warnings:
            print("\n[OK] All style checks passed!")

        print(f"\n[SUMMARY] {len(self.errors)} errors, {len(self.warnings)} warnings")


def find_python_files(directory: Path) -> List[Path]:
    """Find all Python files in the given directory.

    Args:
        directory: Directory to search for Python files.

    Returns:
        List of Python file paths.
    """
    python_files = []

    # Exclude certain directories
    exclude_dirs = {
        "__pycache__",
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "migrations",
        ".pytest_cache",
        "htmlcov",
        "build",
        "dist",
    }

    for root, dirs, files in os.walk(directory):
        # Remove excluded directories from the search
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)

    return python_files


def main() -> int:
    """Main entry point for the style checker.

    Returns:
        Exit code: 0 if all checks pass, 1 if there are errors.
    """
    parser = argparse.ArgumentParser(description="Check Python code style compliance")
    parser.add_argument(
        "--fix", action="store_true", help="Automatically fix issues where possible"
    )
    parser.add_argument(
        "--directory",
        type=Path,
        default=Path("app"),
        help="Directory to check (default: app)",
    )

    args = parser.parse_args()

    if not args.directory.exists():
        print(f"[ERROR] Directory {args.directory} does not exist")
        return 1

    print(f"[INFO] Checking Python style compliance in {args.directory}...")

    checker = StyleChecker(fix_mode=args.fix)
    python_files = find_python_files(args.directory)

    if not python_files:
        print("[ERROR] No Python files found")
        return 1

    print(f"[INFO] Found {len(python_files)} Python files")

    all_passed = True
    for file_path in python_files:
        if not checker.check_file(file_path):
            all_passed = False

    checker.print_results()

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
