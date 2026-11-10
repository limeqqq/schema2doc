"""Markdown documentation generation."""

from datetime import datetime
from typing import List

from ..models import Table, Column, ForeignKey, Index
from .mermaid import MermaidGenerator


class MarkdownDocGenerator:
    """Generates a Markdown document with ERD and schema details."""

    def __init__(self) -> None:
        self.mermaid_generator = MermaidGenerator()

    def generate(self, tables: List[Table], db_name: str = "Database") -> str:
        """Generate a Markdown document from the given tables.

        Args:
            tables: List of tables to document.
            db_name: Name of the database (used in the H1 header).

        Returns:
            A Markdown string containing the full documentation.
        """
        # Count tables and columns
        table_count = len(tables)
        total_columns = sum(len(t.columns) for t in tables)
        generation_date = datetime.now().strftime("%Y-%m-%d")

        # Start the document
        lines = []
        lines.append(f"# {db_name}")
        lines.append(f"**Tables:** {table_count}")
        lines.append(f"**Columns:** {total_columns}")
        lines.append(f"**Generated:** {generation_date}")
        lines.append("")

        # Entity Relationship Diagram
        lines.append("## Entity Relationship Diagram")
        mermaid_block = self.mermaid_generator.generate(tables)
        lines.append(mermaid_block)
        lines.append("")

        # Schema Details
        lines.append("## Schema Details")
        for table in sorted(tables, key=lambda t: t.name):
            lines.append(f"### {table.name}")
            row_count = table.row_count
            if row_count is not None:
                lines.append(f"**Rows:** {row_count}")
            else:
                lines.append(f"**Rows:** N/A")
            lines.append("")

            # Columns table
            col_headers = ["Column", "Type", "Nullable", "Default", "Constraints"]
            lines.append("| " + " | ".join(col_headers) + " |")
            lines.append("| " + " | ".join(["---"] * len(col_headers)) + " |")
            for col in table.columns:
                col_name = col.name
                col_type = self.mermaid_generator.normalize_type(col.data_type)
                nullable = "YES" if col.is_nullable else "NO"
                default = str(col.default_value) if col.default_value is not None else ""
                constraints = []
                if col.is_pk:
                    constraints.append("PRIMARY KEY")
                if self.mermaid_generator._is_fk_column(table, col.name):
                    constraints.append("FOREIGN KEY")
                constraint_str = ", ".join(constraints) if constraints else ""
                lines.append(f"| {col_name} | {col_type} | {nullable} | {default} | {constraint_str} |")
            lines.append("")

            # Indices
            if table.indices:
                lines.append("#### Indices")
                for idx in table.indices:
                    unique = " UNIQUE" if idx.is_unique else ""
                    col_names = ", ".join(idx.columns)
                    lines.append(f"- {idx.name} ({unique.strip()}) -- columns: {col_names}")
                lines.append("")

            # Foreign Keys
            if table.foreign_keys:
                lines.append("#### Foreign Keys")
                for fk in table.foreign_keys:
                    on_delete = fk.on_delete or "NO ACTION"
                    on_update = fk.on_update or "NO ACTION"
                    lines.append(
                        f"- {fk.from_column} -> {fk.target_table}({fk.target_column}) [ON DELETE {on_delete} ON UPDATE {on_update}]"
                    )
                lines.append("")

        return "\n".join(lines)