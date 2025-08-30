#!/usr/bin/env python3
"""Automated docstring generator for Python code.

This script automatically generates docstrings for functions and classes
that are missing them, following the project's documentation standards.

Usage:
    python scripts/fix_specific_docstrings.py [options]
    python scripts/fix_specific_docstrings.py --file path/to/file.py
    python scripts/fix_specific_docstrings.py --directory app/ --auto-generate

Features:
    - Generates Google-style docstrings
    - Analyzes function signatures for parameters
    - Detects return types from type hints
    - Handles async functions
    - Skips private methods and test functions
    - Preserves existing docstrings
"""

import argparse
import ast
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


class DocstringGenerator:
    """Automated docstring generator for Python files.

    This class analyzes Python AST to find functions and classes
    without docstrings and generates appropriate documentation.

    Attributes:
        file_path: Path to the Python file being processed
        content: Current content of the file
        lines: List of lines in the file
        tree: AST tree of the parsed file
        modified: Whether the file has been modified
        docstrings_added: Count of docstrings added
    """

    def __init__(self, file_path: str) -> None:
        """Initialize the docstring generator.

        Args:
            file_path: Path to the Python file to process

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file is not a Python file
            SyntaxError: If the file has syntax errors
        """
        self.file_path = Path(file_path)

        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if self.file_path.suffix != ".py":
            raise ValueError(f"Not a Python file: {file_path}")

        with open(self.file_path, "r", encoding="utf-8") as f:
            self.content = f.read()

        self.lines = self.content.splitlines()

        try:
            self.tree = ast.parse(self.content)
        except SyntaxError as e:
            raise SyntaxError(f"Syntax error in {file_path}: {e}")

        self.modified = False
        self.docstrings_added = 0

    def generate_missing_docstrings(self) -> Dict[str, int]:
        """Generate docstrings for all functions and classes missing them.

        Returns:
            Dictionary with counts of different types of docstrings added
        """
        results = {
            "functions": 0,
            "methods": 0,
            "classes": 0,
            "async_functions": 0,
            "total": 0,
        }

        # Collect all nodes that need docstrings
        nodes_to_document = []

        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not self._has_docstring(node) and self._should_document(node):
                    nodes_to_document.append(node)

        # Sort by line number (reverse order to avoid line number shifts)
        nodes_to_document.sort(key=lambda x: x.lineno, reverse=True)

        # Generate and insert docstrings
        for node in nodes_to_document:
            docstring = self._generate_docstring(node)
            if docstring:
                self._insert_docstring(node, docstring)

                if isinstance(node, ast.ClassDef):
                    results["classes"] += 1
                elif isinstance(node, ast.AsyncFunctionDef):
                    results["async_functions"] += 1
                elif isinstance(node, ast.FunctionDef):
                    if self._is_method(node):
                        results["methods"] += 1
                    else:
                        results["functions"] += 1

                results["total"] += 1
                self.docstrings_added += 1

        return results

    def _has_docstring(self, node: ast.AST) -> bool:
        """Check if a function or class has a docstring.

        Args:
            node: AST node to check

        Returns:
            True if the node has a docstring, False otherwise
        """
        if not hasattr(node, "body") or not node.body:
            return False

        first_stmt = node.body[0]
        return (
            isinstance(first_stmt, ast.Expr)
            and isinstance(first_stmt.value, (ast.Str, ast.Constant))
            and isinstance(getattr(first_stmt.value, "value", first_stmt.value.s), str)
        )

    def _should_document(self, node: ast.AST) -> bool:
        """Determine if a node should be documented.

        Args:
            node: AST node to check

        Returns:
            True if the node should be documented, False otherwise
        """
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Skip private methods (but not __init__, __str__, etc.)
            if node.name.startswith("_") and not node.name.startswith("__"):
                return False

            # Skip test functions
            if node.name.startswith("test_"):
                return False

            # Skip very short functions (likely trivial)
            if len(node.body) == 1 and isinstance(node.body[0], (ast.Return, ast.Pass)):
                return False

        elif isinstance(node, ast.ClassDef):
            # Skip private classes
            if node.name.startswith("_"):
                return False

        return True

    def _is_method(self, node: ast.FunctionDef) -> bool:
        """Check if a function is a method (inside a class).

        Args:
            node: Function node to check

        Returns:
            True if the function is a method, False otherwise
        """
        # Walk up the AST to find if this function is inside a class
        for parent in ast.walk(self.tree):
            if isinstance(parent, ast.ClassDef):
                if node in parent.body:
                    return True
        return False

    def _generate_docstring(self, node: ast.AST) -> Optional[str]:
        """Generate a docstring for a function or class.

        Args:
            node: AST node to generate docstring for

        Returns:
            Generated docstring or None if not applicable
        """
        if isinstance(node, ast.ClassDef):
            return self._generate_class_docstring(node)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return self._generate_function_docstring(node)

        return None

    def _generate_class_docstring(self, node: ast.ClassDef) -> str:
        """Generate a docstring for a class.

        Args:
            node: Class node to document

        Returns:
            Generated docstring
        """
        class_name = node.name

        # Check if it's an exception class
        is_exception = any(
            isinstance(base, ast.Name) and base.id.endswith("Exception")
            for base in node.bases
        )

        if is_exception:
            return f"""Exception raised when {class_name.lower().replace("exception", "")} operations fail.

            This exception is raised when specific error conditions are encountered
            during {class_name.lower().replace("exception", "")} processing.
            """

        # Check for common patterns
        if "model" in class_name.lower() or "Model" in class_name:
            return f"""Data model for {class_name.replace("Model", "").lower()} entities.

            This class represents the data structure and business logic
            for {class_name.replace("Model", "").lower()} objects in the application.

            Attributes:
                TODO: Add class attributes description
            """

        elif "service" in class_name.lower() or "Service" in class_name:
            return f"""Service class for {class_name.replace("Service", "").lower()} operations.

            This class provides business logic and operations for
            {class_name.replace("Service", "").lower()} functionality.

            Methods:
                TODO: Add key methods description
            """

        elif "controller" in class_name.lower() or "Controller" in class_name:
            return f"""Controller for {class_name.replace("Controller", "").lower()} endpoints.

            This class handles HTTP requests and responses for
            {class_name.replace("Controller", "").lower()} related operations.

            Routes:
                TODO: Add route descriptions
            """

        else:
            return f"""Class {class_name}.

            TODO: Add comprehensive class description.

            Attributes:
                TODO: Add class attributes description
            """

    def _generate_function_docstring(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> str:
        """Generate a docstring for a function or method.

        Args:
            node: Function node to document

        Returns:
            Generated docstring
        """
        func_name = node.name
        is_async = isinstance(node, ast.AsyncFunctionDef)
        is_method = self._is_method(node)

        # Analyze function signature
        args_info = self._analyze_function_args(node)
        return_info = self._analyze_return_type(node)

        # Generate description based on function name patterns
        description = self._generate_function_description(
            func_name, is_async, is_method
        )

        # Build docstring parts
        parts = [description]

        # Add arguments section
        if args_info:
            parts.append("")
            parts.append("Args:")
            for arg_name, arg_type, arg_desc in args_info:
                if arg_type:
                    parts.append(f"    {arg_name} ({arg_type}): {arg_desc}")
                else:
                    parts.append(f"    {arg_name}: {arg_desc}")

        # Add returns section
        if return_info:
            parts.append("")
            parts.append("Returns:")
            parts.append(f"    {return_info}")

        # Add raises section for functions that might raise exceptions
        raises_info = self._analyze_exceptions(node)
        if raises_info:
            parts.append("")
            parts.append("Raises:")
            for exc_type, exc_desc in raises_info:
                parts.append(f"    {exc_type}: {exc_desc}")

        return "\n".join(parts)

    def _analyze_function_args(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> List[Tuple[str, Optional[str], str]]:
        """Analyze function arguments and generate descriptions.

        Args:
            node: Function node to analyze

        Returns:
            List of tuples (arg_name, arg_type, description)
        """
        args_info = []

        if not hasattr(node, "args"):
            return args_info

        # Regular arguments
        for i, arg in enumerate(node.args.args):
            if arg.arg == "self" or arg.arg == "cls":
                continue

            arg_type = None
            if arg.annotation:
                arg_type = self._get_type_string(arg.annotation)

            # Generate description based on argument name
            description = self._generate_arg_description(arg.arg, arg_type)

            args_info.append((arg.arg, arg_type, description))

        # Keyword-only arguments
        for arg in node.args.kwonlyargs:
            arg_type = None
            if arg.annotation:
                arg_type = self._get_type_string(arg.annotation)

            description = self._generate_arg_description(arg.arg, arg_type)
            args_info.append((arg.arg, arg_type, description))

        return args_info

    def _analyze_return_type(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> Optional[str]:
        """Analyze function return type and generate description.

        Args:
            node: Function node to analyze

        Returns:
            Return type description or None
        """
        if node.returns:
            return_type = self._get_type_string(node.returns)
            return f"{return_type}: TODO: Add return value description"

        # Check if function has return statements
        has_return = False
        for child in ast.walk(node):
            if isinstance(child, ast.Return) and child.value is not None:
                has_return = True
                break

        if has_return:
            return "TODO: Add return value description"

        return None

    def _analyze_exceptions(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> List[Tuple[str, str]]:
        """Analyze exceptions that might be raised by the function.

        Args:
            node: Function node to analyze

        Returns:
            List of tuples (exception_type, description)
        """
        exceptions = []

        # Look for raise statements
        for child in ast.walk(node):
            if isinstance(child, ast.Raise) and child.exc:
                if isinstance(child.exc, ast.Call) and isinstance(
                    child.exc.func, ast.Name
                ):
                    exc_name = child.exc.func.id
                    exceptions.append(
                        (
                            exc_name,
                            f"When {exc_name.lower().replace('error', '').replace('exception', '')} conditions are met",
                        )
                    )
                elif isinstance(child.exc, ast.Name):
                    exc_name = child.exc.id
                    exceptions.append(
                        (
                            exc_name,
                            f"When {exc_name.lower().replace('error', '').replace('exception', '')} conditions are met",
                        )
                    )

        # Remove duplicates
        seen = set()
        unique_exceptions = []
        for exc_type, desc in exceptions:
            if exc_type not in seen:
                seen.add(exc_type)
                unique_exceptions.append((exc_type, desc))

        return unique_exceptions

    def _get_type_string(self, annotation: ast.AST) -> str:
        """Convert AST type annotation to string.

        Args:
            annotation: AST annotation node

        Returns:
            String representation of the type
        """
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        elif isinstance(annotation, ast.Attribute):
            return f"{self._get_type_string(annotation.value)}.{annotation.attr}"
        elif isinstance(annotation, ast.Subscript):
            value = self._get_type_string(annotation.value)
            slice_val = self._get_type_string(annotation.slice)
            return f"{value}[{slice_val}]"
        else:
            return "Any"

    def _generate_function_description(
        self, func_name: str, is_async: bool, is_method: bool
    ) -> str:
        """Generate a description based on function name patterns.

        Args:
            func_name: Name of the function
            is_async: Whether the function is async
            is_method: Whether the function is a method

        Returns:
            Generated description
        """
        async_prefix = "Asynchronously " if is_async else ""

        # Special method names
        if func_name == "__init__":
            return "Initialize the instance."
        elif func_name == "__str__":
            return "Return string representation of the object."
        elif func_name == "__repr__":
            return "Return detailed string representation of the object."
        elif func_name == "__len__":
            return "Return the length of the object."
        elif func_name == "__bool__":
            return "Return boolean representation of the object."

        # Common patterns
        if func_name.startswith("get_"):
            item = func_name[4:].replace("_", " ")
            return f"{async_prefix}Get {item} information."
        elif func_name.startswith("set_"):
            item = func_name[4:].replace("_", " ")
            return f"{async_prefix}Set {item} value."
        elif func_name.startswith("create_"):
            item = func_name[7:].replace("_", " ")
            return f"{async_prefix}Create a new {item}."
        elif func_name.startswith("update_"):
            item = func_name[7:].replace("_", " ")
            return f"{async_prefix}Update existing {item}."
        elif func_name.startswith("delete_"):
            item = func_name[7:].replace("_", " ")
            return f"{async_prefix}Delete {item}."
        elif func_name.startswith("find_"):
            item = func_name[5:].replace("_", " ")
            return f"{async_prefix}Find {item} based on criteria."
        elif func_name.startswith("list_"):
            item = func_name[5:].replace("_", " ")
            return f"{async_prefix}List all {item}."
        elif func_name.startswith("validate_"):
            item = func_name[9:].replace("_", " ")
            return f"{async_prefix}Validate {item} data."
        elif func_name.startswith("process_"):
            item = func_name[8:].replace("_", " ")
            return f"{async_prefix}Process {item} data."
        elif func_name.startswith("handle_"):
            item = func_name[7:].replace("_", " ")
            return f"{async_prefix}Handle {item} events."
        elif func_name.startswith("is_"):
            condition = func_name[3:].replace("_", " ")
            return f"Check if {condition}."
        elif func_name.startswith("has_"):
            item = func_name[4:].replace("_", " ")
            return f"Check if has {item}."
        elif func_name.startswith("can_"):
            action = func_name[4:].replace("_", " ")
            return f"Check if can {action}."
        elif func_name.endswith("_exists"):
            item = func_name[:-7].replace("_", " ")
            return f"Check if {item} exists."

        # Default description
        action = func_name.replace("_", " ").title()
        return f"{async_prefix}{action}."

    def _generate_arg_description(self, arg_name: str, arg_type: Optional[str]) -> str:
        """Generate description for a function argument.

        Args:
            arg_name: Name of the argument
            arg_type: Type of the argument (if available)

        Returns:
            Generated description
        """
        # Common argument patterns
        if arg_name in ["id", "user_id", "item_id"]:
            return "Unique identifier"
        elif arg_name in ["name", "username", "filename"]:
            return "Name of the entity"
        elif arg_name in ["email", "email_address"]:
            return "Email address"
        elif arg_name in ["password", "passwd"]:
            return "Password for authentication"
        elif arg_name in ["data", "payload"]:
            return "Data to be processed"
        elif arg_name in ["limit", "count"]:
            return "Maximum number of items"
        elif arg_name in ["offset", "skip"]:
            return "Number of items to skip"
        elif arg_name in ["page", "page_number"]:
            return "Page number for pagination"
        elif arg_name in ["size", "page_size"]:
            return "Number of items per page"
        elif arg_name in ["query", "search_term"]:
            return "Search query string"
        elif arg_name in ["filters", "filter_params"]:
            return "Filtering parameters"
        elif arg_name in ["options", "config"]:
            return "Configuration options"
        elif arg_name.endswith("_id"):
            entity = arg_name[:-3].replace("_", " ")
            return f"Identifier for {entity}"
        elif arg_name.endswith("_name"):
            entity = arg_name[:-5].replace("_", " ")
            return f"Name of the {entity}"
        elif arg_name.endswith("_data"):
            entity = arg_name[:-5].replace("_", " ")
            return f"Data for {entity}"
        elif arg_name.endswith("_list"):
            entity = arg_name[:-5].replace("_", " ")
            return f"List of {entity} items"

        # Default description
        return f"TODO: Add description for {arg_name}"

    def _insert_docstring(self, node: ast.AST, docstring: str) -> None:
        """Insert a docstring into the file at the appropriate location.

        Args:
            node: AST node to add docstring to
            docstring: Docstring content to insert
        """
        # Find the line after the function/class definition
        insert_line = node.lineno  # 1-based line number

        # Get indentation level
        def_line = self.lines[insert_line - 1]
        base_indent = len(def_line) - len(def_line.lstrip())
        docstring_indent = base_indent + 4

        # Format docstring
        docstring_lines = self._format_docstring(docstring, docstring_indent)

        # Insert docstring lines
        for i, doc_line in enumerate(reversed(docstring_lines)):
            self.lines.insert(insert_line + i, doc_line)

        self.modified = True

    def _format_docstring(self, docstring: str, indent: int) -> List[str]:
        """Format a docstring with proper indentation and triple quotes.

        Args:
            docstring: Raw docstring content
            indent: Number of spaces to indent

        Returns:
            List of formatted docstring lines
        """
        lines = []
        indent_str = " " * indent

        # Split docstring into lines
        docstring_lines = docstring.strip().split("\n")

        # Add opening triple quotes
        if len(docstring_lines) == 1:
            # Single line docstring
            lines.append(f'{indent_str}"""{docstring_lines[0]}"""')
        else:
            # Multi-line docstring
            lines.append(f'{indent_str}"""')

            for line in docstring_lines:
                if line.strip():
                    lines.append(f"{indent_str}{line}")
                else:
                    lines.append("")

            lines.append(f'{indent_str}"""')

        return lines

    def save_changes(self) -> bool:
        """Save the modified content back to the file.

        Returns:
            True if changes were saved, False if no changes were made
        """
        if not self.modified:
            return False

        # Create backup
        backup_path = self.file_path.with_suffix(".py.backup")

        try:
            # Create backup
            with open(self.file_path, "r", encoding="utf-8") as original:
                with open(backup_path, "w", encoding="utf-8") as backup:
                    backup.write(original.read())

            # Write modified content
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(self.lines))

            # Remove backup if successful
            backup_path.unlink()
            return True

        except Exception as e:
            # Restore from backup if it exists
            if backup_path.exists():
                with open(backup_path, "r", encoding="utf-8") as backup:
                    with open(self.file_path, "w", encoding="utf-8") as original:
                        original.write(backup.read())
                backup_path.unlink()
            raise e


def generate_docstrings_for_file(
    file_path: str, auto_generate: bool = False
) -> Dict[str, Any]:
    """Generate docstrings for a single Python file.

    Args:
        file_path: Path to the Python file
        auto_generate: Whether to automatically save changes

    Returns:
        Dictionary with generation results
    """
    try:
        generator = DocstringGenerator(file_path)
        results = generator.generate_missing_docstrings()

        if results["total"] > 0 and auto_generate:
            generator.save_changes()
            status = "generated"
        elif results["total"] > 0:
            status = "needs_docstrings"
        else:
            status = "complete"

        return {
            "file": file_path,
            "status": status,
            "docstrings_added": results["total"],
            "breakdown": results,
            "modified": generator.modified,
        }

    except Exception as e:
        return {
            "file": file_path,
            "status": "error",
            "error": str(e),
            "docstrings_added": 0,
            "breakdown": {},
            "modified": False,
        }


def generate_docstrings_for_directory(
    directory: str, auto_generate: bool = False
) -> Dict[str, Any]:
    """Generate docstrings for all Python files in a directory.

    Args:
        directory: Path to the directory
        auto_generate: Whether to automatically save changes

    Returns:
        Dictionary with overall generation results
    """
    directory_path = Path(directory)

    if not directory_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    results = []
    total_files = 0
    total_docstrings = 0

    # Find all Python files
    for py_file in directory_path.rglob("*.py"):
        # Skip certain directories
        if any(
            part in str(py_file)
            for part in ["__pycache__", ".git", "migrations", "venv"]
        ):
            continue

        total_files += 1
        result = generate_docstrings_for_file(str(py_file), auto_generate)
        results.append(result)
        total_docstrings += result["docstrings_added"]

    return {
        "directory": directory,
        "total_files": total_files,
        "total_docstrings": total_docstrings,
        "files": results,
        "timestamp": datetime.now().isoformat(),
    }


def main() -> None:
    """Main entry point for the docstring generator script."""
    parser = argparse.ArgumentParser(
        description="Automatically generate Python docstrings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/fix_specific_docstrings.py --file app/models/user.py
  python scripts/fix_specific_docstrings.py --directory app/ --auto-generate
  python scripts/fix_specific_docstrings.py --directory . --dry-run
        """,
    )

    parser.add_argument(
        "--file", type=str, help="Generate docstrings for a specific Python file"
    )

    parser.add_argument(
        "--directory",
        type=str,
        default="app",
        help="Generate docstrings for all Python files in directory (default: app)",
    )

    parser.add_argument(
        "--auto-generate",
        action="store_true",
        help="Automatically save generated docstrings (default: dry run)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what docstrings would be generated without making changes",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )

    args = parser.parse_args()

    # Determine auto-generate mode
    auto_generate = args.auto_generate and not args.dry_run

    try:
        if args.file:
            # Generate docstrings for single file
            result = generate_docstrings_for_file(args.file, auto_generate)

            print(f"File: {result['file']}")
            print(f"Status: {result['status']}")
            print(f"Docstrings added: {result['docstrings_added']}")

            if args.verbose and result["breakdown"]:
                print("\nBreakdown:")
                for doc_type, count in result["breakdown"].items():
                    if count > 0 and doc_type != "total":
                        print(f"  {doc_type}: {count}")

        else:
            # Generate docstrings for directory
            results = generate_docstrings_for_directory(args.directory, auto_generate)

            print(f"Directory: {results['directory']}")
            print(f"Files processed: {results['total_files']}")
            print(f"Total docstrings added: {results['total_docstrings']}")

            if args.verbose:
                print("\nFile details:")
                for file_result in results["files"]:
                    if file_result["docstrings_added"] > 0:
                        print(
                            f"  {file_result['file']}: {file_result['docstrings_added']} docstrings"
                        )

            if not auto_generate and results["total_docstrings"] > 0:
                print("\nRun with --auto-generate to apply changes")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
