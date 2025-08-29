#!/usr/bin/env pwsh
# Docker Production Deployment Script for Windows
# This script helps manage production Docker deployments

param(
    [Parameter(Position=0)]
    [ValidateSet('deploy', 'stop', 'restart', 'logs', 'status', 'scale', 'backup', 'restore', 'update')]
    [string]$Command = 'deploy',
    
    [string]$Service = 'app',
    [int]$Replicas = 2,
    [switch]$Build,
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
    Write-ColorOutput "Docker Production Deployment Manager" $Blue
    Write-ColorOutput "Usage: .\docker-prod.ps1 [command] [options]" $Yellow
    Write-Host ""
    Write-ColorOutput "Commands:" $Green
    Write-Host "  deploy    Deploy production environment (default)"
    Write-Host "  stop      Stop production environment"
    Write-Host "  restart   Restart production environment"
    Write-Host "  logs      Show application logs"
    Write-Host "  status    Show deployment status"
    Write-Host "  scale     Scale service replicas"
    Write-Host "  backup    Backup database"
    Write-Host "  restore   Restore database from backup"
    Write-Host "  update    Update application (rolling update)"
    Write-Host ""
    Write-ColorOutput "Options:" $Green
    Write-Host "  -Service   Target service (default: app)"
    Write-Host "  -Replicas  Number of replicas for scaling (default: 2)"
    Write-Host "  -Build     Force rebuild containers"
    Write-Host "  -Follow    Follow logs"
    Write-Host ""
    Write-ColorOutput "Examples:" $Yellow
    Write-Host "  .\docker-prod.ps1 deploy -Build"
    Write-Host "  .\docker-prod.ps1 scale -Service app -Replicas 4"
    Write-Host "  .\docker-prod.ps1 logs -Follow"
    Write-Host "  .\docker-prod.ps1 backup"
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

function Test-EnvironmentFile {
    if (-not (Test-Path ".env.prod")) {
        Write-ColorOutput "Warning: .env.prod file not found. Creating template..." $Yellow
        
        $envTemplate = @"
# Production Environment Variables
# Copy this file to .env.prod and update with your production values

# Database
POSTGRES_DB=flask_production_template_prod
POSTGRES_USER=postgres
POSTGRES_PASSWORD=change-this-secure-password

# Application
SECRET_KEY=change-this-to-a-secure-random-string
JWT_SECRET_KEY=change-this-to-a-secure-jwt-secret
FLASK_ENV=production

# SSL (if using custom certificates)
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem

# Monitoring (optional)
SENTRY_DSN=
NEW_RELIC_LICENSE_KEY=
"@
        
        $envTemplate | Out-File -FilePath ".env.prod" -Encoding UTF8
        Write-ColorOutput "Template .env.prod created. Please update with your production values." $Red
        return $false
    }
    return $true
}

function Deploy-Production {
    Write-ColorOutput "Deploying production environment..." $Green
    
    if (-not (Test-EnvironmentFile)) {
        Write-ColorOutput "Please configure .env.prod before deploying." $Red
        return
    }
    
    $buildFlag = if ($Build) { "--build" } else { ""
    
    # Use production compose file
    $cmd = "docker-compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod up -d $buildFlag --remove-orphans"
    Write-ColorOutput "Running: $cmd" $Yellow
    
    Invoke-Expression $cmd
    
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "Production environment deployed successfully!" $Green
        Write-ColorOutput "Application: https://localhost (via Nginx)" $Blue
        Write-ColorOutput "Direct access: http://localhost:5000" $Blue
        
        # Wait for health checks
        Write-ColorOutput "Waiting for health checks..." $Yellow
        Start-Sleep -Seconds 30
        
        Show-Status
    }
}

function Stop-Production {
    Write-ColorOutput "Stopping production environment..." $Yellow
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
    Write-ColorOutput "Production environment stopped." $Green
}

function Restart-Production {
    Write-ColorOutput "Restarting production environment..." $Yellow
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart
    Write-ColorOutput "Production environment restarted." $Green
}

function Show-Logs {
    $followFlag = if ($Follow) { "-f" } else { ""
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs $followFlag $Service
}

function Scale-Service {
    Write-ColorOutput "Scaling $Service to $Replicas replicas..." $Green
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale $Service=$Replicas
    Write-ColorOutput "Service scaled successfully." $Green
}

function Backup-Database {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = "backup_$timestamp.sql"
    
    Write-ColorOutput "Creating database backup: $backupFile" $Green
    
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec -T db pg_dump -U postgres flask_production_template_prod > $backupFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "Database backup created successfully: $backupFile" $Green
    } else {
        Write-ColorOutput "Database backup failed!" $Red
    }
}

function Restore-Database {
    $backupFiles = Get-ChildItem -Path "." -Filter "backup_*.sql" | Sort-Object LastWriteTime -Descending
    
    if ($backupFiles.Count -eq 0) {
        Write-ColorOutput "No backup files found!" $Red
        return
    }
    
    Write-ColorOutput "Available backup files:" $Blue
    for ($i = 0; $i -lt $backupFiles.Count; $i++) {
        Write-Host "  [$i] $($backupFiles[$i].Name) ($($backupFiles[$i].LastWriteTime))"
    }
    
    $selection = Read-Host "Select backup file to restore (0-$($backupFiles.Count-1))"
    
    if ($selection -match '^\d+$' -and [int]$selection -lt $backupFiles.Count) {
        $selectedFile = $backupFiles[[int]$selection].Name
        Write-ColorOutput "Restoring database from: $selectedFile" $Yellow
        
        # Stop app containers to prevent connections
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml stop app
        
        # Restore database
        Get-Content $selectedFile | docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec -T db psql -U postgres -d flask_production_template_prod
        
        # Restart app containers
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml start app
        
        Write-ColorOutput "Database restored successfully." $Green
    } else {
        Write-ColorOutput "Invalid selection." $Red
    }
}

function Update-Application {
    Write-ColorOutput "Performing rolling update..." $Green
    
    # Build new image
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml build app
    
    # Rolling update
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps app
    
    Write-ColorOutput "Rolling update completed." $Green
}

function Show-Status {
    Write-ColorOutput "Production Deployment Status:" $Blue
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps
    
    Write-Host ""
    Write-ColorOutput "Health Checks:" $Blue
    
    # Check app health
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000/health/" -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-ColorOutput "✓ Application health check: PASSED" $Green
        } else {
            Write-ColorOutput "✗ Application health check: FAILED (Status: $($response.StatusCode))" $Red
        }
    } catch {
        Write-ColorOutput "✗ Application health check: FAILED (Connection error)" $Red
    }
    
    Write-Host ""
    Write-ColorOutput "Resource Usage:" $Blue
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
}

# Main script logic
if (-not (Test-DockerRunning)) {
    exit 1
}

switch ($Command) {
    'deploy' { Deploy-Production }
    'stop' { Stop-Production }
    'restart' { Restart-Production }
    'logs' { Show-Logs }
    'status' { Show-Status }
    'scale' { Scale-Service }
    'backup' { Backup-Database }
    'restore' { Restore-Database }
    'update' { Update-Application }
    default { Show-Help }
}