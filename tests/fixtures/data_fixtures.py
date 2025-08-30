"""Data fixtures for testing.

Basic data fixtures for testing.
"""

import pytest


@pytest.fixture
def sample_data():
    """Sample data for testing."""
    return {
        "name": "Test Item",
        "description": "A test item for testing purposes",
        "value": 42
    }


@pytest.fixture
def sample_list():
    """Sample list data for testing."""
    return [
        {"id": 1, "name": "Item 1"},
        {"id": 2, "name": "Item 2"},
        {"id": 3, "name": "Item 3"}
    ]


@pytest.fixture
def invalid_data():
    """Invalid data for testing error cases."""
    return {
        "incomplete": "data"
    }