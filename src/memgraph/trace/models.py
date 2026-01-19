"""Data models for memory traces."""

from dataclasses import dataclass
from typing import Literal, Iterator
from pathlib import Path


@dataclass
class MemoryAccess:
    """Single memory access event."""

    operation: Literal["R", "W"]  # Read or Write
    address: int                   # Memory address
    size: int                      # Access size in bytes
    timestamp: int                 # Sequential timestamp/index


@dataclass
class TraceMetadata:
    """Summary statistics for a trace."""

    source: Path
    format: str
    total_accesses: int
    unique_addresses: int
    read_count: int
    write_count: int
    address_range: tuple[int, int]  # min, max addresses


@dataclass
class Trace:
    """Container for parsed trace data."""

    metadata: TraceMetadata
    accesses: list[MemoryAccess]

    def __iter__(self) -> Iterator[MemoryAccess]:
        """Iterate over memory accesses."""
        return iter(self.accesses)

    def __len__(self) -> int:
        """Return number of memory accesses."""
        return len(self.accesses)

    @classmethod
    def from_accesses(
        cls,
        accesses: list[MemoryAccess],
        source: Path,
        format_name: str
    ) -> "Trace":
        """Create a Trace with computed metadata from a list of accesses."""
        if not accesses:
            metadata = TraceMetadata(
                source=source,
                format=format_name,
                total_accesses=0,
                unique_addresses=0,
                read_count=0,
                write_count=0,
                address_range=(0, 0)
            )
            return cls(metadata=metadata, accesses=[])

        # Compute statistics
        addresses = {acc.address for acc in accesses}
        read_count = sum(1 for acc in accesses if acc.operation == "R")
        write_count = sum(1 for acc in accesses if acc.operation == "W")
        min_addr = min(acc.address for acc in accesses)
        max_addr = max(acc.address for acc in accesses)

        metadata = TraceMetadata(
            source=source,
            format=format_name,
            total_accesses=len(accesses),
            unique_addresses=len(addresses),
            read_count=read_count,
            write_count=write_count,
            address_range=(min_addr, max_addr)
        )

        return cls(metadata=metadata, accesses=accesses)
