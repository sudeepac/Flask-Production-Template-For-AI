#!/bin/bash

# Flask Production Template for AI Quick Start Script (Unix/Linux/macOS)
# This script sets up the development environment and starts the Flask application

set -e  # Exit on any error

# Script metadata
SCRIPT_NAME="Flask Production Template for AI Quick Start"
SCRIPT_VERSION="1.0.0"
SCRIPT_AUTHOR="Flask Production Template for AI Project"

# Default configuration
DEFAULT_ENVIRONMENT="development"
DEFAULT_HOST="localhost"
DEFAULT_PORT="5000"
DEFAULT_DEBUG="true"

# Command line arguments
ENVIRONMENT="${1:-$DEFAULT_ENVIRONMENT}"
HOST="${2:-$DEFAULT_HOST}"
PORT="${3:-$DEFAULT_PORT}"
DEBUG="${4:-$DEFAULT_DEBUG}"

# Flags
SKIP_VENV=false
SKIP_DEPS=false
SKIP_DB=false
SKIP_PRECOMMIT=false
VERBOSE=false
HELP=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Output functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1" >&2
}

log_header() {
    echo ""
    echo -e "${CYAN}=== $1 ===${NC}"
}

log_verbose() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${WHITE}[VERBOSE]${NC} $1"
    fi
}

# Help function
show_help() {
    cat << EOF
$SCRIPT_NAME v$SCRIPT_VERSION

Usage: $0 [ENVIRONMENT] [HOST] [PORT] [DEBUG] [OPTIONS]

Arguments:
  ENVIRONMENT    Target environment (development|testing|production) [default: $DEFAULT_ENVIRONMENT]
  HOST          Host address for development server [default: $DEFAULT_HOST]
  PORT          Port number for development server [default: $DEFAULT_PORT]
  DEBUG         Enable debug mode (true|false) [default: $DEFAULT_DEBUG]

Options:
  --skip-venv       Skip virtual environment creation
  --skip-deps       Skip dependency installation
  --skip-db         Skip database initialization
  --skip-precommit  Skip pre-commit hooks setup
  --verbose         Enable verbose output
  --help            Show this help message

Examples:
  $0                                    # Run with defaults
  $0 testing localhost 8000 false      # Testing environment on port 8000
  $0 development --skip-venv --skip-deps # Skip venv and deps
  $0 --help                            # Show help

Environment Variables:
  FLASK_APP         Flask application module [default: app]
  FLASK_ENV         Flask environment [default: ENVIRONMENT]
  FLASK_DEBUG       Flask debug mode [default: DEBUG]
  DATABASE_URL      Database connection URL
  SECRET_KEY        Flask secret key
  JWT_SECRET_KEY    JWT secret key

Requirements:
  - Python 3.8+
  - Git 2.0+
  - pip

Author: $SCRIPT_AUTHOR
EOF
}

# Parse command line options
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-venv)
                SKIP_VENV=true
                shift
                ;;
            --skip-deps)
                SKIP_DEPS=true
                shift
                ;;
            --skip-db)
                SKIP_DB=true
                shift
                ;;
            --skip-precommit)
                SKIP_PRECOMMIT=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help|-h)
                HELP=true
                shift
                ;;
            -*)
                log_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
            *)
                # Positional arguments are handled above
                shift
                ;;
        esac
    done
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Get script directory
get_script_dir() {
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    echo "$script_dir"
}

# Get project root directory
get_project_root() {
    local script_dir
    script_dir="$(get_script_dir)"
    echo "$(dirname "$script_dir")"
}

# Check system requirements
check_requirements() {
    log_header "Checking System Requirements"
    
    local requirements=("python3:Python 3.8+" "git:Git 2.0+" "pip3:pip")
    local all_met=true
    
    for req in "${requirements[@]}"; do
        local cmd="${req%%:*}"
        local name="${req##*:}"
        
        if command_exists "$cmd"; then
            local version
            case "$cmd" in
                python3)
                    version=$(python3 --version 2>&1)
                    ;;
                git)
                    version=$(git --version 2>&1)
                    ;;
                pip3)
                    version=$(pip3 --version 2>&1)
                    ;;
                *)
                    version="installed"
                    ;;
            esac
            log_success "$name is installed: $version"
        else
            log_error "$name is not installed or not in PATH"
            all_met=false
        fi
    done
    
    if [ "$all_met" = false ]; then
        log_error "Please install missing requirements before continuing"
        exit 1
    fi
    
    log_success "All system requirements met"
}

# Create and activate virtual environment
setup_virtual_environment() {
    if [ "$SKIP_VENV" = true ]; then
        log_info "Skipping virtual environment setup"
        return
    fi
    
    log_header "Setting Up Virtual Environment"
    
    local project_root
    project_root="$(get_project_root)"
    local venv_path="$project_root/venv"
    
    if [ -d "$venv_path" ]; then
        log_info "Virtual environment already exists at $venv_path"
    else
        log_info "Creating virtual environment at $venv_path"
        python3 -m venv "$venv_path"
        log_success "Virtual environment created"
    fi
    
    # Activate virtual environment
    local activate_script="$venv_path/bin/activate"
    
    if [ -f "$activate_script" ]; then
        log_info "Activating virtual environment"
        # shellcheck source=/dev/null
        source "$activate_script"
        log_success "Virtual environment activated"
    else
        log_warning "Virtual environment activation script not found"
    fi
}

# Install dependencies
install_dependencies() {
    if [ "$SKIP_DEPS" = true ]; then
        log_info "Skipping dependency installation"
        return
    fi
    
    log_header "Installing Dependencies"
    
    local project_root
    project_root="$(get_project_root)"
    local requirements_file="$project_root/requirements.txt"
    
    if [ ! -f "$requirements_file" ]; then
        log_error "requirements.txt not found at $requirements_file"
        exit 1
    fi
    
    log_info "Installing Python dependencies from requirements.txt"
    
    # Upgrade pip first
    python3 -m pip install --upgrade pip
    
    # Install requirements
    python3 -m pip install -r "$requirements_file"
    
    log_success "Dependencies installed successfully"
}

# Setup pre-commit hooks
setup_precommit_hooks() {
    if [ "$SKIP_PRECOMMIT" = true ]; then
        log_info "Skipping pre-commit hooks setup"
        return
    fi
    
    log_header "Setting Up Pre-commit Hooks"
    
    local project_root
    project_root="$(get_project_root)"
    local precommit_config="$project_root/.pre-commit-config.yaml"
    
    if [ ! -f "$precommit_config" ]; then
        log_warning "Pre-commit config not found, skipping hooks setup"
        return
    fi
    
    if command_exists "pre-commit"; then
        log_info "Installing pre-commit hooks"
        pre-commit install
        log_success "Pre-commit hooks installed"
    else
        log_warning "pre-commit not available, skipping hooks setup"
    fi
}

# Initialize database
init_database() {
    if [ "$SKIP_DB" = true ]; then
        log_info "Skipping database initialization"
        return
    fi
    
    log_header "Initializing Database"
    
    # Set environment variables
    export FLASK_APP="app"
    export FLASK_ENV="$ENVIRONMENT"
    
    # Check if Flask CLI is available
    if command_exists "flask"; then
        local flask_version
        flask_version=$(flask --version 2>&1)
        log_info "Flask CLI available: $flask_version"
    else
        log_warning "Flask CLI not available, skipping database initialization"
        return
    fi
    
    # Initialize database
    log_info "Creating database tables"
    
    # Initialize migration repository
    if flask db init >/dev/null 2>&1; then
        log_info "Database migration repository initialized"
    else
        log_verbose "Database migration repository already exists"
    fi
    
    # Create migration
    if flask db migrate -m "Initial migration" >/dev/null 2>&1; then
        log_info "Database migration created"
    else
        log_verbose "No new migrations to create"
    fi
    
    # Apply migrations
    if flask db upgrade; then
        log_success "Database initialized successfully"
    else
        log_warning "Database upgrade failed or not needed"
    fi
}

# Create environment file
setup_environment() {
    log_header "Setting Up Environment"
    
    local project_root
    project_root="$(get_project_root)"
    local env_file="$project_root/.env"
    
    if [ ! -f "$env_file" ]; then
        log_info "Creating .env file"
        
        cat > "$env_file" << EOF
# Flask Configuration
FLASK_APP=app
FLASK_ENV=$ENVIRONMENT
FLASK_DEBUG=$DEBUG

# Server Configuration
HOST=$HOST
PORT=$PORT

# Database Configuration
DATABASE_URL=sqlite:///app.db

# Security
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=jwt-secret-key-change-in-production

# API Configuration
API_TITLE=Flask Production Template for AI
API_VERSION=1.0.0

# ML Configuration
MODEL_PATH=models/
CACHE_TYPE=simple

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
EOF
        
        log_success ".env file created"
    else
        log_info ".env file already exists"
    fi
    
    # Load environment variables
    if [ -f "$env_file" ]; then
        # shellcheck source=/dev/null
        set -a && source "$env_file" && set +a
        log_success "Environment variables loaded"
    fi
}

# Create necessary directories
setup_directories() {
    log_header "Setting Up Directories"
    
    local project_root
    project_root="$(get_project_root)"
    
    local directories=("logs" "models" "uploads" "temp")
    
    for dir in "${directories[@]}"; do
        local dir_path="$project_root/$dir"
        if [ ! -d "$dir_path" ]; then
            mkdir -p "$dir_path"
            log_info "Created directory: $dir"
        else
            log_verbose "Directory already exists: $dir"
        fi
    done
    
    log_success "Directories setup complete"
}

# Start development server
start_development_server() {
    log_header "Starting Development Server"
    
    # Set Flask environment variables
    export FLASK_APP="app"
    export FLASK_ENV="$ENVIRONMENT"
    export FLASK_DEBUG="$DEBUG"
    
    log_info "Starting Flask development server..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Host: $HOST"
    log_info "Port: $PORT"
    log_info "Debug: $DEBUG"
    echo ""
    log_info "Server will be available at: http://$HOST:$PORT"
    log_info "API documentation: http://$HOST:$PORT/docs"
    echo ""
    log_info "Press Ctrl+C to stop the server"
    echo ""
    
    # Start the server
    if command_exists "flask"; then
        flask run --host="$HOST" --port="$PORT"
    else
        log_error "Flask CLI not available"
        log_info "Trying to start with Python module..."
        python3 -m flask run --host="$HOST" --port="$PORT"
    fi
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    # Add any cleanup tasks here
}

# Signal handlers
trap cleanup EXIT
trap 'log_error "Script interrupted"; exit 130' INT TERM

# Validate environment
validate_environment() {
    case "$ENVIRONMENT" in
        development|testing|production)
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT"
            log_error "Valid environments: development, testing, production"
            exit 1
            ;;
    esac
    
    # Validate port
    if ! [[ "$PORT" =~ ^[0-9]+$ ]] || [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
        log_error "Invalid port: $PORT"
        log_error "Port must be a number between 1 and 65535"
        exit 1
    fi
    
    # Validate debug
    case "$DEBUG" in
        true|false)
            ;;
        *)
            log_error "Invalid debug value: $DEBUG"
            log_error "Debug must be 'true' or 'false'"
            exit 1
            ;;
    esac
}

# Main function
main() {
    # Parse command line arguments
    parse_args "$@"
    
    # Show help if requested
    if [ "$HELP" = true ]; then
        show_help
        exit 0
    fi
    
    # Validate inputs
    validate_environment
    
    log_header "$SCRIPT_NAME"
    log_info "Version: $SCRIPT_VERSION"
    log_info "Environment: $ENVIRONMENT"
    log_info "Host: $HOST"
    log_info "Port: $PORT"
    log_info "Debug: $DEBUG"
    
    local project_root
    project_root="$(get_project_root)"
    log_info "Project root: $project_root"
    
    # Change to project directory
    cd "$project_root" || {
        log_error "Failed to change to project directory: $project_root"
        exit 1
    }
    
    # Run setup steps
    check_requirements
    setup_virtual_environment
    install_dependencies
    setup_precommit_hooks
    setup_environment
    setup_directories
    init_database
    
    log_header "Setup Complete"
    log_success "All setup steps completed successfully!"
    echo ""
    
    # Start development server
    start_development_server
}

# Run main function with all arguments
main "$@"