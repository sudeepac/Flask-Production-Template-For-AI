# GitHub Copilot Instructions for Flask Production Template

## 🚨 CRITICAL: Read AI Instructions First

**Before generating ANY code suggestions, you MUST read and follow the guidelines in [`../AI_INSTRUCTIONS.md`](../AI_INSTRUCTIONS.md).**

This file contains:
- Project architecture and coding standards
- Directory structure rules
- Development workflow guidelines  
- Code generation templates
- Testing guidelines

## Project Overview

This is a production-ready Flask template with:
- ✅ Security (JWT authentication, input validation)
- ✅ Scalability (caching, database optimization)
- ✅ Maintainability (testing, documentation, CI/CD)
- ✅ Developer Experience (auto-setup scripts, clear structure)

## Key Guidelines for Code Generation

1. **Architecture**: Follow the blueprint-based structure in `app/blueprints/`
2. **Templates**: Use the code templates in `__template__/` for new features
3. **Testing**: Every new feature needs corresponding tests in `tests/`
4. **Documentation**: Include docstrings and comments as specified in AI_INSTRUCTIONS.md
5. **Standards**: Follow the coding standards and patterns established in the project

## Quick Reference

- **New Blueprint**: Use `scripts/make_blueprint.py`
- **Database Models**: Extend from `app/models/base.py`
- **API Schemas**: Use versioned schemas in `app/schemas/v1/` or `app/schemas/v2/`
- **Services**: Extend from `app/services/base.py`
- **Tests**: Follow patterns in `tests/` directory

## File Structure to Respect

```
app/
├── blueprints/           # One folder per feature
├── models/              # Database models
├── schemas/             # API schemas (versioned)
├── services/            # Business logic
├── utils/               # Pure helpers
└── static/templates/    # Frontend assets
```

---

**Remember: Always check `AI_INSTRUCTIONS.md` for the most up-to-date guidelines before suggesting code changes.**