#!/usr/bin/env python3
"""Production Configuration Validator.

This script validates that production configurations are secure
and don't contain default development values.
"""

import os
import sys
from typing import List, Tuple


def check_secret_keys() -> List[Tuple[str, str]]:
    """Check for default secret keys that should be changed in production.

    Returns:
        List of (key_name, issue_description) tuples
    """
    issues = []

    # Default values that should not be used in production
    dangerous_defaults = {
        "SECRET_KEY": "dev-secret-key-change-in-production",
        "JWT_SECRET_KEY": "jwt-secret-key-change-in-production",
    }

    for key, dangerous_value in dangerous_defaults.items():
        current_value = os.environ.get(key)

        if not current_value:
            issues.append((key, "Environment variable not set"))
        elif current_value == dangerous_value:
            issues.append((key, f"Using dangerous default value: {dangerous_value}"))
        elif len(current_value) < 32:
            issues.append(
                (
                    key,
                    f"Secret key too short (< 32 characters): {len(current_value)} chars",
                )
            )

    return issues


def check_database_config() -> List[Tuple[str, str]]:
    """Check database configuration for production readiness.

    Returns:
        List of (setting_name, issue_description) tuples
    """
    issues = []

    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        issues.append(
            ("DATABASE_URL", "Environment variable not set - will use SQLite")
        )
    elif database_url.startswith("sqlite:"):
        issues.append(("DATABASE_URL", "Using SQLite in production is not recommended"))

    return issues


def check_debug_settings() -> List[Tuple[str, str]]:
    """Check that debug settings are disabled in production.

    Returns:
        List of (setting_name, issue_description) tuples
    """
    issues = []

    debug_setting = os.environ.get("DEBUG", "False").lower()
    if debug_setting == "true":
        issues.append(
            ("DEBUG", "Debug mode is enabled - should be disabled in production")
        )

    flask_env = os.environ.get("FLASK_ENV", "").lower()
    if flask_env == "development":
        issues.append(("FLASK_ENV", "Flask environment set to development"))

    return issues


def check_cors_settings() -> List[Tuple[str, str]]:
    """Check CORS configuration for production security.

    Returns:
        List of (setting_name, issue_description) tuples
    """
    issues = []

    cors_origins = os.environ.get("CORS_ORIGINS")
    if not cors_origins:
        issues.append(
            ("CORS_ORIGINS", "CORS origins not configured - may allow all origins")
        )
    elif "localhost" in cors_origins.lower():
        issues.append(("CORS_ORIGINS", "CORS allows localhost origins in production"))

    return issues


def main():
    """Main validation function."""
    print("🔒 Validating production configuration...\n")

    all_issues = []

    # Run all checks
    checks = [
        ("Secret Keys", check_secret_keys),
        ("Database Configuration", check_database_config),
        ("Debug Settings", check_debug_settings),
        ("CORS Settings", check_cors_settings),
    ]

    for check_name, check_func in checks:
        print(f"📋 {check_name}:")
        issues = check_func()

        if not issues:
            print("  ✅ No issues found")
        else:
            for setting, issue in issues:
                print(f"  ⚠️  {setting}: {issue}")
                all_issues.append((setting, issue))

        print()

    # Summary
    if not all_issues:
        print("🎉 All production configuration checks passed!")
        print("✅ Your configuration appears to be production-ready.")
        return 0
    else:
        print(
            f"❌ Found {len(all_issues)} configuration issues that should be addressed:"
        )
        print()
        for setting, issue in all_issues:
            print(f"  • {setting}: {issue}")

        print()
        print("🔧 Recommendations:")
        print("  1. Set strong, unique secret keys via environment variables")
        print("  2. Use a production database (PostgreSQL, MySQL, etc.)")
        print("  3. Disable debug mode in production")
        print("  4. Configure CORS origins to only allow your domains")
        print()
        print("📚 See docs/configuration.md for detailed setup instructions.")

        return 1


if __name__ == "__main__":
    sys.exit(main())
