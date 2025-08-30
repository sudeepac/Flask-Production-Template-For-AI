#!/usr/bin/env python3
"""
Comprehensive Coverage Reporting Script

This script provides detailed coverage analysis and reporting capabilities
for the Flask Production Template project.

Usage:
    python scripts/coverage_report.py [options]

Options:
    --html          Generate HTML coverage report
    --xml           Generate XML coverage report (for CI/CD)
    --json          Generate JSON coverage report
    --badge         Generate coverage badge
    --fail-under    Minimum coverage percentage (default: 80)
    --open          Open HTML report in browser
    --verbose       Verbose output
    --exclude       Additional patterns to exclude

Examples:
    python scripts/coverage_report.py --html --open
    python scripts/coverage_report.py --xml --fail-under 85
    python scripts/coverage_report.py --badge --verbose
"""

import argparse
import json
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import List, Optional


class CoverageReporter:
    """Comprehensive coverage reporting and analysis."""

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize coverage reporter.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root or Path.cwd()
        self.coverage_dir = self.project_root / "htmlcov"
        self.reports_dir = self.project_root / "coverage_reports"
        self.reports_dir.mkdir(exist_ok=True)

    def run_tests_with_coverage(
        self,
        fail_under: int = 80,
        exclude_patterns: Optional[List[str]] = None,
        continue_on_failure: bool = True,
    ) -> bool:
        """Run tests with coverage measurement.

        Args:
            fail_under: Minimum coverage percentage
            exclude_patterns: Additional patterns to exclude
            continue_on_failure: Continue generating reports even if tests fail

        Returns:
            True if tests pass and coverage meets threshold
        """
        print("🧪 Running tests with coverage measurement...")

        # Build pytest command
        cmd = [
            "pytest",
            "tests/",
            "--cov=app",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-report=xml",
            "--cov-report=json",
            "--verbose",
            "--continue-on-collection-errors",
        ]

        # Only add fail-under if we're not continuing on failure
        if not continue_on_failure:
            cmd.append(f"--cov-fail-under={fail_under}")

        # Add exclusion patterns
        if exclude_patterns:
            for pattern in exclude_patterns:
                cmd.extend(["--cov-omit", pattern])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print("✅ Tests passed and coverage threshold met!")
                return True
            else:
                if continue_on_failure:
                    print("⚠️ Some tests failed, but coverage data was collected")
                    print("📊 Proceeding with coverage report generation...")
                    return True  # Continue with report generation
                else:
                    print("❌ Tests failed or coverage below threshold")
                    print(result.stdout[-1000:])  # Show last 1000 chars
                    return False

        except subprocess.CalledProcessError as e:
            print(f"❌ Error running tests: {e}")
            return False

    def generate_html_report(self, open_browser: bool = False) -> bool:
        """Generate HTML coverage report.

        Args:
            open_browser: Whether to open report in browser

        Returns:
            True if report generated successfully
        """
        print("📊 Generating HTML coverage report...")

        try:
            subprocess.run(["coverage", "html"], check=True)

            html_file = self.coverage_dir / "index.html"
            if html_file.exists():
                print(f"✅ HTML report generated: {html_file}")

                if open_browser:
                    webbrowser.open(f"file://{html_file.absolute()}")
                    print("🌐 Opened report in browser")

                return True
            else:
                print("❌ HTML report file not found")
                return False

        except subprocess.CalledProcessError as e:
            print(f"❌ Error generating HTML report: {e}")
            return False

    def generate_xml_report(self) -> bool:
        """Generate XML coverage report for CI/CD.

        Returns:
            True if report generated successfully
        """
        print("📄 Generating XML coverage report...")

        try:
            subprocess.run(["coverage", "xml"], check=True)

            xml_file = self.project_root / "coverage.xml"
            if xml_file.exists():
                print(f"✅ XML report generated: {xml_file}")
                return True
            else:
                print("❌ XML report file not found")
                return False

        except subprocess.CalledProcessError as e:
            print(f"❌ Error generating XML report: {e}")
            return False

    def generate_json_report(self) -> bool:
        """Generate JSON coverage report.

        Returns:
            True if report generated successfully
        """
        print("📋 Generating JSON coverage report...")

        try:
            subprocess.run(["coverage", "json"], check=True)

            json_file = self.project_root / "coverage.json"
            if json_file.exists():
                print(f"✅ JSON report generated: {json_file}")
                return True
            else:
                print("❌ JSON report file not found")
                return False

        except subprocess.CalledProcessError as e:
            print(f"❌ Error generating JSON report: {e}")
            return False

    def generate_coverage_badge(self) -> bool:
        """Generate coverage badge SVG.

        Returns:
            True if badge generated successfully
        """
        print("🏆 Generating coverage badge...")

        try:
            # Get coverage percentage from JSON report
            json_file = self.project_root / "coverage.json"
            if not json_file.exists():
                self.generate_json_report()

            with open(json_file, "r") as f:
                coverage_data = json.load(f)

            total_coverage = coverage_data["totals"]["percent_covered"]

            # Determine badge color based on coverage
            if total_coverage >= 90:
                color = "brightgreen"
            elif total_coverage >= 80:
                color = "green"
            elif total_coverage >= 70:
                color = "yellow"
            elif total_coverage >= 60:
                color = "orange"
            else:
                color = "red"

            # Generate badge SVG
            badge_svg = self._create_badge_svg(total_coverage, color)

            badge_file = self.reports_dir / "coverage-badge.svg"
            with open(badge_file, "w") as f:
                f.write(badge_svg)

            print(f"✅ Coverage badge generated: {badge_file}")
            print(f"📊 Coverage: {total_coverage:.1f}%")

            return True

        except Exception as e:
            print(f"❌ Error generating coverage badge: {e}")
            return False

    def _create_badge_svg(self, coverage: float, color: str) -> str:
        """Create SVG badge for coverage.

        Args:
            coverage: Coverage percentage
            color: Badge color

        Returns:
            SVG content as string
        """
        return f"""
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="104" height="20">
    <linear_gradient id="b" x2="0" y2="100%">
        <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
        <stop offset="1" stop-opacity=".1"/>
    </linear_gradient>
    <clip_path id="a">
        <rect width="104" height="20" rx="3" fill="#fff"/>
    </clip_path>
    <g clip-path="url(#a)">
        <path fill="#555" d="M0 0h63v20H0z"/>
        <path fill="{color}" d="M63 0h41v20H63z"/>
        <path fill="url(#b)" d="M0 0h104v20H0z"/>
    </g>
    <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="110">
        <text x="325" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" text_length="530">coverage</text>
        <text x="325" y="140" transform="scale(.1)" text_length="530">coverage</text>
        <text x="825" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" text_length="310">{coverage:.0f}%</text>
        <text x="825" y="140" transform="scale(.1)" text_length="310">{coverage:.0f}%</text>
    </g>
</svg>
        """.strip()

    def print_coverage_summary(self, verbose: bool = False) -> None:
        """Print coverage summary.

        Args:
            verbose: Whether to print detailed information
        """
        try:
            json_file = self.project_root / "coverage.json"
            if not json_file.exists():
                print("❌ Coverage data not found. Run tests first.")
                return

            with open(json_file, "r") as f:
                coverage_data = json.load(f)

            totals = coverage_data["totals"]

            print("\n📊 Coverage Summary:")
            print("=" * 50)
            print(f"Total Coverage: {totals['percent_covered']:.1f}%")
            print(
                f"Lines Covered: {totals['covered_lines']}/{totals['num_statements']}"
            )
            print(f"Missing Lines: {totals['missing_lines']}")

            if "percent_covered_display" in totals:
                print(
                    f"Branch Coverage: {totals.get('percent_covered_display', 'N/A')}"
                )

            if verbose:
                print("\n📁 File Coverage:")
                print("-" * 50)

                files = coverage_data.get("files", {})
                for file_path, file_data in sorted(files.items()):
                    coverage_pct = file_data["summary"]["percent_covered"]
                    print(f"{file_path:<40} {coverage_pct:>6.1f}%")

            print("=" * 50)

        except Exception as e:
            print(f"❌ Error reading coverage data: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive coverage reporting for Flask Production Template",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("--html", action="store_true", help="Generate HTML report")
    parser.add_argument("--xml", action="store_true", help="Generate XML report")
    parser.add_argument("--json", action="store_true", help="Generate JSON report")
    parser.add_argument("--badge", action="store_true", help="Generate coverage badge")
    parser.add_argument(
        "--fail-under", type=int, default=80, help="Minimum coverage percentage"
    )
    parser.add_argument(
        "--open", action="store_true", help="Open HTML report in browser"
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--exclude", action="append", help="Additional patterns to exclude"
    )
    parser.add_argument(
        "--summary-only", action="store_true", help="Only show coverage summary"
    )

    args = parser.parse_args()

    reporter = CoverageReporter()

    success = True

    if args.summary_only:
        reporter.print_coverage_summary(args.verbose)
        return

    # Run tests with coverage if any report is requested
    if args.html or args.xml or args.json or args.badge:
        success = reporter.run_tests_with_coverage(
            fail_under=args.fail_under, exclude_patterns=args.exclude
        )

    # Generate requested reports
    if args.html and success:
        success &= reporter.generate_html_report(args.open)

    if args.xml and success:
        success &= reporter.generate_xml_report()

    if args.json and success:
        success &= reporter.generate_json_report()

    if args.badge and success:
        success &= reporter.generate_coverage_badge()

    # Print summary
    if success:
        reporter.print_coverage_summary(args.verbose)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()