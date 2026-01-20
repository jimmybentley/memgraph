"""Tracer configuration."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class TracerConfig:
    """Configuration for tracing."""

    tool: str = "valgrind"  # Only valgrind supported initially
    trace_instructions: bool = False  # Include instruction fetches
    trace_stores: bool = True
    trace_loads: bool = True
    keep_trace: bool = False  # Keep trace file after analysis
    trace_output: Path | None = None  # Custom trace output path
    timeout: int | None = None  # Timeout in seconds
    verbose: bool = False  # Verbose output
