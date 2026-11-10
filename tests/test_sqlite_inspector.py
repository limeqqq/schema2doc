"""Test the SQLite inspector extracts schema correctly."""

import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

# Make the project root importable so `schema2doc` package can be found
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from schema2doc.inspectors.sqlite import SQLiteInspector
from schema2doc.models import Table, Column, ForeignKey, Index


class TestSQLiteInspector(unittest.TestCase):
    """Verify SQLiteInspector extracts tables, columns, PKs and FKs."""

    def setUp(self):
        # Build a temp SQLite DB with 3 tables and FK relationships.
        self.db_path = None
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self._build_schema(self.db_path)

    def tearDown(self):
        if self.db_path and os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def _build_schema(self, path: str):
        conn = sqlite3.connect(path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY NOT NULL,
                email TEXT NOT NULL,
                created_at TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY NOT NULL,
                user_id INTEGER NOT NULL,
                order_date TEXT,
                total REAL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE RESTRICT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE order_items (
                id INTEGER PRIMARY KEY NOT NULL,
                order_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY (item_id) REFERENCES users(id)
            )
            """
        )
        conn.commit()
        conn.close()

    def test_inspect_returns_three_tables(self):
        inspector = SQLiteInspector(self.db_path)
        try:
            tables = inspector.inspect()
        finally:
            inspector.close()

        self.assertEqual(len(tables), 3, "Expected 3 tables in the schema")
        tables_map = {t.name: t for t in tables}

        # All three tables exist
        self.assertIn("users", tables_map)
        self.assertIn("orders", tables_map)
        self.assertIn("order_items", tables_map)

    def test_users_columns(self):
        inspector = SQLiteInspector(self.db_path)
        try:
            tables = inspector.inspect()
        finally:
            inspector.close()

        tables_map = {t.name: t for t in tables}
        users = tables_map["users"]
        cols = users.columns

        # Number of columns
        self.assertEqual(len(cols), 3)

        # Column names
        self.assertEqual([c.name for c in cols], ["id", "email", "created_at"])

        # Data types
        self.assertEqual(cols[0].data_type, "INTEGER")
        self.assertEqual(cols[1].data_type, "TEXT")

        # PK flags
        self.assertTrue(cols[0].is_pk)
        self.assertFalse(cols[1].is_pk)
        self.assertFalse(cols[2].is_pk)

        # Nullability
        self.assertFalse(cols[1].is_nullable, "email should be NOT NULL")
        self.assertTrue(cols[2].is_nullable, "created_at should be nullable")

    def test_orders_columns(self):
        inspector = SQLiteInspector(self.db_path)
        try:
            tables = inspector.inspect()
        finally:
            inspector.close()

        tables_map = {t.name: t for t in tables}
        orders = tables_map["orders"]
        cols = orders.columns

        self.assertEqual(len(cols), 4)
        self.assertEqual([c.name for c in cols], ["id", "user_id", "order_date", "total"])
        self.assertTrue(cols[0].is_pk)          # id is PK
        self.assertFalse(cols[1].is_pk)         # user_id is FK, not PK

    def test_orders_foreign_keys(self):
        inspector = SQLiteInspector(self.db_path)
        try:
            tables = inspector.inspect()
        finally:
            inspector.close()

        tables_map = {t.name: t for t in tables}
        orders = tables_map["orders"]
        fks = orders.foreign_keys

        self.assertGreaterEqual(len(fks), 1, "orders should have at least one FK")
        fk_users = [
            f for f in fks
            if f.from_column == "user_id" and f.target_table == "users" and f.target_column == "id"
        ]
        self.assertEqual(len(fk_users), 1, "Expected FK orders.user_id -> users.id")

        self.assertTrue(
            any(f.on_delete == "CASCADE" for f in fks),
            f"orders FK on_delete should be CASCADE, got {[f.on_delete for f in fks]}",
        )

    def test_order_items_foreign_keys(self):
        inspector = SQLiteInspector(self.db_path)
        try:
            tables = inspector.inspect()
        finally:
            inspector.close()

        tables_map = {t.name: t for t in tables}
        items = tables_map["order_items"]
        fks = items.foreign_keys

        fk_order = [
            f for f in fks
            if f.from_column == "order_id" and f.target_table == "orders" and f.target_column == "id"
        ]
        self.assertEqual(len(fk_order), 1, "Expected FK order_items.order_id -> orders.id")

        fk_item = [
            f for f in fks
            if f.from_column == "item_id" and f.target_table == "users" and f.target_column == "id"
        ]
        self.assertEqual(len(fk_item), 1, "Expected FK order_items.item_id -> users.id")


if __name__ == "__main__":
    unittest.main()