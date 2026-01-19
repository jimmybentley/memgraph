"""Parser for simple CSV trace format."""

import csv
from pathlib import Path
from typing import Iterator
from memgraph.trace.models import MemoryAccess, Trace
from memgraph.trace.formats.base import BaseParser


class CSVParser(BaseParser):
    """Parser for simple CSV trace format.

    Format:
        op,address,size
        R,0x7fff5a8b1000,8
        W,0x7fff5a8b1008,4
    """

    @classmethod
    def format_name(cls) -> str:
        """Return the name of this format."""
        return "csv"

    @classmethod
    def can_parse(cls, file_path: Path) -> bool:
        """Check if this file is in CSV format.

        Args:
            file_path: Path to the trace file

        Returns:
            True if this appears to be a CSV format file
        """
        if not file_path.exists():
            return False

        try:
            with open(file_path, "r") as f:
                # Try to parse as CSV
                reader = csv.DictReader(f)
                first_row = next(reader, None)
                if first_row is None:
                    return False

                # Check for expected headers
                required_headers = {"op", "address", "size"}
                return required_headers.issubset(set(first_row.keys()))

        except (IOError, UnicodeDecodeError, csv.Error):
            return False

    def parse_iter(self, file_path: Path) -> Iterator[MemoryAccess]:
        """Parse a CSV trace file lazily.

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
            reader = csv.DictReader(f)

            # Validate headers
            if not reader.fieldnames:
                raise ValueError("CSV file is empty")

            required_headers = {"op", "address", "size"}
            if not required_headers.issubset(set(reader.fieldnames)):
                raise ValueError(
                    f"CSV file missing required headers. "
                    f"Expected: {required_headers}, Got: {reader.fieldnames}"
                )

            for row_num, row in enumerate(reader, 2):  # 2 because of header
                try:
                    op = row["op"].strip().upper()
                    if op not in ("R", "W"):
                        raise ValueError(f"Invalid operation: {op}")

                    # Parse address (handle hex with or without 0x prefix)
                    addr_str = row["address"].strip()
                    if addr_str.startswith("0x") or addr_str.startswith("0X"):
                        address = int(addr_str, 16)
                    else:
                        # Try as hex, fall back to decimal
                        try:
                            address = int(addr_str, 16)
                        except ValueError:
                            address = int(addr_str, 10)

                    size = int(row["size"])

                    yield MemoryAccess(op, address, size, timestamp)  # type: ignore
                    timestamp += 1

                except (ValueError, KeyError) as e:
                    raise ValueError(f"Error parsing CSV row {row_num}: {row} - {e}")

    def parse(self, file_path: Path) -> Trace:
        """Parse a CSV trace file.

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
