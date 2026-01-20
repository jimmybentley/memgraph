"""Tests for Valgrind wrapper."""

import pytest
import subprocess
import tempfile
from pathlib import Path

from memgraph.tracer import ValgrindTracer, TracerConfig, ValgrindNotFoundError, TracingError


def is_valgrind_available() -> bool:
    """Check if Valgrind is available."""
    try:
        result = subprocess.run(
            ["valgrind", "--version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


@pytest.fixture
def simple_program(tmp_path: Path) -> Path:
    """Create a simple C program for testing."""
    c_file = tmp_path / "test.c"
    c_file.write_text("""
#include <stdlib.h>

int main() {
    int *arr = malloc(100 * sizeof(int));
    for (int i = 0; i < 100; i++) {
        arr[i] = i;
    }
    int sum = 0;
    for (int i = 0; i < 100; i++) {
        sum += arr[i];
    }
    free(arr);
    return sum % 256;
}
""")

    binary = tmp_path / "test"

    # Compile
    result = subprocess.run(
        ["gcc", "-O0", "-g", "-o", str(binary), str(c_file)],
        capture_output=True
    )

    if result.returncode != 0:
        pytest.skip("GCC not available")

    return binary


def test_valgrind_check():
    """Should detect if Valgrind is installed."""
    if not is_valgrind_available():
        with pytest.raises(ValgrindNotFoundError):
            ValgrindTracer()
    else:
        # Should not raise
        tracer = ValgrindTracer()
        assert tracer is not None


@pytest.mark.skipif(not is_valgrind_available(), reason="Valgrind not installed")
def test_trace_simple_program(simple_program: Path):
    """Should trace a simple program."""
    config = TracerConfig(verbose=False)
    tracer = ValgrindTracer(config)

    trace_path = tracer.trace_to_file(simple_program)

    assert trace_path.exists()
    assert trace_path.stat().st_size > 0

    # Check trace content
    content = trace_path.read_text()
    # Should have load (L) or store (S) instructions
    assert ' L ' in content or ' S ' in content

    # Cleanup
    trace_path.unlink()


@pytest.mark.skipif(not is_valgrind_available(), reason="Valgrind not installed")
def test_trace_with_custom_output(simple_program: Path, tmp_path: Path):
    """Should save trace to custom location."""
    output = tmp_path / "custom_trace.log"

    tracer = ValgrindTracer()
    trace_path = tracer.trace_to_file(simple_program, output=output)

    assert trace_path == output
    assert output.exists()
    assert output.stat().st_size > 0

    # Cleanup
    output.unlink()


@pytest.mark.skipif(not is_valgrind_available(), reason="Valgrind not installed")
def test_trace_with_args(simple_program: Path):
    """Should handle program arguments."""
    tracer = ValgrindTracer()

    # Even though our test program doesn't use args, this tests the interface
    trace_path = tracer.trace_to_file(simple_program, args=["arg1", "arg2"])

    assert trace_path.exists()
    assert trace_path.stat().st_size > 0

    # Cleanup
    trace_path.unlink()


def test_trace_nonexistent_binary():
    """Should raise error for nonexistent binary."""
    if not is_valgrind_available():
        pytest.skip("Valgrind not installed")

    tracer = ValgrindTracer()

    with pytest.raises(TracingError, match="Binary not found"):
        tracer.trace_to_file(Path("/nonexistent/binary"))


@pytest.mark.skipif(not is_valgrind_available(), reason="Valgrind not installed")
def test_trace_with_timeout(simple_program: Path):
    """Should respect timeout setting."""
    config = TracerConfig(timeout=1)  # 1 second timeout
    tracer = ValgrindTracer(config)

    # Our simple program should complete within 1 second even under Valgrind
    trace_path = tracer.trace_to_file(simple_program)

    assert trace_path.exists()

    # Cleanup
    trace_path.unlink()


@pytest.mark.skipif(not is_valgrind_available(), reason="Valgrind not installed")
def test_get_version():
    """Should return Valgrind version."""
    tracer = ValgrindTracer()
    version = tracer.get_version()

    assert "valgrind" in version.lower()
    assert len(version) > 0


def test_config_defaults():
    """TracerConfig should have sensible defaults."""
    config = TracerConfig()

    assert config.tool == "valgrind"
    assert config.trace_stores is True
    assert config.trace_loads is True
    assert config.keep_trace is False
    assert config.trace_output is None
    assert config.timeout is None
