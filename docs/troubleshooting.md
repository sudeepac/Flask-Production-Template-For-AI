# Troubleshooting Guide

This guide provides solutions to common issues and debugging techniques for the Flask Production Template for AI.

## 📋 Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Application Startup Issues](#application-startup-issues)
- [Database Problems](#database-problems)
- [Authentication & Authorization Issues](#authentication--authorization-issues)
- [API & Request Issues](#api--request-issues)
- [Performance Problems](#performance-problems)
- [Docker & Deployment Issues](#docker--deployment-issues)
- [Security-Related Issues](#security-related-issues)
- [Development Environment Issues](#development-environment-issues)
- [Logging & Monitoring](#logging--monitoring)
- [Common Error Messages](#common-error-messages)
- [Debugging Tools & Techniques](#debugging-tools--techniques)

## 🔍 Quick Diagnostics

### Health Check Commands

```bash
# Check application health
curl http://localhost:5000/health

# Check database connection
flask db-health

# Check Redis connection
redis-cli ping

# Check all services status
docker-compose ps

# View recent logs
docker-compose logs --tail=50 app
```

### System Status Script

```bash
#!/bin/bash
# quick-diagnosis.sh

echo "=== Flask Production Template Diagnostics ==="
echo

# Check Python version
echo "Python Version:"
python3 --version
echo

# Check Flask app status
echo "Flask App Status:"
if pgrep -f "flask run\|gunicorn" > /dev/null; then
    echo "✅ Flask app is running"
else
    echo "❌ Flask app is not running"
fi
echo

# Check database connection
echo "Database Status:"
if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "✅ PostgreSQL is accessible"
else
    echo "❌ PostgreSQL is not accessible"
fi
echo

# Check Redis connection
echo "Redis Status:"
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is accessible"
else
    echo "❌ Redis is not accessible"
fi
echo

# Check disk space
echo "Disk Usage:"
df -h | grep -E '^/dev/'
echo

# Check memory usage
echo "Memory Usage:"
free -h
echo

# Check recent errors
echo "Recent Errors (last 10):"
tail -n 10 /var/log/flask-app/app.log | grep -i error || echo "No recent errors found"
```

## 🚀 Application Startup Issues

### Issue: Application Won't Start

**Symptoms:**

- Flask app fails to start
- Import errors
- Configuration errors

**Solutions:**

```bash
# 1. Check Python environment
source venv/bin/activate
python3 -c "import flask; print(flask.__version__)"

# 2. Verify dependencies
pip install -r requirements.txt
pip check

# 3. Check environment variables
echo $FLASK_APP
echo $FLASK_ENV
cat .env | grep -v '^#' | grep -v '^$'

# 4. Test configuration
python3 -c "from app.config import Config; print('Config loaded successfully')"

# 5. Check for syntax errors
python3 -m py_compile app/__init__.py
flake8 app/ --select=E9,F63,F7,F82
```

### Issue: Import Errors

**Common Import Problems:**

```python
# Problem: Circular imports
# Solution: Move imports inside functions or use late imports

# Instead of:
# from app.models import User  # At top of file

# Use:
def get_user(user_id):
    from app.models import User  # Inside function
    return User.query.get(user_id)

# Problem: Missing __init__.py files
# Solution: Ensure all directories have __init__.py
find app/ -type d -exec touch {}/__init__.py \;

# Problem: PYTHONPATH issues
# Solution: Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: Configuration Problems

```python
# Debug configuration loading
from app.config import Config
import os

print("Environment variables:")
for key, value in os.environ.items():
    if key.startswith(('FLASK_', 'DATABASE_', 'REDIS_', 'SECRET_')):
        print(f"{key}: {'*' * len(value) if 'SECRET' in key else value}")

print("\nConfig values:")
config = Config()
for attr in dir(config):
    if not attr.startswith('_'):
        value = getattr(config, attr)
        if 'SECRET' in attr or 'PASSWORD' in attr:
            value = '*' * 8
        print(f"{attr}: {value}")
```

## 🗄️ Database Problems

### Issue: Database Connection Failed

**Symptoms:**

- `sqlalchemy.exc.OperationalError`
- Connection timeout errors
- Authentication failures

**Solutions:**

```bash
# 1. Test database connectivity
psql -h localhost -U your_user -d your_db -c "SELECT version();"

# 2. Check database service
sudo systemctl status postgresql
# or for Docker:
docker-compose ps db

# 3. Verify connection string
python3 -c "
from sqlalchemy import create_engine
from app.config import Config
engine = create_engine(Config.DATABASE_URL)
try:
    conn = engine.connect()
    print('✅ Database connection successful')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"

# 4. Check database logs
sudo tail -f /var/log/postgresql/postgresql-*.log
# or for Docker:
docker-compose logs db
```

### Issue: Migration Problems

```bash
# Check migration status
flask db current
flask db history

# Reset migrations (CAUTION: Development only)
rm -rf migrations/
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Fix migration conflicts
flask db merge -m "Merge migrations"

# Downgrade and retry
flask db downgrade
flask db upgrade

# Manual migration repair
psql your_db -c "SELECT version_num FROM alembic_version;"
# Update version manually if needed
psql your_db -c "UPDATE alembic_version SET version_num='target_revision';"
```

### Issue: Database Performance

```sql
-- Check slow queries
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Check database size
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Analyze tables
ANALYZE;

-- Vacuum tables
VACUUM ANALYZE;
```

## 🔐 Authentication & Authorization Issues

### Issue: JWT Token Problems

**Symptoms:**

- "Token has expired" errors
- "Invalid token" errors
- Authentication failures

**Solutions:**

```python
# Debug JWT token
from flask_jwt_extended import decode_token
import jwt
from datetime import datetime

def debug_jwt_token(token):
    try:
        # Decode without verification to inspect
        unverified = jwt.decode(token, options={"verify_signature": False})
        print(f"Token payload: {unverified}")

        # Check expiration
        exp = unverified.get('exp')
        if exp:
            exp_date = datetime.fromtimestamp(exp)
            print(f"Token expires: {exp_date}")
            print(f"Current time: {datetime.now()}")
            print(f"Token expired: {exp_date < datetime.now()}")

        # Verify with secret
        from app.config import Config
        verified = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        print("✅ Token is valid")
        return verified

    except jwt.ExpiredSignatureError:
        print("❌ Token has expired")
    except jwt.InvalidTokenError as e:
        print(f"❌ Invalid token: {e}")
    except Exception as e:
        print(f"❌ Token decode error: {e}")

# Usage
token = "your_jwt_token_here"
debug_jwt_token(token)
```

### Issue: Permission Denied

```python
# Debug user permissions
def debug_user_permissions(user_id):
    from app.models import User

    user = User.query.get(user_id)
    if not user:
        print(f"❌ User {user_id} not found")
        return

    print(f"User: {user.email}")
    print(f"Role: {user.role}")
    print(f"Active: {user.is_active}")
    print(f"Email verified: {user.email_verified}")

    # Check specific permissions
    permissions = {
        'can_read': user.can_read(),
        'can_write': user.can_write(),
        'can_admin': user.can_admin()
    }

    for perm, has_perm in permissions.items():
        status = "✅" if has_perm else "❌"
        print(f"{status} {perm}: {has_perm}")

# Usage
debug_user_permissions(123)
```

### Issue: Session Problems

```python
# Debug session issues
from flask import session

@app.route('/debug/session')
def debug_session():
    return {
        'session_data': dict(session),
        'session_id': session.get('_id'),
        'permanent': session.permanent,
        'new': session.new,
        'modified': session.modified
    }

# Clear problematic sessions
@app.route('/debug/clear-session')
def clear_session():
    session.clear()
    return {'message': 'Session cleared'}
```

## 🌐 API & Request Issues

### Issue: CORS Problems

**Symptoms:**

- Browser console CORS errors
- Preflight request failures
- Cross-origin request blocked

**Solutions:**

```python
# Debug CORS configuration
from flask_cors import CORS

# Temporary: Allow all origins (development only)
CORS(app, origins="*")

# Production: Specific origins
CORS(app,
     origins=['https://yourdomain.com', 'https://www.yourdomain.com'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization'],
     supports_credentials=True
)

# Debug CORS headers
@app.after_request
def debug_cors(response):
    print(f"CORS headers: {dict(response.headers)}")
    return response
```

### Issue: Request Validation Errors

```python
# Debug request validation
from flask import request
import json

@app.before_request
def debug_request():
    if request.method in ['POST', 'PUT', 'PATCH']:
        print(f"Content-Type: {request.content_type}")
        print(f"Content-Length: {request.content_length}")

        try:
            data = request.get_json()
            print(f"JSON data: {json.dumps(data, indent=2)}")
        except Exception as e:
            print(f"JSON parse error: {e}")
            print(f"Raw data: {request.get_data()}")

# Validate request schema
from marshmallow import ValidationError

def validate_request_debug(schema_class, data):
    try:
        schema = schema_class()
        result = schema.load(data)
        print(f"✅ Validation successful: {result}")
        return result
    except ValidationError as err:
        print(f"❌ Validation errors: {err.messages}")
        return None
```

### Issue: Rate Limiting Problems

```python
# Debug rate limiting
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Check rate limit status
@app.route('/debug/rate-limit')
def debug_rate_limit():
    limiter = app.extensions.get('limiter')
    if not limiter:
        return {'error': 'Rate limiter not configured'}

    ip = get_remote_address()

    # Get current limits
    limits = []
    for limit in limiter._route_limits.get(request.endpoint, []):
        remaining = limiter.storage.get(f"{limit.key_func()}:{limit.limit}")
        limits.append({
            'limit': str(limit.limit),
            'remaining': remaining,
            'window': limit.per
        })

    return {
        'ip': ip,
        'endpoint': request.endpoint,
        'limits': limits
    }

# Reset rate limits (development only)
@app.route('/debug/reset-rate-limit')
def reset_rate_limit():
    limiter = app.extensions.get('limiter')
    if limiter:
        limiter.storage.clear()
        return {'message': 'Rate limits reset'}
    return {'error': 'Rate limiter not configured'}
```

## ⚡ Performance Problems

### Issue: Slow Response Times

**Diagnosis:**

```python
# Performance monitoring middleware
import time
from flask import g, request

@app.before_request
def start_timer():
    g.start_time = time.time()

@app.after_request
def log_request_time(response):
    total_time = time.time() - g.start_time

    if total_time > 1.0:  # Log slow requests
        print(f"⚠️ Slow request: {request.method} {request.path} - {total_time:.2f}s")

    response.headers['X-Response-Time'] = f"{total_time:.3f}s"
    return response

# Database query profiling
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    if total > 0.1:  # Log slow queries
        print(f"⚠️ Slow query ({total:.3f}s): {statement[:100]}...")
```

### Issue: High Memory Usage

```python
# Memory profiling
import psutil
import os

@app.route('/debug/memory')
def debug_memory():
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()

    return {
        'rss': f"{memory_info.rss / 1024 / 1024:.2f} MB",
        'vms': f"{memory_info.vms / 1024 / 1024:.2f} MB",
        'percent': f"{process.memory_percent():.2f}%",
        'available': f"{psutil.virtual_memory().available / 1024 / 1024:.2f} MB"
    }

# Memory leak detection
import gc
import tracemalloc

# Start tracing
tracemalloc.start()

@app.route('/debug/memory-trace')
def memory_trace():
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')

    traces = []
    for stat in top_stats[:10]:
        traces.append({
            'file': stat.traceback.format()[-1],
            'size': f"{stat.size / 1024:.2f} KB",
            'count': stat.count
        })

    return {'top_memory_usage': traces}
```

### Issue: Database Connection Pool Exhaustion

```python
# Monitor connection pool
from sqlalchemy import event

@event.listens_for(db.engine, "connect")
def receive_connect(dbapi_connection, connection_record):
    print(f"📊 New database connection: {id(dbapi_connection)}")

@event.listens_for(db.engine, "close")
def receive_close(dbapi_connection, connection_record):
    print(f"📊 Closed database connection: {id(dbapi_connection)}")

# Check pool status
@app.route('/debug/db-pool')
def debug_db_pool():
    pool = db.engine.pool
    return {
        'size': pool.size(),
        'checked_in': pool.checkedin(),
        'checked_out': pool.checkedout(),
        'overflow': pool.overflow(),
        'invalid': pool.invalid()
    }
```

## 🐳 Docker & Deployment Issues

### Issue: Docker Container Won't Start

```bash
# Check container status
docker-compose ps

# View container logs
docker-compose logs app
docker-compose logs db
docker-compose logs redis

# Check container health
docker-compose exec app curl http://localhost:5000/health

# Debug container environment
docker-compose exec app env | grep -E '^(FLASK_|DATABASE_|REDIS_)'

# Check file permissions
docker-compose exec app ls -la /app

# Test database connection from container
docker-compose exec app python3 -c "
from app.config import Config
from sqlalchemy import create_engine
engine = create_engine(Config.DATABASE_URL)
conn = engine.connect()
print('Database connection successful')
conn.close()
"
```

### Issue: Docker Build Problems

```bash
# Clean build
docker-compose down
docker system prune -f
docker-compose build --no-cache
docker-compose up

# Check Dockerfile syntax
docker build --no-cache -t flask-app .

# Debug build steps
docker build --no-cache --progress=plain -t flask-app .

# Check base image
docker run --rm python:3.9-slim python3 --version
```

### Issue: Volume Mount Problems

```bash
# Check volume mounts
docker-compose exec app mount | grep /app

# Verify file permissions
docker-compose exec app ls -la /app

# Fix permissions (if needed)
docker-compose exec app chown -R app:app /app

# Check volume data
docker volume ls
docker volume inspect flask-production-template_postgres_data
```

## 🔒 Security-Related Issues

### Issue: SSL/TLS Certificate Problems

```bash
# Check certificate status
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/fullchain.pem -text -noout

# Test SSL configuration
ssl-cert-check -c /etc/letsencrypt/live/yourdomain.com/fullchain.pem

# Check certificate expiration
certbot certificates

# Test SSL connection
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Renew certificates
certbot renew --dry-run
certbot renew
```

### Issue: Security Headers Missing

```python
# Debug security headers
@app.after_request
def debug_security_headers(response):
    required_headers = [
        'X-Frame-Options',
        'X-Content-Type-Options',
        'X-XSS-Protection',
        'Strict-Transport-Security',
        'Content-Security-Policy'
    ]

    missing_headers = []
    for header in required_headers:
        if header not in response.headers:
            missing_headers.append(header)

    if missing_headers:
        print(f"⚠️ Missing security headers: {missing_headers}")

    return response

# Test security headers
curl -I https://yourdomain.com
```

## 💻 Development Environment Issues

### Issue: Virtual Environment Problems

```bash
# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Check Python path
which python3
which pip
python3 -c "import sys; print(sys.path)"

# Verify package installation
pip list
pip check
```

### Issue: Environment Variable Problems

```bash
# Check environment variables
env | grep -E '^(FLASK_|DATABASE_|REDIS_|SECRET_)' | sort

# Load .env file manually
set -a
source .env
set +a

# Verify .env file format
cat .env | grep -v '^#' | grep -v '^$' | grep -E '^[A-Z_]+='

# Test environment loading
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('FLASK_ENV:', os.getenv('FLASK_ENV'))
print('DATABASE_URL:', os.getenv('DATABASE_URL', 'Not set'))
"
```

### Issue: Port Conflicts

```bash
# Check port usage
netstat -tulpn | grep :5000
lsof -i :5000

# Kill process using port
sudo kill -9 $(lsof -t -i:5000)

# Use different port
export FLASK_RUN_PORT=5001
flask run
```

## 📊 Logging & Monitoring

### Enhanced Logging Configuration

```python
# Enhanced logging setup
import logging
import logging.handlers
from datetime import datetime
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id

        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id

        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_entry)

# Setup structured logging
def setup_logging(app):
    if not app.debug:
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            '/var/log/flask-app/app.log',
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(JSONFormatter())
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            '/var/log/flask-app/error.log',
            maxBytes=10485760,
            backupCount=10
        )
        error_handler.setFormatter(JSONFormatter())
        error_handler.setLevel(logging.ERROR)
        app.logger.addHandler(error_handler)

        app.logger.setLevel(logging.INFO)
```

### Log Analysis Commands

```bash
# View recent errors
tail -f /var/log/flask-app/error.log | jq .

# Count error types
grep -o '"message":"[^"]*"' /var/log/flask-app/error.log | sort | uniq -c | sort -nr

# Find slow requests
grep "Slow request" /var/log/flask-app/app.log | tail -20

# Monitor real-time logs
tail -f /var/log/flask-app/app.log | jq 'select(.level == "ERROR")'

# Analyze request patterns
grep '"method":"POST"' /var/log/flask-app/app.log | jq -r '.timestamp' | sort | uniq -c
```

## ❌ Common Error Messages

### Database Errors

```
Error: sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) FATAL: password authentication failed
Solution: Check DATABASE_URL credentials and PostgreSQL user permissions

Error: sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server
Solution: Ensure PostgreSQL is running and accessible on specified host/port

Error: alembic.util.exc.CommandError: Can't locate revision identified by 'abc123'
Solution: Check migration history and reset if necessary
```

### JWT Errors

```
Error: flask_jwt_extended.exceptions.DecodeError: Not enough segments
Solution: Check JWT token format and ensure proper Bearer token format

Error: jwt.exceptions.ExpiredSignatureError: Signature has expired
Solution: Refresh JWT token or increase token expiration time

Error: jwt.exceptions.InvalidSignatureError: Signature verification failed
Solution: Verify JWT_SECRET_KEY matches between token creation and verification
```

### Import Errors

```
Error: ModuleNotFoundError: No module named 'app'
Solution: Check PYTHONPATH and ensure you're in the correct directory

Error: ImportError: cannot import name 'db' from 'app'
Solution: Check for circular imports and import order

Error: AttributeError: module 'app' has no attribute 'create_app'
Solution: Verify create_app function exists in app/__init__.py
```

### Configuration Errors

```
Error: KeyError: 'SECRET_KEY'
Solution: Set SECRET_KEY in environment variables or .env file

Error: ValueError: Invalid database URL
Solution: Check DATABASE_URL format: postgresql://user:pass@host:port/db

Error: RuntimeError: Working outside of application context
Solution: Use app.app_context() or ensure proper Flask context
```

## 🛠️ Debugging Tools & Techniques

### Flask Debug Toolbar

```python
# Install and configure debug toolbar
pip install flask-debugtoolbar

from flask_debugtoolbar import DebugToolbarExtension

app.config['DEBUG_TB_ENABLED'] = app.debug
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
toolbar = DebugToolbarExtension(app)
```

### Interactive Debugging

```python
# Add breakpoints for debugging
import pdb

@app.route('/debug-endpoint')
def debug_endpoint():
    data = request.get_json()
    pdb.set_trace()  # Debugger will stop here
    # Process data
    return {'result': 'success'}

# Use ipdb for enhanced debugging
pip install ipdb
import ipdb; ipdb.set_trace()
```

### Performance Profiling

```python
# Profile Flask application
from werkzeug.middleware.profiler import ProfilerMiddleware

if app.debug:
    app.wsgi_app = ProfilerMiddleware(
        app.wsgi_app,
        restrictions=[30],  # Show top 30 functions
        profile_dir='/tmp/profiler'
    )

# Memory profiling
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Function to profile
    pass
```

### Database Query Analysis

```python
# Enable SQL query logging
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Query profiling decorator
from functools import wraps
import time

def profile_queries(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_sqlalchemy import get_debug_queries

        start_time = time.time()
        result = f(*args, **kwargs)
        end_time = time.time()

        queries = get_debug_queries()
        total_query_time = sum(q.duration for q in queries)

        print(f"Function: {f.__name__}")
        print(f"Total time: {end_time - start_time:.3f}s")
        print(f"Query time: {total_query_time:.3f}s")
        print(f"Query count: {len(queries)}")

        for query in queries:
            if query.duration > 0.01:  # Log slow queries
                print(f"Slow query ({query.duration:.3f}s): {query.statement}")

        return result
    return decorated_function
```

### Health Check Endpoint

```python
# Comprehensive health check
@app.route('/health')
def health_check():
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': app.config.get('VERSION', 'unknown'),
        'checks': {}
    }

    # Database check
    try:
        db.session.execute('SELECT 1')
        health_status['checks']['database'] = 'healthy'
    except Exception as e:
        health_status['checks']['database'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'

    # Redis check
    try:
        from app.extensions import redis_client
        redis_client.ping()
        health_status['checks']['redis'] = 'healthy'
    except Exception as e:
        health_status['checks']['redis'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'

    # Disk space check
    import shutil
    try:
        total, used, free = shutil.disk_usage('/')
        free_percent = (free / total) * 100
        if free_percent < 10:
            health_status['checks']['disk'] = f'warning: {free_percent:.1f}% free'
        else:
            health_status['checks']['disk'] = f'healthy: {free_percent:.1f}% free'
    except Exception as e:
        health_status['checks']['disk'] = f'error: {str(e)}'

    status_code = 200 if health_status['status'] == 'healthy' else 503
    return health_status, status_code
```

## 📞 Getting Help

### Support Channels

1. **Documentation**: Check [README.md](../README.md) and other docs
2. **Logs**: Review application and system logs
3. **Community**: Flask, SQLAlchemy, and related project communities
4. **Issues**: Create detailed issue reports with:
   - Error messages
   - Steps to reproduce
   - Environment details
   - Relevant logs

### Creating Bug Reports

```bash
# Collect system information
echo "=== System Information ===" > debug-info.txt
uname -a >> debug-info.txt
python3 --version >> debug-info.txt
pip list >> debug-info.txt
echo "\n=== Environment Variables ===" >> debug-info.txt
env | grep -E '^(FLASK_|DATABASE_|REDIS_)' >> debug-info.txt
echo "\n=== Recent Logs ===" >> debug-info.txt
tail -50 /var/log/flask-app/error.log >> debug-info.txt
```

---

**Remember**: When troubleshooting, always check logs first, verify configuration, and test components individually before investigating complex interactions. Most issues can be resolved by following the systematic approach outlined in this guide.
