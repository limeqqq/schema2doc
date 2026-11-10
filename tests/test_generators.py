"""Tests for the schema2doc generators."""

import sqlite3
import tempfile
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from schema2doc.inspectors.sqlite import SQLiteInspector
from schema2doc.generators.mermaid import MermaidGenerator
from schema2doc.generators.markdown import MarkdownDocGenerator


def test_mermaid_generator_produces_valid_block():
    """Verify that MermaidGenerator produces a valid Mermaid ERD block."""
    # Build a temporary in-memory SQLite database with FK relationships
    fd, db_path = tempfile.mkstemp(suffix=".db")
    import os
    os.close(fd)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY NOT NULL, email TEXT NOT NULL, created_at TEXT)"
    )
    c.execute(
        "CREATE TABLE orders (id INTEGER PRIMARY KEY NOT NULL, user_id INTEGER NOT NULL, order_date TEXT, total REAL, FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE RESTRICT)"
    )
    c.execute(
        "CREATE TABLE order_items (id INTEGER PRIMARY KEY NOT NULL, order_id INTEGER NOT NULL, item_id INTEGER NOT NULL, quantity INTEGER NOT NULL DEFAULT 1, FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE, FOREIGN KEY (item_id) REFERENCES users(id))"
    )
    conn.commit()
    conn.close()

    inspector = SQLiteInspector(db_path)
    tables = inspector.inspect()
    inspector.close()

    mermaid = MermaidGenerator()
    md = mermaid.generate(tables)

    # Should start with ```mermaid and end with ```
    assert md.startswith("```mermaid"), "Mermaid output must start with ```mermaid"
    assert md.endswith("```"), "Mermaid output must end with ```"

    # Should contain the three tables
    assert "users" in md
    assert "orders" in md
    assert "order_items" in md

    # Should contain relationship arrows
    assert "}o--||" in md, "Mermaid ERD must contain relationship arrows (}o--||)"

    # Should contain normalized types (int, string, float) not raw SQL types
    assert '"int"' not in md or "int " in md, "Types should be normalized"
    assert '"string"' not in md or "string " in md

    print("PASS: test_mermaid_generator_produces_valid_block")


def test_mermaid_normalizes_types():
    """Verify that MermaidGenerator normalizes types correctly."""
    from schema2doc.models import Column

    mg = MermaidGenerator()

    # Integer type -> int
    assert mg.normalize_type("INTEGER") == "int"
    assert mg.normalize_type("INT") == "int"

    # Float types -> float
    assert mg.normalize_type("REAL") == "float"
    assert mg.normalize_type("FLOAT") == "float"

    # DateTime types -> datetime
    assert mg.normalize_type("DATETIME") == "datetime"
    assert mg.normalize_type("DATE") == "datetime"

    # VARCHAR -> string
    assert mg.normalize_type("VARCHAR(255)") == "string"
    assert mg.normalize_type("CHAR") == "string"

    # Default fallback
    assert mg.normalize_type("") == "string"
    assert mg.normalize_type("SOME_RANDOM_TYPE") == "some_random_type"

    print("PASS: test_mermaid_normalizes_types")


def test_markdown_generator_produces_valid_structure():
    """Verify that MarkdownDocGenerator produces correct Markdown structure."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    import os
    os.close(fd)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY NOT NULL, email TEXT NOT NULL, created_at TEXT)"
    )
    c.execute(
        "CREATE TABLE orders (id INTEGER PRIMARY KEY NOT NULL, user_id INTEGER NOT NULL, order_date TEXT, total REAL, FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE RESTRICT)"
    )
    conn.commit()
    conn.close()

    inspector = SQLiteInspector(db_path)
    tables = inspector.inspect()
    inspector.close()

    md = MarkdownDocGenerator().generate(tables, db_name="Test DB")

    # Should start with H1
    assert md.startswith("# Test DB"), "Markdown must start with H1 header"

    # Should have table count badge
    assert "**Tables:** 2" in md, "Markdown must show table count"

    # Should have ERD section
    assert "## Entity Relationship Diagram" in md, "Must have ERD section"

    # Should have Schema Details section
    assert "## Schema Details" in md, "Must have Schema Details section"

    # Should have table sections (H3)
    assert "### users" in md, "Must have users table section"
    assert "### orders" in md, "Must have orders table section"

    # Should have markdown table headers
    assert "| Column | Type | Nullable | Default | Constraints |" in md, "Must have column table headers"

    # Should have FK info
    assert "user_id -> users(id)" in md, "Must include foreign key references"

    print("PASS: test_markdown_generator_produces_valid_structure")


def test_markdown_includes_indices_and_fks():
    """Verify that MarkdownDocGenerator includes indices and FK info."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    import os
    os.close(fd)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Create indexes
    c.execute("CREATE TABLE users (id INTEGER PRIMARY KEY NOT NULL, email TEXT NOT NULL, created_at TEXT)")
    c.execute("CREATE INDEX idx_users_email ON users(email)")
    # Create orders with FK
    c.execute(
        "CREATE TABLE orders (id INTEGER PRIMARY KEY NOT NULL, user_id INTEGER NOT NULL, order_date TEXT, total REAL, FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE RESTRICT)"
    )
    conn.commit()
    conn.close()

    inspector = SQLiteInspector(db_path)
    tables = inspector.inspect()
    inspector.close()

    md = MarkdownDocGenerator().generate(tables, db_name="Test DB")

    # Check that Indices section exists
    assert "#### Indices" in md, "Must have Indices section when indexes exist"

    # Check that foreign keys are listed
    assert "#### Foreign Keys" in md, "Must have Foreign Keys section"

    print("PASS: test_markdown_includes_indices_and_fks")


if __name__ == "__main__":
    test_mermaid_generator_produces_valid_block()
    test_mermaid_normalizes_types()
    test_markdown_generator_produces_valid_structure()
    test_markdown_includes_indices_and_fks()
    print("\nAll generator tests passed!")