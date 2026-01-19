"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path
from typing import Generator
import tempfile


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_lackey_trace(temp_dir: Path) -> Path:
    """Create a sample Valgrind Lackey trace file."""
    trace_file = temp_dir / "test_lackey.trace"
    content = """I  04000000,3
 S 7ff000398,8
 L 7ff000398,8
 M 7ff000390,8
 L 1000,4
 S 2000,8
"""
    trace_file.write_text(content)
    return trace_file


@pytest.fixture
def sample_csv_trace(temp_dir: Path) -> Path:
    """Create a sample CSV trace file."""
    trace_file = temp_dir / "test_csv.trace"
    content = """op,address,size
R,0x7fff5a8b1000,8
W,0x7fff5a8b1008,4
R,0x1000,8
W,0x2000,4
"""
    trace_file.write_text(content)
    return trace_file


@pytest.fixture
def sample_native_trace(temp_dir: Path) -> Path:
    """Create a sample native format trace file."""
    trace_file = temp_dir / "test_native.trace"
    content = """# MemGraph Trace v1
R,0x7fff5a8b1000,8,0
W,0x7fff5a8b1008,4,1
R,0x1000,8,2
W,0x2000,4,3
"""
    trace_file.write_text(content)
    return trace_file
