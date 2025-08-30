#!/usr/bin/env python3
"""Manual test for register endpoint."""

from app import create_app


def test_register():
    """Test the register endpoint manually."""
    app = create_app("testing")

    # Create database tables for testing
    with app.app_context():
        from app.extensions import db

        db.create_all()

    with app.test_client() as client:
        # Test data
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPassword123!",
        }

        # Make request
        response = client.post(
            "/auth/register", json=data, headers={"Content-Type": "application/json"}
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.get_json()}")
        print(f"Response Data: {response.data.decode()}")

        return response


if __name__ == "__main__":
    test_register()
