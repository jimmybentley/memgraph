"""Tests for trace parsers."""

import pytest
from pathlib import Path
from memgraph.trace.parser import parse_trace, detect_format
from memgraph.trace.formats.lackey import LackeyParser
from memgraph.trace.formats.csv import CSVParser
from memgraph.trace.formats.native import NativeParser
from memgraph.trace.models import MemoryAccess


def test_lackey_parser_basic(sample_lackey_trace: Path) -> None:
    """Test basic Lackey parser functionality."""
    parser = LackeyParser()
    trace = parser.parse(sample_lackey_trace)

    # Should have 6 accesses (I is skipped, M counts as 2)
    assert len(trace) == 6
    assert trace.metadata.format == "lackey"
    assert trace.metadata.total_accesses == 6

    # Check first few accesses
    accesses = trace.accesses
    assert accesses[0].operation == "W"  # S
    assert accesses[0].address == 0x7ff000398
    assert accesses[0].size == 8

    assert accesses[1].operation == "R"  # L
    assert accesses[1].address == 0x7ff000398
    assert accesses[1].size == 8

    # Check M operation (read + write)
    assert accesses[2].operation == "R"  # M (read)
    assert accesses[2].address == 0x7ff000390
    assert accesses[3].operation == "W"  # M (write)
    assert accesses[3].address == 0x7ff000390


def test_lackey_parser_can_parse(sample_lackey_trace: Path, temp_dir: Path) -> None:
    """Test Lackey parser format detection."""
    assert LackeyParser.can_parse(sample_lackey_trace) is True

    # Test with non-Lackey file
    other_file = temp_dir / "not_lackey.txt"
    other_file.write_text("This is not a lackey trace")
    assert LackeyParser.can_parse(other_file) is False


def test_csv_parser_basic(sample_csv_trace: Path) -> None:
    """Test basic CSV parser functionality."""
    parser = CSVParser()
    trace = parser.parse(sample_csv_trace)

    assert len(trace) == 4
    assert trace.metadata.format == "csv"
    assert trace.metadata.total_accesses == 4

    # Check first access
    accesses = trace.accesses
    assert accesses[0].operation == "R"
    assert accesses[0].address == 0x7fff5a8b1000
    assert accesses[0].size == 8

    assert accesses[1].operation == "W"
    assert accesses[1].address == 0x7fff5a8b1008
    assert accesses[1].size == 4


def test_csv_parser_can_parse(sample_csv_trace: Path, temp_dir: Path) -> None:
    """Test CSV parser format detection."""
    assert CSVParser.can_parse(sample_csv_trace) is True

    # Test with non-CSV file
    other_file = temp_dir / "not_csv.txt"
    other_file.write_text("This is not a CSV trace")
    assert CSVParser.can_parse(other_file) is False


def test_native_parser_basic(sample_native_trace: Path) -> None:
    """Test basic native parser functionality."""
    parser = NativeParser()
    trace = parser.parse(sample_native_trace)

    assert len(trace) == 4
    assert trace.metadata.format == "native"
    assert trace.metadata.total_accesses == 4

    # Check first access
    accesses = trace.accesses
    assert accesses[0].operation == "R"
    assert accesses[0].address == 0x7fff5a8b1000
    assert accesses[0].size == 8
    assert accesses[0].timestamp == 0

    assert accesses[1].operation == "W"
    assert accesses[1].address == 0x7fff5a8b1008
    assert accesses[1].size == 4
    assert accesses[1].timestamp == 1


def test_native_parser_can_parse(sample_native_trace: Path, temp_dir: Path) -> None:
    """Test native parser format detection."""
    assert NativeParser.can_parse(sample_native_trace) is True

    # Test with non-native file
    other_file = temp_dir / "not_native.txt"
    other_file.write_text("This is not a native trace")
    assert NativeParser.can_parse(other_file) is False


def test_native_parser_write(temp_dir: Path) -> None:
    """Test native parser write functionality."""
    from memgraph.trace.models import Trace

    # Create a simple trace
    accesses = [
        MemoryAccess("R", 0x1000, 8, 0),
        MemoryAccess("W", 0x2000, 4, 1),
    ]
    trace = Trace.from_accesses(accesses, Path("<test>"), "native")

    # Write it
    output_file = temp_dir / "output.trace"
    parser = NativeParser()
    parser.write(trace, output_file)

    # Read it back
    read_trace = parser.parse(output_file)

    assert len(read_trace) == 2
    assert read_trace.accesses[0].operation == "R"
    assert read_trace.accesses[0].address == 0x1000
    assert read_trace.accesses[1].operation == "W"
    assert read_trace.accesses[1].address == 0x2000


def test_parse_trace_auto_detect(
    sample_lackey_trace: Path,
    sample_csv_trace: Path,
    sample_native_trace: Path
) -> None:
    """Test automatic format detection."""
    # Test Lackey
    trace = parse_trace(sample_lackey_trace)
    assert trace.metadata.format == "lackey"
    assert len(trace) == 6

    # Test CSV
    trace = parse_trace(sample_csv_trace)
    assert trace.metadata.format == "csv"
    assert len(trace) == 4

    # Test Native
    trace = parse_trace(sample_native_trace)
    assert trace.metadata.format == "native"
    assert len(trace) == 4


def test_parse_trace_explicit_format(sample_lackey_trace: Path) -> None:
    """Test parsing with explicit format specification."""
    trace = parse_trace(sample_lackey_trace, format="lackey")
    assert trace.metadata.format == "lackey"
    assert len(trace) == 6


def test_parse_trace_invalid_format(sample_lackey_trace: Path) -> None:
    """Test parsing with invalid format."""
    with pytest.raises(ValueError, match="Unknown format"):
        parse_trace(sample_lackey_trace, format="invalid")


def test_parse_trace_nonexistent_file() -> None:
    """Test parsing nonexistent file."""
    with pytest.raises(FileNotFoundError):
        parse_trace(Path("/nonexistent/file.trace"))


def test_detect_format(
    sample_lackey_trace: Path,
    sample_csv_trace: Path,
    sample_native_trace: Path
) -> None:
    """Test format detection function."""
    assert detect_format(sample_lackey_trace) == LackeyParser
    assert detect_format(sample_csv_trace) == CSVParser
    assert detect_format(sample_native_trace) == NativeParser


def test_trace_metadata(sample_native_trace: Path) -> None:
    """Test that metadata is correctly computed."""
    trace = parse_trace(sample_native_trace)
    meta = trace.metadata

    assert meta.total_accesses == 4
    assert meta.unique_addresses == 4
    assert meta.read_count == 2
    assert meta.write_count == 2
    assert meta.address_range[0] == 0x1000
    assert meta.address_range[1] == 0x7fff5a8b1008


def test_trace_iteration(sample_native_trace: Path) -> None:
    """Test that Trace objects can be iterated."""
    trace = parse_trace(sample_native_trace)

    count = 0
    for access in trace:
        assert isinstance(access, MemoryAccess)
        count += 1

    assert count == 4
