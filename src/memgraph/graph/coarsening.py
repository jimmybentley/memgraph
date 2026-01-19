"""Address coarsening for different granularities."""

from enum import Enum


class Granularity(Enum):
    """Memory address granularity levels."""

    BYTE = 1           # No coarsening
    CACHELINE = 64     # 64-byte cache lines
    PAGE = 4096        # 4KB pages

    @property
    def shift_bits(self) -> int:
        """Get the number of bits to shift for this granularity."""
        if self == Granularity.BYTE:
            return 0
        elif self == Granularity.CACHELINE:
            return 6  # 2^6 = 64
        elif self == Granularity.PAGE:
            return 12  # 2^12 = 4096
        return 0


def coarsen_address(address: int, granularity: Granularity) -> int:
    """Map address to coarsened granularity.

    Args:
        address: Memory address to coarsen
        granularity: Target granularity level

    Returns:
        Coarsened address (aligned to granularity boundary)

    Examples:
        >>> coarsen_address(0x1234, Granularity.CACHELINE)
        0x1200  # Aligned to 64-byte boundary
        >>> coarsen_address(0x1234, Granularity.PAGE)
        0x1000  # Aligned to 4KB boundary
    """
    return address >> granularity.shift_bits
