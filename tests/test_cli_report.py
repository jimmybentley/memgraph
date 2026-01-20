"""Tests for CLI reporter."""

from rich.console import Console
from io import StringIO

from memgraph.report.cli_report import CLIReporter
from tests.test_result import create_mock_result


def test_cli_report_renders():
    """CLI report should render without errors."""
    result = create_mock_result()

    # Create console with string buffer
    output = StringIO()
    console = Console(file=output, force_terminal=True, width=120)

    reporter = CLIReporter(console)
    reporter.report(result)

    # Get output
    rendered = output.getvalue()

    # Check that key information is present
    assert "MemGraph Analysis Report" in rendered
    assert "test_trace.log" in rendered
    assert "sequential" in rendered
    assert "1,000" in rendered  # Total accesses formatted


def test_cli_report_with_empty_recommendations():
    """CLI report should handle empty recommendations."""
    result = create_mock_result()
    result.recommendations = []

    output = StringIO()
    console = Console(file=output, force_terminal=True, width=120)

    reporter = CLIReporter(console)
    reporter.report(result)

    rendered = output.getvalue()
    assert "Recommendations" in rendered


def test_cli_report_with_empty_graphlets():
    """CLI report should handle empty graphlet data."""
    result = create_mock_result()
    result.graphlet_counts = {}
    result.graphlet_frequencies = {}

    output = StringIO()
    console = Console(file=output, force_terminal=True, width=120)

    reporter = CLIReporter(console)
    reporter.report(result)

    rendered = output.getvalue()
    assert "Graphlet Distribution" in rendered
