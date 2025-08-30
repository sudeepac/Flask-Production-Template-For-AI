# Test Coverage Guide

This guide explains how to use the comprehensive test coverage reporting system in the Flask Production Template.

## Overview

The project includes a robust test coverage system with multiple reporting formats and CI/CD integration. Coverage is measured using `pytest-cov` and `coverage.py` with comprehensive configuration.

## Quick Start

### Run Tests with Coverage

```bash
# Basic coverage report
make test-coverage

# Generate HTML report and open in browser
make coverage-html

# Generate all coverage reports
make coverage-all

# Show coverage summary only
make coverage-summary
```

### Using the Coverage Script Directly

```bash
# Generate HTML report and open in browser
python scripts/coverage_report.py --html --open

# Generate XML report for CI/CD
python scripts/coverage_report.py --xml

# Generate coverage badge
python scripts/coverage_report.py --badge

# Generate all reports with custom threshold
python scripts/coverage_report.py --html --xml --json --badge --fail-under 85
```

## Coverage Configuration

### Configuration Files

1. **`.coveragerc`** - Main coverage configuration
2. **`pytest.ini`** - Pytest and coverage integration
3. **`pyproject.toml`** - Additional project configuration

### Coverage Settings

- **Minimum Coverage**: 80% (configurable)
- **Branch Coverage**: Enabled
- **Source Directory**: `app/`
- **Excluded Files**: Tests, migrations, config files, static files

## Report Types

### 1. Terminal Report

Shows coverage summary in the terminal with missing lines:

```bash
pytest tests/ --cov=app --cov-report=term-missing
```

### 2. HTML Report

Interactive HTML report with detailed file-by-file coverage:

```bash
make coverage-html
# Opens htmlcov/index.html in browser
```

### 3. XML Report

Machine-readable XML format for CI/CD systems:

```bash
make coverage-xml
# Generates coverage.xml
```

### 4. JSON Report

Structured JSON data for programmatic analysis:

```bash
make coverage-json
# Generates coverage.json
```

### 5. Coverage Badge

SVG badge showing coverage percentage:

```bash
make coverage-badge
# Generates coverage_reports/coverage-badge.svg
```

## Coverage Targets

### Makefile Targets

| Target | Description |
|--------|-------------|
| `test-coverage` | Run tests with basic coverage report |
| `coverage-html` | Generate HTML report and open in browser |
| `coverage-xml` | Generate XML report for CI/CD |
| `coverage-json` | Generate JSON report |
| `coverage-badge` | Generate coverage badge SVG |
| `coverage-all` | Generate all coverage reports |
| `coverage-summary` | Show coverage summary only |

### Script Options

```bash
python scripts/coverage_report.py --help
```

**Available Options:**

- `--html` - Generate HTML report
- `--xml` - Generate XML report
- `--json` - Generate JSON report
- `--badge` - Generate coverage badge
- `--fail-under N` - Set minimum coverage percentage
- `--open` - Open HTML report in browser
- `--verbose` - Verbose output
- `--exclude PATTERN` - Additional exclusion patterns
- `--summary-only` - Show summary without running tests

## CI/CD Integration

### GitHub Actions

The project includes comprehensive CI/CD with coverage reporting:

```yaml
# .github/workflows/ci.yml
- name: Run unit tests
  run: |
    pytest tests/unit/ -v --cov=app --cov-report=xml --cov-report=html

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
    flags: unittests
    name: codecov-umbrella
    fail_ci_if_error: false
```

### Coverage Services

The project is configured to work with:

- **Codecov** - Integrated in GitHub Actions
- **Coveralls** - Alternative coverage service
- **SonarQube** - Code quality and coverage analysis

## Coverage Best Practices

### 1. Writing Testable Code

```python
# Good: Testable function
def calculate_total(items: List[Item]) -> float:
    """Calculate total price of items."""
    return sum(item.price for item in items)

# Better: With error handling
def calculate_total(items: List[Item]) -> float:
    """Calculate total price of items."""
    if not items:
        return 0.0
    return sum(item.price for item in items if item.price > 0)
```

### 2. Testing Edge Cases

```python
def test_calculate_total_edge_cases():
    """Test edge cases for calculate_total function."""
    # Empty list
    assert calculate_total([]) == 0.0

    # Negative prices
    items = [Item(price=-10), Item(price=20)]
    assert calculate_total(items) == 20.0

    # Zero prices
    items = [Item(price=0), Item(price=10)]
    assert calculate_total(items) == 10.0
```

### 3. Excluding Code from Coverage

```python
# Exclude specific lines
if DEBUG:  # pragma: no cover
    print("Debug information")

# Exclude abstract methods
@abstractmethod
def process_data(self) -> None:  # pragma: no cover
    """Process data - implemented by subclasses."""
    pass

# Exclude defensive code
if not isinstance(data, dict):
    raise TypeError("Data must be a dictionary")  # pragma: no cover
```

## Coverage Analysis

### Understanding Coverage Metrics

1. **Line Coverage**: Percentage of code lines executed
2. **Branch Coverage**: Percentage of code branches taken
3. **Function Coverage**: Percentage of functions called
4. **Statement Coverage**: Percentage of statements executed

### Coverage Thresholds

- **90%+**: Excellent coverage
- **80-89%**: Good coverage (project minimum)
- **70-79%**: Acceptable coverage
- **<70%**: Needs improvement

### Improving Coverage

1. **Identify Uncovered Code**:

   ```bash
   make coverage-html
   # Review htmlcov/index.html for uncovered lines
   ```

2. **Write Missing Tests**:
   - Focus on uncovered branches
   - Test error conditions
   - Test edge cases

3. **Refactor Complex Code**:
   - Break down large functions
   - Reduce cyclomatic complexity
   - Improve testability

## Troubleshooting

### Common Issues

1. **Coverage Not Measured**:

   ```bash
   # Ensure coverage is installed
   pip install pytest-cov coverage

   # Check configuration
   coverage config --show
   ```

2. **Files Not Included**:

   ```bash
   # Check source configuration in .coveragerc
   [run]
   source = app
   ```

3. **Low Coverage**:

   ```bash
   # Identify missing tests
   make coverage-html
   # Review uncovered lines in HTML report
   ```

### Debug Coverage

```bash
# Show coverage configuration
coverage config --show

# Debug coverage measurement
coverage debug sys
coverage debug config

# Show detailed coverage data
coverage report --show-missing
```

## Integration Examples

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: coverage-check
      name: Coverage Check
      entry: python scripts/coverage_report.py --fail-under 80
      language: system
      pass_filenames: false
```

### VS Code Integration

```json
// .vscode/tasks.json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Run Coverage",
            "type": "shell",
            "command": "make coverage-html",
            "group": "test",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            }
        }
    ]
}
```

### Docker Integration

```dockerfile
# Dockerfile.test
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN make coverage-all

# Export coverage reports
VOLUME ["/app/htmlcov", "/app/coverage_reports"]
```

## Resources

- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Codecov Documentation](https://docs.codecov.com/)
- [Testing Best Practices](./testing_guide.md)
