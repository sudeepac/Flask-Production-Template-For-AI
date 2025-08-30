# Flask Production Template - Development Makefile
# Provides convenient commands for code quality, testing, and development tasks

.PHONY: help install install-dev setup clean test test-unit test-integration test-coverage
.PHONY: lint format check-format check-imports check-types check-security check-docs
.PHONY: fix fix-format fix-imports pre-commit run dev docker-build docker-run
.PHONY: db-init db-migrate db-upgrade db-downgrade db-reset

# Default target
help: ## Show this help message
	@echo "Flask Production Template - Development Commands"
	@echo "================================================"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Quick Start:"
	@echo "  make setup     # Set up development environment"
	@echo "  make test      # Run all tests"
	@echo "  make lint      # Run all linting checks"
	@echo "  make fix       # Auto-fix code formatting issues"
	@echo "  make dev       # Start development server"

# Installation and Setup
install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements.txt -r requirements-optional.txt

setup: ## Set up complete development environment
	@echo "Setting up development environment..."
	python scripts/setup_dev_environment.py
	@echo "Development environment setup complete!"

clean: ## Clean up build artifacts and cache files
	@echo "Cleaning up build artifacts..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/ .mypy_cache/ .tox/
	@echo "Cleanup complete!"

# Testing
test: ## Run all tests
	@echo "Running all tests..."
	pytest tests/ -v

test-unit: ## Run unit tests only
	@echo "Running unit tests..."
	pytest tests/unit/ -v

test-integration: ## Run integration tests only
	@echo "Running integration tests..."
	pytest tests/integration/ -v

test-coverage: ## Run tests with coverage report
	@echo "Running tests with coverage..."
	pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/"

coverage-html: ## Generate HTML coverage report and open in browser
	@echo "Generating HTML coverage report..."
	python scripts/coverage_report.py --html --open

coverage-xml: ## Generate XML coverage report for CI/CD
	@echo "Generating XML coverage report..."
	python scripts/coverage_report.py --xml

coverage-json: ## Generate JSON coverage report
	@echo "Generating JSON coverage report..."
	python scripts/coverage_report.py --json

coverage-badge: ## Generate coverage badge SVG
	@echo "Generating coverage badge..."
	python scripts/coverage_report.py --badge

coverage-all: ## Generate all coverage reports
	@echo "Generating all coverage reports..."
	python scripts/coverage_report.py --html --xml --json --badge --open

coverage-summary: ## Show coverage summary
	@echo "Coverage Summary:"
	python scripts/coverage_report.py --summary-only --verbose

test-performance: ## Run performance tests
	@echo "Running performance tests..."
	pytest tests/performance/ -v

# Code Quality Checks
lint: check-format check-imports check-types check-security check-docs ## Run all linting checks
	@echo "All linting checks completed!"

check-format: ## Check code formatting with Black
	@echo "Checking code formatting..."
	black --check --diff app tests scripts

check-imports: ## Check import sorting with isort
	@echo "Checking import sorting..."
	isort --check-only --diff app tests scripts

check-types: ## Check type hints with mypy
	@echo "Checking type hints..."
	mypy app --ignore-missing-imports

check-security: ## Check for security issues with bandit
	@echo "Checking for security issues..."
	bandit -r app -f json -o bandit-report.json
	@echo "Security report generated: bandit-report.json"

check-docs: ## Check docstring coverage
	@echo "Checking docstring coverage..."
	docstring-coverage app --fail-under=90

check-style: ## Run custom style compliance checks
	@echo "Running custom style compliance checks..."
	python scripts/check_style_compliance.py

# Code Formatting and Fixes
fix: fix-format fix-imports ## Auto-fix all formatting issues
	@echo "All auto-fixes applied!"

fix-format: ## Auto-fix code formatting with Black
	@echo "Fixing code formatting..."
	black app tests scripts

fix-imports: ## Auto-fix import sorting with isort
	@echo "Fixing import sorting..."
	isort app tests scripts

fix-style: ## Auto-fix style issues where possible
	@echo "Fixing style issues..."
	python scripts/check_style_compliance.py --fix

# Pre-commit
pre-commit: ## Run pre-commit hooks on all files
	@echo "Running pre-commit hooks..."
	pre-commit run --all-files

pre-commit-install: ## Install pre-commit hooks
	@echo "Installing pre-commit hooks..."
	pre-commit install
	pre-commit install --hook-type commit-msg
	pre-commit install --hook-type pre-push

# Development Server
run: ## Start Flask development server
	@echo "Starting Flask development server..."
	flask run --host=0.0.0.0 --port=5000 --debug

dev: ## Start development server with auto-reload
	@echo "Starting development server with auto-reload..."
	python -m flask run --host=0.0.0.0 --port=5000 --debug --reload

# Database Operations
db-init: ## Initialize database
	@echo "Initializing database..."
	python scripts/db_init.py

db-migrate: ## Create new database migration
	@echo "Creating database migration..."
	flask db migrate -m "$(MSG)"

db-upgrade: ## Apply database migrations
	@echo "Applying database migrations..."
	flask db upgrade

db-downgrade: ## Rollback database migration
	@echo "Rolling back database migration..."
	flask db downgrade

db-reset: ## Reset database (WARNING: destroys all data)
	@echo "Resetting database..."
	python scripts/db_init.py --reset

db-seed: ## Seed database with sample data
	@echo "Seeding database..."
	python scripts/db_seeds.py

# Docker Operations
docker-build: ## Build Docker image
	@echo "Building Docker image..."
	docker build -t flask-production-template .

docker-run: ## Run application in Docker container
	@echo "Running application in Docker..."
	docker-compose up --build

docker-dev: ## Run development environment with Docker
	@echo "Starting Docker development environment..."
	docker-compose -f docker-compose.yml up --build

docker-prod: ## Run production environment with Docker
	@echo "Starting Docker production environment..."
	docker-compose -f docker-compose.prod.yml up --build

docker-clean: ## Clean up Docker containers and images
	@echo "Cleaning up Docker resources..."
	docker-compose down --volumes --remove-orphans
	docker system prune -f

# Security and Compliance
security-scan: ## Run comprehensive security scan
	@echo "Running comprehensive security scan..."
	bandit -r app -f json -o bandit-report.json
	safety check --json --output safety-report.json
	@echo "Security reports generated: bandit-report.json, safety-report.json"

compliance-check: ## Run full compliance check
	@echo "Running full compliance check..."
	make lint
	make test-coverage
	make security-scan
	make check-docs
	@echo "Compliance check completed!"

# Documentation
docs-serve: ## Serve documentation locally
	@echo "Serving documentation..."
	python -m http.server 8080 --directory docs

# CI/CD Simulation
ci-test: ## Simulate CI/CD pipeline locally
	@echo "Simulating CI/CD pipeline..."
	make clean
	make install-dev
	make lint
	make test-coverage
	make security-scan
	make docker-build
	@echo "CI/CD simulation completed!"

# Utility Commands
check-deps: ## Check for outdated dependencies
	@echo "Checking for outdated dependencies..."
	pip list --outdated

update-deps: ## Update dependencies (use with caution)
	@echo "Updating dependencies..."
	pip-review --auto

generate-requirements: ## Generate requirements.txt from current environment
	@echo "Generating requirements.txt..."
	pip freeze > requirements-generated.txt
	@echo "Generated requirements-generated.txt"

# Environment Information
info: ## Show environment information
	@echo "Environment Information:"
	@echo "======================"
	@echo "Python version: $$(python --version)"
	@echo "Pip version: $$(pip --version)"
	@echo "Flask version: $$(python -c 'import flask; print(flask.__version__)')"
	@echo "Git branch: $$(git branch --show-current 2>/dev/null || echo 'Not a git repository')"
	@echo "Virtual environment: $$(echo $$VIRTUAL_ENV || echo 'Not in virtual environment')"
	@echo "Working directory: $$(pwd)"

# =============================================================================
# DEVELOPER ONBOARDING & QUALITY MONITORING
# =============================================================================

# Developer Onboarding
onboard: ## Onboard new developer with complete setup
	@echo "🚀 Starting developer onboarding..."
	python scripts/onboard_developer.py

onboard-force: ## Force onboard (recreate everything)
	@echo "🚀 Starting developer onboarding (force mode)..."
	python scripts/onboard_developer.py --force

# Quality Monitoring
quality-monitor: ## Run quality monitoring check
	@echo "📊 Running quality monitoring..."
	python scripts/quality_monitor.py

quality-watch: ## Run quality monitoring in watch mode
	@echo "👀 Starting quality monitoring (watch mode)..."
	python scripts/quality_monitor.py --watch

quality-report: ## Generate quality trend report
	@echo "📈 Generating quality trend report..."
	python scripts/quality_monitor.py --report

quality-threshold: ## Set quality threshold and check
	@echo "🎯 Running quality check with custom threshold..."
	python scripts/quality_monitor.py --threshold $(THRESHOLD)

# Complete Quality Pipeline
quality-pipeline: ## Run complete quality pipeline
	@echo "🔄 Running complete quality pipeline..."
	make lint
	make type-check
	make security-scan
	make test-coverage
	make quality-monitor
	@echo "✅ Quality pipeline completed!"
