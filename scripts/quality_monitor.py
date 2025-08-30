#!/usr/bin/env python3
"""
Real-time Code Quality Monitor

This script provides real-time monitoring of code quality metrics
and can be integrated into development workflows for continuous feedback.

Usage:
    python scripts/quality_monitor.py [--watch] [--report] [--threshold]
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class QualityMetrics:
    """Data class for storing quality metrics."""

    timestamp: str
    files_checked: int
    lines_of_code: int
    complexity_score: float
    test_coverage: float
    linting_issues: int
    security_issues: int
    type_coverage: float
    docstring_coverage: float
    duplication_percentage: float
    technical_debt_minutes: int
    quality_score: float


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"


class QualityMonitor:
    """Real-time code quality monitoring system."""

    def __init__(self, project_root: Path, threshold: float = 8.0):
        self.project_root = project_root
        self.threshold = threshold
        self.metrics_file = project_root / ".quality_metrics.json"
        self.last_check_hash = None

    def print_header(self, title: str) -> None:
        """Print a formatted header."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{title.center(60)}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")

    def print_metric(self, name: str, value: str, status: str = "info") -> None:
        """Print a formatted metric."""
        color = {
            "good": Colors.GREEN,
            "warning": Colors.YELLOW,
            "error": Colors.RED,
            "info": Colors.CYAN,
        }.get(status, Colors.CYAN)

        print(f"{color}📊 {name:<25}: {value}{Colors.END}")

    def run_command(
        self, command: List[str], capture_output: bool = True
    ) -> Tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                capture_output=capture_output,
                text=True,
                timeout=60,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out"
        except Exception as e:
            return 1, "", str(e)

    def get_file_hash(self) -> str:
        """Get hash of all Python files for change detection."""
        python_files = list(self.project_root.rglob("*.py"))
        python_files = [
            f for f in python_files if not any(part.startswith(".") for part in f.parts)
        ]

        content = ""
        for file_path in sorted(python_files):
            try:
                content += file_path.read_text(encoding="utf-8")
            except Exception:
                continue

        return hashlib.md5(content.encode()).hexdigest()

    def count_lines_of_code(self) -> int:
        """Count total lines of code."""
        total_lines = 0
        python_files = list(self.project_root.rglob("*.py"))
        python_files = [
            f for f in python_files if not any(part.startswith(".") for part in f.parts)
        ]

        for file_path in python_files:
            try:
                lines = file_path.read_text(encoding="utf-8").splitlines()
                # Count non-empty, non-comment lines
                code_lines = [
                    line
                    for line in lines
                    if line.strip() and not line.strip().startswith("#")
                ]
                total_lines += len(code_lines)
            except Exception:
                continue

        return total_lines

    def get_complexity_score(self) -> float:
        """Get cyclomatic complexity score using radon."""
        exit_code, stdout, stderr = self.run_command(["radon", "cc", "app", "--json"])

        if exit_code != 0:
            return 0.0

        try:
            data = json.loads(stdout)
            total_complexity = 0
            total_functions = 0

            for file_data in data.values():
                for item in file_data:
                    if item["type"] in ["function", "method"]:
                        total_complexity += item["complexity"]
                        total_functions += 1

            return total_complexity / max(total_functions, 1)
        except Exception:
            return 0.0

    def get_test_coverage(self) -> float:
        """Get test coverage percentage."""
        exit_code, stdout, stderr = self.run_command(
            ["coverage", "run", "--source=app", "-m", "pytest", "tests/", "-q"]
        )

        if exit_code != 0:
            return 0.0

        exit_code, stdout, stderr = self.run_command(
            ["coverage", "report", "--format=json"]
        )

        if exit_code != 0:
            return 0.0

        try:
            data = json.loads(stdout)
            return data.get("totals", {}).get("percent_covered", 0.0)
        except Exception:
            return 0.0

    def get_linting_issues(self) -> int:
        """Get number of linting issues from flake8."""
        exit_code, stdout, stderr = self.run_command(
            ["flake8", "app", "tests", "--count", "--statistics"]
        )

        if exit_code == 0:
            return 0

        # Parse the count from flake8 output
        lines = stdout.strip().split("\n")
        for line in lines:
            if line.strip().isdigit():
                return int(line.strip())

        return len([line for line in lines if line.strip()])

    def get_security_issues(self) -> int:
        """Get number of security issues from bandit."""
        exit_code, stdout, stderr = self.run_command(
            ["bandit", "-r", "app", "-f", "json"]
        )

        try:
            data = json.loads(stdout)
            return len(data.get("results", []))
        except Exception:
            return 0

    def get_type_coverage(self) -> float:
        """Get type coverage from mypy."""
        exit_code, stdout, stderr = self.run_command(
            ["mypy", "app", "--strict", "--show-error-codes"]
        )

        # Simple heuristic: fewer mypy errors = better type coverage
        error_count = len([line for line in stderr.split("\n") if "error:" in line])
        total_files = len(list(self.project_root.glob("app/**/*.py")))

        if total_files == 0:
            return 100.0

        # Rough calculation: assume good type coverage if < 1 error per file
        return max(0, 100 - (error_count / total_files) * 10)

    def get_docstring_coverage(self) -> float:
        """Get docstring coverage percentage."""
        exit_code, stdout, stderr = self.run_command(
            ["docstring-coverage", "app", "--percentage-only"]
        )

        if exit_code != 0:
            return 0.0

        try:
            # Extract percentage from output
            percentage_str = stdout.strip().replace("%", "")
            return float(percentage_str)
        except Exception:
            return 0.0

    def get_duplication_percentage(self) -> float:
        """Get code duplication percentage using simple heuristic."""
        # This is a simplified implementation
        # In a real scenario, you might use tools like jscpd or similar
        python_files = list(self.project_root.rglob("app/**/*.py"))

        if not python_files:
            return 0.0

        # Simple line-based duplication detection
        all_lines = []
        for file_path in python_files:
            try:
                lines = file_path.read_text(encoding="utf-8").splitlines()
                # Normalize lines (remove whitespace, comments)
                normalized_lines = [
                    line.strip()
                    for line in lines
                    if line.strip() and not line.strip().startswith("#")
                ]
                all_lines.extend(normalized_lines)
            except Exception:
                continue

        if not all_lines:
            return 0.0

        unique_lines = set(all_lines)
        duplication_ratio = 1 - (len(unique_lines) / len(all_lines))
        return duplication_ratio * 100

    def calculate_technical_debt(self, metrics: QualityMetrics) -> int:
        """Calculate technical debt in minutes based on various metrics."""
        debt_minutes = 0

        # Linting issues (2 minutes per issue)
        debt_minutes += metrics.linting_issues * 2

        # Security issues (30 minutes per issue)
        debt_minutes += metrics.security_issues * 30

        # Low test coverage (1 minute per % below 80%)
        if metrics.test_coverage < 80:
            debt_minutes += (80 - metrics.test_coverage) * 1

        # Low docstring coverage (0.5 minutes per % below 90%)
        if metrics.docstring_coverage < 90:
            debt_minutes += (90 - metrics.docstring_coverage) * 0.5

        # High complexity (5 minutes per point above 10)
        if metrics.complexity_score > 10:
            debt_minutes += (metrics.complexity_score - 10) * 5

        # Code duplication (1 minute per % above 5%)
        if metrics.duplication_percentage > 5:
            debt_minutes += (metrics.duplication_percentage - 5) * 1

        return int(debt_minutes)

    def calculate_quality_score(self, metrics: QualityMetrics) -> float:
        """Calculate overall quality score (0-10)."""
        score = 10.0

        # Deduct for linting issues
        score -= min(metrics.linting_issues * 0.1, 2.0)

        # Deduct for security issues
        score -= min(metrics.security_issues * 0.5, 3.0)

        # Deduct for low test coverage
        if metrics.test_coverage < 80:
            score -= (80 - metrics.test_coverage) * 0.02

        # Deduct for low docstring coverage
        if metrics.docstring_coverage < 90:
            score -= (90 - metrics.docstring_coverage) * 0.01

        # Deduct for high complexity
        if metrics.complexity_score > 10:
            score -= (metrics.complexity_score - 10) * 0.1

        # Deduct for code duplication
        if metrics.duplication_percentage > 5:
            score -= (metrics.duplication_percentage - 5) * 0.05

        return max(0.0, score)

    def collect_metrics(self) -> QualityMetrics:
        """Collect all quality metrics."""
        print(f"{Colors.BLUE}🔍 Collecting quality metrics...{Colors.END}")

        files_checked = len(list(self.project_root.rglob("app/**/*.py")))
        lines_of_code = self.count_lines_of_code()
        complexity_score = self.get_complexity_score()
        test_coverage = self.get_test_coverage()
        linting_issues = self.get_linting_issues()
        security_issues = self.get_security_issues()
        type_coverage = self.get_type_coverage()
        docstring_coverage = self.get_docstring_coverage()
        duplication_percentage = self.get_duplication_percentage()

        metrics = QualityMetrics(
            timestamp=datetime.now().isoformat(),
            files_checked=files_checked,
            lines_of_code=lines_of_code,
            complexity_score=complexity_score,
            test_coverage=test_coverage,
            linting_issues=linting_issues,
            security_issues=security_issues,
            type_coverage=type_coverage,
            docstring_coverage=docstring_coverage,
            duplication_percentage=duplication_percentage,
            technical_debt_minutes=0,  # Will be calculated
            quality_score=0.0,  # Will be calculated
        )

        metrics.technical_debt_minutes = self.calculate_technical_debt(metrics)
        metrics.quality_score = self.calculate_quality_score(metrics)

        return metrics

    def display_metrics(self, metrics: QualityMetrics) -> None:
        """Display metrics in a formatted way."""
        self.print_header("CODE QUALITY METRICS")

        # Basic metrics
        self.print_metric("Files Checked", str(metrics.files_checked))
        self.print_metric("Lines of Code", f"{metrics.lines_of_code:,}")

        # Quality metrics with status
        self.print_metric(
            "Test Coverage",
            f"{metrics.test_coverage:.1f}%",
            "good"
            if metrics.test_coverage >= 80
            else "warning"
            if metrics.test_coverage >= 60
            else "error",
        )

        self.print_metric(
            "Docstring Coverage",
            f"{metrics.docstring_coverage:.1f}%",
            "good"
            if metrics.docstring_coverage >= 90
            else "warning"
            if metrics.docstring_coverage >= 70
            else "error",
        )

        self.print_metric(
            "Type Coverage",
            f"{metrics.type_coverage:.1f}%",
            "good"
            if metrics.type_coverage >= 80
            else "warning"
            if metrics.type_coverage >= 60
            else "error",
        )

        self.print_metric(
            "Complexity Score",
            f"{metrics.complexity_score:.1f}",
            "good"
            if metrics.complexity_score <= 10
            else "warning"
            if metrics.complexity_score <= 15
            else "error",
        )

        self.print_metric(
            "Code Duplication",
            f"{metrics.duplication_percentage:.1f}%",
            "good"
            if metrics.duplication_percentage <= 5
            else "warning"
            if metrics.duplication_percentage <= 10
            else "error",
        )

        self.print_metric(
            "Linting Issues",
            str(metrics.linting_issues),
            "good"
            if metrics.linting_issues == 0
            else "warning"
            if metrics.linting_issues <= 5
            else "error",
        )

        self.print_metric(
            "Security Issues",
            str(metrics.security_issues),
            "good" if metrics.security_issues == 0 else "error",
        )

        # Summary metrics
        print()
        self.print_metric(
            "Technical Debt",
            f"{metrics.technical_debt_minutes} minutes",
            "good"
            if metrics.technical_debt_minutes <= 30
            else "warning"
            if metrics.technical_debt_minutes <= 120
            else "error",
        )

        self.print_metric(
            "Quality Score",
            f"{metrics.quality_score:.1f}/10",
            "good"
            if metrics.quality_score >= self.threshold
            else "warning"
            if metrics.quality_score >= 6
            else "error",
        )

        # Quality gate status
        print()
        if metrics.quality_score >= self.threshold:
            print(f"{Colors.GREEN}✅ Quality gate: PASSED{Colors.END}")
        else:
            print(f"{Colors.RED}❌ Quality gate: FAILED{Colors.END}")
            print(
                f"{Colors.YELLOW}   Minimum score required: {self.threshold}{Colors.END}"
            )

    def save_metrics(self, metrics: QualityMetrics) -> None:
        """Save metrics to file for historical tracking."""
        try:
            if self.metrics_file.exists():
                with open(self.metrics_file, "r") as f:
                    history = json.load(f)
            else:
                history = []

            history.append(asdict(metrics))

            # Keep only last 100 entries
            history = history[-100:]

            with open(self.metrics_file, "w") as f:
                json.dump(history, f, indent=2)

        except Exception as e:
            print(f"{Colors.YELLOW}⚠️  Could not save metrics: {e}{Colors.END}")

    def generate_report(self) -> None:
        """Generate a detailed quality report."""
        if not self.metrics_file.exists():
            print(f"{Colors.RED}❌ No metrics history found{Colors.END}")
            return

        try:
            with open(self.metrics_file, "r") as f:
                history = json.load(f)

            if not history:
                print(f"{Colors.RED}❌ No metrics data available{Colors.END}")
                return

            self.print_header("QUALITY TREND REPORT")

            # Show last 5 entries
            recent_entries = history[-5:]

            print(f"{Colors.BOLD}Recent Quality Scores:{Colors.END}")
            for entry in recent_entries:
                timestamp = datetime.fromisoformat(entry["timestamp"]).strftime(
                    "%Y-%m-%d %H:%M"
                )
                score = entry["quality_score"]
                status = "✅" if score >= self.threshold else "❌"
                print(f"  {timestamp}: {score:.1f}/10 {status}")

            # Calculate trends
            if len(history) >= 2:
                current = history[-1]
                previous = history[-2]

                print(f"\n{Colors.BOLD}Trends:{Colors.END}")

                score_change = current["quality_score"] - previous["quality_score"]
                trend_icon = (
                    "📈" if score_change > 0 else "📉" if score_change < 0 else "➡️"
                )
                print(f"  Quality Score: {trend_icon} {score_change:+.1f}")

                coverage_change = current["test_coverage"] - previous["test_coverage"]
                trend_icon = (
                    "📈" if coverage_change > 0 else "📉" if coverage_change < 0 else "➡️"
                )
                print(f"  Test Coverage: {trend_icon} {coverage_change:+.1f}%")

                debt_change = (
                    current["technical_debt_minutes"]
                    - previous["technical_debt_minutes"]
                )
                trend_icon = (
                    "📉" if debt_change < 0 else "📈" if debt_change > 0 else "➡️"
                )
                print(f"  Technical Debt: {trend_icon} {debt_change:+d} minutes")

        except Exception as e:
            print(f"{Colors.RED}❌ Error generating report: {e}{Colors.END}")

    def watch_mode(self) -> None:
        """Run in watch mode, monitoring for changes."""
        print(f"{Colors.BOLD}👀 Starting quality monitoring (watch mode){Colors.END}")
        print(f"{Colors.YELLOW}Press Ctrl+C to stop{Colors.END}\n")

        try:
            while True:
                current_hash = self.get_file_hash()

                if current_hash != self.last_check_hash:
                    print(
                        f"{Colors.CYAN}🔄 Code changes detected, running quality check...{Colors.END}"
                    )

                    metrics = self.collect_metrics()
                    self.display_metrics(metrics)
                    self.save_metrics(metrics)

                    self.last_check_hash = current_hash

                    if metrics.quality_score < self.threshold:
                        print(
                            f"\n{Colors.RED}🚨 Quality threshold not met! Consider fixing issues before committing.{Colors.END}"
                        )

                time.sleep(5)  # Check every 5 seconds

        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}👋 Quality monitoring stopped{Colors.END}")

    def run_single_check(self) -> bool:
        """Run a single quality check."""
        metrics = self.collect_metrics()
        self.display_metrics(metrics)
        self.save_metrics(metrics)

        return metrics.quality_score >= self.threshold


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Monitor code quality metrics in real-time"
    )
    parser.add_argument(
        "--watch", action="store_true", help="Run in watch mode, monitoring for changes"
    )
    parser.add_argument(
        "--report", action="store_true", help="Generate a quality trend report"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=8.0,
        help="Quality score threshold (default: 8.0)",
    )

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    monitor = QualityMonitor(project_root, args.threshold)

    if args.report:
        monitor.generate_report()
    elif args.watch:
        monitor.watch_mode()
    else:
        success = monitor.run_single_check()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
