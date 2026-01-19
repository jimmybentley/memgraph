"""Parser for Valgrind Lackey trace format."""

from pathlib import Path
from typing import Iterator
from memgraph.trace.models import MemoryAccess, Trace
from memgraph.trace.formats.base import BaseParser


class LackeyParser(BaseParser):
    """Parser for Valgrind Lackey trace format.

    Format:
        I  04000000,3     - Instruction fetch (ignored)
         S 7ff000398,8   - Store (write)
         L 7ff000398,8   - Load (read)
         M 7ff000390,8   - Modify (read + write)
    """

    @classmethod
    def format_name(cls) -> str:
        """Return the name of this format."""
        return "lackey"

    @classmethod
    def can_parse(cls, file_path: Path) -> bool:
        """Check if this file is in Lackey format.

        Args:
            file_path: Path to the trace file

        Returns:
            True if this appears to be a Lackey format file
        """
        if not file_path.exists():
            return False

        try:
            with open(file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    # Check for typical Lackey format patterns
                    if line[0] in ("I", " ") and "," in line:
                        parts = line.strip().split()
                        if len(parts) == 2:
                            op = parts[0]
                            if op in ("S", "L", "M", "I"):
                                return True
                    # Only check first few non-empty lines
                    break
        except (IOError, UnicodeDecodeError):
            return False

        return False

    def parse_iter(self, file_path: Path) -> Iterator[MemoryAccess]:
        """Parse a Lackey trace file lazily.

        Args:
            file_path: Path to the trace file

        Yields:
            MemoryAccess objects

        Raises:
            ValueError: If the file format is invalid
            FileNotFoundError: If the file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Trace file not found: {file_path}")

        timestamp = 0

        with open(file_path, "r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # Skip empty lines
                if not line:
                    continue

                # Skip instruction fetches (I)
                if line.startswith("I"):
                    continue

                # Parse the line
                try:
                    parts = line.strip().split()
                    if len(parts) != 2:
                        continue

                    op = parts[0]
                    addr_size = parts[1]

                    # Parse address and size
                    if "," not in addr_size:
                        raise ValueError(f"Invalid format at line {line_num}: {line}")

                    addr_str, size_str = addr_size.split(",", 1)

                    # Convert address (hex) and size (decimal)
                    address = int(addr_str, 16)
                    size = int(size_str)

                    # Handle different operation types
                    if op == "L":
                        # Load (read)
                        yield MemoryAccess("R", address, size, timestamp)
                        timestamp += 1
                    elif op == "S":
                        # Store (write)
                        yield MemoryAccess("W", address, size, timestamp)
                        timestamp += 1
                    elif op == "M":
                        # Modify (read then write)
                        yield MemoryAccess("R", address, size, timestamp)
                        timestamp += 1
                        yield MemoryAccess("W", address, size, timestamp)
                        timestamp += 1

                except ValueError as e:
                    raise ValueError(f"Error parsing line {line_num}: {line} - {e}")

    def parse(self, file_path: Path) -> Trace:
        """Parse a Lackey trace file.

        Args:
            file_path: Path to the trace file

        Returns:
            Parsed Trace object

        Raises:
            ValueError: If the file format is invalid
            FileNotFoundError: If the file doesn't exist
        """
        accesses = list(self.parse_iter(file_path))
        return Trace.from_accesses(accesses, file_path, self.format_name())
