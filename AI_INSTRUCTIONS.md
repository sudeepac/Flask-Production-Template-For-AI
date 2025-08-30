# AI Instructions for Flask Production Template

**Essential reading for AI assistants before writing any code.**

## Quick Start

```bash
./scripts/quickstart.sh          # macOS / Linux
.\scripts\quickstart.ps1         # Windows (PowerShell)
```

This creates virtual environment, installs dependencies, runs migrations, and starts the dev server.

## Project Structure

```
flask-app/
├── app/
│   ├── __init__.py           # Application factory
│   ├── config.py             # Configuration
│   ├── extensions.py         # Flask extensions
│   ├── blueprints/           # Feature modules
│   ├── services/             # Business logic
│   ├── models/               # Database models
│   ├── schemas/              # Data validation
│   └── utils/                # Helper functions
├── tests/                    # Test files
├── scripts/                  # Utility scripts
└── requirements.txt          # Dependencies
```

## Creating New Features

1. **Create Blueprint Directory**
   ```bash
   mkdir app/blueprints/<feature_name>
   ```

2. **Add Required Files**
   - `__init__.py` - Blueprint registration
   - `routes.py` - Route definitions
   - `services.py` - Business logic (optional)
   - `models.py` - Database models (optional)

3. **Register Blueprint**
   Add to `app/__init__.py` in the `_register_blueprints()` function

4. **Add Tests**
   Create corresponding test files in `tests/` directory

## Coding Standards

### File Organization
- One class per file when possible
- Use descriptive file and function names
- Follow Python PEP 8 naming conventions

### Error Handling
- Use custom exceptions from `app.utils.service_helpers`
- Log errors with appropriate context
- Handle database transactions properly

### Database
- Use SQLAlchemy models in `app/models/`
- Always handle database sessions properly
- Use migrations for schema changes

### Testing
- Write tests for all new features
- Use pytest fixtures for common test data
- Aim for good test coverage

### Security
- Validate all input data
- Use proper authentication/authorization
- Never commit secrets to version control

## Essential Rules

1. **One feature = one blueprint folder** - Keeps code organized
2. **Use service layer for business logic** - Separates concerns
3. **Write tests for new features** - Ensures reliability
4. **Follow naming conventions** - Maintains consistency
5. **Handle errors gracefully** - Improves user experience

## Quick Commands

```bash
# Create new blueprint
python scripts/make_blueprint.py <feature_name>

# Run tests
pytest

# Format code
black .
isort .

# Type checking
mypy app/

# Start development server
flask run
```

## Documentation Files

- `README.md` - Project overview and setup
- `CONTRIBUTING.md` - Development guidelines
- `docs/python_style_guide.md` - Coding standards
- `AI_INSTRUCTIONS.md` - This file (AI guidance)

---

**Remember**: Keep it simple, maintainable, and well-tested. Focus on essential patterns that work for both AI and human developers.
