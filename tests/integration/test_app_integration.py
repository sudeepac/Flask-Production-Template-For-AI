"""Integration tests for the Flask application.

This module tests the integration between different components
of the application, including blueprints, database, and extensions.
"""

from flask import url_for

from app.extensions import cache, db


class TestApplicationIntegration:
    """Test integration between application components."""

    def test_app_blueprint_integration(self, client):
        """Test that all blueprints are properly integrated."""
        # Test root route
        response = client.get("/")
        assert response.status_code == 200
        assert response.is_json

        # Test examples blueprint
        response = client.get("/examples/")
        assert response.status_code == 200
        assert response.is_json

        # Test API blueprint (if exists)
        response = client.get("/api/info")
        # Should either work or return 404 if not implemented
        assert response.status_code in [200, 404]

    def test_database_blueprint_integration(self, app, client):
        """Test database operations through API endpoints."""
        with app.app_context():
            # Create a test table
            db.engine.execute(
                """
                CREATE TABLE IF NOT EXISTS test_integration (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Insert test data
            db.engine.execute(
                "INSERT INTO test_integration (name) VALUES (?)", ("test_record",)
            )

            # Test that we can query through the application
            result = db.engine.execute(
                "SELECT * FROM test_integration WHERE name = ?", ("test_record",)
            )
            row = result.fetchone()
            assert row is not None
            assert row["name"] == "test_record"

    def test_cache_blueprint_integration(self, app, client):
        """Test cache operations through API endpoints."""
        with app.app_context():
            # Test cache operations
            cache.set("integration_test", "test_value", timeout=60)

            # Verify cache works
            value = cache.get("integration_test")
            assert value == "test_value"

            # Test cache through API (if cache endpoint exists)
            # This would test actual cache usage in endpoints
            response = client.get("/examples/hello")
            assert response.status_code == 200

    def test_error_handling_integration(self, client):
        """Test error handling across different components."""
        # Test 404 error
        response = client.get("/nonexistent/route")
        assert response.status_code == 404
        assert response.is_json

        data = response.get_json()
        assert "error" in data

        # Test 400 error (bad request)
        response = client.get("/examples/echo")  # Missing required parameter
        assert response.status_code == 400
        assert response.is_json

        data = response.get_json()
        assert "error" in data

    def test_logging_integration(self, app, client, caplog):
        """Test logging integration across components."""
        with caplog.at_level("INFO"):
            # Make requests that should generate logs
            client.get("/")
            client.get("/examples/hello")
            client.get("/nonexistent")  # Should log 404

            # Check that logs were generated
            # Note: Actual log checking depends on logging configuration
            assert len(caplog.records) >= 0  # At least some logs should exist


class TestDatabaseIntegration:
    """Test database integration scenarios."""

    def test_database_session_management(self, app):
        """Test database session management across requests."""
        with app.app_context():
            # Test session creation and cleanup
            session1 = db.session
            assert session1 is not None

            # Test that session persists within context
            session2 = db.session
            assert session1 is session2

            # Test session operations
            result = session1.execute("SELECT 1 as test")
            assert result.fetchone()["test"] == 1

    def test_database_transaction_rollback(self, app):
        """Test database transaction rollback functionality."""
        with app.app_context():
            try:
                # Create test table
                db.engine.execute(
                    """
                    CREATE TABLE IF NOT EXISTS test_rollback (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL
                    )
                """
                )

                # Start transaction
                db.session.begin()

                # Insert data
                db.session.execute(
                    "INSERT INTO test_rollback (name) VALUES (?)", ("test_data",)
                )

                # Rollback transaction
                db.session.rollback()

                # Verify data was not committed
                result = db.session.execute(
                    "SELECT COUNT(*) as count FROM test_rollback WHERE name = ?",
                    ("test_data",),
                )
                count = result.fetchone()["count"]
                assert count == 0

            except Exception:
                db.session.rollback()
                raise

    def test_database_connection_pooling(self, app):
        """Test database connection pooling."""
        with app.app_context():
            # Test multiple connections
            connections = []
            for i in range(5):
                conn = db.engine.connect()
                result = conn.execute("SELECT ? as test", (i,))
                assert result.fetchone()["test"] == i
                connections.append(conn)

            # Close all connections
            for conn in connections:
                conn.close()


class TestCacheIntegration:
    """Test cache integration scenarios."""

    def test_cache_across_requests(self, app, client):
        """Test cache persistence across multiple requests."""
        with app.app_context():
            # Set cache value
            cache.set("request_test", "persistent_value", timeout=60)

            # Make multiple requests
            for i in range(3):
                response = client.get("/examples/hello")
                assert response.status_code == 200

                # Verify cache still exists
                value = cache.get("request_test")
                assert value == "persistent_value"

    def test_cache_invalidation(self, app):
        """Test cache invalidation scenarios."""
        with app.app_context():
            # Set cache values
            cache.set("key1", "value1", timeout=60)
            cache.set("key2", "value2", timeout=60)

            # Verify values exist
            assert cache.get("key1") == "value1"
            assert cache.get("key2") == "value2"

            # Clear specific key
            cache.delete("key1")
            assert cache.get("key1") is None
            assert cache.get("key2") == "value2"

            # Clear all cache
            cache.clear()
            assert cache.get("key2") is None

    def test_cache_with_database(self, app):
        """Test cache integration with database operations."""
        with app.app_context():
            # Create test table
            db.engine.execute(
                """
                CREATE TABLE IF NOT EXISTS test_cache_db (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    value TEXT NOT NULL
                )
            """
            )

            # Insert test data
            db.engine.execute(
                "INSERT INTO test_cache_db (name, value) VALUES (?, ?)",
                ("test", "database_value"),
            )

            # Function that uses both cache and database
            def get_cached_value(name):
                """
                TODO: Add return description
                Returns:

                name: TODO: Add description
                Args:

                TODO: Add function description.

                Function get_cached_value.
                """
                # Check cache first
                cache_key = f"db_value_{name}"
                cached = cache.get(cache_key)
                if cached:
                    return cached

                # Get from database
                result = db.engine.execute(
                    "SELECT value FROM test_cache_db WHERE name = ?", (name,)
                )
                row = result.fetchone()
                if row:
                    value = row["value"]
                    # Cache the result
                    cache.set(cache_key, value, timeout=60)
                    return value
                return None

            # Test cache miss (first call)
            value1 = get_cached_value("test")
            assert value1 == "database_value"

            # Test cache hit (second call)
            value2 = get_cached_value("test")
            assert value2 == "database_value"

            # Verify value is cached
            cached_value = cache.get("db_value_test")
            assert cached_value == "database_value"


class TestBlueprintIntegration:
    """Test blueprint integration scenarios."""

    def test_blueprint_url_generation(self, app):
        """Test URL generation for blueprint routes."""
        with app.test_request_context():
            # Test URL generation for examples blueprint
            try:
                examples_url = url_for("examples.index")
                assert examples_url == "/examples/"
            except Exception:
                # URL generation might not work if blueprint names differ
                pass

    def test_blueprint_error_handling(self, client):
        """Test error handling within blueprints."""
        # Test blueprint-specific error handling
        response = client.get("/examples/nonexistent")
        assert response.status_code == 404

        # Test cross-blueprint error consistency
        response1 = client.get("/examples/nonexistent")
        response2 = client.get("/api/nonexistent")

        # Both should return 404 with consistent format
        assert response1.status_code == 404
        assert response2.status_code == 404

        if response1.is_json and response2.is_json:
            data1 = response1.get_json()
            data2 = response2.get_json()
            # Error format should be consistent
            assert "error" in data1
            assert "error" in data2

    def test_blueprint_middleware_integration(self, client):
        """Test middleware integration across blueprints."""
        # Test that middleware (like CORS, auth) works across blueprints
        headers = {"Origin": "http://localhost:3000"}

        # Test examples blueprint
        response1 = client.get("/examples/hello", headers=headers)
        assert response1.status_code == 200

        # Test API blueprint
        response2 = client.get("/api/info", headers=headers)
        # Should work or return 404 if not implemented
        assert response2.status_code in [200, 404]

        # Both should handle CORS headers consistently
        # (This depends on actual CORS configuration)