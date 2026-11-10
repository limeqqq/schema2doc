"""Mermaid ERD generation."""

from typing import List

from ..models import Table, Column, ForeignKey, Index


class MermaidGenerator:
    """Generates a Mermaid erDiagram block from a list of tables."""

    def generate(self, tables: List[Table]) -> str:
        """Generate a mermaid erDiagram code block from the given tables.

        Args:
            tables: List of tables to include in the diagram.

        Returns:
            A string starting with ```mermaid and ending with ``` containing the ERD.
        """
        lines: List[str] = ["```mermaid", "erDiagram"]

        # Emit table blocks with normalized columns, including PK/FK markers.
        for table in sorted(tables, key=lambda t: t.name):
            lines.append(f"    {table.name} {{")
            for col in table.columns:
                normalized_type = self.normalize_type(col.data_type)
                pk_marker = " PK" if col.is_pk else ""
                fk_marker = " FK" if self._is_fk_column(table, col.name) else ""
                lines.append(f"        {normalized_type} {col.name}{pk_marker}{fk_marker}".rstrip())
            lines.append("    }")

        # Emit relationships based on foreign keys.
        # Format: <FROM_TABLE> }o--|| <TO_TABLE> : "<from_column>"
        for table in sorted(tables, key=lambda t: t.name):
            for fk in table.foreign_keys:
                lines.append(
                    f'{table.name} }}o--|| {fk.target_table} : "{fk.from_column}"'
                )

        lines.append("```")
        return "\n".join(lines)

    @staticmethod
    def normalize_type(type_str: str) -> str:
        """Normalize a database type string into a compact, Mermaid-safe name.

        Examples:
            "INTEGER" -> "int"
            "VARCHAR(255)" -> "string"
            "DATETIME" -> "datetime"
            "REAL" -> "float"
        """
        t = (type_str or "").upper().strip()
        if not t:
            return "string"
        if t.startswith("VARCHAR") or t.startswith("CHAR") or t.startswith("TEXT"):
            return "string"
        if t in ("INTEGER", "INT", "BIGINT", "SMALLINT", "TINYINT"):
            return "int"
        if t in ("REAL", "DOUBLE", "FLOAT"):
            return "float"
        if t in ("DATE", "DATETIME", "TIMESTAMP"):
            return "datetime"
        if t in ("BLOB", "BINARY", "BYTEA"):
            return "binary"
        if t in ("NUMERIC", "DECIMAL"):
            return "number"
        # Fallback: lower-case without parentheses/spaces.
        return t.replace("(", "").replace(")", "").strip().lower()

    @staticmethod
    def _is_fk_column(table: Table, column_name: str) -> bool:
        """Check whether a column is used as a foreign key in the given table."""
        for fk in table.foreign_keys:
            if fk.from_column == column_name:
                return True
        return False
