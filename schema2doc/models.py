"""Data transfer objects (DTOs) for database schema inspection."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Column:
    """Represents a single column of a table."""

    name: str
    data_type: str  # e.g. "INTEGER", "TEXT", "REAL", "BLOB"
    is_nullable: bool = False
    default_value: any = None
    is_pk: bool = False


@dataclass
class ForeignKey:
    """A foreign-key relationship between two columns/tables."""

    from_column: str
    target_table: str
    target_column: str
    on_delete: str = "CASCADE"
    on_update: str = "NO_OP"


@dataclass
class Index:
    """An index definition on a table."""

    name: str
    columns: List[str]
    is_unique: bool = False


@dataclass
class Table:
    """Full description of a table (columns, foreign keys, indices, optional row count)."""

    name: str
    columns: List[Column] = field(default_factory=list)
    foreign_keys: List[ForeignKey] = field(default_factory=list)
    indices: List[Index] = field(default_factory=list)
    row_count: Optional[int] = None