"""Tests for synthetic trace generators."""

import pytest
from pathlib import Path
from memgraph.trace.generator import (
    generate_sequential,
    generate_random,
    generate_strided,
    generate_pointer_chase,
    generate_working_set,
    get_available_patterns,
)
from memgraph.trace.formats.native import NativeParser


def test_generate_sequential_basic() -> None:
    """Test basic sequential trace generation."""
    trace = generate_sequential(n=10, start_addr=0x1000, stride=8)

    assert len(trace) == 10
    assert trace.metadata.format == "synthetic"
    assert trace.metadata.total_accesses == 10

    # Check sequential pattern
    for i, access in enumerate(trace.accesses):
        expected_addr = 0x1000 + (i * 8)
        assert access.address == expected_addr
        assert access.size == 8
        assert access.timestamp == i
        assert access.operation == "R"


def test_generate_sequential_mixed_operations() -> None:
    """Test sequential trace with mixed R/W operations."""
    trace = generate_sequential(n=10, operation="mixed")

    # Should alternate R and W
    for i, access in enumerate(trace.accesses):
        if i % 2 == 0:
            assert access.operation == "R"
        else:
            assert access.operation == "W"


def test_generate_random_basic() -> None:
    """Test basic random trace generation."""
    trace = generate_random(n=100, seed=42)

    assert len(trace) == 100
    assert trace.metadata.format == "synthetic"

    # Check addresses are within range
    addr_range = (0x1000, 0x10000)
    for access in trace.accesses:
        assert addr_range[0] <= access.address < addr_range[1]
        assert access.size == 8


def test_generate_random_reproducibility() -> None:
    """Test that random generation with same seed produces same trace."""
    trace1 = generate_random(n=50, seed=42)
    trace2 = generate_random(n=50, seed=42)

    assert len(trace1) == len(trace2)

    for acc1, acc2 in zip(trace1.accesses, trace2.accesses):
        assert acc1.address == acc2.address
        assert acc1.operation == acc2.operation
        assert acc1.size == acc2.size


def test_generate_strided_basic() -> None:
    """Test basic strided trace generation."""
    trace = generate_strided(n=50, start_addr=0x1000, stride=64, count=10)

    assert len(trace) == 50

    # Check strided pattern repeats
    for i in range(10):
        # First cycle
        expected_addr = 0x1000 + (i * 64)
        assert trace.accesses[i].address == expected_addr

        # Second cycle (should repeat)
        if i < 40:
            assert trace.accesses[i + 10].address == expected_addr


def test_generate_pointer_chase_basic() -> None:
    """Test basic pointer chase generation."""
    trace = generate_pointer_chase(n=100, num_nodes=20, seed=42)

    assert len(trace) == 100
    assert trace.metadata.format == "synthetic"

    # Should access exactly num_nodes unique addresses in first cycle
    first_cycle = trace.accesses[:20]
    unique_addrs = {acc.address for acc in first_cycle}
    assert len(unique_addrs) == 20


def test_generate_pointer_chase_reproducibility() -> None:
    """Test pointer chase reproducibility with seed."""
    trace1 = generate_pointer_chase(n=50, num_nodes=10, seed=42)
    trace2 = generate_pointer_chase(n=50, num_nodes=10, seed=42)

    for acc1, acc2 in zip(trace1.accesses, trace2.accesses):
        assert acc1.address == acc2.address


def test_generate_working_set_basic() -> None:
    """Test basic working set generation."""
    trace = generate_working_set(
        n=100,
        working_set_size=10,
        total_addresses=100,
        hot_probability=0.8,
        seed=42
    )

    assert len(trace) == 100
    assert trace.metadata.format == "synthetic"

    # Count accesses to hot set (first 10 addresses)
    hot_addrs = set(range(0x1000, 0x1000 + 10 * 8, 8))
    hot_count = sum(1 for acc in trace.accesses if acc.address in hot_addrs)

    # With 80% hot probability and 100 accesses, expect roughly 80 hot accesses
    # Allow some variance due to randomness
    assert 60 <= hot_count <= 95


def test_generate_working_set_invalid_params() -> None:
    """Test working set with invalid parameters."""
    with pytest.raises(ValueError):
        generate_working_set(
            n=100,
            working_set_size=200,  # Larger than total
            total_addresses=100
        )


def test_get_available_patterns() -> None:
    """Test getting list of available patterns."""
    patterns = get_available_patterns()

    assert "sequential" in patterns
    assert "random" in patterns
    assert "strided" in patterns
    assert "pointer_chase" in patterns
    assert "working_set" in patterns
    assert len(patterns) == 5


def test_trace_round_trip(temp_dir: Path) -> None:
    """Test that generated traces can be written and parsed back."""
    # Generate a trace
    original_trace = generate_sequential(n=100, start_addr=0x1000, stride=8)

    # Write it to a file
    output_file = temp_dir / "generated.trace"
    parser = NativeParser()
    parser.write(original_trace, output_file)

    # Parse it back
    parsed_trace = parser.parse(output_file)

    # Verify they match
    assert len(parsed_trace) == len(original_trace)

    for orig, parsed in zip(original_trace.accesses, parsed_trace.accesses):
        assert orig.operation == parsed.operation
        assert orig.address == parsed.address
        assert orig.size == parsed.size
        assert orig.timestamp == parsed.timestamp


def test_all_generators_produce_correct_count() -> None:
    """Test that all generators produce the requested number of accesses."""
    n = 50

    trace = generate_sequential(n)
    assert len(trace) == n

    trace = generate_random(n, seed=42)
    assert len(trace) == n

    trace = generate_strided(n)
    assert len(trace) == n

    trace = generate_pointer_chase(n, seed=42)
    assert len(trace) == n

    trace = generate_working_set(n, seed=42)
    assert len(trace) == n


def test_all_generators_have_valid_timestamps() -> None:
    """Test that all generators produce sequential timestamps."""
    n = 20

    for trace in [
        generate_sequential(n),
        generate_random(n, seed=42),
        generate_strided(n),
        generate_pointer_chase(n, seed=42),
        generate_working_set(n, seed=42),
    ]:
        for i, access in enumerate(trace.accesses):
            assert access.timestamp == i


def test_trace_metadata_computation() -> None:
    """Test that generated traces have correct metadata."""
    trace = generate_sequential(n=100, start_addr=0x1000, stride=8)

    meta = trace.metadata
    assert meta.total_accesses == 100
    assert meta.unique_addresses == 100
    assert meta.read_count == 100
    assert meta.write_count == 0
    assert meta.address_range[0] == 0x1000
    assert meta.address_range[1] == 0x1000 + 99 * 8
