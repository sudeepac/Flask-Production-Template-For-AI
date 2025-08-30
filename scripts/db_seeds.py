#!/usr/bin/env python3
"""Database seeding utilities.

This module provides functions to populate the database with sample data
for development and testing purposes.
"""

import os
import random
import string
import sys
from datetime import datetime
from typing import Any, Dict, List

import click
from faker import Faker

from app import create_app
from app.extensions import db
from app.models.example import Post, User

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Initialize Faker for generating realistic sample data
fake = Faker()


def generate_random_string(length: int = 10) -> str:
    """Generate a random string of specified length."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_sample_users(count: int = 10) -> List[Dict[str, Any]]:
    """Generate sample user data.

    Args:
        count: Number of users to generate

    Returns:
        List of user dictionaries
    """
    users = []

    for i in range(count):
        user = {
            "id": i + 1,
            "username": fake.user_name(),
            "email": fake.email(),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            # 75% active
            "is_active": random.choice([True, True, True, False]),
            # 25% admin
            "is_admin": random.choice([True, False, False, False]),
            "created_at": fake.date_time_between(start_date="-1y", end_date="now"),
            "last_login": (
                fake.date_time_between(start_date="-30d", end_date="now")
                if random.random() > 0.2
                else None
            ),
            "profile": {
                "bio": fake.text(max_nb_chars=200),
                "location": fake.city(),
                "website": fake.url() if random.random() > 0.5 else None,
                "avatar_url": fake.image_url() if random.random() > 0.3 else None,
            },
        }
        users.append(user)

    return users


def generate_sample_posts(
    count: int = 50, user_count: int = 10
) -> List[Dict[str, Any]]:
    """Generate sample blog post data.

    Args:
        count: Number of posts to generate
        user_count: Number of users (for foreign key references)

    Returns:
        List of post dictionaries
    """
    posts = []

    categories = [
        "Technology",
        "Science",
        "Health",
        "Travel",
        "Food",
        "Sports",
        "Entertainment",
    ]
    statuses = ["draft", "published", "archived"]

    for i in range(count):
        post = {
            "id": i + 1,
            "title": fake.sentence(nb_words=6).rstrip("."),
            "slug": fake.slug(),
            "content": fake.text(max_nb_chars=2000),
            "excerpt": fake.text(max_nb_chars=200),
            "author_id": random.randint(1, user_count),
            "category": random.choice(categories),
            "status": random.choice(statuses),
            # 25% featured
            "is_featured": random.choice([True, False, False, False]),
            "view_count": random.randint(0, 1000),
            "like_count": random.randint(0, 100),
            "created_at": fake.date_time_between(start_date="-6m", end_date="now"),
            "updated_at": fake.date_time_between(start_date="-1m", end_date="now"),
            "published_at": (
                fake.date_time_between(start_date="-3m", end_date="now")
                if random.random() > 0.3
                else None
            ),
            "tags": random.sample(
                [
                    "python",
                    "flask",
                    "api",
                    "web",
                    "backend",
                    "frontend",
                    "database",
                    "ml",
                    "ai",
                ],
                k=random.randint(1, 4),
            ),
        }
        posts.append(post)

    return posts


def generate_sample_products(count: int = 30) -> List[Dict[str, Any]]:
    """Generate sample product data for e-commerce scenarios.

    Args:
        count: Number of products to generate

    Returns:
        List of product dictionaries
    """
    products = []

    categories = ["Electronics", "Clothing", "Books", "Home & Garden", "Sports", "Toys"]
    brands = ["TechCorp", "StyleBrand", "HomeComfort", "SportsPro", "BookWorld"]

    for i in range(count):
        product = {
            "id": i + 1,
            "name": fake.catch_phrase(),
            "description": fake.text(max_nb_chars=500),
            "sku": generate_random_string(8).upper(),
            "price": round(random.uniform(9.99, 999.99), 2),
            "cost": round(random.uniform(5.00, 500.00), 2),
            "category": random.choice(categories),
            "brand": random.choice(brands),
            "stock_quantity": random.randint(0, 100),
            # 75% active
            "is_active": random.choice([True, True, True, False]),
            # 25% featured
            "is_featured": random.choice([True, False, False, False]),
            "weight": round(random.uniform(0.1, 10.0), 2),
            "dimensions": {
                "length": round(random.uniform(1, 50), 1),
                "width": round(random.uniform(1, 50), 1),
                "height": round(random.uniform(1, 50), 1),
            },
            "rating": round(random.uniform(1.0, 5.0), 1),
            "review_count": random.randint(0, 500),
            "created_at": fake.date_time_between(start_date="-1y", end_date="now"),
            "updated_at": fake.date_time_between(start_date="-1m", end_date="now"),
        }
        products.append(product)

    return products


def generate_sample_orders(
    count: int = 100, user_count: int = 10, product_count: int = 30
) -> List[Dict[str, Any]]:
    """Generate sample order data.

    Args:
        count: Number of orders to generate
        user_count: Number of users (for foreign key references)
        product_count: Number of products (for order items)

    Returns:
        List of order dictionaries
    """
    orders = []

    statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]
    payment_methods = ["credit_card", "debit_card", "paypal", "bank_transfer"]

    for i in range(count):
        # Generate order items
        num_items = random.randint(1, 5)
        items = []
        total_amount = 0

        for _ in range(num_items):
            product_id = random.randint(1, product_count)
            quantity = random.randint(1, 3)
            unit_price = round(random.uniform(9.99, 199.99), 2)
            item_total = quantity * unit_price
            total_amount += item_total

            items.append(
                {
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "total_price": item_total,
                }
            )

        order = {
            "id": i + 1,
            "order_number": f"ORD-{datetime.now().year}-{str(i + 1).zfill(6)}",
            "user_id": random.randint(1, user_count),
            "status": random.choice(statuses),
            "payment_method": random.choice(payment_methods),
            "payment_status": random.choice(["pending", "completed", "failed"]),
            "subtotal": round(total_amount, 2),
            "tax_amount": round(total_amount * 0.08, 2),  # 8% tax
            "shipping_amount": round(random.uniform(0, 25.99), 2),
            "total_amount": round(total_amount * 1.08 + random.uniform(0, 25.99), 2),
            "currency": "USD",
            "shipping_address": {
                "street": fake.street_address(),
                "city": fake.city(),
                "state": fake.state(),
                "zip_code": fake.zipcode(),
                "country": fake.country(),
            },
            "billing_address": {
                "street": fake.street_address(),
                "city": fake.city(),
                "state": fake.state(),
                "zip_code": fake.zipcode(),
                "country": fake.country(),
            },
            "items": items,
            "notes": fake.text(max_nb_chars=100) if random.random() > 0.7 else None,
            "created_at": fake.date_time_between(start_date="-6m", end_date="now"),
            "updated_at": fake.date_time_between(start_date="-1m", end_date="now"),
        }
        orders.append(order)

    return orders


def generate_api_logs(count: int = 200) -> List[Dict[str, Any]]:
    """Generate sample API access logs.

    Args:
        count: Number of log entries to generate

    Returns:
        List of log dictionaries
    """
    logs = []

    endpoints = [
        "/api/users",
        "/api/posts",
        "/api/products",
        "/api/orders",
        "/health",
        "/api/status",
    ]
    methods = ["GET", "POST", "PUT", "DELETE"]
    status_codes = [200, 201, 400, 401, 403, 404, 500]
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "PostmanRuntime/7.29.0",
        "curl/7.68.0",
        "Python/3.9 requests/2.25.1",
    ]

    for i in range(count):
        log = {
            "id": i + 1,
            "timestamp": fake.date_time_between(start_date="-30d", end_date="now"),
            "method": random.choice(methods),
            "endpoint": random.choice(endpoints),
            "status_code": random.choice(status_codes),
            "response_time_ms": random.randint(10, 2000),
            "ip_address": fake.ipv4(),
            "user_agent": random.choice(user_agents),
            "user_id": random.randint(1, 10) if random.random() > 0.3 else None,
            "request_size": random.randint(100, 5000),
            "response_size": random.randint(200, 10000),
        }
        logs.append(log)

    return logs


def seed_users(count: int = 10) -> None:
    """Seed the database with sample users.

    Args:
        count: Number of users to generate
    """
    print(f"Seeding {count} users...")

    for i in range(count):
        user = User(
            username=fake.user_name(),
            email=fake.email(),
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            is_active=random.choice([True, True, True, False]),  # 75% active
            is_admin=random.choice([True, False, False, False]),  # 25% admin
        )
        db.session.add(user)

    db.session.commit()
    print(f"Successfully seeded {count} users")


def seed_posts(count: int = 20) -> None:
    """Seed the database with sample posts.

    Args:
        count: Number of posts to generate
    """
    print(f"Seeding {count} posts...")

    # Get all users to assign posts to
    users = User.query.all()
    if not users:
        print("No users found. Please seed users first.")
        return

    for i in range(count):
        is_published = random.choice([True, True, False])  # 66% published
        title = fake.sentence(nb_words=6)
        # Generate slug from title
        slug = (
            title.lower()
            .replace(" ", "-")
            .replace(".", "")
            .replace(",", "")
            .replace("!", "")
            .replace("?", "")
            + f"-{i}"
        )

        post = Post(
            title=title,
            slug=slug,
            content=fake.text(max_nb_chars=500),
            excerpt=fake.text(max_nb_chars=150),
            category=random.choice(
                ["Technology", "Science", "Business", "Health", "Education"]
            ),
            author_id=random.choice(users).id,
            status="published" if is_published else "draft",
            published_at=(
                fake.date_time_between(start_date="-30d", end_date="now")
                if is_published
                else None
            ),
        )
        db.session.add(post)

    db.session.commit()
    print(f"Successfully seeded {count} posts")


def seed_all_data(sample_size: int = 10) -> None:
    """Seed the database with all sample data types.

    Args:
        sample_size: Number of records to generate for each type
    """
    print("Seeding database with sample data...")

    seed_users(sample_size)
    seed_posts(sample_size * 2)  # More posts than users

    print("\n_database seeding completed successfully!")


def clear_all_data() -> None:
    """Clear all data from database tables.

    Warning: This will delete all data!
    """
    print("Clearing all database data...")

    # Delete in reverse order of dependencies
    Post.query.delete()
    User.query.delete()

    db.session.commit()
    print("All data cleared successfully!")


@click.command()
@click.option("--users", default=10, help="Number of users to create")
@click.option("--posts", default=20, help="Number of posts to create")
@click.option("--clear", is_flag=True, help="Clear existing data first")
def seed_db(users, posts, clear):
    """Seed the database with sample data."""
    app = create_app()

    with app.app_context():
        if clear:
            clear_all_data()

        seed_users(users)
        seed_posts(posts)


if __name__ == "__main__":
    seed_db()