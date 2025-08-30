#!/usr/bin/env pwsh
# Docker Development Environment Script for Windows
# This script helps manage the Docker development environment

param(
    [Parameter(Position=0)]
    [ValidateSet('up', 'down', 'restart', 'logs', 'shell', 'db-shell', 'redis-shell', 'build', 'clean', 'status')]
    [string]$Command = 'up',

    [switch]$Build,
    [switch]$Detach,
    [switch]$Follow
)

# Colors for output
$Green = "`e[32m"
$Yellow = "`e[33m"
$Red = "`e[31m"
$Blue = "`e[34m"
$Reset = "`e[0m"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = $Reset)
    Write-Host "$Color$Message$Reset"
}

function Show-Help {
    Write-ColorOutput "Docker Development Environment Manager" $Blue
    Write-ColorOutput "Usage: .\docker-dev.ps1 [command] [options]" $Yellow
    Write-Host ""
    Write-ColorOutput "Commands:" $Green
    Write-Host "  up        Start the development environment (default)"
    Write-Host "  down      Stop the development environment"
    Write-Host "  restart   Restart the development environment"
    Write-Host "  logs      Show application logs"
    Write-Host "  shell     Open shell in the app container"
    Write-Host "  db-shell  Open PostgreSQL shell"
    Write-Host "  redis-shell Open Redis CLI"
    Write-Host "  build     Build/rebuild containers"
    Write-Host "  clean     Clean up containers, volumes, and images"
    Write-Host "  status    Show container status"
    Write-Host ""
    Write-ColorOutput "Options:" $Green
    Write-Host "  -Build    Force rebuild containers"
    Write-Host "  -Detach   Run in background (for 'up' command)"
    Write-Host "  -Follow   Follow logs (for 'logs' command)"
    Write-Host ""
    Write-ColorOutput "Examples:" $Yellow
    Write-Host "  .\docker-dev.ps1 up -Build -Detach"
    Write-Host "  .\docker-dev.ps1 logs -Follow"
    Write-Host "  .\docker-dev.ps1 shell"
}

function Test-DockerRunning {
    try {
        docker info | Out-Null
        return $true
    }
    catch {
        Write-ColorOutput "Error: Docker is not running. Please start Docker Desktop." $Red
        return $false
    }
}

function Start-Environment {
    Write-ColorOutput "Starting development environment..." $Green

    $buildFlag = if ($Build) { "--build" } else { "" }
    $detachFlag = if ($Detach) { "-d" } else { "" }

    $cmd = "docker-compose up $buildFlag $detachFlag"
    Write-ColorOutput "Running: $cmd" $Yellow

    Invoke-Expression $cmd

    if ($LASTEXITCODE -eq 0 -and $Detach) {
        Write-ColorOutput "Environment started successfully!" $Green
        Write-ColorOutput "Application: http://localhost:5000" $Blue
        Write-ColorOutput "Database: localhost:5432" $Blue
        Write-ColorOutput "Redis: localhost:6379" $Blue
    }
}

function Stop-Environment {
    Write-ColorOutput "Stopping development environment..." $Yellow
    docker-compose down
    Write-ColorOutput "Environment stopped." $Green
}

function Restart-Environment {
    Write-ColorOutput "Restarting development environment..." $Yellow
    docker-compose restart
    Write-ColorOutput "Environment restarted." $Green
}

function Show-Logs {
    $followFlag = if ($Follow) { "-f" } else { "" }
    docker-compose logs $followFlag app
}

function Open-AppShell {
    Write-ColorOutput "Opening shell in app container..." $Green
    docker-compose exec app /bin/bash
}

function Open-DbShell {
    Write-ColorOutput "Opening PostgreSQL shell..." $Green
    docker-compose exec db psql -U postgres -d flask_production_template_dev
}

function Open-RedisShell {
    Write-ColorOutput "Opening Redis CLI..." $Green
    docker-compose exec redis redis-cli
}

function Build-Containers {
    Write-ColorOutput "Building containers..." $Green
    docker-compose build --no-cache
    Write-ColorOutput "Build completed." $Green
}

function Clean-Environment {
    Write-ColorOutput "Cleaning up Docker environment..." $Yellow

    # Stop and remove containers
    docker-compose down -v --remove-orphans

    # Remove images
    $images = docker images "flask-production-template*" -q
    if ($images) {
        docker rmi $images -f
    }

    # Clean up unused resources
    docker system prune -f

    Write-ColorOutput "Cleanup completed." $Green
}

function Show-Status {
    Write-ColorOutput "Container Status:" $Blue
    docker-compose ps

    Write-Host ""
    Write-ColorOutput "Resource Usage:" $Blue
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
}

# Main script logic
if (-not (Test-DockerRunning)) {
    exit 1
}

switch ($Command) {
    'up' { Start-Environment }
    'down' { Stop-Environment }
    'restart' { Restart-Environment }
    'logs' { Show-Logs }
    'shell' { Open-AppShell }
    'db-shell' { Open-DbShell }
    'redis-shell' { Open-RedisShell }
    'build' { Build-Containers }
    'clean' { Clean-Environment }
    'status' { Show-Status }
    default { Show-Help }
}
