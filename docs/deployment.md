# Production Deployment Guide

This guide provides comprehensive instructions for deploying the Flask Production Template for AI to production environments.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Docker Deployment](#docker-deployment)
- [Traditional Deployment](#traditional-deployment)
- [Database Setup](#database-setup)
- [Security Configuration](#security-configuration)
- [Monitoring and Logging](#monitoring-and-logging)
- [Performance Optimization](#performance-optimization)
- [Backup and Recovery](#backup-and-recovery)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

The Flask Production Template for AI supports multiple deployment strategies:

- **Docker Deployment** (Recommended): Containerized deployment with Docker Compose
- **Traditional Deployment**: Direct server deployment with systemd
- **Cloud Deployment**: AWS, GCP, Azure with container services
- **Kubernetes**: Scalable container orchestration

## 📋 Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+ recommended), Windows Server, or macOS
- **Python**: 3.8 or higher
- **Memory**: Minimum 2GB RAM (4GB+ recommended)
- **Storage**: 10GB+ available space
- **Network**: HTTPS-capable domain (for production)

### Required Software

```bash
# Docker deployment
sudo apt update
sudo apt install docker.io docker-compose
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Traditional deployment
sudo apt install python3 python3-pip python3-venv nginx postgresql
```

## 🔧 Environment Setup

### 1. Production Environment Variables

Create a production `.env` file:

```bash
# Security (REQUIRED)
SECRET_KEY=your-super-secure-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# Environment
FLASK_ENV=production
FLASK_DEBUG=False

# Database (PostgreSQL recommended for production)
DATABASE_URL=postgresql://username:password@localhost:5432/your_db

# Redis Cache
REDIS_URL=redis://localhost:6379/0

# Security Headers
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True

# CORS (adjust for your frontend domain)
CORS_ORIGINS=https://yourdomain.com

# File Uploads
UPLOAD_FOLDER=/var/www/uploads
MAX_CONTENT_LENGTH=16777216

# Logging
LOG_LEVEL=WARNING
LOG_FILE=/var/log/flask-app/app.log

# Performance
WORKERS=4
WORKER_CONNECTIONS=1000
```

### 2. Generate Secure Keys

```bash
# Generate SECRET_KEY
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"

# Generate JWT_SECRET_KEY
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"
```

## 🐳 Docker Deployment (Recommended)

### 1. Production Docker Compose

Use the provided production configuration:

```bash
# Clone and setup
git clone <your-repo-url>
cd flask-production-template

# Copy and configure environment
cp .env.example .env
# Edit .env with production values

# Deploy with production compose
docker-compose -f docker-compose.prod.yml up -d
```

### 2. Production Docker Compose Configuration

The `docker-compose.prod.yml` includes:

- **Flask App**: Gunicorn WSGI server
- **PostgreSQL**: Production database
- **Redis**: Caching and sessions
- **Nginx**: Reverse proxy and static files
- **Certbot**: SSL certificate management

### 3. SSL Certificate Setup

```bash
# Initial certificate generation
docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot --webroot-path=/var/www/certbot \
  -d yourdomain.com -d www.yourdomain.com

# Auto-renewal (add to crontab)
0 12 * * * docker-compose -f docker-compose.prod.yml run --rm certbot renew
```

### 4. Health Checks and Monitoring

```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f app

# Health check endpoint
curl https://yourdomain.com/health
```

## 🖥️ Traditional Deployment

### 1. Server Setup

```bash
# Create application user
sudo useradd -m -s /bin/bash flaskapp
sudo su - flaskapp

# Clone repository
git clone <your-repo-url> /home/flaskapp/app
cd /home/flaskapp/app

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Gunicorn Configuration

Create `/home/flaskapp/app/gunicorn.conf.py`:

```python
# Gunicorn configuration
bind = "127.0.0.1:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
user = "flaskapp"
group = "flaskapp"
tmp_upload_dir = None
logfile = "/var/log/gunicorn/access.log"
loglevel = "info"
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
```

### 3. Systemd Service

Create `/etc/systemd/system/flaskapp.service`:

```ini
[Unit]
Description=Flask Production Template for AI
After=network.target

[Service]
User=flaskapp
Group=flaskapp
WorkingDirectory=/home/flaskapp/app
Environment=PATH=/home/flaskapp/app/venv/bin
EnvironmentFile=/home/flaskapp/app/.env
ExecStart=/home/flaskapp/app/venv/bin/gunicorn -c gunicorn.conf.py "app:create_app()"
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable flaskapp
sudo systemctl start flaskapp
sudo systemctl status flaskapp
```

### 4. Nginx Configuration

Create `/etc/nginx/sites-available/flaskapp`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # Static files
    location /static {
        alias /home/flaskapp/app/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Uploads
    location /uploads {
        alias /var/www/uploads;
        expires 1y;
    }

    # Application
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/flaskapp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🗄️ Database Setup

### PostgreSQL Production Setup

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE your_db;
CREATE USER your_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE your_db TO your_user;
\q

# Run migrations
cd /home/flaskapp/app
source venv/bin/activate
flask db upgrade
```

### Database Backup

```bash
# Create backup script
cat > /home/flaskapp/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
pg_dump your_db > $BACKUP_DIR/backup_$DATE.sql
find $BACKUP_DIR -name "backup_*.sql" -mtime +7 -delete
EOF

chmod +x /home/flaskapp/backup.sh

# Add to crontab
echo "0 2 * * * /home/flaskapp/backup.sh" | sudo crontab -u flaskapp -
```

## 🔒 Security Configuration

### 1. Firewall Setup

```bash
# UFW firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw status
```

### 2. SSL/TLS Configuration

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 3. Security Hardening

```bash
# Disable root login
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart ssh

# Update system
sudo apt update && sudo apt upgrade -y

# Install fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

## 📊 Monitoring and Logging

### 1. Log Management

```bash
# Create log directories
sudo mkdir -p /var/log/flask-app
sudo mkdir -p /var/log/gunicorn
sudo chown flaskapp:flaskapp /var/log/flask-app
sudo chown flaskapp:flaskapp /var/log/gunicorn

# Logrotate configuration
sudo cat > /etc/logrotate.d/flaskapp << 'EOF'
/var/log/flask-app/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 flaskapp flaskapp
    postrotate
        systemctl reload flaskapp
    endscript
}
EOF
```

### 2. Health Monitoring

```bash
# Simple health check script
cat > /home/flaskapp/health_check.sh << 'EOF'
#!/bin/bash
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" https://yourdomain.com/health)
if [ $RESPONSE -ne 200 ]; then
    echo "Health check failed: $RESPONSE" | logger -t flaskapp
    # Add notification logic here
fi
EOF

chmod +x /home/flaskapp/health_check.sh

# Add to crontab (every 5 minutes)
echo "*/5 * * * * /home/flaskapp/health_check.sh" | sudo crontab -u flaskapp -
```

## ⚡ Performance Optimization

### 1. Gunicorn Tuning

```python
# Optimal worker calculation
# workers = (2 x CPU cores) + 1
# For 2 CPU cores: workers = 5
# For 4 CPU cores: workers = 9

# Memory-based calculation
# workers = Available RAM / Worker Memory Usage
# Typical Flask app uses 50-100MB per worker
```

### 2. Database Optimization

```sql
-- PostgreSQL performance tuning
-- Add to postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
max_connections = 100
```

### 3. Caching Strategy

```bash
# Redis configuration for production
# Add to /etc/redis/redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

## 💾 Backup and Recovery

### 1. Complete Backup Script

```bash
cat > /home/flaskapp/full_backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/flaskapp"
DATE=$(date +%Y%m%d_%H%M%S)
APP_DIR="/home/flaskapp/app"

mkdir -p $BACKUP_DIR

# Database backup
pg_dump your_db > $BACKUP_DIR/db_$DATE.sql

# Application files backup
tar -czf $BACKUP_DIR/app_$DATE.tar.gz -C $APP_DIR .

# Uploads backup
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz -C /var/www uploads

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*_*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*_*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE" | logger -t flaskapp-backup
EOF

chmod +x /home/flaskapp/full_backup.sh

# Schedule daily backups
echo "0 3 * * * /home/flaskapp/full_backup.sh" | sudo crontab -u flaskapp -
```

### 2. Recovery Procedures

```bash
# Database recovery
psql your_db < /var/backups/flaskapp/db_YYYYMMDD_HHMMSS.sql

# Application recovery
cd /home/flaskapp
tar -xzf /var/backups/flaskapp/app_YYYYMMDD_HHMMSS.tar.gz

# Uploads recovery
cd /var/www
tar -xzf /var/backups/flaskapp/uploads_YYYYMMDD_HHMMSS.tar.gz
```

## 🔧 Troubleshooting

### Common Issues

1. **Application won't start**

   ```bash
   # Check service status
   sudo systemctl status flaskapp

   # Check logs
   sudo journalctl -u flaskapp -f
   ```

2. **Database connection errors**

   ```bash
   # Test database connection
   psql -h localhost -U your_user -d your_db

   # Check PostgreSQL status
   sudo systemctl status postgresql
   ```

3. **SSL certificate issues**

   ```bash
   # Check certificate status
   sudo certbot certificates

   # Renew certificates
   sudo certbot renew --dry-run
   ```

### Performance Issues

1. **High memory usage**

   ```bash
   # Monitor memory
   htop

   # Check worker processes
   ps aux | grep gunicorn
   ```

2. **Slow database queries**

   ```sql
   -- Enable query logging in PostgreSQL
   ALTER SYSTEM SET log_statement = 'all';
   SELECT pg_reload_conf();
   ```

## 📚 Additional Resources

- [Flask Deployment Options](https://flask.palletsprojects.com/en/2.0.x/deploying/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Security Best Practices](docs/security.md)

---

**Next Steps**: After deployment, review the [Security Guide](security.md) and set up monitoring as described in the [Configuration Guide](configuration.md).
