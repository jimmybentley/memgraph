"""Base parser interface for trace formats."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator
from memgraph.trace.models import MemoryAccess, Trace


class BaseParser(ABC):
    """Abstract base class for trace format parsers."""

    @abstractmethod
    def parse(self, file_path: Path) -> Trace:
        """Parse a trace file and return a Trace object.

        Args:
            file_path: Path to the trace file

        Returns:
            Parsed Trace object

        Raises:
            ValueError: If the file format is invalid
            FileNotFoundError: If the file doesn't exist
        """
        pass

    @abstractmethod
    def parse_iter(self, file_path: Path) -> Iterator[MemoryAccess]:
        """Parse a trace file lazily, yielding memory accesses one at a time.

        Args:
            file_path: Path to the trace file

        Yields:
            MemoryAccess objects

        Raises:
            ValueError: If the file format is invalid
            FileNotFoundError: If the file doesn't exist
        """
        pass

    @classmethod
    @abstractmethod
    def can_parse(cls, file_path: Path) -> bool:
        """Check if this parser can handle the given file.

        Args:
            file_path: Path to the trace file

        Returns:
            True if this parser can handle the file format
        """
        pass

    @classmethod
    @abstractmethod
    def format_name(cls) -> str:
        """Return the name of this format."""
        pass
