"""Windowing strategies for temporal adjacency graph construction."""

from abc import ABC, abstractmethod
from typing import Iterator
from memgraph.trace.models import MemoryAccess


class WindowStrategy(ABC):
    """Abstract base class for windowing strategies."""

    @abstractmethod
    def windows(self, accesses: list[MemoryAccess]) -> Iterator[list[MemoryAccess]]:
        """Yield windows of memory accesses.

        Args:
            accesses: List of memory accesses

        Yields:
            Lists of memory accesses representing windows
        """
        pass


class FixedWindow(WindowStrategy):
    """Non-overlapping fixed-size windows.

    Divides the trace into consecutive, non-overlapping windows of fixed size.
    """

    def __init__(self, size: int = 100):
        """Initialize fixed window strategy.

        Args:
            size: Number of accesses per window
        """
        if size <= 0:
            raise ValueError("Window size must be positive")
        self.size = size

    def windows(self, accesses: list[MemoryAccess]) -> Iterator[list[MemoryAccess]]:
        """Yield non-overlapping fixed-size windows.

        Args:
            accesses: List of memory accesses

        Yields:
            Non-overlapping windows of size `self.size`
        """
        for i in range(0, len(accesses), self.size):
            window = accesses[i:i + self.size]
            if window:  # Skip empty windows
                yield window


class SlidingWindow(WindowStrategy):
    """Overlapping sliding window.

    Creates overlapping windows by sliding with a specified step size.
    """

    def __init__(self, size: int = 100, step: int = 1):
        """Initialize sliding window strategy.

        Args:
            size: Number of accesses per window
            step: Number of accesses to slide forward each time
        """
        if size <= 0:
            raise ValueError("Window size must be positive")
        if step <= 0:
            raise ValueError("Step size must be positive")
        self.size = size
        self.step = step

    def windows(self, accesses: list[MemoryAccess]) -> Iterator[list[MemoryAccess]]:
        """Yield overlapping sliding windows.

        Args:
            accesses: List of memory accesses

        Yields:
            Overlapping windows of size `self.size`, sliding by `self.step`
        """
        i = 0
        while i < len(accesses):
            window = accesses[i:i + self.size]
            if len(window) < self.size:
                # Last window might be smaller
                if window:
                    yield window
                break
            yield window
            i += self.step


class AdaptiveWindow(WindowStrategy):
    """Adaptive window that adjusts size based on temporal locality.

    Window size increases when locality is high (many reuses) and decreases
    when locality is low (few reuses).
    """

    def __init__(
        self,
        base_size: int = 100,
        min_size: int = 20,
        max_size: int = 500,
        locality_threshold: float = 0.5
    ):
        """Initialize adaptive window strategy.

        Args:
            base_size: Initial window size
            min_size: Minimum window size
            max_size: Maximum window size
            locality_threshold: Threshold for locality ratio (0.0 to 1.0)
                High locality (>threshold) increases window size
                Low locality (<threshold) decreases window size
        """
        if base_size <= 0 or min_size <= 0 or max_size <= 0:
            raise ValueError("All sizes must be positive")
        if min_size > max_size:
            raise ValueError("min_size must be <= max_size")
        if not 0.0 <= locality_threshold <= 1.0:
            raise ValueError("locality_threshold must be between 0.0 and 1.0")

        self.base_size = base_size
        self.min_size = min_size
        self.max_size = max_size
        self.locality_threshold = locality_threshold

    def _compute_locality(self, window: list[MemoryAccess], seen: set[int]) -> float:
        """Compute locality ratio for a window.

        Args:
            window: Current window of accesses
            seen: Set of addresses seen before this window

        Returns:
            Ratio of accesses to previously seen addresses (0.0 to 1.0)
        """
        if not window:
            return 0.0

        reuse_count = sum(1 for acc in window if acc.address in seen)
        return reuse_count / len(window)

    def windows(self, accesses: list[MemoryAccess]) -> Iterator[list[MemoryAccess]]:
        """Yield adaptive windows that adjust size based on locality.

        Args:
            accesses: List of memory accesses

        Yields:
            Windows with adaptive sizes based on temporal locality
        """
        if not accesses:
            return

        current_size = self.base_size
        seen_addresses: set[int] = set()
        i = 0

        while i < len(accesses):
            # Get current window
            window_end = min(i + current_size, len(accesses))
            window = accesses[i:window_end]

            if not window:
                break

            yield window

            # Compute locality for this window
            locality = self._compute_locality(window, seen_addresses)

            # Update seen addresses
            for acc in window:
                seen_addresses.add(acc.address)

            # Adjust window size based on locality
            if locality > self.locality_threshold:
                # High locality - increase window size
                current_size = min(int(current_size * 1.2), self.max_size)
            else:
                # Low locality - decrease window size
                current_size = max(int(current_size * 0.8), self.min_size)

            i = window_end
