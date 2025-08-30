# Security Guide

This guide outlines security best practices and configurations for the Flask Production Template for AI.

## 📋 Table of Contents

- [Overview](#overview)
- [Authentication & Authorization](#authentication--authorization)
- [Data Protection](#data-protection)
- [Input Validation](#input-validation)
- [Security Headers](#security-headers)
- [HTTPS & SSL/TLS](#https--ssltls)
- [Database Security](#database-security)
- [File Upload Security](#file-upload-security)
- [API Security](#api-security)
- [Logging & Monitoring](#logging--monitoring)
- [Environment Security](#environment-security)
- [Security Testing](#security-testing)
- [Incident Response](#incident-response)

## 🛡️ Overview

Security is built into every layer of the Flask Production Template for AI:

- **Authentication**: JWT-based with secure token handling
- **Authorization**: Role-based access control (RBAC)
- **Data Protection**: Encryption at rest and in transit
- **Input Validation**: Comprehensive sanitization and validation
- **Security Headers**: OWASP-recommended HTTP security headers
- **Monitoring**: Real-time security event logging

## 🔐 Authentication & Authorization

### JWT Configuration

```python
# Secure JWT settings in config.py
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')  # Must be 256-bit
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
JWT_ALGORITHM = 'HS256'
JWT_BLACKLIST_ENABLED = True
JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
```

### Password Security

```python
# Strong password requirements
PASSWORD_MIN_LENGTH = 12
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_NUMBERS = True
PASSWORD_REQUIRE_SPECIAL = True

# Password hashing with bcrypt
from flask_bcrypt import Bcrypt
bcrypt = Bcrypt()

# Hash password
password_hash = bcrypt.generate_password_hash('password').decode('utf-8')

# Verify password
bcrypt.check_password_hash(password_hash, 'password')
```

### Role-Based Access Control

```python
# User roles and permissions
class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"
    READONLY = "readonly"

# Permission decorator
from functools import wraps
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

def require_role(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)

            if not user or user.role != required_role:
                return {'error': 'Insufficient permissions'}, 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Usage
@app.route('/admin/users')
@require_role(UserRole.ADMIN)
def admin_users():
    return {'users': []}
```

### Multi-Factor Authentication (MFA)

```python
# TOTP-based MFA implementation
import pyotp
import qrcode
from io import BytesIO
import base64

class MFAService:
    @staticmethod
    def generate_secret():
        return pyotp.random_base32()

    @staticmethod
    def generate_qr_code(user_email, secret, app_name="Flask App"):
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name=app_name
        )

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        return base64.b64encode(buffer.getvalue()).decode()

    @staticmethod
    def verify_token(secret, token):
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
```

## 🔒 Data Protection

### Encryption at Rest

```python
# Database field encryption
from cryptography.fernet import Fernet
import os

class EncryptedField:
    def __init__(self):
        key = os.getenv('ENCRYPTION_KEY')
        if not key:
            raise ValueError("ENCRYPTION_KEY environment variable required")
        self.cipher = Fernet(key.encode())

    def encrypt(self, data):
        if isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data).decode()

    def decrypt(self, encrypted_data):
        if isinstance(encrypted_data, str):
            encrypted_data = encrypted_data.encode()
        return self.cipher.decrypt(encrypted_data).decode()

# Usage in models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    _encrypted_ssn = db.Column(db.Text)  # Encrypted field

    @property
    def ssn(self):
        if self._encrypted_ssn:
            return EncryptedField().decrypt(self._encrypted_ssn)
        return None

    @ssn.setter
    def ssn(self, value):
        if value:
            self._encrypted_ssn = EncryptedField().encrypt(value)
        else:
            self._encrypted_ssn = None
```

### Secure Session Management

```python
# Session configuration
SESSION_COOKIE_SECURE = True  # HTTPS only
SESSION_COOKIE_HTTPONLY = True  # No JavaScript access
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
PERMANENT_SESSION_LIFETIME = timedelta(hours=2)

# Session security middleware
@app.before_request
def security_headers():
    # Regenerate session ID on login
    if request.endpoint == 'auth.login' and request.method == 'POST':
        session.permanent = True
        session.regenerate()
```

## ✅ Input Validation

### Request Validation

```python
# Comprehensive input validation
from marshmallow import Schema, fields, validate, ValidationError
from flask import request, jsonify
from functools import wraps

class UserRegistrationSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(
        required=True,
        validate=[
            validate.Length(min=12, max=128),
            validate.Regexp(
                r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]',
                error="Password must contain uppercase, lowercase, number, and special character"
            )
        ]
    )
    name = fields.Str(
        required=True,
        validate=[
            validate.Length(min=2, max=50),
            validate.Regexp(r'^[a-zA-Z\s]+$', error="Name can only contain letters and spaces")
        ]
    )

def validate_json(schema_class):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                schema = schema_class()
                data = schema.load(request.get_json())
                request.validated_data = data
                return f(*args, **kwargs)
            except ValidationError as err:
                return jsonify({'errors': err.messages}), 400
        return decorated_function
    return decorator

# Usage
@app.route('/register', methods=['POST'])
@validate_json(UserRegistrationSchema)
def register():
    data = request.validated_data
    # Process validated data
```

### SQL Injection Prevention

```python
# Always use parameterized queries
from sqlalchemy import text

# GOOD: Parameterized query
def get_user_by_email(email):
    return db.session.execute(
        text("SELECT * FROM users WHERE email = :email"),
        {'email': email}
    ).fetchone()

# BAD: String concatenation (vulnerable to SQL injection)
# def get_user_by_email(email):
#     return db.session.execute(
#         f"SELECT * FROM users WHERE email = '{email}'"
#     ).fetchone()

# Use SQLAlchemy ORM (automatically parameterized)
def get_user_by_email_orm(email):
    return User.query.filter_by(email=email).first()
```

### XSS Prevention

```python
# HTML sanitization
from markupsafe import escape
import bleach

# Escape user input
def safe_render(user_input):
    return escape(user_input)

# Sanitize HTML content
ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li']
ALLOWED_ATTRIBUTES = {}

def sanitize_html(html_content):
    return bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )
```

## 🛡️ Security Headers

### HTTP Security Headers

```python
# Security headers middleware
@app.after_request
def security_headers(response):
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'

    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'

    # XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # HTTPS enforcement
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    # Content Security Policy
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none';"
    )

    # Referrer policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    # Permissions policy
    response.headers['Permissions-Policy'] = (
        "geolocation=(), "
        "microphone=(), "
        "camera=()"
    )

    return response
```

### CORS Security

```python
# Secure CORS configuration
from flask_cors import CORS

# Production CORS settings
CORS(app,
     origins=['https://yourdomain.com'],  # Specific origins only
     methods=['GET', 'POST', 'PUT', 'DELETE'],
     allow_headers=['Content-Type', 'Authorization'],
     supports_credentials=True,
     max_age=3600
)
```

## 🔐 HTTPS & SSL/TLS

### SSL/TLS Configuration

```nginx
# Nginx SSL configuration
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # SSL security
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # OCSP stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/yourdomain.com/chain.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

### Certificate Management

```bash
# Automated certificate renewal
#!/bin/bash
# /etc/cron.daily/certbot-renew

certbot renew --quiet --no-self-upgrade

# Reload nginx if certificates were renewed
if [ $? -eq 0 ]; then
    systemctl reload nginx
    logger "SSL certificates renewed successfully"
fi
```

## 🗄️ Database Security

### PostgreSQL Security

```sql
-- Database security configuration

-- Create dedicated application user
CREATE USER app_user WITH PASSWORD 'secure_random_password';

-- Grant minimal required permissions
GRANT CONNECT ON DATABASE your_db TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- Enable row-level security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create policy for user data access
CREATE POLICY user_data_policy ON users
    FOR ALL TO app_user
    USING (id = current_setting('app.current_user_id')::integer);
```

### Database Connection Security

```python
# Secure database configuration
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME'),
    'username': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'sslmode': 'require',  # Force SSL
    'sslcert': '/path/to/client-cert.pem',
    'sslkey': '/path/to/client-key.pem',
    'sslrootcert': '/path/to/ca-cert.pem'
}

# Connection string with SSL
DATABASE_URL = (
    f"postgresql://{DATABASE_CONFIG['username']}:{DATABASE_CONFIG['password']}"
    f"@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"
    f"?sslmode={DATABASE_CONFIG['sslmode']}"
)
```

## 📁 File Upload Security

### Secure File Upload

```python
# File upload security
import magic
from werkzeug.utils import secure_filename
import os
from PIL import Image

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_MIME_TYPES = {
    'image/jpeg', 'image/png', 'image/gif',
    'application/pdf', 'text/plain'
}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_type(file_path):
    mime_type = magic.from_file(file_path, mime=True)
    return mime_type in ALLOWED_MIME_TYPES

def secure_upload(file):
    if not file or file.filename == '':
        raise ValueError("No file selected")

    if not allowed_file(file.filename):
        raise ValueError("File type not allowed")

    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise ValueError("File too large")

    # Secure filename
    filename = secure_filename(file.filename)

    # Generate unique filename
    import uuid
    unique_filename = f"{uuid.uuid4()}_{filename}"

    # Save file
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(upload_path)

    # Validate MIME type
    if not validate_file_type(upload_path):
        os.remove(upload_path)
        raise ValueError("Invalid file type")

    # Additional validation for images
    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        try:
            with Image.open(upload_path) as img:
                img.verify()  # Verify it's a valid image
        except Exception:
            os.remove(upload_path)
            raise ValueError("Invalid image file")

    return unique_filename
```

### File Access Control

```python
# Secure file serving
from flask import send_from_directory, abort
from flask_jwt_extended import jwt_required, get_jwt_identity

@app.route('/uploads/<filename>')
@jwt_required()
def uploaded_file(filename):
    # Validate filename
    if not secure_filename(filename) == filename:
        abort(404)

    # Check file ownership/permissions
    current_user_id = get_jwt_identity()
    file_record = File.query.filter_by(
        filename=filename,
        user_id=current_user_id
    ).first()

    if not file_record:
        abort(404)

    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename,
        as_attachment=True
    )
```

## 🔌 API Security

### Rate Limiting

```python
# Rate limiting implementation
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis

# Redis-backed rate limiter
limiter = Limiter(
    app,
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379",
    default_limits=["1000 per hour"]
)

# API endpoint rate limits
@app.route('/api/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    # Login logic
    pass

@app.route('/api/register', methods=['POST'])
@limiter.limit("3 per minute")
def register():
    # Registration logic
    pass

@app.route('/api/data')
@limiter.limit("100 per minute")
@jwt_required()
def get_data():
    # Data retrieval logic
    pass
```

### API Key Management

```python
# API key authentication
import secrets
import hashlib
from datetime import datetime, timedelta

class APIKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key_hash = db.Column(db.String(64), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    last_used = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    @staticmethod
    def generate_key():
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_key(key):
        return hashlib.sha256(key.encode()).hexdigest()

    def is_valid(self):
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True

# API key authentication decorator
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return {'error': 'API key required'}, 401

        key_hash = APIKey.hash_key(api_key)
        api_key_record = APIKey.query.filter_by(key_hash=key_hash).first()

        if not api_key_record or not api_key_record.is_valid():
            return {'error': 'Invalid API key'}, 401

        # Update last used timestamp
        api_key_record.last_used = datetime.utcnow()
        db.session.commit()

        request.api_key = api_key_record
        return f(*args, **kwargs)
    return decorated_function
```

## 📊 Logging & Monitoring

### Security Event Logging

```python
# Security event logging
import logging
from datetime import datetime
from flask import request, g

# Security logger configuration
security_logger = logging.getLogger('security')
security_handler = logging.FileHandler('/var/log/flask-app/security.log')
security_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s - IP: %(ip)s - User: %(user)s'
)
security_handler.setFormatter(security_formatter)
security_logger.addHandler(security_handler)
security_logger.setLevel(logging.INFO)

class SecurityEvent:
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILURE = "LOGIN_FAILURE"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"
    FILE_UPLOAD = "FILE_UPLOAD"
    DATA_ACCESS = "DATA_ACCESS"

def log_security_event(event_type, message, user_id=None, extra_data=None):
    user_info = f"user_id:{user_id}" if user_id else "anonymous"
    ip_address = request.remote_addr if request else "unknown"

    log_data = {
        'event_type': event_type,
        'message': message,
        'ip': ip_address,
        'user': user_info,
        'timestamp': datetime.utcnow().isoformat(),
        'user_agent': request.headers.get('User-Agent', '') if request else '',
        'extra_data': extra_data or {}
    }

    security_logger.info(
        f"{event_type}: {message}",
        extra={'ip': ip_address, 'user': user_info}
    )

# Usage examples
@app.route('/login', methods=['POST'])
def login():
    # Login logic
    if login_successful:
        log_security_event(
            SecurityEvent.LOGIN_SUCCESS,
            f"User {user.email} logged in successfully",
            user_id=user.id
        )
    else:
        log_security_event(
            SecurityEvent.LOGIN_FAILURE,
            f"Failed login attempt for {email}",
            extra_data={'email': email}
        )
```

### Intrusion Detection

```python
# Simple intrusion detection
from collections import defaultdict
from datetime import datetime, timedelta
import redis

class IntrusionDetector:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.thresholds = {
            'failed_logins': {'count': 5, 'window': 300},  # 5 failures in 5 minutes
            'api_requests': {'count': 1000, 'window': 3600},  # 1000 requests per hour
            'file_uploads': {'count': 10, 'window': 3600}  # 10 uploads per hour
        }

    def check_threshold(self, event_type, identifier):
        key = f"intrusion:{event_type}:{identifier}"
        threshold = self.thresholds.get(event_type)

        if not threshold:
            return False

        # Increment counter
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, threshold['window'])
        count = pipe.execute()[0]

        if count > threshold['count']:
            self.trigger_alert(event_type, identifier, count)
            return True

        return False

    def trigger_alert(self, event_type, identifier, count):
        alert_message = f"Intrusion detected: {event_type} from {identifier} - {count} events"

        # Log alert
        log_security_event(
            SecurityEvent.SUSPICIOUS_ACTIVITY,
            alert_message,
            extra_data={'event_type': event_type, 'count': count}
        )

        # Send notification (implement based on your needs)
        # send_security_alert(alert_message)

# Usage in routes
detector = IntrusionDetector(redis.Redis())

@app.before_request
def check_intrusion():
    ip = request.remote_addr

    # Check API request rate
    if detector.check_threshold('api_requests', ip):
        abort(429)  # Too Many Requests
```

## 🌍 Environment Security

### Environment Variables

```bash
# Secure environment configuration
# .env file (never commit to version control)

# Generate secure keys
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Database credentials
DB_PASSWORD=$(openssl rand -base64 32)

# API keys
THIRD_PARTY_API_KEY=your-secure-api-key

# File permissions
chmod 600 .env
chown app:app .env
```

### Secrets Management

```python
# Secrets management with HashiCorp Vault (optional)
import hvac
import os

class SecretsManager:
    def __init__(self):
        self.client = hvac.Client(
            url=os.getenv('VAULT_URL', 'http://localhost:8200'),
            token=os.getenv('VAULT_TOKEN')
        )

    def get_secret(self, path, key):
        try:
            response = self.client.secrets.kv.v2.read_secret_version(path=path)
            return response['data']['data'][key]
        except Exception as e:
            # Fallback to environment variable
            return os.getenv(key.upper())

    def set_secret(self, path, secrets_dict):
        return self.client.secrets.kv.v2.create_or_update_secret(
            path=path,
            secret=secrets_dict
        )

# Usage
secrets_manager = SecretsManager()
db_password = secrets_manager.get_secret('myapp/database', 'password')
```

## 🧪 Security Testing

### Automated Security Tests

```python
# Security test cases
import pytest
from app import create_app
from app.models import User

class TestSecurity:
    def test_sql_injection_protection(self, client):
        """Test SQL injection protection"""
        malicious_input = "'; DROP TABLE users; --"
        response = client.post('/login', json={
            'email': malicious_input,
            'password': 'password'
        })
        # Should not cause server error
        assert response.status_code in [400, 401]

    def test_xss_protection(self, client):
        """Test XSS protection"""
        malicious_script = "<script>alert('xss')</script>"
        response = client.post('/api/profile', json={
            'name': malicious_script
        }, headers={'Authorization': 'Bearer valid_token'})

        # Check that script is escaped/sanitized
        assert '<script>' not in response.get_data(as_text=True)

    def test_csrf_protection(self, client):
        """Test CSRF protection"""
        # Attempt request without CSRF token
        response = client.post('/api/sensitive-action')
        assert response.status_code == 403

    def test_rate_limiting(self, client):
        """Test rate limiting"""
        # Make multiple rapid requests
        for _ in range(10):
            response = client.post('/login', json={
                'email': 'test@example.com',
                'password': 'wrong'
            })

        # Should be rate limited
        assert response.status_code == 429

    def test_jwt_expiration(self, client):
        """Test JWT token expiration"""
        # Create expired token
        expired_token = create_expired_jwt_token()

        response = client.get('/api/protected', headers={
            'Authorization': f'Bearer {expired_token}'
        })

        assert response.status_code == 401

    def test_file_upload_security(self, client):
        """Test file upload security"""
        # Test malicious file upload
        malicious_file = {
            'file': (BytesIO(b'<?php system($_GET["cmd"]); ?>'), 'shell.php')
        }

        response = client.post('/upload', data=malicious_file)
        assert response.status_code == 400
```

### Security Scanning

```bash
# Automated security scanning

# Install security tools
pip install bandit safety

# Run security scans
bandit -r app/  # Static analysis
safety check   # Dependency vulnerability check

# OWASP ZAP integration
docker run -t owasp/zap2docker-stable zap-baseline.py \
    -t http://localhost:5000
```

## 🚨 Incident Response

### Incident Response Plan

```python
# Incident response automation
class IncidentResponse:
    def __init__(self):
        self.alert_channels = {
            'email': 'security@company.com',
            'slack': '#security-alerts',
            'sms': '+1234567890'
        }

    def handle_security_incident(self, incident_type, details):
        """Handle security incident"""

        # Log incident
        log_security_event(
            SecurityEvent.SUSPICIOUS_ACTIVITY,
            f"Security incident: {incident_type}",
            extra_data=details
        )

        # Determine severity
        severity = self.assess_severity(incident_type, details)

        # Take immediate action
        if severity == 'CRITICAL':
            self.emergency_response(incident_type, details)
        elif severity == 'HIGH':
            self.high_priority_response(incident_type, details)

        # Send alerts
        self.send_alerts(incident_type, details, severity)

    def emergency_response(self, incident_type, details):
        """Emergency response for critical incidents"""

        if incident_type == 'DATA_BREACH':
            # Immediately disable affected accounts
            self.disable_compromised_accounts(details.get('user_ids', []))

            # Revoke all active sessions
            self.revoke_all_sessions()

            # Enable maintenance mode
            self.enable_maintenance_mode()

        elif incident_type == 'SYSTEM_COMPROMISE':
            # Isolate affected systems
            self.isolate_systems(details.get('affected_systems', []))

            # Collect forensic data
            self.collect_forensic_data()

    def disable_compromised_accounts(self, user_ids):
        """Disable compromised user accounts"""
        for user_id in user_ids:
            user = User.query.get(user_id)
            if user:
                user.is_active = False
                db.session.commit()

                log_security_event(
                    SecurityEvent.SUSPICIOUS_ACTIVITY,
                    f"Account {user.email} disabled due to security incident",
                    user_id=user_id
                )
```

### Security Monitoring Dashboard

```python
# Security metrics collection
from prometheus_client import Counter, Histogram, Gauge

# Security metrics
security_events = Counter('security_events_total', 'Total security events', ['event_type'])
login_attempts = Counter('login_attempts_total', 'Total login attempts', ['status'])
api_requests = Counter('api_requests_total', 'Total API requests', ['endpoint', 'status'])
active_sessions = Gauge('active_sessions', 'Number of active user sessions')

# Middleware to collect metrics
@app.before_request
def collect_request_metrics():
    g.start_time = time.time()

@app.after_request
def collect_response_metrics(response):
    request_duration = time.time() - g.start_time

    api_requests.labels(
        endpoint=request.endpoint or 'unknown',
        status=response.status_code
    ).inc()

    return response
```

## 📚 Security Resources

### Security Checklists

- [ ] All secrets stored in environment variables
- [ ] HTTPS enforced in production
- [ ] Security headers implemented
- [ ] Input validation on all endpoints
- [ ] SQL injection protection verified
- [ ] XSS protection implemented
- [ ] CSRF protection enabled
- [ ] Rate limiting configured
- [ ] File upload security implemented
- [ ] Database access controls configured
- [ ] Logging and monitoring active
- [ ] Security tests passing
- [ ] Dependency vulnerabilities checked
- [ ] Incident response plan documented

### External Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.0.x/security/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CIS Controls](https://www.cisecurity.org/controls/)

---

**Next Steps**: After implementing security measures, review the [Deployment Guide](deployment.md) for secure production deployment and the [Troubleshooting Guide](troubleshooting.md) for security-related issues.
