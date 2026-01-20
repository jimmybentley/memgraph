"""Tests for AnalysisResult dataclass."""

from datetime import datetime
import pytest

from memgraph.report.result import AnalysisResult


def create_mock_result() -> AnalysisResult:
    """Create a mock AnalysisResult for testing."""
    return AnalysisResult(
        trace_source="test_trace.log",
        analysis_timestamp=datetime(2024, 1, 1, 12, 0, 0),
        memgraph_version="0.1.0",
        total_accesses=1000,
        unique_addresses=100,
        read_count=700,
        write_count=300,
        node_count=50,
        edge_count=80,
        density=0.0653,
        avg_degree=3.2,
        avg_clustering=0.45,
        graphlet_counts={"G0": 10, "G1": 20, "G2": 15},
        graphlet_frequencies={"G0": 0.22, "G1": 0.44, "G2": 0.33},
        detected_pattern="sequential",
        confidence=0.85,
        all_similarities={
            "sequential": 0.95,
            "random": 0.25,
            "strided": 0.50,
        },
        recommendations=[
            "Use prefetching to reduce memory latency",
            "Consider increasing cache line size",
        ],
        window_strategy="fixed",
        window_size=100,
        granularity="cacheline",
    )


def test_to_dict():
    """Test converting AnalysisResult to dict."""
    result = create_mock_result()
    d = result.to_dict()

    assert d["trace_source"] == "test_trace.log"
    assert d["total_accesses"] == 1000
    assert d["detected_pattern"] == "sequential"
    assert d["analysis_timestamp"] == "2024-01-01T12:00:00"


def test_to_json():
    """Test JSON serialization."""
    result = create_mock_result()
    json_str = result.to_json()

    assert "test_trace.log" in json_str
    assert "sequential" in json_str
    assert "2024-01-01T12:00:00" in json_str


def test_from_json():
    """Test JSON deserialization."""
    result = create_mock_result()
    json_str = result.to_json()

    loaded = AnalysisResult.from_json(json_str)

    assert loaded.trace_source == result.trace_source
    assert loaded.total_accesses == result.total_accesses
    assert loaded.detected_pattern == result.detected_pattern
    assert loaded.confidence == result.confidence
    assert loaded.analysis_timestamp == result.analysis_timestamp


def test_json_round_trip():
    """Test JSON serialization round-trip."""
    result = create_mock_result()
    json_str = result.to_json()
    loaded = AnalysisResult.from_json(json_str)

    assert loaded.trace_source == result.trace_source
    assert loaded.memgraph_version == result.memgraph_version
    assert loaded.total_accesses == result.total_accesses
    assert loaded.unique_addresses == result.unique_addresses
    assert loaded.read_count == result.read_count
    assert loaded.write_count == result.write_count
    assert loaded.node_count == result.node_count
    assert loaded.edge_count == result.edge_count
    assert loaded.density == result.density
    assert loaded.avg_degree == result.avg_degree
    assert loaded.avg_clustering == result.avg_clustering
    assert loaded.detected_pattern == result.detected_pattern
    assert loaded.confidence == result.confidence
    assert loaded.window_strategy == result.window_strategy
    assert loaded.window_size == result.window_size
    assert loaded.granularity == result.granularity
