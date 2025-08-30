#!/usr/bin/env python3
"""
Style Issues Fixer

This script automatically fixes common Python style issues found in the codebase.
It addresses naming conventions, missing docstrings, and other style violations.

Usage:
    python scripts/fix_style_issues.py [--directory DIR] [--dry-run]
"""

import argparse
import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Set


class StyleFixer:
    """Fixes common Python style issues."""

    def __init__(self, directory: str, dry_run: bool = False):
        self.directory = Path(directory)
        self.dry_run = dry_run
        self.fixes_applied = 0
        self.files_modified = 0

    def print_info(self, message: str) -> None:
        """Print info message."""
        print(f"[INFO] {message}")

    def print_success(self, message: str) -> None:
        """Print success message."""
        print(f"[OK] {message}")

    def print_warning(self, message: str) -> None:
        """Print warning message."""
        print(f"[WARNING] {message}")

    def get_python_files(self) -> List[Path]:
        """Get all Python files in the directory."""
        python_files = []
        for root, dirs, files in os.walk(self.directory):
            # Skip common directories that shouldn't be modified
            dirs[:] = [
                d
                for d in dirs
                if d not in {"__pycache__", ".git", "venv", ".venv", "node_modules"}
            ]

            for file in files:
                if file.endswith(".py"):
                    python_files.append(Path(root) / file)
        return python_files

    def fix_snake_case_functions(self, content: str, filepath: Path) -> str:
        """Fix function names that should use snake_case."""
        lines = content.split("\n")
        modified = False

        for i, line in enumerate(lines):
            # Skip __init__, __enter__, __exit__ and other dunder methods
            if re.search(r"def __\w+__\(", line):
                continue

            # Look for function definitions with camelCase or PascalCase
            match = re.search(r"def ([a-z][a-zA-Z0-9]*[A-Z][a-zA-Z0-9]*)\(", line)
            if match:
                old_name = match.group(1)
                # Convert to snake_case
                new_name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", old_name).lower()

                if old_name != new_name:
                    lines[i] = line.replace(f"def {old_name}(", f"def {new_name}(")
                    self.print_info(
                        f"Fixed function name: {old_name} -> {new_name} in {filepath}"
                    )
                    modified = True
                    self.fixes_applied += 1

        return "\n".join(lines) if modified else content

    def add_missing_docstrings(self, content: str, filepath: Path) -> str:
        """Add basic docstrings to functions and classes missing them."""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            self.print_warning(f"Could not parse {filepath} - skipping docstring fixes")
            return content

        lines = content.split("\n")
        modifications = []

        class DocstringChecker(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                # Skip private functions, test functions, and dunder methods
                if (
                    node.name.startswith("_")
                    or node.name.startswith("test_")
                    or (node.name.startswith("__") and node.name.endswith("__"))
                ):
                    return

                # Skip simple decorator functions (usually just return a function)
                if (
                    len(node.body) == 1
                    and isinstance(node.body[0], ast.Return)
                    and isinstance(node.body[0].value, ast.Name)
                ):
                    return

                # Don't skip short functions - they might still need docstrings
                # Only skip if it's a very simple one-liner decorator
                if (
                    len(node.body) == 1
                    and isinstance(node.body[0], ast.Return)
                    and isinstance(node.body[0].value, ast.Call)
                ):
                    return

                # Check if function already has a docstring
                has_docstring = ast.get_docstring(node) is not None

                if not has_docstring:
                    self._add_docstring_modification(
                        node, lines, modifications, "function"
                    )

            def visit_ClassDef(self, node):
                # Skip private classes
                if node.name.startswith("_"):
                    return

                # Check if class already has a docstring
                has_docstring = ast.get_docstring(node) is not None

                if not has_docstring:
                    self._add_docstring_modification(
                        node, lines, modifications, "class"
                    )

            def _add_docstring_modification(
                self, node, lines, modifications, node_type
            ):
                # Find the line after the definition
                def_line = node.lineno - 1  # ast uses 1-based indexing

                # Find the end of the definition signature (could be multi-line)
                insert_line = def_line + 1
                while insert_line < len(lines) and not lines[
                    insert_line
                ].strip().endswith(":"):
                    insert_line += 1
                insert_line += 1

                # Get indentation from the definition
                def_indent = len(lines[def_line]) - len(lines[def_line].lstrip())
                docstring_indent = " " * (def_indent + 4)

                # Create a basic docstring based on type
                if node_type == "class":
                    docstring = f'{docstring_indent}"""TODO: Add class description."""'
                else:
                    docstring = (
                        f'{docstring_indent}"""TODO: Add function description."""'
                    )

                modifications.append((insert_line, docstring, node.name, node_type))

        checker = DocstringChecker()
        checker.visit(tree)

        # Apply modifications in reverse order to maintain line numbers
        for line_num, docstring, name, node_type in reversed(modifications):
            lines.insert(line_num, docstring)
            self.print_info(
                f"Added docstring to {node_type} '{name}' at line {line_num + 1} in {filepath}"
            )
            self.fixes_applied += 1

        return "\n".join(lines) if modifications else content

    def fix_variable_naming(self, content: str, filepath: Path) -> str:
        """Fix variable names that should use snake_case."""
        lines = content.split("\n")
        modified = False

        # Common patterns for schema variables that are intentionally PascalCase
        schema_patterns = [
            r"\w*Schema\s*=",
            r"from\s+\w+\s+import\s+.*Schema",
            r"class\s+\w*Schema",
        ]

        for i, line in enumerate(lines):
            # Skip lines that are defining schemas (these are intentionally PascalCase)
            if any(re.search(pattern, line) for pattern in schema_patterns):
                continue

            # Look for variable assignments with PascalCase
            match = re.search(r"^(\s*)([A-Z][a-zA-Z0-9]*[a-z][a-zA-Z0-9]*)\s*=", line)
            if match:
                indent, old_name = match.groups()
                # Convert to snake_case
                new_name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", old_name).lower()

                if old_name != new_name and "Schema" not in old_name:
                    lines[i] = line.replace(f"{old_name} =", f"{new_name} =")
                    self.print_info(
                        f"Fixed variable name: {old_name} -> {new_name} in {filepath}"
                    )
                    modified = True
                    self.fixes_applied += 1

        return "\n".join(lines) if modified else content

    def fix_file(self, filepath: Path) -> bool:
        """Fix style issues in a single file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                original_content = f.read()
        except UnicodeDecodeError:
            self.print_warning(f"Could not read {filepath} - encoding issue")
            return False

        content = original_content

        # Apply fixes
        content = self.fix_snake_case_functions(content, filepath)
        content = self.add_missing_docstrings(content, filepath)
        content = self.fix_variable_naming(content, filepath)

        # Write back if changes were made
        if content != original_content:
            if not self.dry_run:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                self.print_success(f"Fixed issues in {filepath}")
            else:
                self.print_info(f"Would fix issues in {filepath} (dry run)")

            self.files_modified += 1
            return True

        return False

    def run(self) -> None:
        """Run the style fixer on all Python files."""
        self.print_info(f"Scanning for Python files in {self.directory}...")

        python_files = self.get_python_files()
        self.print_info(f"Found {len(python_files)} Python files")

        if self.dry_run:
            self.print_info("Running in dry-run mode - no files will be modified")

        for filepath in python_files:
            self.fix_file(filepath)

        self.print_success(f"Style fixing complete!")
        self.print_success(f"Files modified: {self.files_modified}")
        self.print_success(f"Total fixes applied: {self.fixes_applied}")

        if self.dry_run:
            self.print_info("Run without --dry-run to apply the fixes")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fix common Python style issues in the codebase"
    )
    parser.add_argument(
        "--directory",
        default="app",
        help="Directory to scan for Python files (default: app)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without making changes",
    )

    args = parser.parse_args()

    fixer = StyleFixer(args.directory, args.dry_run)
    fixer.run()


if __name__ == "__main__":
    main()
