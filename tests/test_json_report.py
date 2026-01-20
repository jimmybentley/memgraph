"""Tests for JSON reporter."""

import json
from pathlib import Path
import tempfile

from memgraph.report.json_report import JSONReporter
from memgraph.report.result import AnalysisResult
from tests.test_result import create_mock_result


def test_json_report_returns_string():
    """JSON reporter should return valid JSON string."""
    result = create_mock_result()
    reporter = JSONReporter()

    json_str = reporter.report(result)

    # Should be valid JSON
    data = json.loads(json_str)
    assert data["trace_source"] == "test_trace.log"
    assert data["detected_pattern"] == "sequential"


def test_json_report_writes_file():
    """JSON reporter should write to file."""
    result = create_mock_result()
    reporter = JSONReporter()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_path = Path(f.name)

    try:
        reporter.report(result, output_path)

        # File should exist and contain valid JSON
        assert output_path.exists()

        data = json.loads(output_path.read_text())
        assert data["trace_source"] == "test_trace.log"
        assert data["detected_pattern"] == "sequential"
    finally:
        output_path.unlink()


def test_json_round_trip():
    """JSON export should be deserializable."""
    result = create_mock_result()
    reporter = JSONReporter()

    json_str = reporter.report(result)
    loaded = AnalysisResult.from_json(json_str)

    assert loaded.detected_pattern == result.detected_pattern
    assert loaded.confidence == result.confidence
    assert loaded.total_accesses == result.total_accesses


def test_json_minimal_report():
    """Minimal JSON report should contain only essential fields."""
    result = create_mock_result()
    reporter = JSONReporter()

    minimal_str = reporter.report_minimal(result)
    data = json.loads(minimal_str)

    assert "pattern" in data
    assert "confidence" in data
    assert "recommendations" in data
    assert data["pattern"] == "sequential"
    assert data["confidence"] == 0.85
    assert len(data["recommendations"]) == 2
