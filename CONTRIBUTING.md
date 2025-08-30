# Contributing to Flask Production Template

Thank you for contributing! This guide helps both AI assistants and human developers work effectively with this codebase.

## Quick Start for Contributors

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/flask-production-template.git
   cd flask-production-template
   ```

2. **Set Up Environment**
   ```bash
   # Windows
   .\scripts\quickstart.ps1
   
   # Unix/Linux/macOS
   ./scripts/quickstart.sh
   ```

3. **Install Development Tools**
   ```bash
   pip install -r requirements-dev.txt
   pre-commit install
   ```

## AI-Assisted Development

If you're using AI coding assistants (GitHub Copilot, Cursor, Claude, etc.):

1. **Read AI_INSTRUCTIONS.md first** - Contains project architecture and coding standards
2. **Review generated code** - Ensure it follows project patterns
3. **Test thoroughly** - All code must pass existing tests

**Example AI prompt:**
```
Before writing code for this Flask project, read AI_INSTRUCTIONS.md for 
project architecture, coding standards, and templates.
```

## Development Guidelines

### Code Style

- Follow **PEP 8** Python style guide
- Use **type hints** for function parameters and return values
- Write **docstrings** for all public functions and classes
- Keep functions **small and focused** (single responsibility)
- Use **descriptive variable names**

### Project Structure

- **One feature = one blueprint folder**
- **Services contain business logic**
- **Models define database structure**
- **Tests mirror the app structure**

### Error Handling

- Use custom exceptions from `app.utils.service_helpers`
- Log errors with appropriate context
- Handle database transactions properly
- Provide meaningful error messages

### Testing Requirements

- Write tests for all new features
- Maintain test coverage above 80%
- Use pytest fixtures for common test data
- Test both success and error cases

## Making Changes

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Follow the coding standards above
- Add tests for new functionality
- Update documentation if needed

### 3. Run Quality Checks

```bash
# Format code
black .
isort .

# Run linting
flake8 app/ tests/

# Type checking
mypy app/

# Run tests
pytest

# Run all pre-commit checks
pre-commit run --all-files
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "feat: add new feature description"
```

Use conventional commit messages:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation
- `test:` for tests
- `refactor:` for code refactoring

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Pull Request Guidelines

### Before Submitting

- [ ] All tests pass
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] No merge conflicts

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Added tests for new functionality
- [ ] All existing tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
```

## Common Development Tasks

### Adding a New Blueprint

```bash
# Use the blueprint generator
python scripts/make_blueprint.py my_feature

# Or create manually
mkdir app/blueprints/my_feature
touch app/blueprints/my_feature/__init__.py
touch app/blueprints/my_feature/routes.py
```

### Adding Database Models

1. Create model in `app/models/`
2. Import in `app/models/__init__.py`
3. Create migration: `flask db migrate -m "Add new model"`
4. Apply migration: `flask db upgrade`

### Adding Tests

1. Create test file in `tests/` matching the app structure
2. Use existing fixtures from `conftest.py`
3. Test both success and error cases
4. Run tests: `pytest tests/path/to/test_file.py`

## Getting Help

- **Documentation**: Check `docs/` directory
- **Style Guide**: See `docs/python_style_guide.md`
- **AI Instructions**: Read `AI_INSTRUCTIONS.md`
- **Issues**: Create GitHub issue for bugs or questions

## Code of Conduct

Be respectful, inclusive, and constructive in all interactions. We welcome contributors of all skill levels and backgrounds.

---

**Remember**: This template is designed to work well with both AI assistants and human developers. Keep changes simple, well-tested, and well-documented.
