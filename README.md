# Flask Production Template for AI

> A production-ready Flask template for building scalable web applications and APIs for AI coders and humans too.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📖 Introduction

Welcome to the **Flask Production Template for AI** - a comprehensive, battle-tested Flask template specifically designed for AI developers and coding assistants. This template eliminates the tedious setup process and provides you with a robust foundation to build production-ready applications quickly.

Whether you're building REST APIs, web applications, microservices, or ML-powered services, this template includes everything you need: security features, database integration, testing frameworks, Docker support, and deployment configurations. It follows industry best practices and includes detailed documentation to help both human developers and AI assistants understand and extend the codebase effectively.

**Key Benefits:**

- 🚀 **Rapid Development**: Get from idea to production in minutes, not hours
- 🛡️ **Enterprise-Ready**: Built-in security, monitoring, and error handling
- 🤖 **AI-Friendly**: Structured for easy understanding by coding assistants
- 📚 **Well-Documented**: Comprehensive guides and inline documentation
- 🔧 **Highly Configurable**: Easily adaptable to your specific needs

## 🤖 For AI Coding Assistants

**⚠️ IMPORTANT: Before writing any code, please read [`AI_INSTRUCTIONS.md`](./AI_INSTRUCTIONS.md) first!**

This file contains:

- Project architecture and coding standards
- Directory structure rules
- Development workflow guidelines
- Code generation templates

**Quick AI Setup:**

```bash
# Read the AI instructions first
cat AI_INSTRUCTIONS.md

# Then run the quickstart
./scripts/quickstart.sh          # macOS/Linux
.\scripts\quickstart.ps1         # Windows
```

## 🎯 What is this?

This template provides everything you need to build a **production-ready Flask application** with:

- ✅ **Security** (JWT authentication, input validation)
- ✅ **Scalability** (caching, database optimization)
- ✅ **Maintainability** (testing, documentation, CI/CD)
- ✅ **Developer Experience** (auto-setup scripts, clear structure)

**Perfect for**: REST APIs, web applications, microservices, ML services

## 🚀 Get Started in 2 Minutes

### Option 1: Quick Setup (Recommended)

**Windows:**

```powershell
git clone <your-repo-url>
cd flask-production-template
.\scripts\quickstart.ps1
```

**macOS/Linux:**

```bash
git clone <your-repo-url>
cd flask-production-template
chmod +x scripts/quickstart.sh && ./scripts/quickstart.sh
```

### Option 2: Manual Setup

**Prerequisites:** Python 3.8+, Git, pip

**Step-by-step:**

1. **Clone and setup**:

   ```bash
   git clone <your-repo-url>
   cd flask-production-template
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment** (⚠️ **Important**):

   ```bash
   cp .env.example .env
   # Edit .env file - see "Environment Setup" section below
   ```

3. **Initialize database**:

   ```bash
   flask db upgrade
   ```

4. **Start the server**:

   ```bash
   flask run
   ```

5. **Test it works**: Visit [http://localhost:5000/docs](http://localhost:5000/docs)

---

## 📖 What's Next?

**👋 New to this template?** Start here:

1. 📝 [Environment Setup](#-environment-setup) - **Required first step**
2. 🏗️ [Project Structure](#-project-structure) - Understand the codebase
3. 🧪 [Testing Guide](TESTING.md) - Run tests and understand quality
4. 🤝 [Contributing Guide](CONTRIBUTING.md) - Development workflow

**🚀 Ready to build?** Jump to:

- 🔌 [API Documentation](#-api-endpoints) - Available endpoints
- 🛠️ [Adding Features](#-adding-features) - Extend the template
- 🐳 [Docker Setup](#-docker-deployment) - Containerized development
- 🔒 [Security Guide](#-security) - Production security

**📚 Deep dive documentation:**

- 📋 [Configuration Guide](docs/configuration.md) - Advanced settings
- 🔍 [Error Handling & Logging](docs/error_handling_and_logging.md) - Debugging
- 🚀 [Deployment Guide](#-deployment) - Production deployment

## 🔧 Environment Setup

> ⚠️ **This step is required** - The application won't start without proper environment configuration.

### 1. Copy Environment Template

```bash
cp .env.example .env
```

### 2. Generate Secure Keys

```bash
# Run these commands and copy the output to your .env file
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"
```

### 3. Edit Your .env File

Open `.env` and update these **required** settings:

```env
# Required - Replace with generated keys above
SECRET_KEY=your-generated-secret-key-here
JWT_SECRET_KEY=your-generated-jwt-key-here

# Database (SQLite for development, PostgreSQL for production)
DATABASE_URL=sqlite:///app.db

# Environment
FLASK_ENV=development
FLASK_DEBUG=True
```

**Need help?** See the [complete environment variables guide](#-environment-variables) below.

### 4. Test Your Setup

```bash
flask run
# Visit: http://localhost:5000/docs
```

## 🏗️ Project Structure

**Key directories to know:**

```
flask-production-template/
├── app/                    # 🏠 Main application code
│   ├── blueprints/        # 🔌 API endpoints & routes
│   ├── schemas/           # 📋 Request/response validation
│   ├── services/          # 🔧 Business logic
│   └── config.py          # ⚙️ App configuration
├── tests/                 # 🧪 Test suite
├── docs/                  # 📚 Documentation
├── scripts/               # 🛠️ Setup & utility scripts
├── .env.example           # 🔒 Environment template
└── requirements.txt       # 📦 Dependencies
```

**🎯 Quick orientation:**

- **Adding a new API?** → `app/blueprints/`
- **Business logic?** → `app/services/`
- **Data validation?** → `app/schemas/`
- **Configuration?** → `app/config.py`
- **Tests?** → `tests/`

**📖 Learn more:** [Detailed architecture guide](docs/configuration.md)

## 🔌 API Endpoints

**Quick test:** Visit [http://localhost:5000/docs](http://localhost:5000/docs) for interactive API documentation.

### Available Endpoints

| Endpoint | Method | Description |
|----------|--------|--------------|
| `/docs/` | GET | 📖 Interactive API documentation |
| `/examples/` | GET | 🧪 Example API responses |
| `/health/` | GET | ❤️ Health check |
| `/api/v1/` | GET | 🔗 API v1 endpoints |
| `/api/v2/` | GET | 🔗 API v2 endpoints |

**📚 Learn more:** [Complete API documentation](http://localhost:5000/docs) (start the server first)

---

## 🛠️ Adding Features

### Quick Blueprint Creation

1. **Copy the template**:

   ```bash
   cp -r __template__ app/blueprints/my_feature
   ```

2. **Register your blueprint** in `app/blueprints/__init__.py`

3. **Add routes** in `app/blueprints/my_feature/routes.py`

**📖 Learn more:** [Blueprint development guide](CONTRIBUTING.md#adding-new-features)

#### Required Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `SECRET_KEY` | ✅ | Flask secret key for sessions | `your-secret-key` |
| `JWT_SECRET_KEY` | ✅ | JWT token signing key | `your-jwt-secret` |
| `DATABASE_URL` | ✅ | Database connection string | `sqlite:///app.db` |
| `FLASK_ENV` | ✅ | Environment mode | `development` |
| `API_TITLE` | ❌ | API documentation title | `My API` |
| `LOG_LEVEL` | ❌ | Logging level | `INFO` |

### Configuration Classes

- `DevelopmentConfig`: Development settings
- `TestingConfig`: Testing settings
- `ProductionConfig`: Production settings

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_api.py

# Run with verbose output
pytest -v
```

---

## 🐳 Docker Deployment

### Development

```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d
```

### Production

```bash
# Use production configuration
docker-compose -f docker-compose.prod.yml up -d
```

**📖 Learn more:** [Docker setup guide](docker/README.md)

---

## 🧪 Testing

```bash
# Quick test
pytest

# With coverage report
pytest --cov=app --cov-report=html
```

**📖 Learn more:** [Complete testing guide](TESTING.md)

---

## 📋 Environment Variables

**Required variables:**

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | Generated above |
| `JWT_SECRET_KEY` | JWT signing key | Generated above |
| `DATABASE_URL` | Database connection | `sqlite:///app.db` |
| `FLASK_ENV` | Environment mode | `development` |

**📖 Complete list:** See [.env.example](.env.example) for all available options

---

## 🚀 Deployment

### Quick Deploy with Docker

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d
```

### Production Checklist

- ✅ Set `FLASK_ENV=production`
- ✅ Use strong secret keys
- ✅ Configure production database
- ✅ Set up reverse proxy (Nginx)
- ✅ Enable HTTPS
- ✅ Configure monitoring

**📖 Learn more:** [Production deployment guide](docs/deployment.md)

## 🔒 Security

### Quick Security Checklist

**🔑 Environment Security:**

- ✅ Never commit `.env` files
- ✅ Use strong generated keys (see [Environment Setup](#-environment-setup))
- ✅ Different keys per environment
- ✅ `FLASK_DEBUG=False` in production

**🛡️ Production Security:**

- ✅ HTTPS enabled
- ✅ Rate limiting configured
- ✅ Input validation on all endpoints
- ✅ Security headers implemented
- ✅ Regular security updates

**📖 Learn more:** [Complete security guide](docs/security.md)

---

## 🆘 Troubleshooting

**Common issues:**

- **`KeyError: 'SECRET_KEY'`** → Check your `.env` file setup
- **Database connection errors** → Verify `DATABASE_URL` in `.env`
- **JWT token errors** → Ensure `JWT_SECRET_KEY` is set
- **Import errors** → Run `pip install -r requirements.txt`

**📖 Learn more:** [Troubleshooting guide](docs/troubleshooting.md)

---

## 📚 Resources & Support

**📚 Documentation:**

- [AI Instructions](AI_INSTRUCTIONS.md) - **Essential for AI coding assistants**
- [Contributing Guide](CONTRIBUTING.md) - Development workflow
- [Python Style Guide](docs/python_style_guide.md) - Comprehensive coding standards
- [Testing Guide](TESTING.md) - Running tests
- [Configuration Guide](docs/configuration.md) - Advanced settings
- [Error Handling & Logging](docs/error_handling_and_logging.md) - Debugging

**🔗 Links:**

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Flask-RESTful](https://flask-restful.readthedocs.io/)
- [SQLAlchemy](https://docs.sqlalchemy.org/)

**💬 Support:**

- 🐛 [Report Issues](https://github.com/your-repo/issues)
- 💡 [Feature Requests](https://github.com/your-repo/discussions)
- 📧 [Contact](mailto:your-email@example.com)

---

**⭐ Star this repo if it helped you!**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**⭐ Happy coding! Star this repo if it helped you! 🎉**
