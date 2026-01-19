"""Parser for MemGraph native trace format."""

from pathlib import Path
from typing import Iterator
from memgraph.trace.models import MemoryAccess, Trace
from memgraph.trace.formats.base import BaseParser


class NativeParser(BaseParser):
    """Parser for MemGraph native trace format.

    Format:
        # MemGraph Trace v1
        R,0x7fff5a8b1000,8,1
        W,0x7fff5a8b1008,4,2

    Fields: operation,address,size,timestamp
    """

    HEADER = "# MemGraph Trace v1"

    @classmethod
    def format_name(cls) -> str:
        """Return the name of this format."""
        return "native"

    @classmethod
    def can_parse(cls, file_path: Path) -> bool:
        """Check if this file is in native format.

        Args:
            file_path: Path to the trace file

        Returns:
            True if this appears to be a native format file
        """
        if not file_path.exists():
            return False

        try:
            with open(file_path, "r") as f:
                first_line = f.readline().strip()
                return first_line == cls.HEADER
        except (IOError, UnicodeDecodeError):
            return False

    def parse_iter(self, file_path: Path) -> Iterator[MemoryAccess]:
        """Parse a native trace file lazily.

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

        with open(file_path, "r") as f:
            first_line = f.readline().strip()
            if first_line != self.HEADER:
                raise ValueError(
                    f"Invalid native format: expected '{self.HEADER}', "
                    f"got '{first_line}'"
                )

            for line_num, line in enumerate(f, 2):  # 2 because header is line 1
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                try:
                    parts = line.split(",")
                    if len(parts) != 4:
                        raise ValueError(
                            f"Expected 4 fields, got {len(parts)}"
                        )

                    op, addr_str, size_str, ts_str = parts

                    # Validate operation
                    op = op.strip().upper()
                    if op not in ("R", "W"):
                        raise ValueError(f"Invalid operation: {op}")

                    # Parse address (handle hex with or without 0x prefix)
                    addr_str = addr_str.strip()
                    if addr_str.startswith("0x") or addr_str.startswith("0X"):
                        address = int(addr_str, 16)
                    else:
                        # Try as hex first, fall back to decimal
                        try:
                            address = int(addr_str, 16)
                        except ValueError:
                            address = int(addr_str, 10)

                    size = int(size_str.strip())
                    timestamp = int(ts_str.strip())

                    yield MemoryAccess(op, address, size, timestamp)  # type: ignore

                except (ValueError, IndexError) as e:
                    raise ValueError(
                        f"Error parsing line {line_num}: {line} - {e}"
                    )

    def parse(self, file_path: Path) -> Trace:
        """Parse a native trace file.

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

    def write(self, trace: Trace, file_path: Path) -> None:
        """Write a trace to a file in native format.

        Args:
            trace: Trace object to write
            file_path: Path to write to
        """
        with open(file_path, "w") as f:
            f.write(self.HEADER + "\n")
            for access in trace.accesses:
                f.write(
                    f"{access.operation},{hex(access.address)},"
                    f"{access.size},{access.timestamp}\n"
                )
