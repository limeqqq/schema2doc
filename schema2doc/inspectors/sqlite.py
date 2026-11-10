"""SQLite-specific inspector using the standard library ``sqlite3`` and PRAGMA queries."""

import sqlite3
from typing import List

from ..models import Table, Column, ForeignKey, Index


class SQLiteInspector:
    """Concrete inspector for SQLite databases.

    Uses the standard-library ``sqlite3`` module together with the following
    PRAGMAs::

        * ``sqlite_master``       – lists all objects (tables, views, etc.)
        * ``table_info(?)``      – ``PRAGMA table_info(name)``
        * ``foreign_key_list(?)``– ``PRAGMA foreign_key_list(name)``
        * ``index_list(?)``       – ``PRAGMA index_list(name)``
        * ``index_info(?)``      – ``PRAGMA index_info(index_name)``

    Parameters
    ----------
    db_path:
        Path to the SQLite file (e.g. ``:memory:`` or an absolute path).

    Attributes
    ----------
    _conn:
        Open connection kept alive during inspection.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def inspect(self) -> List[Table]:
        """
        Extract the complete schema of every table defined in the database.

        Returns
        -------
        List[Table]
            One ``Table`` object per table found in the database.
        """
        cursor = self._conn.cursor()
        # ``sqlite_master`` contains rows for tables, views, etc.; filter out
        # the internal sqlite_ tables and keep only real tables.
        cursor.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name"
        )
        rows = cursor.fetchall()
        tables: List[Table] = []
        for row in rows:
            name = row["name"]
            tables.append(self._build_table(name))
        return tables

    def close(self) -> None:
        """Close the underlying database connection."""
        self._conn.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_table(self, name: str) -> Table:
        columns = self._query_table_info(name)
        foreign_keys = self._query_foreign_keys(name)
        indices = self._query_index_list(name)

        table = Table(
            name=name,
            columns=columns,
            foreign_keys=foreign_keys,
            indices=indices,
        )

        # Optional row count (``SELECT COUNT(*)``)
        try:
            cur = self._conn.cursor()
            cur.execute(f"SELECT COUNT(*) FROM '{name}'")
            table.row_count = cur.fetchone()[0]
        except Exception:  # pragma: no cover - defensive
            table.row_count = None
        return table

    def _query_table_info(self, name: str) -> List[Column]:
        """Return column metadata via ``PRAGMA table_info(name)``."""
        cursor = self._conn.cursor()
        cursor.execute(f"PRAGMA table_info('{name}')")
        columns: List[Column] = []
        for row in cursor.fetchall():
            # A column is nullable only if it has no NOT NULL constraint AND is not a primary key
            is_nullable = not row["notnull"] and not row["pk"]
            columns.append(Column(
                name=row["name"],
                data_type=row["type"] or "TEXT",
                is_nullable=is_nullable,
                default_value=row["dflt_value"],
                is_pk=bool(row["pk"]),
            ))
        return columns

    def _query_foreign_keys(self, name: str) -> List[ForeignKey]:
        """Return foreign-key relationships via ``PRAGMA foreign_key_list(name)``."""
        cursor = self._conn.cursor()
        cursor.execute(f"PRAGMA foreign_key_list('{name}')")
        rows = cursor.fetchall()
        fk_list: List[ForeignKey] = []
        for row in rows:
            # PRAGMA foreign_key_list returns rows with these columns:
            #   id, seq, table, from, to, on_update, on_delete, match
            # We map them onto the ``ForeignKey`` model:
            #   from_column -> from, target_table -> table,
            #   target_column -> to, on_delete -> on_delete,
            #   on_update -> on_update
            fk_list.append(ForeignKey(
                from_column=row["from"],
                target_table=row["table"],
                target_column=row["to"],
                on_delete=row["on_delete"] or "NO ACTION",
                on_update=row["on_update"] or "NO ACTION",
            ))
        return fk_list

    def _query_index_list(self, name: str) -> List[Index]:
        """Return indexes for ``name`` via ``PRAGMA index_list(name)``."""
        cursor = self._conn.cursor()
        cursor.execute(f"PRAGMA index_list('{name}')")
        rows = cursor.fetchall()
        indices: List[Index] = []
        for row in rows:
            index_name = row["name"]
            index_info = self._query_index_info(index_name)
            columns_in_index = [
                info["name"] for info in index_info if info["name"]
            ]
            indices.append(Index(
                name=index_name,
                columns=columns_in_index,
                is_unique=bool(row["unique"]),
            ))
        return indices

    def _query_index_info(self, index_name: str):
        """Return column definitions for a specific index via ``PRAGMA index_info(index_name)``."""
        cursor = self._conn.cursor()
        cursor.execute(f"PRAGMA index_info('{index_name}')")
        return cursor.fetchall()
