"""Valgrind Lackey wrapper for memory tracing."""

import subprocess
import tempfile
from pathlib import Path

from memgraph.tracer.config import TracerConfig
from memgraph.tracer.exceptions import ValgrindNotFoundError, TracingError


class ValgrindTracer:
    """Wrapper for Valgrind's Lackey tool."""

    def __init__(self, config: TracerConfig | None = None):
        self.config = config or TracerConfig()
        self._check_valgrind()

    def _check_valgrind(self) -> None:
        """Verify Valgrind is installed."""
        try:
            result = subprocess.run(
                ["valgrind", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise ValgrindNotFoundError("Valgrind not functional")
        except FileNotFoundError:
            raise ValgrindNotFoundError(
                "Valgrind not found. Install with:\n"
                "  Ubuntu/Debian: sudo apt install valgrind\n"
                "  macOS: brew install valgrind\n"
                "  Fedora: sudo dnf install valgrind"
            )
        except subprocess.TimeoutExpired:
            raise ValgrindNotFoundError("Valgrind check timed out")

    def trace_to_file(
        self,
        binary: Path,
        args: list[str] | None = None,
        output: Path | None = None
    ) -> Path:
        """
        Trace a binary and save memory accesses to a file.

        Args:
            binary: Path to the binary to trace
            args: Arguments to pass to the binary
            output: Output file path (creates temp file if None)

        Returns:
            Path to the trace file

        Raises:
            TracingError: If tracing fails
        """
        args = args or []

        if not binary.exists():
            raise TracingError(f"Binary not found: {binary}")

        if not binary.is_file():
            raise TracingError(f"Not a file: {binary}")

        # Resolve to absolute path
        binary = binary.resolve()

        # Create output file
        if output is None:
            fd, temp_path = tempfile.mkstemp(suffix='.trace', prefix='memgraph_')
            output = Path(temp_path)
        else:
            output = Path(output)

        # Build Valgrind command
        # Lackey writes trace output to stderr, we filter and redirect
        valgrind_cmd = [
            "valgrind",
            "--tool=lackey",
            "--basic-counts=no",
            "--trace-mem=yes",
            str(binary)
        ] + args

        if self.config.verbose:
            print(f"Running: {' '.join(valgrind_cmd)}")

        # Use shell to filter Lackey output (only memory access lines)
        # Lackey outputs lines like " L 7ff000398,8" or " S 7ff000390,8"
        # Filter out instruction fetches (I) and keep only L (load), S (store), M (modify)
        # Need to use shlex.join for proper quoting
        from shlex import join as shlex_join
        cmd_str = shlex_join(valgrind_cmd) + f" 2>&1 | grep -E '^[[:space:]]+(L|S|M) ' > {output}"

        try:
            result = subprocess.run(
                cmd_str,
                shell=True,
                timeout=self.config.timeout,
                cwd=binary.parent  # Run in same directory as binary
            )
        except subprocess.TimeoutExpired:
            if output.exists():
                output.unlink()
            raise TracingError(f"Tracing timed out after {self.config.timeout}s")
        except Exception as e:
            if output.exists():
                output.unlink()
            raise TracingError(f"Tracing failed: {e}")

        # Check if trace file was created and has content
        if not output.exists():
            raise TracingError("Trace file was not created")

        if output.stat().st_size == 0:
            output.unlink()
            raise TracingError(
                "Trace file is empty. The program may have:\n"
                "  - Crashed or exited immediately\n"
                "  - Not performed any memory accesses\n"
                "  - Run with errors\n"
                f"Try running manually: {' '.join(valgrind_cmd)}"
            )

        return output

    def get_version(self) -> str:
        """Get Valgrind version string."""
        try:
            result = subprocess.run(
                ["valgrind", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()
        except Exception:
            return "unknown"
