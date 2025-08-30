#!/usr/bin/env python3
"""
Development Environment Setup Script

This script automatically sets up the development environment with all necessary
code quality tools and pre-commit hooks to ensure consistent code standards.

Usage:
    python scripts/setup_dev_environment.py
    python scripts/setup_dev_environment.py --force  # Force reinstall
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List


class DevEnvironmentSetup:
    """Development environment setup manager."""

    def __init__(self, force: bool = False):
        """Initialize the setup manager.

        Args:
            force: Whether to force reinstall existing tools.
        """
        self.force = force
        self.project_root = Path(__file__).parent.parent
        self.errors: List[str] = []

    def run_command(self, command: List[str], description: str) -> bool:
        """Run a command and handle errors.

        Args:
            command: Command to run as list of strings.
            description: Description of what the command does.

        Returns:
            True if command succeeded, False otherwise.
        """
        print(f"\n🔧 {description}...")
        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            print(f"✅ {description} completed successfully")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            error_msg = (
                f"❌ {description} failed: {e.stderr.strip() if e.stderr else str(e)}"
            )
            print(error_msg)
            self.errors.append(error_msg)
            return False
        except FileNotFoundError:
            error_msg = f"❌ {description} failed: Command not found"
            print(error_msg)
            self.errors.append(error_msg)
            return False

    def check_python_version(self) -> bool:
        """Check if Python version is compatible."""
        print("🐍 Checking Python version...")
        if sys.version_info < (3, 9):
            print("❌ Python 3.9+ is required")
            return False
        print(f"✅ Python {sys.version.split()[0]} is compatible")
        return True

    def install_pre_commit(self) -> bool:
        """Install pre-commit if not already installed."""
        # Check if pre-commit is already installed
        try:
            result = subprocess.run(
                ["pre-commit", "--version"], capture_output=True, text=True, check=True
            )
            if not self.force:
                print(f"✅ pre-commit already installed: {result.stdout.strip()}")
                return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        return self.run_command(
            [sys.executable, "-m", "pip", "install", "pre-commit"],
            "Installing pre-commit",
        )

    def setup_pre_commit_hooks(self) -> bool:
        """Install and setup pre-commit hooks."""
        success = True

        # Install pre-commit hooks
        if not self.run_command(
            ["pre-commit", "install"], "Installing pre-commit hooks"
        ):
            success = False

        # Install commit-msg hook for conventional commits
        if not self.run_command(
            ["pre-commit", "install", "--hook-type", "commit-msg"],
            "Installing commit-msg hooks",
        ):
            success = False

        # Install pre-push hooks
        if not self.run_command(
            ["pre-commit", "install", "--hook-type", "pre-push"],
            "Installing pre-push hooks",
        ):
            success = False

        return success

    def install_development_dependencies(self) -> bool:
        """Install development dependencies."""
        return self.run_command(
            [sys.executable, "-m", "pip", "install", "-r", "requirements-optional.txt"],
            "Installing development dependencies",
        )

    def run_initial_pre_commit(self) -> bool:
        """Run pre-commit on all files to ensure everything is set up correctly."""
        print("\n🔍 Running initial pre-commit check on all files...")
        print("   This may take a few minutes on first run...")

        return self.run_command(
            ["pre-commit", "run", "--all-files"], "Running pre-commit on all files"
        )

    def create_git_hooks_backup(self) -> bool:
        """Create backup of existing git hooks."""
        git_hooks_dir = self.project_root / ".git" / "hooks"
        if not git_hooks_dir.exists():
            return True

        backup_dir = self.project_root / ".git" / "hooks.backup"
        if backup_dir.exists() and not self.force:
            print("✅ Git hooks backup already exists")
            return True

        try:
            import shutil

            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            shutil.copytree(git_hooks_dir, backup_dir)
            print("✅ Created backup of existing git hooks")
            return True
        except Exception as e:
            print(f"⚠️  Warning: Could not backup git hooks: {e}")
            return True  # Non-critical error

    def validate_setup(self) -> bool:
        """Validate that the setup was successful."""
        print("\n🔍 Validating setup...")

        # Check if pre-commit is working
        try:
            subprocess.run(
                ["pre-commit", "--version"], capture_output=True, text=True, check=True
            )
            print("✅ pre-commit is working")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ pre-commit validation failed")
            return False

        # Check if git hooks are installed
        pre_commit_hook = self.project_root / ".git" / "hooks" / "pre-commit"
        if pre_commit_hook.exists():
            print("✅ Git pre-commit hook is installed")
        else:
            print("❌ Git pre-commit hook is not installed")
            return False

        return True

    def run_setup(self) -> bool:
        """Run the complete setup process."""
        print("🚀 Setting up development environment...")
        print(f"   Project root: {self.project_root}")
        print(f"   Force reinstall: {self.force}")

        steps = [
            ("Check Python version", self.check_python_version),
            ("Create git hooks backup", self.create_git_hooks_backup),
            ("Install development dependencies", self.install_development_dependencies),
            ("Install pre-commit", self.install_pre_commit),
            ("Setup pre-commit hooks", self.setup_pre_commit_hooks),
            ("Run initial pre-commit check", self.run_initial_pre_commit),
            ("Validate setup", self.validate_setup),
        ]

        for step_name, step_func in steps:
            if not step_func():
                print(f"\n❌ Setup failed at step: {step_name}")
                return False

        print("\n🎉 Development environment setup completed successfully!")
        print("\n📋 Next steps:")
        print("   1. Make a test commit to verify pre-commit hooks")
        print("   2. Run 'pre-commit run --all-files' to check all files")

        if self.errors:
            print("\n⚠️  Warnings encountered during setup:")
            for error in self.errors:
                print(f"   {error}")

        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Setup development environment with code quality tools"
    )
    parser.add_argument(
        "--force", action="store_true", help="Force reinstall of existing tools"
    )

    args = parser.parse_args()

    setup = DevEnvironmentSetup(force=args.force)
    success = setup.run_setup()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
