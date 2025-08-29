# Database Management Scripts

This directory contains scripts for managing the database, migrations, and seeding data.

## Scripts Overview

### `db_init.py` - Database Initialization and Migration Management

A comprehensive CLI tool for managing database schema and migrations.

**Usage:**
```bash
# Initialize database with migrations
python scripts/db_init.py init

# Create a new migration
python scripts/db_init.py migrate -m "Add new table"

# Apply pending migrations
python scripts/db_init.py upgrade

# Downgrade database by one migration
python scripts/db_init.py downgrade

# Reset database (WARNING: Deletes all data!)
python scripts/db_init.py reset

# Show help
python scripts/db_init.py --help
```

### `db_seeds.py` - Database Seeding

A CLI tool for populating the database with sample data for development and testing.

**Usage:**
```bash
# Seed with default amounts (10 users, 20 posts)
python scripts/db_seeds.py

# Seed with custom amounts
python scripts/db_seeds.py --users 5 --posts 10

# Clear existing data before seeding
python scripts/db_seeds.py --clear --users 3 --posts 6

# Show help
python scripts/db_seeds.py --help
```

## Quick Setup Workflow

For a fresh database setup:

1. **Initialize the database:**
   ```bash
   python scripts/db_init.py init
   ```

2. **Seed with sample data:**
   ```bash
   python scripts/db_seeds.py --users 10 --posts 20
   ```

3. **Start the development server:**
   ```bash
   python -m flask run
   ```

## Development Workflow

When making model changes:

1. **Create a migration:**
   ```bash
   python scripts/db_init.py migrate -m "Describe your changes"
   ```

2. **Apply the migration:**
   ```bash
   python scripts/db_init.py upgrade
   ```

3. **Re-seed if needed:**
   ```bash
   python scripts/db_seeds.py --clear --users 5 --posts 10
   ```

## Features

### Database Initialization (`db_init.py`)
- ✅ Initialize Flask-Migrate
- ✅ Create initial migrations
- ✅ Apply/rollback migrations
- ✅ Database reset functionality
- ✅ Status checking
- ✅ CLI interface with help

### Database Seeding (`db_seeds.py`)
- ✅ Generate realistic sample users
- ✅ Generate sample blog posts with relationships
- ✅ Configurable data amounts
- ✅ Clear existing data option
- ✅ CLI interface with options
- ✅ Uses Faker for realistic data

## Dependencies

These scripts require:
- `flask-migrate` - Database migrations
- `click` - CLI interface
- `faker` - Sample data generation (for seeding)

All dependencies are included in `requirements.txt` and `requirements-optional.txt`.