"""Unit tests for Flask extensions.

This module tests the initialization and functionality of
Flask extensions used in the application.
"""

import pytest
from flask import Flask
from app.extensions import db, cache, migrate
from app import create_app


class TestDatabaseExtension:
    """Test SQLAlchemy database extension."""
    
    def test_db_initialization(self, app):
        """Test database extension initialization."""
        with app.app_context():
            assert db is not None
            assert hasattr(db, 'engine')
            assert hasattr(db, 'session')
            assert hasattr(db, 'Model')
    
    def test_db_connection(self, app):
        """Test database connection."""
        with app.app_context():
            # Test basic connection
            result = db.engine.execute('SELECT 1 as test')
            assert result.fetchone()['test'] == 1
    
    def test_db_session(self, app):
        """Test database session functionality."""
        with app.app_context():
            # Test session is available
            assert db.session is not None
            
            # Test session operations
            db.session.execute('SELECT 1')
            db.session.commit()
    
    def test_db_model_base(self, app):
        """Test database model base class."""
        with app.app_context():
            # Test Model base class
            assert hasattr(db.Model, 'query')
            assert hasattr(db.Model, '__tablename__')


class TestCacheExtension:
    """Test Flask-Caching extension."""
    
    def test_cache_initialization(self, app):
        """Test cache extension initialization."""
        with app.app_context():
            assert cache is not None
            assert hasattr(cache, 'get')
            assert hasattr(cache, 'set')
            assert hasattr(cache, 'delete')
    
    def test_cache_operations(self, app):
        """Test basic cache operations."""
        with app.app_context():
            # Test set and get
            cache.set('test_key', 'test_value', timeout=60)
            value = cache.get('test_key')
            assert value == 'test_value'
            
            # Test delete
            cache.delete('test_key')
            value = cache.get('test_key')
            assert value is None
    
    def test_cache_timeout(self, app):
        """Test cache timeout functionality."""
        with app.app_context():
            # Set with very short timeout
            cache.set('timeout_key', 'timeout_value', timeout=1)
            
            # Should be available immediately
            value = cache.get('timeout_key')
            assert value == 'timeout_value'
            
            # Note: We can't easily test timeout in unit tests
            # without adding sleep, which slows down tests
    
    def test_cache_decorator(self, app):
        """Test cache decorator functionality."""
        with app.app_context():
            call_count = 0
            
            @cache.memoize(timeout=60)
            def expensive_function(x):
                nonlocal call_count
                call_count += 1
                return x * 2
            
            # First call
            result1 = expensive_function(5)
            assert result1 == 10
            assert call_count == 1
            
            # Second call should use cache
            result2 = expensive_function(5)
            assert result2 == 10
            assert call_count == 1  # Should not increment


class TestMigrateExtension:
    """Test Flask-Migrate extension."""
    
    def test_migrate_initialization(self, app):
        """Test migrate extension initialization."""
        with app.app_context():
            assert migrate is not None
            assert hasattr(migrate, 'init_app')
    
    def test_migrate_commands_available(self, app):
        """Test that migrate commands are available."""
        # Test that CLI commands are registered
        runner = app.test_cli_runner()
        result = runner.invoke(args=['--help'])
        assert 'db' in result.output


class TestExtensionIntegration:
    """Test integration between extensions."""
    
    def test_db_cache_integration(self, app):
        """Test database and cache working together."""
        with app.app_context():
            # Create a simple model for testing
            class TestModel(db.Model):
                __tablename__ = 'test_model'
                id = db.Column(db.Integer, primary_key=True)
                name = db.Column(db.String(50))
            
            # Create tables
            db.create_all()
            
            # Test caching database results
            @cache.memoize(timeout=60)
            def get_test_data():
                return TestModel.query.all()
            
            # Should work without errors
            result = get_test_data()
            assert isinstance(result, list)
    
    def test_all_extensions_configured(self, app):
        """Test that all extensions are properly configured."""
        with app.app_context():
            # Check that all extensions are initialized
            extensions = [
                ('db', db),
                ('cache', cache),
                ('migrate', migrate),
            ]
            
            for name, ext in extensions:
                assert ext is not None, f"Extension {name} is not initialized"
    
    def test_extension_cleanup(self, app):
        """Test extension cleanup on app teardown."""
        with app.app_context():
            # Test that extensions handle cleanup properly
            # This is mainly to ensure no exceptions are raised
            db.session.remove()
            cache.clear()


class TestExtensionConfiguration:
    """Test extension configuration."""
    
    def test_database_config(self, app):
        """Test database configuration."""
        assert 'SQLALCHEMY_DATABASE_URI' in app.config
        assert app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] is False
    
    def test_cache_config(self, app):
        """Test cache configuration."""
        # Cache type should be configured
        assert 'CACHE_TYPE' in app.config
    
    def test_migrate_config(self, app):
        """Test migrate configuration."""
        # Migrate should have a directory configured
        with app.app_context():
            # This tests that migrate is properly configured
            # without requiring actual migration files
            assert migrate.get_config() is not None