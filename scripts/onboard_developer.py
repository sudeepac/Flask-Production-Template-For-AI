#!/usr/bin/env python3
"""
Developer Onboarding Script

This script automates the complete setup of a development environment
with all code quality tools and enforcement mechanisms.

Usage:
    python scripts/onboard_developer.py [--force] [--skip-git-config]
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


class DeveloperOnboarding:
    """Handles the complete developer onboarding process."""

    def __init__(self, force: bool = False, skip_git_config: bool = False):
        self.force = force
        self.skip_git_config = skip_git_config
        self.project_root = Path(__file__).parent.parent
        self.errors: List[str] = []

    def print_step(self, message: str) -> None:
        """Print a step message with formatting."""
        print(f"{Colors.BLUE}📋 {message}{Colors.END}")

    def print_success(self, message: str) -> None:
        """Print a success message with formatting."""
        print(f"{Colors.GREEN}✅ {message}{Colors.END}")

    def print_warning(self, message: str) -> None:
        """Print a warning message with formatting."""
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

    def print_error(self, message: str) -> None:
        """Print an error message with formatting."""
        print(f"{Colors.RED}❌ {message}{Colors.END}")
        self.errors.append(message)

    def run_command(
        self, command: List[str], cwd: Optional[Path] = None, check: bool = True
    ) -> subprocess.CompletedProcess:
        """Run a command and handle errors."""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                check=check,
            )
            return result
        except subprocess.CalledProcessError as e:
            self.print_error(f"Command failed: {' '.join(command)}")
            self.print_error(f"Error: {e.stderr}")
            if check:
                raise
            return e

    def check_python_version(self) -> bool:
        """Check if Python version meets requirements."""
        self.print_step("Checking Python version...")

        if sys.version_info < (3, 9):
            self.print_error("Python 3.9+ is required")
            return False

        self.print_success(f"Python {sys.version.split()[0]} detected")
        return True

    def check_git_installation(self) -> bool:
        """Check if Git is installed."""
        self.print_step("Checking Git installation...")

        try:
            result = self.run_command(["git", "--version"])
            self.print_success(f"Git detected: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.print_error("Git is not installed or not in PATH")
            return False

    def setup_virtual_environment(self) -> bool:
        """Set up Python virtual environment."""
        self.print_step("Setting up virtual environment...")

        venv_path = self.project_root / "venv"

        if venv_path.exists() and not self.force:
            self.print_warning(
                "Virtual environment already exists. Use --force to recreate."
            )
            return True

        if venv_path.exists() and self.force:
            self.print_step("Removing existing virtual environment...")
            import shutil

            shutil.rmtree(venv_path)

        try:
            self.run_command([sys.executable, "-m", "venv", "venv"])
            self.print_success("Virtual environment created")
            return True
        except subprocess.CalledProcessError:
            self.print_error("Failed to create virtual environment")
            return False

    def install_dependencies(self) -> bool:
        """Install project dependencies."""
        self.print_step("Installing dependencies...")

        # Determine Python executable in venv
        if os.name == "nt":  # Windows
            python_exe = self.project_root / "venv" / "Scripts" / "python.exe"
            pip_exe = self.project_root / "venv" / "Scripts" / "pip.exe"
        else:  # Unix-like
            python_exe = self.project_root / "venv" / "bin" / "python"
            pip_exe = self.project_root / "venv" / "bin" / "pip"

        try:
            # Upgrade pip
            self.run_command(
                [str(python_exe), "-m", "pip", "install", "--upgrade", "pip"]
            )

            # Install requirements
            self.run_command([str(pip_exe), "install", "-r", "requirements.txt"])

            # Install development dependencies
            dev_requirements = self.project_root / "requirements-dev.txt"
            if dev_requirements.exists():
                self.run_command(
                    [str(pip_exe), "install", "-r", "requirements-dev.txt"]
                )

            self.print_success("Dependencies installed")
            return True
        except subprocess.CalledProcessError:
            self.print_error("Failed to install dependencies")
            return False

    def setup_pre_commit_hooks(self) -> bool:
        """Set up pre-commit hooks."""
        self.print_step("Setting up pre-commit hooks...")

        try:
            # Install pre-commit
            self.run_command([sys.executable, "-m", "pip", "install", "pre-commit"])

            # Install hooks
            self.run_command(["pre-commit", "install"])
            self.run_command(["pre-commit", "install", "--hook-type", "commit-msg"])
            self.run_command(["pre-commit", "install", "--hook-type", "pre-push"])

            # Run initial check
            self.print_step("Running initial pre-commit check...")
            result = self.run_command(["pre-commit", "run", "--all-files"], check=False)

            if result.returncode == 0:
                self.print_success("Pre-commit hooks installed and validated")
            else:
                self.print_warning("Pre-commit hooks installed but some checks failed")
                self.print_warning(
                    "This is normal for first setup. Run 'pre-commit run --all-files' to fix."
                )

            return True
        except subprocess.CalledProcessError:
            self.print_error("Failed to setup pre-commit hooks")
            return False

    def configure_git_settings(self) -> bool:
        """Configure Git settings for the project."""
        if self.skip_git_config:
            self.print_step("Skipping Git configuration...")
            return True

        self.print_step("Configuring Git settings...")

        try:
            # Check if user has global Git config
            try:
                self.run_command(["git", "config", "--global", "user.name"])
                self.run_command(["git", "config", "--global", "user.email"])
                self.print_success("Git user configuration found")
            except subprocess.CalledProcessError:
                self.print_warning("No global Git user configuration found")
                self.print_warning(
                    "Please run: git config --global user.name 'Your Name'"
                )
                self.print_warning(
                    "Please run: git config --global user.email 'your.email@example.com'"
                )

            # Set project-specific Git hooks path
            self.run_command(["git", "config", "core.hooksPath", ".git/hooks"])

            # Configure Git to use the project's gitignore
            gitignore_path = self.project_root / ".gitignore"
            if gitignore_path.exists():
                self.run_command(
                    ["git", "config", "core.excludesFile", str(gitignore_path)]
                )

            self.print_success("Git settings configured")
            return True
        except subprocess.CalledProcessError:
            self.print_error("Failed to configure Git settings")
            return False

    def setup_ide_integration(self) -> bool:
        """Set up IDE integration files."""
        self.print_step("Setting up IDE integration...")

        # VS Code settings should already exist
        vscode_dir = self.project_root / ".vscode"
        if vscode_dir.exists():
            self.print_success("VS Code configuration found")
        else:
            self.print_warning("VS Code configuration not found")

        # PyCharm/IntelliJ settings
        idea_dir = self.project_root / ".idea"
        if not idea_dir.exists():
            idea_dir.mkdir(exist_ok=True)

        # Create basic PyCharm configuration
        pycharm_config = idea_dir / "inspectionProfiles" / "profiles_settings.xml"
        pycharm_config.parent.mkdir(exist_ok=True)

        if not pycharm_config.exists():
            pycharm_config.write_text(
                """
<component name="InspectionProjectProfileManager">
  <settings>
    <option name="USE_PROJECT_PROFILE" value="true" />
    <version value="1.0" />
  </settings>
</component>
"""
            )

        self.print_success("IDE integration configured")
        return True

    def run_initial_quality_check(self) -> bool:
        """Run initial code quality checks."""
        self.print_step("Running initial code quality checks...")

        try:
            # Run style compliance check
            style_script = self.project_root / "scripts" / "check_style_compliance.py"
            if style_script.exists():
                result = self.run_command(
                    [sys.executable, str(style_script)], check=False
                )
                if result.returncode == 0:
                    self.print_success("Style compliance check passed")
                else:
                    self.print_warning("Style compliance check found issues")

            # Run basic linting
            result = self.run_command(["flake8", "--version"], check=False)
            if result.returncode == 0:
                self.print_success("Code quality tools are working")
            else:
                self.print_warning(
                    "Some code quality tools may not be properly installed"
                )

            return True
        except Exception as e:
            self.print_error(f"Failed to run quality checks: {e}")
            return False

    def print_next_steps(self) -> None:
        """Print next steps for the developer."""
        print(f"\n{Colors.BOLD}🎉 Developer onboarding complete!{Colors.END}\n")

        print(f"{Colors.BLUE}Next steps:{Colors.END}")
        print("1. Activate your virtual environment:")
        if os.name == "nt":
            print(f"   {Colors.GREEN}venv\\Scripts\\activate{Colors.END}")
        else:
            print(f"   {Colors.GREEN}source venv/bin/activate{Colors.END}")

        print("\n2. Start developing with confidence:")
        print(f"   {Colors.GREEN}make dev{Colors.END} - Start development server")
        print(f"   {Colors.GREEN}make test{Colors.END} - Run tests")
        print(f"   {Colors.GREEN}make lint{Colors.END} - Check code quality")
        print(f"   {Colors.GREEN}make fix{Colors.END} - Auto-fix code issues")

        print("\n3. Your code will be automatically checked:")
        print("   • Before each commit (pre-commit hooks)")
        print("   • Before each push (pre-push hooks)")
        print("   • In CI/CD pipeline (GitHub Actions)")

        print(f"\n{Colors.YELLOW}📚 Documentation:{Colors.END}")
        print("   • README.md - Project overview")
        print("   • docs/ - Detailed documentation")
        print("   • .pre-commit-config.yaml - Code quality rules")

        if self.errors:
            print(f"\n{Colors.RED}⚠️  Some issues occurred during setup:{Colors.END}")
            for error in self.errors:
                print(f"   • {error}")
            print("\nPlease resolve these issues before proceeding.")

    def run(self) -> bool:
        """Run the complete onboarding process."""
        print(f"{Colors.BOLD}🚀 Starting Developer Onboarding{Colors.END}\n")

        steps = [
            self.check_python_version,
            self.check_git_installation,
            self.setup_virtual_environment,
            self.install_dependencies,
            self.setup_pre_commit_hooks,
            self.configure_git_settings,
            self.setup_ide_integration,
            self.run_initial_quality_check,
        ]

        success = True
        for step in steps:
            try:
                if not step():
                    success = False
                    break
            except KeyboardInterrupt:
                self.print_error("Onboarding interrupted by user")
                return False
            except Exception as e:
                self.print_error(f"Unexpected error in {step.__name__}: {e}")
                success = False
                break

        self.print_next_steps()
        return success and len(self.errors) == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Onboard a new developer with complete environment setup"
    )
    parser.add_argument(
        "--force", action="store_true", help="Force recreation of existing components"
    )
    parser.add_argument(
        "--skip-git-config", action="store_true", help="Skip Git configuration setup"
    )

    args = parser.parse_args()

    onboarding = DeveloperOnboarding(
        force=args.force, skip_git_config=args.skip_git_config
    )

    success = onboarding.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
