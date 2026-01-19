"""Tests for address coarsening."""

import pytest
from memgraph.graph.coarsening import Granularity, coarsen_address


def test_granularity_values() -> None:
    """Test Granularity enum values."""
    assert Granularity.BYTE.value == 1
    assert Granularity.CACHELINE.value == 64
    assert Granularity.PAGE.value == 4096


def test_granularity_shift_bits() -> None:
    """Test shift bits calculation."""
    assert Granularity.BYTE.shift_bits == 0
    assert Granularity.CACHELINE.shift_bits == 6
    assert Granularity.PAGE.shift_bits == 12


def test_coarsen_byte_granularity() -> None:
    """Test coarsening with byte granularity (no coarsening)."""
    assert coarsen_address(0x1234, Granularity.BYTE) == 0x1234
    assert coarsen_address(0xABCD, Granularity.BYTE) == 0xABCD
    assert coarsen_address(0, Granularity.BYTE) == 0


def test_coarsen_cacheline_granularity() -> None:
    """Test coarsening with cache line granularity (64 bytes)."""
    # Addresses in same cache line should map to same value
    assert coarsen_address(0x1000, Granularity.CACHELINE) == 0x40  # 0x1000 >> 6
    assert coarsen_address(0x1001, Granularity.CACHELINE) == 0x40
    assert coarsen_address(0x103F, Granularity.CACHELINE) == 0x40  # Last byte in cache line

    # Next cache line
    assert coarsen_address(0x1040, Granularity.CACHELINE) == 0x41  # 0x1040 >> 6
    assert coarsen_address(0x1041, Granularity.CACHELINE) == 0x41


def test_coarsen_page_granularity() -> None:
    """Test coarsening with page granularity (4KB)."""
    # Addresses in same page should map to same value
    assert coarsen_address(0x1000, Granularity.PAGE) == 0x1  # 0x1000 >> 12
    assert coarsen_address(0x1FFF, Granularity.PAGE) == 0x1  # Last byte in page

    # Next page
    assert coarsen_address(0x2000, Granularity.PAGE) == 0x2  # 0x2000 >> 12
    assert coarsen_address(0x2001, Granularity.PAGE) == 0x2


def test_coarsen_zero_address() -> None:
    """Test coarsening zero address."""
    assert coarsen_address(0, Granularity.BYTE) == 0
    assert coarsen_address(0, Granularity.CACHELINE) == 0
    assert coarsen_address(0, Granularity.PAGE) == 0


def test_coarsen_reduces_uniqueness() -> None:
    """Test that coarsening reduces number of unique addresses."""
    # Sequential addresses with 8-byte stride
    addresses = [0x1000 + i * 8 for i in range(100)]

    # Byte granularity: all unique
    byte_coarsened = [coarsen_address(addr, Granularity.BYTE) for addr in addresses]
    assert len(set(byte_coarsened)) == 100

    # Cache line granularity: many map to same cache line
    cl_coarsened = [coarsen_address(addr, Granularity.CACHELINE) for addr in addresses]
    assert len(set(cl_coarsened)) < 100

    # Page granularity: even fewer unique
    page_coarsened = [coarsen_address(addr, Granularity.PAGE) for addr in addresses]
    assert len(set(page_coarsened)) < len(set(cl_coarsened))


def test_coarsen_alignment() -> None:
    """Test that coarsening aligns addresses to boundaries."""
    # Cache line alignment
    addr = 0x1234  # Arbitrary address
    coarsened = coarsen_address(addr, Granularity.CACHELINE)
    # Result should be the cache line index (addr >> 6)
    assert coarsened == addr >> 6

    # Page alignment
    coarsened_page = coarsen_address(addr, Granularity.PAGE)
    # Result should be the page index (addr >> 12)
    assert coarsened_page == addr >> 12


def test_coarsen_large_addresses() -> None:
    """Test coarsening with large addresses."""
    large_addr = 0x7FFFFFFF_FFFFF000

    byte = coarsen_address(large_addr, Granularity.BYTE)
    cacheline = coarsen_address(large_addr, Granularity.CACHELINE)
    page = coarsen_address(large_addr, Granularity.PAGE)

    assert byte == large_addr
    assert cacheline == large_addr >> 6
    assert page == large_addr >> 12
