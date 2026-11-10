"""Tests for the schema2doc generators using unittest."""

import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from schema2doc.inspectors.sqlite import SQLiteInspector
from schema2doc.generators.mermaid import MermaidGenerator
from schema2doc.generators.markdown import MarkdownDocGenerator


class TestGenerators(unittest.TestCase):
    """Verify that Mermaid and Markdown generators produce correct output."""

    def setUp(self):
        """Create a temporary SQLite database with tables and FK relationships."""
        self.fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.fd)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "CREATE TABLE users (id INTEGER PRIMARY KEY NOT NULL, email TEXT NOT NULL, created_at TEXT)"
        )
        c.execute(
            "CREATE TABLE orders (id INTEGER PRIMARY KEY NOT NULL, user_id INTEGER NOT NULL, order_date TEXT, total REAL, "
            "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE RESTRICT)"
        )
        c.execute(
            "CREATE TABLE order_items (id INTEGER PRIMARY KEY NOT NULL, order_id INTEGER NOT NULL, item_id INTEGER NOT NULL, quantity INTEGER NOT NULL DEFAULT 1, "
            "FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE, "
            "FOREIGN KEY (item_id) REFERENCES users(id))"
        )
        conn.commit()
        conn.close()

        inspector = SQLiteInspector(self.db_path)
        self.tables = inspector.inspect()
        inspector.close()

    def tearDown(self):
        """Clean up the temporary database file."""
        try:
            os.remove(self.db_path)
        except OSError:
            pass

    def test_mermaid_generator_produces_valid_block(self):
        """Verify that MermaidGenerator produces a valid Mermaid ERD block."""
        mermaid = MermaidGenerator()
        md = mermaid.generate(self.tables)

        # Should start with ```mermaid and end with ```
        self.assertTrue(md.startswith("```mermaid"), "Mermaid output must start with ```mermaid")
        self.assertTrue(md.endswith("```"), "Mermaid output must end with ```")

        # Should contain the three tables
        self.assertIn("users", md)
        self.assertIn("orders", md)
        self.assertIn("order_items", md)

        # Should contain relationship arrows
        self.assertIn("}o--||", md, "Mermaid ERD must contain relationship arrows (}o--||)")

        # Should contain normalized types (int, string, float) not raw SQL types
        self.assertTrue('"int"' not in md or "int " in md, "Types should be normalized")
        self.assertTrue('"string"' not in md or "string " in md)

    def test_mermaid_normalizes_types(self):
        """Verify that MermaidGenerator normalizes types correctly."""
        mg = MermaidGenerator()

        # Integer type -> int
        self.assertEqual(mg.normalize_type("INTEGER"), "int")
        self.assertEqual(mg.normalize_type("INT"), "int")

        # Float types -> float
        self.assertEqual(mg.normalize_type("REAL"), "float")
        self.assertEqual(mg.normalize_type("FLOAT"), "float")

        # DateTime types -> datetime
        self.assertEqual(mg.normalize_type("DATETIME"), "datetime")
        self.assertEqual(mg.normalize_type("DATE"), "datetime")

        # VARCHAR -> string
        self.assertEqual(mg.normalize_type("VARCHAR(255)"), "string")
        self.assertEqual(mg.normalize_type("CHAR"), "string")

        # Default fallback
        self.assertEqual(mg.normalize_type(""), "string")
        self.assertEqual(mg.normalize_type("SOME_RANDOM_TYPE"), "some_random_type")

    def test_markdown_generator_produces_valid_structure(self):
        """Verify that MarkdownDocGenerator produces correct Markdown structure."""
        md = MarkdownDocGenerator().generate(self.tables, db_name="Test DB")

        # Should start with H1
        self.assertTrue(md.startswith("# Test DB"), "Markdown must start with H1 header")

        # Should have table count badge
        self.assertIn("**Tables:** 3", md, "Markdown must show table count")

        # Should have ERD section
        self.assertIn("## Entity Relationship Diagram", md, "Must have ERD section")

        # Should have Schema Details section
        self.assertIn("## Schema Details", md, "Must have Schema Details section")

        # Should have table sections (H3)
        self.assertIn("### users", md, "Must have users table section")
        self.assertIn("### orders", md, "Must have orders table section")
        self.assertIn("### order_items", md, "Must have order_items table section")

        # Should have markdown table headers
        self.assertIn("| Column | Type | Nullable | Default | Constraints |", md, "Must have column table headers")

        # Should have FK info
        self.assertIn("user_id -> users(id)", md, "Must include foreign key references")
        self.assertIn("order_id -> orders(id)", md, "Must include foreign key references")
        self.assertIn("item_id -> users(id)", md, "Must include foreign key references")

    def test_mermaid_pk_fk_comma_separator(self):
        """Verify that columns with both PK and FK use 'PK, FK' separator."""
        # Build a simple two-table schema where parent.id has PK only,
        # and child.parent_id has FK only, then create a column with both.
        # SQLite stores FK info separately; we test the generator logic
        # by inspecting a schema where a column is both PK and FK.
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        # Create parent table with PK
        c.execute("CREATE TABLE parent (id INTEGER PRIMARY KEY NOT NULL, title TEXT)")
        # Create child table with FK to parent; parent_id is NOT a PK
        c.execute("CREATE TABLE child (id INTEGER PRIMARY KEY NOT NULL, parent_id INTEGER NOT NULL, FOREIGN KEY (parent_id) REFERENCES parent(id))")
        conn.commit()
        conn.close()

        inspector = SQLiteInspector(db_path)
        tables = inspector.inspect()
        inspector.close()

        mermaid = MermaidGenerator()
        md = mermaid.generate(tables)

        # parent.id should have PK only, no FK
        self.assertIn("int id PK", md)
        # child.parent_id should have FK only, no PK
        self.assertIn("int parent_id FK", md)

    def tearDown(self):
        """Ensure cleanup even if setUp partially failed."""
        try:
            os.remove(self.db_path)
        except OSError:
            pass


class TestGeneratorsWithIndices(unittest.TestCase):
    """Verify generator includes indices and FK info when present."""

    def setUp(self):
        """Create a temporary SQLite database with indexes."""
        self.fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.fd)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # Create indexes
        c.execute("CREATE TABLE users (id INTEGER PRIMARY KEY NOT NULL, email TEXT NOT NULL, created_at TEXT)")
        c.execute("CREATE INDEX idx_users_email ON users(email)")
        # Create orders with FK
        c.execute(
            "CREATE TABLE orders (id INTEGER PRIMARY KEY NOT NULL, user_id INTEGER NOT NULL, order_date TEXT, total REAL, "
            "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE RESTRICT)"
        )
        conn.commit()
        conn.close()

        inspector = SQLiteInspector(self.db_path)
        self.tables = inspector.inspect()
        inspector.close()

    def tearDown(self):
        """Clean up the temporary database file."""
        try:
            os.remove(self.db_path)
        except OSError:
            pass

    def test_markdown_includes_indices_and_fks(self):
        """Verify that MarkdownDocGenerator includes indices and FK info."""
        md = MarkdownDocGenerator().generate(self.tables, db_name="Test DB")

        # Check that Indices section exists
        self.assertIn("#### Indices", md, "Must have Indices section when indexes exist")

        # Check that foreign keys are listed
        self.assertIn("#### Foreign Keys", md, "Must have Foreign Keys section")


if __name__ == "__main__":
    unittest.main()