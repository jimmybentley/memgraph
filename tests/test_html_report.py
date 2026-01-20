"""Tests for HTML reporter."""

from pathlib import Path
import tempfile

from memgraph.report.html_report import HTMLReporter
from tests.test_result import create_mock_result


def test_html_report_generates():
    """HTML report should generate valid HTML."""
    result = create_mock_result()
    reporter = HTMLReporter()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        output_path = Path(f.name)

    try:
        reporter.report(result, output_path)

        # File should exist
        assert output_path.exists()

        # Read content
        html = output_path.read_text()

        # Check for HTML structure
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html

        # Check for key content
        assert "MemGraph Analysis Report" in html
        assert result.detected_pattern in html
        assert result.trace_source in html

        # Check for base64 encoded images
        assert "data:image/png;base64," in html

    finally:
        output_path.unlink()


def test_html_report_with_empty_data():
    """HTML report should handle empty graphlet data."""
    result = create_mock_result()
    result.graphlet_counts = {}
    result.graphlet_frequencies = {}
    result.all_similarities = {}

    reporter = HTMLReporter()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        output_path = Path(f.name)

    try:
        reporter.report(result, output_path)

        assert output_path.exists()
        html = output_path.read_text()

        # Should still generate HTML even with empty data
        assert "<!DOCTYPE html>" in html
        assert "MemGraph Analysis Report" in html

    finally:
        output_path.unlink()


def test_html_report_confidence_styling():
    """HTML report should apply correct confidence styling."""
    result = create_mock_result()
    reporter = HTMLReporter()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        output_path = Path(f.name)

    try:
        reporter.report(result, output_path)
        html = output_path.read_text()

        # High confidence (>0.7) should use confidence-high class
        assert "confidence-high" in html

    finally:
        output_path.unlink()
