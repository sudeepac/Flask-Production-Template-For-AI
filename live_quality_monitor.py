#!/usr/bin/env python3
"""
Live Code Quality Monitor

A simple script that continuously monitors code quality by running pre-commit hooks.
"""

import os
import subprocess
import time
from datetime import datetime


def clear_screen():
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def run_quality_check():
    """Run pre-commit hooks and return the result."""
    try:
        result = subprocess.run(
            ["pre-commit", "run", "--all-files"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Quality check timed out after 2 minutes"
    except Exception as e:
        return False, f"Error running quality check: {str(e)}"


def main():
    """Main monitoring loop."""
    print("🔍 Starting Live Code Quality Monitor")
    print("Press Ctrl+C to stop monitoring...\n")

    try:
        while True:
            clear_screen()

            # Display header
            print("🔍 Live Code Quality Monitor")
            print(f"📅 Last check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)

            # Run quality check
            success, output = run_quality_check()

            # Display results
            if success:
                print("✅ All quality checks PASSED!")
                print("\n📊 Recent output:")
                # Show last 15 lines of output
                lines = output.strip().split("\n")
                for line in lines[-15:]:
                    print(f"  {line}")
            else:
                print("❌ Quality checks FAILED!")
                print("\n🔧 Issues found:")
                # Show last 20 lines of output
                lines = output.strip().split("\n")
                for line in lines[-20:]:
                    print(f"  {line}")

            print("\n" + "=" * 60)
            print("⏱️  Next check in 15 seconds... (Press Ctrl+C to stop)")

            # Wait before next check
            time.sleep(15)

    except KeyboardInterrupt:
        print("\n\n👋 Live monitoring stopped. Goodbye!")
    except Exception as e:
        print(f"\n\n❌ Monitoring error: {str(e)}")


if __name__ == "__main__":
    main()
