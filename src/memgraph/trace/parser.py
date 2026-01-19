"""Main trace parsing module with format auto-detection."""

from pathlib import Path
from typing import Optional
from memgraph.trace.models import Trace
from memgraph.trace.formats.base import BaseParser
from memgraph.trace.formats.native import NativeParser
from memgraph.trace.formats.lackey import LackeyParser
from memgraph.trace.formats.csv import CSVParser


# Parsers in order of precedence (most specific first)
PARSERS: list[type[BaseParser]] = [
    NativeParser,  # Check native first (has explicit header)
    CSVParser,     # Check CSV second (has header row)
    LackeyParser,  # Check Lackey last (more ambiguous format)
]


def detect_format(file_path: Path) -> Optional[type[BaseParser]]:
    """Detect the format of a trace file.

    Args:
        file_path: Path to the trace file

    Returns:
        Parser class that can handle this file, or None if no parser found
    """
    for parser_cls in PARSERS:
        if parser_cls.can_parse(file_path):
            return parser_cls
    return None


def parse_trace(
    file_path: Path | str,
    format: Optional[str] = None
) -> Trace:
    """Parse a trace file, auto-detecting format if not specified.

    Args:
        file_path: Path to the trace file
        format: Optional format name ("native", "lackey", "csv").
                If None, format will be auto-detected.

    Returns:
        Parsed Trace object

    Raises:
        ValueError: If format is invalid or file cannot be parsed
        FileNotFoundError: If the file doesn't exist
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Trace file not found: {file_path}")

    # If format specified, use that parser
    if format:
        format = format.lower()
        parser_map: dict[str, type[BaseParser]] = {
            "native": NativeParser,
            "lackey": LackeyParser,
            "csv": CSVParser,
        }

        if format not in parser_map:
            raise ValueError(
                f"Unknown format: {format}. "
                f"Supported formats: {', '.join(parser_map.keys())}"
            )

        parser_cls = parser_map[format]
        parser = parser_cls()
        return parser.parse(file_path)

    # Auto-detect format
    parser_cls = detect_format(file_path)
    if parser_cls is None:
        raise ValueError(
            f"Could not detect format of trace file: {file_path}. "
            f"Try specifying format explicitly."
        )

    parser = parser_cls()
    return parser.parse(file_path)
