"""Tests for windowing strategies."""

import pytest
from memgraph.graph.windowing import (
    FixedWindow,
    SlidingWindow,
    AdaptiveWindow,
)
from memgraph.trace.models import MemoryAccess


def test_fixed_window_basic() -> None:
    """Test basic fixed window functionality."""
    accesses = [MemoryAccess("R", i * 8, 8, i) for i in range(10)]
    strategy = FixedWindow(size=3)

    windows = list(strategy.windows(accesses))

    assert len(windows) == 4  # 3, 3, 3, 1
    assert len(windows[0]) == 3
    assert len(windows[1]) == 3
    assert len(windows[2]) == 3
    assert len(windows[3]) == 1


def test_fixed_window_exact_fit() -> None:
    """Test fixed window when trace size is multiple of window size."""
    accesses = [MemoryAccess("R", i * 8, 8, i) for i in range(12)]
    strategy = FixedWindow(size=4)

    windows = list(strategy.windows(accesses))

    assert len(windows) == 3
    assert all(len(w) == 4 for w in windows)


def test_fixed_window_empty_trace() -> None:
    """Test fixed window with empty trace."""
    strategy = FixedWindow(size=10)
    windows = list(strategy.windows([]))

    assert len(windows) == 0


def test_fixed_window_single_element() -> None:
    """Test fixed window with single element."""
    accesses = [MemoryAccess("R", 0x1000, 8, 0)]
    strategy = FixedWindow(size=10)

    windows = list(strategy.windows(accesses))

    assert len(windows) == 1
    assert len(windows[0]) == 1


def test_fixed_window_invalid_size() -> None:
    """Test that invalid window size raises error."""
    with pytest.raises(ValueError, match="Window size must be positive"):
        FixedWindow(size=0)

    with pytest.raises(ValueError, match="Window size must be positive"):
        FixedWindow(size=-1)


def test_sliding_window_basic() -> None:
    """Test basic sliding window functionality."""
    accesses = [MemoryAccess("R", i * 8, 8, i) for i in range(10)]
    strategy = SlidingWindow(size=3, step=1)

    windows = list(strategy.windows(accesses))

    # Should have 8 full windows + 1 partial (positions 0-8)
    assert len(windows) >= 8

    # Check first window
    assert windows[0][0].address == 0
    assert windows[0][1].address == 8
    assert windows[0][2].address == 16

    # Check second window (overlaps with first)
    assert windows[1][0].address == 8
    assert windows[1][1].address == 16
    assert windows[1][2].address == 24


def test_sliding_window_step_size() -> None:
    """Test sliding window with different step sizes."""
    accesses = [MemoryAccess("R", i * 8, 8, i) for i in range(20)]

    # Step size 2
    strategy = SlidingWindow(size=4, step=2)
    windows = list(strategy.windows(accesses))

    # Should have windows at positions 0, 2, 4, 6, 8, 10, 12, 14, 16, 18
    assert len(windows) >= 9

    # Step size equals window size (becomes fixed window)
    strategy = SlidingWindow(size=5, step=5)
    windows = list(strategy.windows(accesses))

    assert len(windows) == 4


def test_sliding_window_last_partial() -> None:
    """Test that sliding window includes partial last window."""
    accesses = [MemoryAccess("R", i * 8, 8, i) for i in range(11)]
    strategy = SlidingWindow(size=5, step=5)

    windows = list(strategy.windows(accesses))

    assert len(windows) == 3
    assert len(windows[0]) == 5
    assert len(windows[1]) == 5
    assert len(windows[2]) == 1  # Last partial window


def test_sliding_window_large_step() -> None:
    """Test sliding window with step larger than window."""
    accesses = [MemoryAccess("R", i * 8, 8, i) for i in range(20)]
    strategy = SlidingWindow(size=3, step=10)

    windows = list(strategy.windows(accesses))

    # Should have windows at positions 0, 10
    assert len(windows) >= 2
    assert windows[0][0].timestamp == 0
    assert windows[1][0].timestamp == 10


def test_sliding_window_overlap() -> None:
    """Test that sliding windows properly overlap."""
    accesses = [MemoryAccess("R", i * 8, 8, i) for i in range(10)]
    strategy = SlidingWindow(size=4, step=2)

    windows = list(strategy.windows(accesses))

    # Windows should overlap by 2 elements
    assert windows[0][2] == windows[1][0]
    assert windows[0][3] == windows[1][1]


def test_sliding_window_invalid_params() -> None:
    """Test that invalid parameters raise errors."""
    with pytest.raises(ValueError, match="Window size must be positive"):
        SlidingWindow(size=0, step=1)

    with pytest.raises(ValueError, match="Step size must be positive"):
        SlidingWindow(size=10, step=0)


def test_adaptive_window_high_locality() -> None:
    """Test that adaptive window grows with high locality."""
    # Create trace with high reuse (same addresses repeated)
    accesses = []
    for i in range(100):
        addr = (i % 10) * 8  # Only 10 unique addresses, high reuse
        accesses.append(MemoryAccess("R", addr, 8, i))

    strategy = AdaptiveWindow(
        base_size=20,
        min_size=10,
        max_size=50,
        locality_threshold=0.5
    )

    windows = list(strategy.windows(accesses))

    # Windows should generally grow in size due to high locality
    # Check that at least some windows are larger than base size
    sizes = [len(w) for w in windows]
    assert max(sizes) > 20  # At least one window grew


def test_adaptive_window_low_locality() -> None:
    """Test that adaptive window shrinks with low locality."""
    # Create trace with low reuse (unique addresses)
    accesses = [MemoryAccess("R", i * 8, 8, i) for i in range(100)]

    strategy = AdaptiveWindow(
        base_size=30,
        min_size=10,
        max_size=50,
        locality_threshold=0.5
    )

    windows = list(strategy.windows(accesses))

    # Windows should generally shrink due to low locality
    # At least some windows should be smaller than base size
    sizes = [len(w) for w in windows]
    assert min(sizes) < 30


def test_adaptive_window_respects_bounds() -> None:
    """Test that adaptive window respects min/max bounds."""
    accesses = [MemoryAccess("R", i * 8, 8, i) for i in range(200)]

    strategy = AdaptiveWindow(
        base_size=30,
        min_size=10,
        max_size=50,
        locality_threshold=0.5
    )

    windows = list(strategy.windows(accesses))
    sizes = [len(w) for w in windows]

    # All windows should be within bounds
    for size in sizes:
        assert 10 <= size <= 50


def test_adaptive_window_empty_trace() -> None:
    """Test adaptive window with empty trace."""
    strategy = AdaptiveWindow(base_size=20)
    windows = list(strategy.windows([]))

    assert len(windows) == 0


def test_adaptive_window_locality_computation() -> None:
    """Test that locality is computed correctly."""
    # Create trace where same addresses repeat later (for high locality)
    accesses = []
    # First 20: addresses 0-19
    for i in range(20):
        accesses.append(MemoryAccess("R", i * 8, 8, i))
    # Next 80: repeat addresses 0-19 (high locality)
    for i in range(80):
        addr = (i % 20) * 8
        accesses.append(MemoryAccess("R", addr, 8, i + 20))

    strategy = AdaptiveWindow(
        base_size=15,
        min_size=5,
        max_size=40,
        locality_threshold=0.5
    )

    windows = list(strategy.windows(accesses))

    # Windows later in the trace should see high locality and grow
    # Check that some windows exceeded the base size
    sizes = [len(w) for w in windows]
    assert max(sizes) > 15  # At least one window grew beyond base


def test_adaptive_window_invalid_params() -> None:
    """Test that invalid parameters raise errors."""
    with pytest.raises(ValueError, match="All sizes must be positive"):
        AdaptiveWindow(base_size=0)

    with pytest.raises(ValueError, match="All sizes must be positive"):
        AdaptiveWindow(base_size=10, min_size=-1)

    with pytest.raises(ValueError, match="min_size must be <= max_size"):
        AdaptiveWindow(min_size=100, max_size=50)

    with pytest.raises(ValueError, match="locality_threshold must be between"):
        AdaptiveWindow(locality_threshold=1.5)

    with pytest.raises(ValueError, match="locality_threshold must be between"):
        AdaptiveWindow(locality_threshold=-0.1)


def test_window_strategies_produce_windows() -> None:
    """Test that all window strategies produce at least one window."""
    accesses = [MemoryAccess("R", i * 8, 8, i) for i in range(50)]

    strategies = [
        FixedWindow(size=10),
        SlidingWindow(size=10, step=5),
        AdaptiveWindow(base_size=10),
    ]

    for strategy in strategies:
        windows = list(strategy.windows(accesses))
        assert len(windows) > 0, f"{strategy.__class__.__name__} produced no windows"


def test_window_strategies_preserve_order() -> None:
    """Test that windows preserve access order."""
    accesses = [MemoryAccess("R", i * 8, 8, i) for i in range(20)]

    strategies = [
        FixedWindow(size=5),
        SlidingWindow(size=5, step=2),
        AdaptiveWindow(base_size=5),
    ]

    for strategy in strategies:
        for window in strategy.windows(accesses):
            # Timestamps should be increasing
            timestamps = [acc.timestamp for acc in window]
            assert timestamps == sorted(timestamps), \
                f"{strategy.__class__.__name__} didn't preserve order"
