"""API tests for the examples blueprint.

This module tests all API endpoints in the examples blueprint,
including request/response validation and error handling.
"""

import json

import pytest
from flask import url_for


class TestExamplesAPI:
    """Test examples API endpoints."""

    def test_examples_index(self, client):
        """Test the examples index endpoint."""
        response = client.get("/examples/")
        assert response.status_code == 200
        assert response.is_json

        data = response.get_json()
        assert "endpoints" in data
        assert "description" in data
        assert isinstance(data["endpoints"], list)

    def test_examples_hello_world(self, client):
        """Test the hello world endpoint."""
        response = client.get("/examples/hello")
        assert response.status_code == 200
        assert response.is_json

        data = response.get_json()
        assert "message" in data
        assert data["message"] == "Hello, World!"
        assert "timestamp" in data

    def test_examples_echo_get(self, client):
        """Test the echo endpoint with GET request."""
        response = client.get("/examples/echo?message=test")
        assert response.status_code == 200
        assert response.is_json

        data = response.get_json()
        assert "echo" in data
        assert data["echo"] == "test"
        assert "method" in data
        assert data["method"] == "GET"

    def test_examples_echo_post(self, client, api_headers):
        """Test the echo endpoint with POST request."""
        payload = {"message": "test post message"}
        response = client.post(
            "/examples/echo", data=json.dumps(payload), headers=api_headers
        )
        assert response.status_code == 200
        assert response.is_json

        data = response.get_json()
        assert "echo" in data
        assert data["echo"] == "test post message"
        assert "method" in data
        assert data["method"] == "POST"

    def test_examples_echo_no_message(self, client):
        """Test the echo endpoint without message parameter."""
        response = client.get("/examples/echo")
        assert response.status_code == 400
        assert response.is_json

        data = response.get_json()
        assert "error" in data

    def test_examples_status_codes(self, client):
        """Test the status codes endpoint."""
        # Test different status codes
        test_codes = [200, 201, 400, 404, 500]

        for code in test_codes:
            response = client.get(f"/examples/status/{code}")
            assert response.status_code == code

            if response.is_json:
                data = response.get_json()
                assert "status_code" in data
                assert data["status_code"] == code

    def test_examples_json_response(self, client):
        """Test the JSON response endpoint."""
        response = client.get("/examples/json")
        assert response.status_code == 200
        assert response.is_json
        assert response.headers["Content-Type"] == "application/json"

        data = response.get_json()
        assert "data" in data
        assert "metadata" in data
        assert isinstance(data["data"], dict)

    def test_examples_headers(self, client):
        """Test the headers endpoint."""
        custom_headers = {"X-Custom-Header": "test-value", "User-Agent": "test-agent"}

        response = client.get("/examples/headers", headers=custom_headers)
        assert response.status_code == 200
        assert response.is_json

        data = response.get_json()
        assert "headers" in data
        assert "X-Custom-Header" in data["headers"]
        assert data["headers"]["X-Custom-Header"] == "test-value"

    def test_examples_user_agent(self, client):
        """Test the user agent endpoint."""
        custom_user_agent = "TestBot/1.0"
        headers = {"User-Agent": custom_user_agent}

        response = client.get("/examples/user-agent", headers=headers)
        assert response.status_code == 200
        assert response.is_json

        data = response.get_json()
        assert "user_agent" in data
        assert data["user_agent"] == custom_user_agent


class TestExamplesAPIValidation:
    """Test API validation and error handling."""

    def test_invalid_json_request(self, client):
        """Test handling of invalid JSON in request."""
        headers = {"Content-Type": "application/json"}
        response = client.post("/examples/echo", data="invalid json", headers=headers)
        assert response.status_code == 400
        assert response.is_json

        data = response.get_json()
        assert "error" in data

    def test_missing_content_type(self, client):
        """Test handling of missing content type."""
        payload = {"message": "test"}
        response = client.post(
            "/examples/echo",
            data=json.dumps(payload)
            # No Content-Type header
        )
        # Should still work or return appropriate error
        assert response.status_code in [200, 400, 415]

    def test_large_payload(self, client, api_headers):
        """Test handling of large payloads."""
        # Create a large message
        large_message = "x" * 10000
        payload = {"message": large_message}

        response = client.post(
            "/examples/echo", data=json.dumps(payload), headers=api_headers
        )

        # Should handle large payloads gracefully
        assert response.status_code in [200, 413]  # 413 = Payload Too Large

    def test_special_characters(self, client, api_headers):
        """Test handling of special characters."""
        special_message = 'Hello 世界! 🌍 <script>alert("xss")</script>'
        payload = {"message": special_message}

        response = client.post(
            "/examples/echo", data=json.dumps(payload), headers=api_headers
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data["echo"] == special_message


class TestExamplesAPIPerformance:
    """Test API performance characteristics."""

    @pytest.mark.performance
    def test_response_time(self, client):
        """Test API response time."""
        import time

        start_time = time.time()
        response = client.get("/examples/hello")
        end_time = time.time()

        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 1.0  # Should respond within 1 second

    @pytest.mark.performance
    def test_concurrent_requests(self, client):
        """Test handling of multiple concurrent requests."""
        import threading
        import time

        results = []

        def make_request():
            response = client.get("/examples/hello")
            results.append(response.status_code)

        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)

        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        end_time = time.time()

        # All requests should succeed
        assert len(results) == 10
        assert all(status == 200 for status in results)

        # Should complete within reasonable time
        total_time = end_time - start_time
        assert total_time < 5.0  # Should complete within 5 seconds


class TestExamplesAPIDocumentation:
    """Test API documentation and metadata."""

    def test_api_endpoints_documented(self, client):
        """Test that API endpoints are properly documented."""
        response = client.get("/examples/")
        assert response.status_code == 200

        data = response.get_json()
        endpoints = data.get("endpoints", [])

        # Check that endpoints have required documentation
        for endpoint in endpoints:
            assert "path" in endpoint
            assert "method" in endpoint
            assert "description" in endpoint

    def test_api_version_info(self, client):
        """Test that API version information is available."""
        response = client.get("/examples/")
        assert response.status_code == 200

        data = response.get_json()
        # Should have some version or metadata information
        assert "description" in data or "version" in data

    def test_api_error_format(self, client):
        """Test that API errors follow consistent format."""
        # Test a known error endpoint
        response = client.get("/examples/echo")  # Missing required parameter
        assert response.status_code == 400
        assert response.is_json

        data = response.get_json()
        # Error responses should have consistent structure
        assert "error" in data
        assert isinstance(data["error"], str)
