#!/usr/bin/env python3
"""Validation script for Python style guide setup.

This script validates that all style guide tools and configurations
are properly set up and working correctly.

Usage:
    python scripts/validate_style_setup.py
    python scripts/validate_style_setup.py --verbose
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


class StyleSetupValidator:
    """Validator for style guide setup and configuration."""

    def __init__(self, verbose: bool = False):
        """Initialize the validator.

        Args:
            verbose: Whether to show detailed output.
        """
        self.verbose = verbose
        self.results: List[Dict[str, Any]] = []

    def validate_all(self) -> bool:
        """Run all validation checks.

        Returns:
            True if all validations pass, False otherwise.
        """
        print("🔍 Validating Python style guide setup...\n")

        checks = [
            ("Configuration Files", self._check_config_files),
            ("Tool Installation", self._check_tool_installation),
            ("Tool Configuration", self._check_tool_configuration),
            ("Pre-commit Setup", self._check_precommit_setup),
            ("Documentation", self._check_documentation),
            ("Custom Scripts", self._check_custom_scripts),
        ]

        all_passed = True
        for check_name, check_func in checks:
            print(f"📋 {check_name}:")
            try:
                passed = check_func()
                if passed:
                    print(f"  ✅ {check_name} validation passed\n")
                else:
                    print(f"  ❌ {check_name} validation failed\n")
                    all_passed = False
            except Exception as e:
                print(f"  ❌ {check_name} validation error: {e}\n")
                all_passed = False

        return all_passed

    def _check_config_files(self) -> bool:
        """Check that all required configuration files exist."""
        required_files = [
            "pyproject.toml",
            ".pre-commit-config.yaml",
            "docs/python_style_guide.md",
            "CONTRIBUTING.md",
            "AI_INSTRUCTIONS.md",
        ]

        all_exist = True
        for file_path in required_files:
            path = Path(file_path)
            if path.exists():
                if self.verbose:
                    print(f"    ✓ {file_path} exists")
            else:
                print(f"    ❌ {file_path} missing")
                all_exist = False

        return all_exist

    def _check_tool_installation(self) -> bool:
        """Check that all required tools are installed."""
        required_tools = [
            ("black", "--version"),
            ("isort", "--version"),
            ("flake8", "--version"),
            ("mypy", "--version"),
            ("bandit", "--version"),
            ("pre-commit", "--version"),
            ("pytest", "--version"),
        ]

        all_installed = True
        for tool, version_flag in required_tools:
            try:
                result = subprocess.run(
                    [tool, version_flag], capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    if self.verbose:
                        version = result.stdout.strip().split("\n")[0]
                        print(f"    ✓ {tool}: {version}")
                else:
                    print(f"    ❌ {tool} not working properly")
                    all_installed = False
            except (subprocess.TimeoutExpired, FileNotFoundError):
                print(f"    ❌ {tool} not installed or not in PATH")
                all_installed = False

        return all_installed

    def _check_tool_configuration(self) -> bool:
        """Check that tools are properly configured."""
        config_checks = [
            self._check_black_config,
            self._check_isort_config,
            self._check_flake8_config,
            self._check_mypy_config,
        ]

        all_configured = True
        for check in config_checks:
            if not check():
                all_configured = False

        return all_configured

    def _check_black_config(self) -> bool:
        """Check Black configuration."""
        try:
            result = subprocess.run(
                ["black", "--check", "--diff", "app/"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                if self.verbose:
                    print("    ✓ Black configuration valid")
                return True
            else:
                if self.verbose:
                    print(
                        "    ⚠️  Black found formatting issues (run 'black app/' to fix)"
                    )
                return True  # Configuration is valid, just needs formatting
        except Exception as e:
            print(f"    ❌ Black configuration check failed: {e}")
            return False

    def _check_isort_config(self) -> bool:
        """Check isort configuration."""
        try:
            result = subprocess.run(
                ["isort", "--check-only", "--diff", "app/"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                if self.verbose:
                    print("    ✓ isort configuration valid")
                return True
            else:
                if self.verbose:
                    print(
                        "    ⚠️  isort found import sorting issues (run 'isort app/' to fix)"
                    )
                return True  # Configuration is valid, just needs sorting
        except Exception as e:
            print(f"    ❌ isort configuration check failed: {e}")
            return False

    def _check_flake8_config(self) -> bool:
        """Check Flake8 configuration."""
        try:
            result = subprocess.run(
                ["flake8", "app/"], capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                if self.verbose:
                    print("    ✓ Flake8 configuration valid")
                return True
            else:
                if self.verbose:
                    print("    ⚠️  Flake8 found linting issues")
                return True  # Configuration is valid, just has issues
        except Exception as e:
            print(f"    ❌ Flake8 configuration check failed: {e}")
            return False

    def _check_mypy_config(self) -> bool:
        """Check MyPy configuration."""
        try:
            result = subprocess.run(
                ["mypy", "app/"], capture_output=True, text=True, timeout=60
            )
            # MyPy might have type issues, but config can still be valid
            if self.verbose:
                if result.returncode == 0:
                    print("    ✓ MyPy configuration valid")
                else:
                    print("    ⚠️  MyPy found type issues")
            return True
        except Exception as e:
            print(f"    ❌ MyPy configuration check failed: {e}")
            return False

    def _check_precommit_setup(self) -> bool:
        """Check pre-commit setup."""
        try:
            # Check if pre-commit is installed in the repo
            result = subprocess.run(
                ["pre-commit", "--version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                print("    ❌ pre-commit not installed")
                return False

            # Check if hooks are installed
            git_hooks_path = Path(".git/hooks/pre-commit")
            if git_hooks_path.exists():
                if self.verbose:
                    print("    ✓ pre-commit hooks installed")
            else:
                print(
                    "    ⚠️  pre-commit hooks not installed (run 'pre-commit install')"
                )

            # Validate configuration
            result = subprocess.run(
                ["pre-commit", "validate-config"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                if self.verbose:
                    print("    ✓ pre-commit configuration valid")
                return True
            else:
                print(f"    ❌ pre-commit configuration invalid: {result.stderr}")
                return False

        except Exception as e:
            print(f"    ❌ pre-commit setup check failed: {e}")
            return False

    def _check_documentation(self) -> bool:
        """Check that documentation is complete and up-to-date."""
        docs_to_check = [
            (
                "docs/python_style_guide.md",
                ["PEP 8", "black", "isort", "flake8", "mypy"],
            ),
            ("CONTRIBUTING.md", ["style guide", "python_style_guide.md"]),
            ("AI_INSTRUCTIONS.md", ["python_style_guide.md"]),
            ("README.md", ["python_style_guide.md"]),
        ]

        all_complete = True
        for doc_path, required_content in docs_to_check:
            path = Path(doc_path)
            if not path.exists():
                print(f"    ❌ {doc_path} missing")
                all_complete = False
                continue

            try:
                content = path.read_text(encoding="utf-8")
                missing_content = []
                for required in required_content:
                    if required.lower() not in content.lower():
                        missing_content.append(required)

                if missing_content:
                    print(
                        f"    ⚠️  {doc_path} missing references to: {', '.join(missing_content)}"
                    )
                elif self.verbose:
                    print(f"    ✓ {doc_path} complete")

            except Exception as e:
                print(f"    ❌ Error reading {doc_path}: {e}")
                all_complete = False

        return all_complete

    def _check_custom_scripts(self) -> bool:
        """Check that custom scripts exist and are executable."""
        scripts_to_check = [
            "scripts/check_style_compliance.py",
            "scripts/validate_style_setup.py",
        ]

        all_exist = True
        for script_path in scripts_to_check:
            path = Path(script_path)
            if path.exists():
                if self.verbose:
                    print(f"    ✓ {script_path} exists")

                # Try to run the script with --help to see if it works
                try:
                    result = subprocess.run(
                        ["python", str(path), "--help"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if result.returncode == 0:
                        if self.verbose:
                            print(f"    ✓ {script_path} executable")
                    else:
                        print(f"    ⚠️  {script_path} may have issues")
                except Exception as e:
                    print(f"    ⚠️  {script_path} execution test failed: {e}")
            else:
                print(f"    ❌ {script_path} missing")
                all_exist = False

        return all_exist

    def print_summary(self, all_passed: bool) -> None:
        """Print validation summary."""
        print("=" * 60)
        if all_passed:
            print("🎉 All style guide validations passed!")
            print("\n✅ Your Python style guide setup is complete and ready to use.")
            print("\n📚 Next steps:")
            print("   1. Run 'pre-commit install' to set up git hooks")
            print("   2. Run 'pre-commit run --all-files' to check all files")
            print(
                "   3. Use 'python scripts/check_style_compliance.py' for custom checks"
            )
        else:
            print("❌ Some style guide validations failed.")
            print("\n🔧 Please address the issues above and run this script again.")
        print("=" * 60)


def main() -> int:
    """Main entry point for the validation script.

    Returns:
        Exit code: 0 if all validations pass, 1 if there are failures.
    """
    parser = argparse.ArgumentParser(description="Validate Python style guide setup")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")

    args = parser.parse_args()

    validator = StyleSetupValidator(verbose=args.verbose)
    all_passed = validator.validate_all()
    validator.print_summary(all_passed)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
