"""Abstract base class for database schema inspectors."""

from abc import ABC, abstractmethod
from typing import List

from ..models import Table, Column, ForeignKey, Index


class BaseInspector(ABC):
    """Abstract inspector that defines the interface for extracting schema information."""

    @abstractmethod
    def inspect(self) -> List[Table]:
        """
        Extract the schema of the database and return a list of Table objects.

        Returns:
            A list of Table dataclasses describing the tables in the database.
        """
        ...
