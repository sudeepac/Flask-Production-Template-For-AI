#!/usr/bin/env python3
"""Database initialization and migration utilities.

This module provides functions to initialize, migrate, and manage
the database schema using Flask-Migrate.
"""

import os
import sys
from pathlib import Path
import click
from flask import Flask
from flask.cli import with_appcontext

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from flask_migrate import Migrate, init as flask_migrate_init, migrate as flask_migrate_migrate, upgrade as flask_migrate_upgrade, downgrade as flask_migrate_downgrade

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import create_app
from app.extensions import db


def create_cli_app():
    """Create Flask app for CLI operations."""
    app = create_app()
    return app


@click.group()
@click.pass_context
def cli(ctx):
    """Database management commands."""
    ctx.ensure_object(dict)
    ctx.obj['app'] = create_cli_app()


@cli.command()
@click.pass_context
def init_db(ctx):
    """Initialize database and migration repository."""
    app = ctx.obj['app']
    
    with app.app_context():
        try:
            # Initialize migration repository
            click.echo("Initializing migration repository...")
            flask_migrate_init()
            click.echo("✓ Migration repository initialized")
        except Exception as e:
            if "already exists" in str(e).lower():
                click.echo("✓ Migration repository already exists")
            else:
                click.echo(f"✗ Error initializing migration repository: {e}")
                return
        
        try:
            # Create initial migration
            click.echo("Creating initial migration...")
            flask_migrate_migrate(message="Initial migration")
            click.echo("✓ Initial migration created")
        except Exception as e:
            if "no changes" in str(e).lower():
                click.echo("✓ No changes detected for migration")
            else:
                click.echo(f"✗ Error creating migration: {e}")
                return
        
        try:
            # Apply migrations
            click.echo("Applying migrations...")
            flask_migrate_upgrade()
            click.echo("✓ Database initialized successfully")
        except Exception as e:
            click.echo(f"✗ Error applying migrations: {e}")


@cli.command()
@click.pass_context
def create_migration(ctx):
    """Create a new migration."""
    app = ctx.obj['app']
    message = click.prompt("Migration message", default="Auto migration")
    
    with app.app_context():
        try:
            flask_migrate_migrate(message=message)
            click.echo(f"✓ Migration '{message}' created successfully")
        except Exception as e:
            click.echo(f"✗ Error creating migration: {e}")


@cli.command()
@click.pass_context
def upgrade_db(ctx):
    """Apply pending migrations."""
    app = ctx.obj['app']
    
    with app.app_context():
        try:
            flask_migrate_upgrade()
            click.echo("✓ Database upgraded successfully")
        except Exception as e:
            click.echo(f"✗ Error upgrading database: {e}")


@cli.command()
@click.option('--revision', '-r', help='Target revision (default: -1 for one step back)')
@click.pass_context
def downgrade_db(ctx, revision):
    """Downgrade database to previous migration."""
    app = ctx.obj['app']
    target = revision or '-1'
    
    if click.confirm(f"Are you sure you want to downgrade to revision '{target}'?"):
        with app.app_context():
            try:
                flask_migrate_downgrade(revision=target)
                click.echo(f"✓ Database downgraded to revision '{target}'")
            except Exception as e:
                click.echo(f"✗ Error downgrading database: {e}")


@cli.command()
@click.option('--force', is_flag=True, help='Force reset without confirmation')
@click.pass_context
def reset_db(ctx, force):
    """Reset database (drop all tables and recreate)."""
    app = ctx.obj['app']
    
    if not force:
        if not click.confirm("This will delete ALL data. Are you sure?"):
            click.echo("Operation cancelled")
            return
    
    with app.app_context():
        try:
            # Drop all tables
            click.echo("Dropping all tables...")
            db.drop_all()
            
            # Recreate tables
            click.echo("Creating tables...")
            db.create_all()
            
            click.echo("✓ Database reset successfully")
        except Exception as e:
            click.echo(f"✗ Error resetting database: {e}")


@cli.command()
@click.option('--sample-size', '-s', default=10, help='Number of sample records to create')
@click.pass_context
def seed_db(ctx, sample_size):
    """Seed database with sample data."""
    app = ctx.obj['app']
    
    with app.app_context():
        try:
            click.echo(f"Seeding database with {sample_size} sample records...")
            
            # Import seeding functions
            from scripts.db_seeds import seed_all_data
            
            # Run seeding
            seed_all_data(sample_size=sample_size)
            
            click.echo("✓ Database seeded successfully")
        except ImportError:
            click.echo("✗ Seeding module not found. Creating basic seed data...")
            # Basic seeding without external module
            _create_basic_seed_data(sample_size)
        except Exception as e:
            click.echo(f"✗ Error seeding database: {e}")


def _create_basic_seed_data(sample_size):
    """Create basic seed data when seeding module is not available."""
    # This is a placeholder for basic seeding
    # In a real application, you would create sample records here
    click.echo("Basic seed data creation not implemented yet")
    click.echo("Create scripts/db_seeds.py for custom seeding logic")


@cli.command()
@click.pass_context
def status(ctx):
    """Show database status and migration info."""
    app = ctx.obj['app']
    
    with app.app_context():
        try:
            # Check if database exists
            db_path = app.config.get('DATABASE_URL', '').replace('sqlite:///', '')
            if db_path and os.path.exists(db_path):
                db_size = os.path.getsize(db_path)
                click.echo(f"Database: {db_path} ({db_size} bytes)")
            else:
                click.echo("Database: Not found or not SQLite")
            
            # Check tables
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            click.echo(f"Tables: {len(tables)}")
            for table in tables:
                click.echo(f"  - {table}")
            
            # Migration info
            migrations_dir = project_root / "migrations"
            if migrations_dir.exists():
                versions_dir = migrations_dir / "versions"
                if versions_dir.exists():
                    migrations = list(versions_dir.glob("*.py"))
                    click.echo(f"Migrations: {len(migrations)}")
                else:
                    click.echo("Migrations: No versions directory")
            else:
                click.echo("Migrations: Not initialized")
                
        except Exception as e:
            click.echo(f"✗ Error getting database status: {e}")


@cli.command()
@click.pass_context
def setup(ctx):
    """Complete database setup (init + upgrade + seed)."""
    app = ctx.obj['app']
    
    click.echo("Starting complete database setup...")
    
    # Initialize
    ctx.invoke(init_db)
    
    # Seed with sample data
    if click.confirm("Would you like to seed the database with sample data?"):
        sample_size = click.prompt("Sample size", default=10, type=int)
        ctx.invoke(seed_db, sample_size=sample_size)
    
    click.echo("✓ Database setup completed")


@click.group()
@click.pass_context
def cli(ctx):
    """Database management CLI."""
    # Create Flask app and store in context
    app = create_app()
    ctx.ensure_object(dict)
    ctx.obj['app'] = app


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize the database with migrations."""
    app = ctx.obj['app']
    with app.app_context():
        init_database()


@cli.command()
@click.option('--message', '-m', help='Migration message')
@click.pass_context
def migrate(ctx, message):
    """Create a new migration."""
    app = ctx.obj['app']
    with app.app_context():
        create_migration(message)


@cli.command()
@click.pass_context
def upgrade(ctx):
    """Apply pending migrations."""
    app = ctx.obj['app']
    with app.app_context():
        upgrade_database()


@cli.command()
@click.pass_context
def downgrade(ctx):
    """Downgrade database by one migration."""
    app = ctx.obj['app']
    with app.app_context():
        downgrade_database()


@cli.command()
@click.confirmation_option(prompt='Are you sure you want to reset the database?')
@click.pass_context
def reset(ctx):
    """Reset the database (WARNING: This will delete all data!)."""
    app = ctx.obj['app']
    with app.app_context():
        reset_database()


if __name__ == '__main__':
    cli()