"""Test script for generators."""
import sys
import sqlite3
import tempfile
from pathlib import Path
from schema2doc.inspectors.sqlite import SQLiteInspector
from schema2doc.generators.mermaid import MermaidGenerator
from schema2doc.generators.markdown import MarkdownDocGenerator

def test_generators():
    # Create a temporary SQLite DB with 3 tables
    fd, db_path = tempfile.mkstemp(suffix='.db')
    import os
    os.close(fd)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('CREATE TABLE users (id INTEGER PRIMARY KEY NOT NULL, email TEXT NOT NULL, created_at TEXT)')
    c.execute('CREATE TABLE orders (id INTEGER PRIMARY KEY NOT NULL, user_id INTEGER NOT NULL, order_date TEXT, total REAL, FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE RESTRICT)')
    c.execute('CREATE TABLE order_items (id INTEGER PRIMARY KEY NOT NULL, order_id INTEGER NOT NULL, item_id INTEGER NOT NULL, quantity INTEGER NOT NULL DEFAULT 1, FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE, FOREIGN KEY (item_id) REFERENCES users(id))')
    conn.commit()
    conn.close()

    # Inspect schema
    inspector = SQLiteInspector(db_path)
    tables = inspector.inspect()
    inspector.close()

    # Test MermaidGenerator
    mermaid = MermaidGenerator()
    md = mermaid.generate(tables)
    print('=== MermaIde Block ===')
    print(md)
    print('======================')

    # Test MarkdownDocGenerator
    doc = MarkdownDocGenerator()
    markdown = doc.generate(tables, db_name='Test DB')
    print('=== Markdown Output ===')
    print(markdown)
    print('======================')

if __name__ == '__main__':
    test_generators()