# Flask Production Template - Streamlined Makefile
# Essential commands for development workflow

.PHONY: help setup test lint fix dev quality clean

# Default target
help: ## Show available commands
	@echo "Flask Production Template - Essential Commands"
	@echo "============================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Quick Start:"
	@echo "  make setup    # Set up development environment"
	@echo "  make test     # Run tests with coverage"
	@echo "  make lint     # Run quality checks"
	@echo "  make fix      # Auto-fix code issues"
	@echo "  make dev      # Start development server"

setup: ## Set up development environment
	@echo "Setting up development environment..."
	python scripts/setup_dev_environment.py
	@echo "Development environment ready!"

test: ## Run tests with coverage report
	@echo "Running tests with coverage..."
	pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
	@echo "Coverage report: htmlcov/index.html"

lint: ## Run all quality checks (ruff, mypy, bandit, interrogate)
	@echo "Running quality checks..."
	ruff check app tests scripts
	mypy app --ignore-missing-imports
	bandit -r app -q
	interrogate app --fail-under=80
	@echo "Quality checks completed!"

fix: ## Auto-fix code formatting and import issues
	@echo "Auto-fixing code issues..."
	ruff format app tests scripts
	ruff check --fix app tests scripts
	@echo "Auto-fixes applied!"

dev: ## Start development server
	@echo "Starting development server..."
	flask run --host=0.0.0.0 --port=5000 --debug

quality: ## Run comprehensive quality monitoring
	@echo "Running quality monitoring..."
	python scripts/quality_monitor.py

validate: ## Validate production configuration and style setup
	@echo "Validating configuration..."
	python scripts/setup_dev_environment.py --validate-only

check-encoding: ## Check for encoding issues in Python files
	@echo "Checking encoding issues..."
	python scripts/quality_monitor.py --encoding-check

check-docstrings: ## Check for missing docstrings
	@echo "Checking docstrings..."
	python scripts/quality_monitor.py --docstring-check

clean: ## Clean build artifacts and cache files
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/ .mypy_cache/
	@echo "Cleanup complete!"
