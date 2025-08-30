"""Application-specific test fixtures.

This module contains fixtures for testing Flask application
components and functionality.
"""

import os
import tempfile

import pytest

from app import create_app
from app.extensions import db as _db


@pytest.fixture(scope="session")
def app_config():
    """Test application configuration."""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp()

    config = {
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SECRET_KEY": "test-secret-key-for-testing-only",
        "JWT_SECRET_KEY": "test-jwt-secret-key",
        "CACHE_TYPE": "simple",
        "CACHE_DEFAULT_TIMEOUT": 300,
        "ML_MODEL_PATH": "tests/fixtures/models",
        "ML_AUTO_DISCOVER_SERVICES": False,
        "UPLOAD_FOLDER": tempfile.mkdtemp(),
        "MAX_CONTENT_LENGTH": 16 * 1024 * 1024,  # 16MB
        "RATELIMIT_STORAGE_URL": "memory://",
        "CELERY_BROKER_URL": "memory://",
        "CELERY_RESULT_BACKEND": "cache+memory://",
        "ALLOWED_EXTENSIONS": "txt,pdf,png,jpg,jpeg,gif,csv,json",
    }

    yield config

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)

    # Clean up upload folder
    import shutil

    if os.path.exists(config["UPLOAD_FOLDER"]):
        shutil.rmtree(config["UPLOAD_FOLDER"])


@pytest.fixture(scope="session")
def app(app_config):
    """Create Flask application for testing."""
    app = create_app(app_config)

    # Establish application context
    with app.app_context():
        # Create all database tables
        _db.create_all()

        yield app

        # Cleanup
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """Create test client for making HTTP requests."""
    return app.test_client()


@pytest.fixture(scope="function")
def runner(app):
    """Create test runner for CLI commands."""
    return app.test_cli_runner()


@pytest.fixture(scope="function")
def app_context(app):
    """Create application context for testing."""
    with app.app_context():
        yield app


@pytest.fixture(scope="function")
def request_context(app):
    """Create request context for testing."""
    with app.test_request_context():
        yield app


@pytest.fixture(scope="function")
def authenticated_client(client, auth_headers):
    """Create authenticated test client."""

    class AuthenticatedClient:
        def __init__(self, client, headers):
            self.client = client
            self.headers = headers

        def get(self, *args, **kwargs):
            kwargs.setdefault("headers", {}).update(self.headers)
            return self.client.get(*args, **kwargs)

        def post(self, *args, **kwargs):
            kwargs.setdefault("headers", {}).update(self.headers)
            return self.client.post(*args, **kwargs)

        def put(self, *args, **kwargs):
            kwargs.setdefault("headers", {}).update(self.headers)
            return self.client.put(*args, **kwargs)

        def delete(self, *args, **kwargs):
            kwargs.setdefault("headers", {}).update(self.headers)
            return self.client.delete(*args, **kwargs)

        def patch(self, *args, **kwargs):
            kwargs.setdefault("headers", {}).update(self.headers)
            return self.client.patch(*args, **kwargs)

    return AuthenticatedClient(client, auth_headers)


@pytest.fixture(scope="function")
def mock_external_api(monkeypatch):
    """Mock external API calls."""

    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self.json_data = json_data
            self.status_code = status_code
            self.headers = {"Content-Type": "application/json"}

        def json(self):
            return self.json_data

        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"HTTP {self.status_code}")

    def mock_get(url, **kwargs):
        if "api.example.com" in url:
            return MockResponse({"data": "mocked response"})
        return MockResponse({"error": "not found"}, 404)

    def mock_post(url, **kwargs):
        return MockResponse({"success": True, "id": 123})

    monkeypatch.setattr("requests.get", mock_get)
    monkeypatch.setattr("requests.post", mock_post)

    return {"get": mock_get, "post": mock_post}


@pytest.fixture(scope="function")
def temp_file():
    """Create temporary file for testing."""
    fd, path = tempfile.mkstemp()

    try:
        yield path
    finally:
        os.close(fd)
        os.unlink(path)


@pytest.fixture(scope="function")
def temp_directory():
    """Create temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()

    try:
        yield temp_dir
    finally:
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def sample_file_upload(temp_directory):
    """Create sample file for upload testing."""
    file_path = os.path.join(temp_directory, "test_upload.txt")

    with open(file_path, "w") as f:
        f.write("This is a test file for upload testing.\n")
        f.write("It contains multiple lines.\n")
        f.write("And some test data.")

    return file_path


@pytest.fixture(scope="function")
def sample_image_file(temp_directory):
    """Create sample image file for testing."""
    try:
        pass

        from PIL import Image

        # Create a simple test image
        image = Image.new("RGB", (100, 100), color="red")
        file_path = os.path.join(temp_directory, "test_image.png")
        image.save(file_path, "PNG")

        return file_path
    except ImportError:
        # If PIL is not available, create a fake image file
        file_path = os.path.join(temp_directory, "test_image.png")
        with open(file_path, "wb") as f:
            # Write minimal PNG header
            f.write(b"\x89PNG\r\n\x1a\n")
            f.write(b"\x00\x00\x00\rIHDR")
            f.write(b"\x00\x00\x00d\x00\x00\x00d")
            f.write(b"\x08\x02\x00\x00\x00")

        return file_path


@pytest.fixture(scope="function")
def mock_celery_task(monkeypatch):
    """Mock Celery task execution."""

    class MockTask:
        def __init__(self, result=None):
            self.result = result
            self.id = "mock-task-id-123"
            self.state = "SUCCESS"

        def delay(self, *args, **kwargs):
            return self

        def apply_async(self, *args, **kwargs):
            return self

        def get(self, timeout=None):
            return self.result

    def mock_task_decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return MockTask(result)

        return wrapper

    # Mock common Celery decorators and functions
    monkeypatch.setattr("celery.task", mock_task_decorator)
    monkeypatch.setattr(
        "app.tasks.example_task.delay",
        lambda *args, **kwargs: MockTask("task completed"),
    )

    return MockTask


@pytest.fixture(scope="function")
def mock_email_service(monkeypatch):
    """Mock email service for testing."""
    sent_emails = []

    def mock_send_email(to, subject, body, **kwargs):
        email = {"to": to, "subject": subject, "body": body, "kwargs": kwargs}
        sent_emails.append(email)
        return True

    monkeypatch.setattr("app.services.email.send_email", mock_send_email)

    return {"send_email": mock_send_email, "sent_emails": sent_emails}


@pytest.fixture(scope="function")
def performance_monitor():
    """Monitor performance during tests."""
    import os
    import time

    import psutil

    class PerformanceMonitor:
        def __init__(self):
            self.process = psutil.Process(os.getpid())
            self.start_time = None
            self.start_memory = None
            self.measurements = []

        def start(self):
            self.start_time = time.time()
            self.start_memory = self.process.memory_info().rss

        def stop(self):
            if self.start_time is None:
                return None

            end_time = time.time()
            end_memory = self.process.memory_info().rss

            measurement = {
                "duration": end_time - self.start_time,
                "memory_delta": end_memory - self.start_memory,
                "peak_memory": self.process.memory_info().rss,
            }

            self.measurements.append(measurement)
            return measurement

        def get_stats(self):
            if not self.measurements:
                return None

            durations = [m["duration"] for m in self.measurements]
            memory_deltas = [m["memory_delta"] for m in self.measurements]

            return {
                "avg_duration": sum(durations) / len(durations),
                "max_duration": max(durations),
                "min_duration": min(durations),
                "avg_memory_delta": sum(memory_deltas) / len(memory_deltas),
                "max_memory_delta": max(memory_deltas),
                "total_measurements": len(self.measurements),
            }

    return PerformanceMonitor()


@pytest.fixture(scope="function")
def capture_logs(caplog):
    """Enhanced log capturing with filtering."""
    import logging

    class LogCapture:
        def __init__(self, caplog):
            self.caplog = caplog

        def get_logs(self, level=None, logger_name=None):
            logs = self.caplog.records

            if level:
                level_num = getattr(logging, level.upper())
                logs = [log for log in logs if log.levelno >= level_num]

            if logger_name:
                logs = [log for log in logs if logger_name in log.name]

            return logs

        def has_log(self, message, level=None):
            logs = self.get_logs(level)
            return any(message in log.message for log in logs)

        def clear(self):
            self.caplog.clear()

    return LogCapture(caplog)
