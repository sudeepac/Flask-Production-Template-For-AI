#!/usr/bin/env python3
"""Test runner script for Flask Production Template for AI application.

This script provides a convenient way to run different types of tests
with various configurations and options.
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd, cwd=None, capture_output=False):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")

    try:
        if capture_output:
            result = subprocess.run(
                cmd, cwd=cwd, capture_output=True, text=True, check=True
            )
            return result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, cwd=cwd, check=True)
            return None, None
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        if capture_output and e.stderr:
            print(f"Error output: {e.stderr}")
        return None, e.stderr if capture_output else None


def setup_test_environment():
    """Setup test environment and dependencies."""
    print("Setting up test environment...")

    # Install test dependencies
    test_deps = [
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "pytest-mock>=3.10.0",
        "pytest-xdist>=3.0.0",
        "pytest-benchmark>=4.0.0",
        "pytest-html>=3.1.0",
        "pytest-json-report>=1.5.0",
        "coverage>=7.0.0",
        "factory-boy>=3.2.0",
        "faker>=18.0.0",
        "responses>=0.23.0",
        "freezegun>=1.2.0",
        "psutil>=5.9.0",
    ]

    for dep in test_deps:
        cmd = [sys.executable, "-m", "pip", "install", dep]
        stdout, stderr = run_command(cmd, capture_output=True)
        if stderr:
            print(f"Warning: Failed to install {dep}")

    print("Test environment setup complete.")


def run_unit_tests(args):
    """Run unit tests."""
    print("\n" + "=" * 50)
    print("RUNNING UNIT TESTS")
    print("=" * 50)

    cmd = [sys.executable, "-m", "pytest", "tests/unit/", "-v", "--tb=short"]

    if args.coverage:
        cmd.extend(["--cov=app", "--cov-report=term-missing"])

    if args.parallel:
        cmd.extend(["-n", "auto"])

    if args.markers:
        cmd.extend(["-m", args.markers])

    run_command(cmd)


def run_integration_tests(args):
    """Run integration tests."""
    print("\n" + "=" * 50)
    print("RUNNING INTEGRATION TESTS")
    print("=" * 50)

    cmd = [sys.executable, "-m", "pytest", "tests/integration/", "-v", "--tb=short"]

    if args.coverage:
        cmd.extend(["--cov=app", "--cov-report=term-missing", "--cov-append"])

    if args.parallel:
        cmd.extend(["-n", "auto"])

    if args.markers:
        cmd.extend(["-m", args.markers])

    run_command(cmd)


def run_api_tests(args):
    """Run API tests."""
    print("\n" + "=" * 50)
    print("RUNNING API TESTS")
    print("=" * 50)

    cmd = [sys.executable, "-m", "pytest", "tests/api/", "-v", "--tb=short"]

    if args.coverage:
        cmd.extend(["--cov=app", "--cov-report=term-missing", "--cov-append"])

    if args.parallel:
        cmd.extend(["-n", "auto"])

    if args.markers:
        cmd.extend(["-m", args.markers])

    run_command(cmd)


def run_ml_tests(args):
    """Run ML tests."""
    print("\n" + "=" * 50)
    print("RUNNING ML TESTS")
    print("=" * 50)

    cmd = [sys.executable, "-m", "pytest", "tests/ml/", "-v", "--tb=short"]

    if args.coverage:
        cmd.extend(["--cov=app", "--cov-report=term-missing", "--cov-append"])

    if args.parallel:
        cmd.extend(["-n", "auto"])

    if args.markers:
        cmd.extend(["-m", args.markers])

    run_command(cmd)


def run_performance_tests(args):
    """Run performance tests."""
    print("\n" + "=" * 50)
    print("RUNNING PERFORMANCE TESTS")
    print("=" * 50)

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/performance/",
        "-v",
        "--tb=short",
        "-m",
        "performance",
    ]

    if args.benchmark:
        cmd.extend(["--benchmark-only", "--benchmark-sort=mean"])

    if args.markers:
        cmd.extend(["-m", f"performance and {args.markers}"])

    run_command(cmd)


def run_smoke_tests(args):
    """Run smoke tests."""
    print("\n" + "=" * 50)
    print("RUNNING SMOKE TESTS")
    print("=" * 50)

    cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-m", "smoke"]

    if args.coverage:
        cmd.extend(["--cov=app", "--cov-report=term-missing"])

    run_command(cmd)


def run_all_tests(args):
    """Run all tests."""
    print("\n" + "=" * 50)
    print("RUNNING ALL TESTS")
    print("=" * 50)

    start_time = time.time()

    cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"]

    if args.coverage:
        cmd.extend(
            [
                "--cov=app",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov",
                "--cov-report=xml:coverage.xml",
            ]
        )

    if args.parallel:
        cmd.extend(["-n", "auto"])

    if args.markers:
        cmd.extend(["-m", args.markers])

    if args.html_report:
        cmd.extend(["--html=reports/test_report.html", "--self-contained-html"])

    if args.json_report:
        cmd.extend(["--json-report", "--json-report-file=reports/test_report.json"])

    run_command(cmd)

    end_time = time.time()
    duration = end_time - start_time
    print(f"\nAll tests completed in {duration:.2f} seconds")


def run_linting(args):
    """Run code linting and formatting checks."""
    print("\n" + "=" * 50)
    print("RUNNING CODE QUALITY CHECKS")
    print("=" * 50)

    # Run flake8
    print("\nRunning flake8...")
    cmd = [sys.executable, "-m", "flake8", "app/", "tests/"]
    run_command(cmd)

    # Run black check
    print("\nChecking code formatting with black...")
    cmd = [sys.executable, "-m", "black", "--check", "app/", "tests/"]
    run_command(cmd)

    # Run isort check
    print("\nChecking import sorting with isort...")
    cmd = [sys.executable, "-m", "isort", "--check-only", "app/", "tests/"]
    run_command(cmd)

    # Run mypy
    print("\nRunning type checking with mypy...")
    cmd = [sys.executable, "-m", "mypy", "app/"]
    run_command(cmd)


def run_security_checks(args):
    """Run security checks."""
    print("\n" + "=" * 50)
    print("RUNNING SECURITY CHECKS")
    print("=" * 50)

    # Run bandit
    print("\nRunning bandit security checks...")
    cmd = [
        sys.executable,
        "-m",
        "bandit",
        "-r",
        "app/",
        "-f",
        "json",
        "-o",
        "reports/bandit_report.json",
    ]
    run_command(cmd)

    # Run safety
    print("\nChecking dependencies for known vulnerabilities...")
    cmd = [
        sys.executable,
        "-m",
        "safety",
        "check",
        "--json",
        "--output",
        "reports/safety_report.json",
    ]
    run_command(cmd)


def generate_test_report(args):
    """Generate comprehensive test report."""
    print("\n" + "=" * 50)
    print("GENERATING TEST REPORT")
    print("=" * 50)

    # Create reports directory
    os.makedirs("reports", exist_ok=True)

    # Run tests with comprehensive reporting
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/",
        "--cov=app",
        "--cov-report=html:reports/coverage",
        "--cov-report=xml:reports/coverage.xml",
        "--cov-report=term-missing",
        "--html=reports/test_report.html",
        "--self-contained-html",
        "--json-report",
        "--json-report-file=reports/test_report.json",
        "--junitxml=reports/junit.xml",
        "-v",
    ]

    if args.parallel:
        cmd.extend(["-n", "auto"])

    run_command(cmd)

    print("\nTest reports generated in 'reports/' directory:")
    print("- HTML report: reports/test_report.html")
    print("- Coverage report: reports/coverage/index.html")
    print("- JSON report: reports/test_report.json")
    print("- JUnit XML: reports/junit.xml")
    print("- Coverage XML: reports/coverage.xml")


def clean_test_artifacts():
    """Clean test artifacts and cache files."""
    print("\nCleaning test artifacts...")

    import shutil

    # Directories to clean
    dirs_to_clean = [
        ".pytest_cache",
        "__pycache__",
        ".coverage",
        "htmlcov",
        "reports",
        ".mypy_cache",
    ]

    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            if os.path.isfile(dir_name):
                os.remove(dir_name)
                print(f"Removed file: {dir_name}")
            else:
                shutil.rmtree(dir_name)
                print(f"Removed directory: {dir_name}")

    # Find and remove __pycache__ directories recursively
    for root, dirs, files in os.walk("."):
        for dir_name in dirs[:]:
            if dir_name == "__pycache__":
                cache_path = os.path.join(root, dir_name)
                shutil.rmtree(cache_path)
                print(f"Removed cache: {cache_path}")
                dirs.remove(dir_name)

    print("Test artifacts cleaned.")


def main():
    """Main function to parse arguments and run tests."""
    parser = argparse.ArgumentParser(
        description="Test runner for Flask Production Template for AI application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --all --coverage          # Run all tests with coverage
  python run_tests.py --unit --parallel         # Run unit tests in parallel
  python run_tests.py --api --markers "not slow" # Run API tests excluding slow tests
  python run_tests.py --performance --benchmark # Run performance tests with benchmarking
  python run_tests.py --smoke                   # Run smoke tests only
  python run_tests.py --lint --security         # Run code quality and security checks
  python run_tests.py --report                  # Generate comprehensive test report
  python run_tests.py --clean                   # Clean test artifacts
        """,
    )

    # Test type arguments
    test_group = parser.add_argument_group("Test Types")
    test_group.add_argument("--all", action="store_true", help="Run all tests")
    test_group.add_argument("--unit", action="store_true", help="Run unit tests")
    test_group.add_argument(
        "--integration", action="store_true", help="Run integration tests"
    )
    test_group.add_argument("--api", action="store_true", help="Run API tests")
    test_group.add_argument("--ml", action="store_true", help="Run ML tests")
    test_group.add_argument(
        "--performance", action="store_true", help="Run performance tests"
    )
    test_group.add_argument("--smoke", action="store_true", help="Run smoke tests")

    # Quality checks
    quality_group = parser.add_argument_group("Quality Checks")
    quality_group.add_argument(
        "--lint", action="store_true", help="Run linting and formatting checks"
    )
    quality_group.add_argument(
        "--security", action="store_true", help="Run security checks"
    )

    # Options
    options_group = parser.add_argument_group("Options")
    options_group.add_argument(
        "--coverage", action="store_true", help="Generate coverage report"
    )
    options_group.add_argument(
        "--parallel", action="store_true", help="Run tests in parallel"
    )
    options_group.add_argument(
        "--benchmark", action="store_true", help="Run benchmark tests"
    )
    options_group.add_argument(
        "--html-report", action="store_true", help="Generate HTML test report"
    )
    options_group.add_argument(
        "--json-report", action="store_true", help="Generate JSON test report"
    )
    options_group.add_argument(
        "--markers", type=str, help="Pytest markers to filter tests"
    )

    # Utility commands
    utility_group = parser.add_argument_group("Utilities")
    utility_group.add_argument(
        "--setup", action="store_true", help="Setup test environment"
    )
    utility_group.add_argument(
        "--report", action="store_true", help="Generate comprehensive test report"
    )
    utility_group.add_argument(
        "--clean", action="store_true", help="Clean test artifacts"
    )

    args = parser.parse_args()

    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return

    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # Handle utility commands first
    if args.setup:
        setup_test_environment()
        return

    if args.clean:
        clean_test_artifacts()
        return

    if args.report:
        generate_test_report(args)
        return

    # Create reports directory
    os.makedirs("reports", exist_ok=True)

    # Run quality checks
    if args.lint:
        run_linting(args)

    if args.security:
        run_security_checks(args)

    # Run tests
    if args.all:
        run_all_tests(args)
    elif args.unit:
        run_unit_tests(args)
    elif args.integration:
        run_integration_tests(args)
    elif args.api:
        run_api_tests(args)
    elif args.ml:
        run_ml_tests(args)
    elif args.performance:
        run_performance_tests(args)
    elif args.smoke:
        run_smoke_tests(args)
    else:
        print("No test type specified. Use --help for options.")
        parser.print_help()


if __name__ == "__main__":
    main()
