"""Generate a demo SQLite database for schema2doc.

Run with:  python examples/create_demo_db.py
"""

import os
import sqlite3
from pathlib import Path


def create_demo_db(output_path: str = "examples/ecommerce.db") -> None:
    """Create a realistic e-commerce schema with 5 tables and FK relationships."""
    # Ensure parent directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Remove existing file if present
    if os.path.exists(output_path):
        os.remove(output_path)

    conn = sqlite3.connect(output_path)
    cursor = conn.cursor()

    # Users table
    cursor.execute(
        """
        CREATE TABLE users (
            id         INTEGER PRIMARY KEY NOT NULL,
            email      TEXT    NOT NULL UNIQUE,
            full_name  TEXT    NOT NULL,
            created_at TEXT
        )
        """
    )

    # Categories table
    cursor.execute(
        """
        CREATE TABLE categories (
            id   INTEGER PRIMARY KEY NOT NULL,
            name TEXT    NOT NULL,
            slug TEXT    NOT NULL UNIQUE
        )
        """
    )

    # Products table (FK -> categories)
    cursor.execute(
        """
        CREATE TABLE products (
            id         INTEGER PRIMARY KEY NOT NULL,
            category_id INTEGER NOT NULL,
            title      TEXT    NOT NULL,
            price      REAL    NOT NULL,
            is_active  INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE ON UPDATE RESTRICT
        )
        """
    )

    # Orders table (FK -> users)
    cursor.execute(
        """
        CREATE TABLE orders (
            id           INTEGER PRIMARY KEY NOT NULL,
            user_id      INTEGER NOT NULL,
            status       TEXT    NOT NULL,
            total_amount REAL    NOT NULL,
            created_at   TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE RESTRICT
        )
        """
    )

    # Order items table (FK -> orders, FK -> products)
    cursor.execute(
        """
        CREATE TABLE order_items (
            id         INTEGER PRIMARY KEY NOT NULL,
            order_id   INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity   INTEGER NOT NULL,
            unit_price REAL    NOT NULL,
            FOREIGN KEY (order_id)   REFERENCES orders(id)   ON DELETE CASCADE ON UPDATE RESTRICT,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE ON UPDATE RESTRICT
        )
        """
    )

    conn.commit()
    conn.close()
    print(f"Demo database created at: {output_path}")


if __name__ == "__main__":
    create_demo_db()