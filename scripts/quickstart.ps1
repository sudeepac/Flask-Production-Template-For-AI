#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Quick start script for the Flask Production Template project (Windows PowerShell)

.DESCRIPTION
    This script sets up the development environment, installs dependencies,
    initializes the database, and starts the development server.
    
    Features:
    - Virtual environment creation and activation
    - Dependency installation
    - Database initialization
    - Pre-commit hooks setup
    - Development server startup
    - Environment validation

.PARAMETER Environment
    Target environment (development, testing, production)
    Default: development

.PARAMETER SkipVenv
    Skip virtual environment creation

.PARAMETER SkipDeps
    Skip dependency installation

.PARAMETER SkipDB
    Skip database initialization

.PARAMETER SkipPreCommit
    Skip pre-commit hooks setup

.PARAMETER Port
    Port number for development server
    Default: 5000

.PARAMETER Host
    Host address for development server
    Default: localhost

.PARAMETER Debug
    Enable debug mode
    Default: true for development

.EXAMPLE
    .\scripts\quickstart.ps1
    Run with default settings

.EXAMPLE
    .\scripts\quickstart.ps1 -Environment testing -Port 8000
    Run in testing environment on port 8000

.EXAMPLE
    .\scripts\quickstart.ps1 -SkipVenv -SkipDeps
    Skip virtual environment and dependency installation

.NOTES
    Author: Flask Production Template Project
    Version: 1.0.0
    Requires: PowerShell 5.1+ or PowerShell Core 6+
#>

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('development', 'testing', 'production')]
    [string]$Environment = 'development',
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipVenv,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipDeps,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipDB,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipPreCommit,
    
    [Parameter(Mandatory=$false)]
    [int]$Port = 5000,
    
    [Parameter(Mandatory=$false)]
    [string]$Host = 'localhost',
    
    [Parameter(Mandatory=$false)]
    [bool]$Debug = ($Environment -eq 'development')
)

# Set error action preference
$ErrorActionPreference = 'Stop'

# Color functions for output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = 'White'
    )
    
    $colors = @{
        'Red' = 'Red'
        'Green' = 'Green'
        'Yellow' = 'Yellow'
        'Blue' = 'Blue'
        'Magenta' = 'Magenta'
        'Cyan' = 'Cyan'
        'White' = 'White'
    }
    
    Write-Host $Message -ForegroundColor $colors[$Color]
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "✓ $Message" 'Green'
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput "ℹ $Message" 'Blue'
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "⚠ $Message" 'Yellow'
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "✗ $Message" 'Red'
}

function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-ColorOutput "=== $Message ===" 'Cyan'
}

# Check if command exists
function Test-Command {
    param([string]$Command)
    
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Get project root directory
function Get-ProjectRoot {
    $scriptDir = Split-Path -Parent $PSScriptRoot
    return $scriptDir
}

# Check system requirements
function Test-SystemRequirements {
    Write-Header "Checking System Requirements"
    
    $requirements = @(
        @{ Name = 'Python'; Command = 'python'; MinVersion = '3.8' },
        @{ Name = 'Git'; Command = 'git'; MinVersion = '2.0' }
    )
    
    $allMet = $true
    
    foreach ($req in $requirements) {
        if (Test-Command $req.Command) {
            try {
                $version = & $req.Command --version 2>$null
                Write-Success "$($req.Name) is installed: $version"
            }
            catch {
                Write-Success "$($req.Name) is installed"
            }
        }
        else {
            Write-Error "$($req.Name) is not installed or not in PATH"
            $allMet = $false
        }
    }
    
    if (-not $allMet) {
        Write-Error "Please install missing requirements before continuing"
        exit 1
    }
    
    Write-Success "All system requirements met"
}

# Create and activate virtual environment
function Initialize-VirtualEnvironment {
    param([string]$ProjectRoot)
    
    if ($SkipVenv) {
        Write-Info "Skipping virtual environment setup"
        return
    }
    
    Write-Header "Setting Up Virtual Environment"
    
    $venvPath = Join-Path $ProjectRoot 'venv'
    
    if (Test-Path $venvPath) {
        Write-Info "Virtual environment already exists at $venvPath"
    }
    else {
        Write-Info "Creating virtual environment at $venvPath"
        python -m venv $venvPath
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to create virtual environment"
            exit 1
        }
        
        Write-Success "Virtual environment created"
    }
    
    # Activate virtual environment
    $activateScript = Join-Path $venvPath 'Scripts\Activate.ps1'
    
    if (Test-Path $activateScript) {
        Write-Info "Activating virtual environment"
        & $activateScript
        Write-Success "Virtual environment activated"
    }
    else {
        Write-Warning "Virtual environment activation script not found"
    }
}

# Install dependencies
function Install-Dependencies {
    param([string]$ProjectRoot)
    
    if ($SkipDeps) {
        Write-Info "Skipping dependency installation"
        return
    }
    
    Write-Header "Installing Dependencies"
    
    $requirementsFile = Join-Path $ProjectRoot 'requirements.txt'
    
    if (-not (Test-Path $requirementsFile)) {
        Write-Error "requirements.txt not found at $requirementsFile"
        exit 1
    }
    
    Write-Info "Installing Python dependencies from requirements.txt"
    python -m pip install --upgrade pip
    python -m pip install -r $requirementsFile
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install dependencies"
        exit 1
    }
    
    Write-Success "Dependencies installed successfully"
}

# Setup pre-commit hooks
function Initialize-PreCommitHooks {
    param([string]$ProjectRoot)
    
    if ($SkipPreCommit) {
        Write-Info "Skipping pre-commit hooks setup"
        return
    }
    
    Write-Header "Setting Up Pre-commit Hooks"
    
    $preCommitConfig = Join-Path $ProjectRoot '.pre-commit-config.yaml'
    
    if (-not (Test-Path $preCommitConfig)) {
        Write-Warning "Pre-commit config not found, skipping hooks setup"
        return
    }
    
    if (Test-Command 'pre-commit') {
        Write-Info "Installing pre-commit hooks"
        pre-commit install
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Pre-commit hooks installed"
        }
        else {
            Write-Warning "Failed to install pre-commit hooks"
        }
    }
    else {
        Write-Warning "pre-commit not available, skipping hooks setup"
    }
}

# Initialize database
function Initialize-Database {
    param([string]$ProjectRoot)
    
    if ($SkipDB) {
        Write-Info "Skipping database initialization"
        return
    }
    
    Write-Header "Initializing Database"
    
    # Set environment variables
    $env:FLASK_APP = 'app'
    $env:FLASK_ENV = $Environment
    
    # Check if Flask CLI is available
    try {
        $flaskVersion = flask --version 2>$null
        Write-Info "Flask CLI available: $flaskVersion"
    }
    catch {
        Write-Warning "Flask CLI not available, skipping database initialization"
        return
    }
    
    # Initialize database
    Write-Info "Creating database tables"
    
    try {
        flask db init 2>$null
        Write-Info "Database migration repository initialized"
    }
    catch {
        Write-Info "Database migration repository already exists"
    }
    
    try {
        flask db migrate -m "Initial migration" 2>$null
        Write-Info "Database migration created"
    }
    catch {
        Write-Info "No new migrations to create"
    }
    
    try {
        flask db upgrade
        Write-Success "Database initialized successfully"
    }
    catch {
        Write-Warning "Database upgrade failed or not needed"
    }
}

# Create environment file
function Initialize-Environment {
    param([string]$ProjectRoot)
    
    Write-Header "Setting Up Environment"
    
    $envFile = Join-Path $ProjectRoot '.env'
    
    if (-not (Test-Path $envFile)) {
        Write-Info "Creating .env file"
        
        $envContent = @"
# Flask Configuration
FLASK_APP=app
FLASK_ENV=$Environment
FLASK_DEBUG=$($Debug.ToString().ToLower())

# Server Configuration
HOST=$Host
PORT=$Port

# Database Configuration
DATABASE_URL=sqlite:///app.db

# Security
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=jwt-secret-key-change-in-production

# API Configuration
API_TITLE=Flask Production Template
API_VERSION=1.0.0

# ML Configuration
MODEL_PATH=models/
CACHE_TYPE=simple

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
"@
        
        $envContent | Out-File -FilePath $envFile -Encoding UTF8
        Write-Success ".env file created"
    }
    else {
        Write-Info ".env file already exists"
    }
    
    # Load environment variables
    if (Test-Path $envFile) {
        Get-Content $envFile | ForEach-Object {
            if ($_ -match '^([^#][^=]+)=(.*)$') {
                [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
            }
        }
        Write-Success "Environment variables loaded"
    }
}

# Start development server
function Start-DevelopmentServer {
    param([string]$ProjectRoot)
    
    Write-Header "Starting Development Server"
    
    # Set Flask environment variables
    $env:FLASK_APP = 'app'
    $env:FLASK_ENV = $Environment
    $env:FLASK_DEBUG = $Debug.ToString().ToLower()
    
    Write-Info "Starting Flask development server..."
    Write-Info "Environment: $Environment"
    Write-Info "Host: $Host"
    Write-Info "Port: $Port"
    Write-Info "Debug: $Debug"
    Write-Info ""
    Write-Info "Server will be available at: http://$Host`:$Port"
    Write-Info "API documentation: http://$Host`:$Port/docs"
    Write-Info ""
    Write-Info "Press Ctrl+C to stop the server"
    Write-Info ""
    
    try {
        flask run --host=$Host --port=$Port
    }
    catch {
        Write-Error "Failed to start development server"
        Write-Error $_.Exception.Message
        exit 1
    }
}

# Main execution
function Main {
    try {
        Write-Header "Flask Production Template Quick Start"
        Write-Info "Environment: $Environment"
        Write-Info "Host: $Host"
        Write-Info "Port: $Port"
        Write-Info "Debug: $Debug"
        
        $projectRoot = Get-ProjectRoot
        Write-Info "Project root: $projectRoot"
        
        # Change to project directory
        Set-Location $projectRoot
        
        # Run setup steps
        Test-SystemRequirements
        Initialize-VirtualEnvironment -ProjectRoot $projectRoot
        Install-Dependencies -ProjectRoot $projectRoot
        Initialize-PreCommitHooks -ProjectRoot $projectRoot
        Initialize-Environment -ProjectRoot $projectRoot
        Initialize-Database -ProjectRoot $projectRoot
        
        Write-Header "Setup Complete"
        Write-Success "All setup steps completed successfully!"
        Write-Info ""
        
        # Start development server
        Start-DevelopmentServer -ProjectRoot $projectRoot
    }
    catch {
        Write-Error "Setup failed: $($_.Exception.Message)"
        Write-Error "Stack trace: $($_.ScriptStackTrace)"
        exit 1
    }
}

# Run main function
Main