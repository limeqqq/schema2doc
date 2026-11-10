"""Command-line interface for schema2doc."""

import argparse
import sqlite3
import sys
from pathlib import Path

from .inspectors.sqlite import SQLiteInspector
from .generators.markdown import MarkdownDocGenerator


def main(argv: list[str] | None = None) -> int:
    """Run the schema2doc CLI.

    Args:
        argv: Optional list of CLI arguments (for testing). Defaults to sys.argv[1:].

    Returns:
        Exit code 0 on success, non-zero on failure.
    """
    parser = argparse.ArgumentParser(
        prog="schema2doc",
        description="Generate Markdown documentation from a SQLite database schema.",
    )
    parser.add_argument(
        "source",
        help="Path to the SQLite database file (.db / .sqlite).",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="SCHEMA.md",
        help="Path to the output Markdown file (default: SCHEMA.md).",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Database title for the report (default: derived from source file name).",
    )

    args = parser.parse_args(argv)

    source_path = Path(args.source)
    if not source_path.exists():
        print(f"Error: source database file not found: {source_path}", file=sys.stderr)
        return 1

    if args.title is None:
        args.title = source_path.stem

    inspector = SQLiteInspector(str(source_path))
    try:
        tables = inspector.inspect()
    except sqlite3.DatabaseError:
        print(f"Error: '{source_path}' is not a valid SQLite database.", file=sys.stderr)
        return 1
    finally:
        inspector.close()

    table_count = len(tables)
    fk_count = sum(len(t.foreign_keys) for t in tables)
    content = MarkdownDocGenerator().generate(tables, db_name=args.title)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")

    print(f"Tables found: {table_count}")
    print(f"Foreign keys found: {fk_count}")
    print(f"Markdown file written to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
