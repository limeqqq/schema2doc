"""Tests for the schema2doc CLI."""

import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure running from the project root so the package is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestCLI(unittest.TestCase):
    """Verify CLI generates markdown from a temporary SQLite database."""

    def test_cli_generates_valid_markdown(self):
        """Run CLI via subprocess and check output file existence and content."""
        # Build a temporary SQLite database with tables and FK relationships.
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(
                "CREATE TABLE users (id INTEGER PRIMARY KEY NOT NULL, email TEXT NOT NULL, created_at TEXT)"
            )
            cursor.execute(
                "CREATE TABLE orders (id INTEGER PRIMARY KEY NOT NULL, user_id INTEGER NOT NULL, order_date TEXT, total REAL, "
                "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE RESTRICT)"
            )
            conn.commit()
            conn.close()

            # Output file path (temp file)
            output_path = Path(tempfile.mktemp(suffix=".md"))

            # Run CLI via python -m schema2db ... (note: package is schema2doc)
            result = subprocess.run(
                [sys.executable, "-m", "schema2doc", db_path, "-o", str(output_path)],
                capture_output=True,
                text=True,
                cwd=str(PROJECT_ROOT),
            )

            # Check exit code
            self.assertEqual(
                result.returncode,
                0,
                f"CLI exited with code {result.returncode}. stderr: {result.stderr}",
            )

            # Check output file was created
            self.assertTrue(
                output_path.exists(),
                f"Output file was not created at {output_path}",
            )

            # Check content starts with H1 header
            content = output_path.read_text(encoding="utf-8")
            self.assertIn("#", content)
            self.assertIn("Entity Relationship Diagram", content)
            self.assertIn("Schema Details", content)

            # Cleanup
            try:
                output_path.unlink()
            except OSError:
                pass
        finally:
            # Clean up the temp db
            try:
                os.remove(db_path)
            except OSError:
                pass

    def test_cli_missing_source_exits_with_error(self):
        """Verify that missing source file causes a non-zero exit code."""
        result = subprocess.run(
            [sys.executable, "-m", "schema2doc", "nonexistent_file.db"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        self.assertNotEqual(result.returncode, 0)
        # stderr should contain an error message about missing file
        self.assertIn("Error", result.stderr)

    def test_cli_title_from_source_stem(self):
        """Verify that --title defaults to the source file stem."""
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY NOT NULL, name TEXT)")
            conn.commit()
            conn.close()

            output_path = Path(tempfile.mktemp(suffix=".md"))
            # Run without --title; it should default to the db stem ("test_file")
            result = subprocess.run(
                [sys.executable, "-m", "schema2doc", db_path, "-o", str(output_path)],
                capture_output=True,
                text=True,
                cwd=str(PROJECT_ROOT),
            )
            self.assertEqual(result.returncode, 0)

            content = output_path.read_text(encoding="utf-8")
            # The H1 header should use the db stem as title
            expected_title = Path(db_path).stem
            self.assertIn(f"# {expected_title}", content)

            try:
                output_path.unlink()
            except OSError:
                pass
        finally:
            try:
                os.remove(db_path)
            except OSError:
                pass

    def test_cli_non_sqlite_file(self):
        """Verify that passing a non-SQLite .db file results in a clean exit 1."""
        # Write some garbage to a .db path so it opens as a file but not a valid DB.
        garbage_path = Path(tempfile.mktemp(suffix=".db"))
        garbage_path.write_text("this is not a database")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "schema2doc", str(garbage_path)],
                capture_output=True,
                text=True,
                cwd=str(PROJECT_ROOT),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Error", result.stderr)
        finally:
            try:
                garbage_path.unlink()
            except OSError:
                pass


if __name__ == "__main__":
    unittest.main()