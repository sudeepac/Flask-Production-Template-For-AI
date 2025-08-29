# Docker Deployment Guide

This directory contains Docker configuration files for containerized deployment of the Flask Production Template application.

## Quick Start

### Development Environment

```powershell
# Start development environment
.\docker-dev.ps1 up -Build

# View logs
.\docker-dev.ps1 logs -Follow

# Open application shell
.\docker-dev.ps1 shell

# Stop environment
.\docker-dev.ps1 down
```

### Production Environment

```powershell
# Configure production environment
cp .env.example .env.prod
# Edit .env.prod with your production values

# Deploy production environment
.\docker-prod.ps1 deploy -Build

# Check status
.\docker-prod.ps1 status

# Scale application
.\docker-prod.ps1 scale -Replicas 4
```

## Architecture

### Development Stack
- **Flask App**: Development server with hot reload
- **PostgreSQL**: Database with persistent storage
- **Redis**: Caching and session storage
- **Volumes**: Code mounted for live editing

### Production Stack
- **Flask App**: Gunicorn WSGI server with multiple workers
- **Nginx**: Reverse proxy with SSL termination and load balancing
- **PostgreSQL**: Optimized database configuration
- **Redis**: Persistent cache with memory optimization
- **Health Checks**: Automated container health monitoring

## Configuration Files

### Core Files
- `Dockerfile`: Multi-stage build (development/production)
- `docker-compose.yml`: Base services configuration
- `docker-compose.prod.yml`: Production overrides
- `.dockerignore`: Build context optimization

### Scripts
- `docker-dev.ps1`: Development environment management
- `docker-prod.ps1`: Production deployment management

### Nginx
- `nginx/nginx.conf`: Production reverse proxy configuration
- SSL termination and security headers
- Rate limiting and load balancing
- Static file serving

## Environment Variables

### Development (.env)
```bash
FLASK_ENV=development
FLASK_DEBUG=1
DATABASE_URL=postgresql://postgres:password@db:5432/flask_production_template_dev
REDIS_URL=redis://redis:6379/0
SECRET_KEY=dev-secret-key
JWT_SECRET_KEY=dev-jwt-secret
```

### Production (.env.prod)
```bash
FLASK_ENV=production
FLASK_DEBUG=0
POSTGRES_DB=flask_production_template_prod
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secure-password
DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
REDIS_URL=redis://redis:6379/0
SECRET_KEY=secure-random-string
JWT_SECRET_KEY=secure-jwt-secret
```

## Service Endpoints

### Development
- **Application**: http://localhost:5000
- **Database**: localhost:5432
- **Redis**: localhost:6379

### Production
- **Application (Nginx)**: https://localhost
- **Application (Direct)**: http://localhost:5000
- **Database**: localhost:5432 (if exposed)
- **Redis**: localhost:6379 (if exposed)

## Management Commands

### Development Commands
```powershell
# Start with rebuild
.\docker-dev.ps1 up -Build

# Start in background
.\docker-dev.ps1 up -Detach

# View logs
.\docker-dev.ps1 logs -Follow

# Open shells
.\docker-dev.ps1 shell        # App container
.\docker-dev.ps1 db-shell     # PostgreSQL
.\docker-dev.ps1 redis-shell  # Redis CLI

# Clean environment
.\docker-dev.ps1 clean
```

### Production Commands
```powershell
# Deploy
.\docker-prod.ps1 deploy -Build

# Scale services
.\docker-prod.ps1 scale -Service app -Replicas 4

# Database operations
.\docker-prod.ps1 backup
.\docker-prod.ps1 restore

# Rolling updates
.\docker-prod.ps1 update

# Monitor
.\docker-prod.ps1 status
.\docker-prod.ps1 logs -Follow
```

## Health Checks

### Application Health
- **Endpoint**: `/health/`
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3

### Database Health
- Connection testing
- Query performance monitoring
- Automatic failover (in clustered setup)

### Redis Health
- Connection testing
- Memory usage monitoring
- Cache hit rate tracking

## Security Features

### Nginx Security
- SSL/TLS termination
- Security headers (HSTS, CSP, etc.)
- Rate limiting
- Request size limits

### Container Security
- Non-root user execution
- Minimal base images
- Security scanning
- Resource limits

## Monitoring & Logging

### Application Logs
```powershell
# View all logs
docker-compose logs

# Follow specific service
docker-compose logs -f app

# View with timestamps
docker-compose logs -t app
```

### Resource Monitoring
```powershell
# Container stats
docker stats

# Service status
docker-compose ps

# Health status
docker-compose exec app curl -f http://localhost:5000/health/
```

## Troubleshooting

### Common Issues

1. **Port conflicts**
   ```powershell
   # Check port usage
   netstat -an | findstr :5000
   ```

2. **Database connection issues**
   ```powershell
   # Check database logs
   docker-compose logs db
   
   # Test connection
   docker-compose exec app python -c "from app.extensions import db; print(db.engine.execute('SELECT 1').scalar())"
   ```

3. **Memory issues**
   ```powershell
   # Check resource usage
   docker stats --no-stream
   
   # Increase memory limits in docker-compose.prod.yml
   ```

4. **SSL certificate issues**
   ```powershell
   # Generate self-signed certificates for testing
   mkdir -p docker/nginx/ssl
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout docker/nginx/ssl/key.pem \
     -out docker/nginx/ssl/cert.pem
   ```

### Performance Tuning

1. **Application scaling**
   - Increase Gunicorn workers
   - Scale container replicas
   - Optimize database queries

2. **Database optimization**
   - Tune PostgreSQL configuration
   - Add connection pooling
   - Implement read replicas

3. **Cache optimization**
   - Tune Redis memory settings
   - Implement cache warming
   - Monitor cache hit rates

## Backup & Recovery

### Database Backup
```powershell
# Automated backup
.\docker-prod.ps1 backup

# Manual backup
docker-compose exec db pg_dump -U postgres flask_production_template_prod > backup.sql
```

### Database Restore
```powershell
# Automated restore
.\docker-prod.ps1 restore

# Manual restore
cat backup.sql | docker-compose exec -T db psql -U postgres -d flask_production_template_prod
```

### Volume Backup
```powershell
# Backup volumes
docker run --rm -v flask_production_template_postgres_data:/data -v ${PWD}:/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .
docker run --rm -v flask_production_template_redis_data:/data -v ${PWD}:/backup alpine tar czf /backup/redis_backup.tar.gz -C /data .
```

## CI/CD Integration

The Docker configuration is designed to work with CI/CD pipelines:

1. **Build stage**: `docker build --target production`
2. **Test stage**: `docker-compose -f docker-compose.test.yml up --abort-on-container-exit`
3. **Deploy stage**: `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d`

See the main README.md for complete CI/CD pipeline examples.