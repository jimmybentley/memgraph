"""Tests for pattern database and reference patterns."""

import pytest
import numpy as np

from memgraph.classifier.patterns import PatternDatabase, ReferencePattern
from memgraph.graphlets.signatures import GraphletSignature
from memgraph.graphlets.definitions import GraphletType


def test_pattern_database_initialization() -> None:
    """Test that PatternDatabase initializes with built-in patterns."""
    db = PatternDatabase()

    # Should have 6 built-in patterns
    assert len(db.patterns) == 6

    # Verify all expected patterns exist
    expected = {
        "SEQUENTIAL",
        "RANDOM",
        "STRIDED",
        "POINTER_CHASE",
        "WORKING_SET",
        "PRODUCER_CONSUMER",
    }
    assert set(db.pattern_names()) == expected


def test_pattern_database_get_pattern() -> None:
    """Test retrieving patterns by name."""
    db = PatternDatabase()

    # Should retrieve existing pattern
    pattern = db.get_pattern("SEQUENTIAL")
    assert pattern is not None
    assert pattern.name == "SEQUENTIAL"
    assert isinstance(pattern.signature, GraphletSignature)

    # Should return None for non-existent pattern
    assert db.get_pattern("NONEXISTENT") is None


def test_pattern_database_add_pattern() -> None:
    """Test adding custom patterns to database."""
    db = PatternDatabase()
    initial_count = len(db.patterns)

    # Add custom pattern
    custom_pattern = ReferencePattern(
        name="CUSTOM",
        description="Custom test pattern",
        signature=GraphletSignature(
            vector=np.array([0.1] * 9, dtype=np.float64),
            graphlet_types=list(GraphletType),
        ),
        characteristics=["Test characteristic"],
        recommendations=["Test recommendation"],
    )

    db.add_pattern(custom_pattern)

    # Should have one more pattern
    assert len(db.patterns) == initial_count + 1
    assert "CUSTOM" in db.pattern_names()

    # Should be retrievable
    retrieved = db.get_pattern("CUSTOM")
    assert retrieved is not None
    assert retrieved.name == "CUSTOM"


def test_pattern_database_all_patterns() -> None:
    """Test retrieving all patterns."""
    db = PatternDatabase()

    patterns = db.all_patterns()

    # Should return list of ReferencePattern objects
    assert isinstance(patterns, list)
    assert len(patterns) == 6
    assert all(isinstance(p, ReferencePattern) for p in patterns)


def test_reference_pattern_structure() -> None:
    """Test ReferencePattern dataclass structure."""
    db = PatternDatabase()
    pattern = db.get_pattern("SEQUENTIAL")

    assert pattern is not None
    assert isinstance(pattern.name, str)
    assert isinstance(pattern.description, str)
    assert isinstance(pattern.signature, GraphletSignature)
    assert isinstance(pattern.characteristics, list)
    assert isinstance(pattern.recommendations, list)
    assert len(pattern.characteristics) > 0
    assert len(pattern.recommendations) > 0


def test_sequential_pattern_signature() -> None:
    """Test SEQUENTIAL pattern has expected signature characteristics."""
    db = PatternDatabase()
    pattern = db.get_pattern("SEQUENTIAL")

    assert pattern is not None
    vec = pattern.signature.vector

    # Sequential should be edge/path dominated
    assert vec[GraphletType.G0_EDGE.value] > 0.3  # High edges
    assert vec[GraphletType.G1_PATH.value] > 0.2  # High 2-paths
    assert vec[GraphletType.G2_TRIANGLE.value] < 0.05  # Low triangles


def test_random_pattern_signature() -> None:
    """Test RANDOM pattern has expected signature characteristics."""
    db = PatternDatabase()
    pattern = db.get_pattern("RANDOM")

    assert pattern is not None
    vec = pattern.signature.vector

    # Random should be edge-dominated with low clustering
    assert vec[GraphletType.G0_EDGE.value] > 0.6  # Very high edges
    assert vec[GraphletType.G2_TRIANGLE.value] < 0.05  # Very low triangles


def test_working_set_pattern_signature() -> None:
    """Test WORKING_SET pattern has expected signature characteristics."""
    db = PatternDatabase()
    pattern = db.get_pattern("WORKING_SET")

    assert pattern is not None
    vec = pattern.signature.vector

    # Working set should be triangle/clique rich
    assert vec[GraphletType.G2_TRIANGLE.value] > 0.15  # High triangles
    assert vec[GraphletType.G8_CLIQUE.value] > 0.0  # Some cliques


def test_pointer_chase_pattern_signature() -> None:
    """Test POINTER_CHASE pattern has expected signature characteristics."""
    db = PatternDatabase()
    pattern = db.get_pattern("POINTER_CHASE")

    assert pattern is not None
    vec = pattern.signature.vector

    # Pointer chase should have elevated star content
    assert vec[GraphletType.G4_STAR.value] > 0.1  # Elevated 3-stars


def test_strided_pattern_signature() -> None:
    """Test STRIDED pattern has expected signature characteristics."""
    db = PatternDatabase()
    pattern = db.get_pattern("STRIDED")

    assert pattern is not None
    vec = pattern.signature.vector

    # Strided should be similar to sequential but with periodic structure
    assert vec[GraphletType.G0_EDGE.value] > 0.3  # High edges
    assert vec[GraphletType.G1_PATH.value] > 0.2  # Moderate-high paths


def test_producer_consumer_pattern_signature() -> None:
    """Test PRODUCER_CONSUMER pattern has expected signature characteristics."""
    db = PatternDatabase()
    pattern = db.get_pattern("PRODUCER_CONSUMER")

    assert pattern is not None
    vec = pattern.signature.vector

    # Producer-consumer should have elevated 4-paths
    assert vec[GraphletType.G3_4PATH.value] > 0.15  # Elevated 4-paths


def test_all_signatures_normalized() -> None:
    """Test that all reference pattern signatures are L1-normalized."""
    db = PatternDatabase()

    for pattern in db.all_patterns():
        vec_sum = pattern.signature.vector.sum()
        # Should sum to approximately 1.0
        assert abs(vec_sum - 1.0) < 0.001, f"{pattern.name} not normalized: {vec_sum}"


def test_all_signatures_have_correct_length() -> None:
    """Test that all signatures have 9 elements (one per graphlet type)."""
    db = PatternDatabase()

    for pattern in db.all_patterns():
        assert len(pattern.signature.vector) == 9
        assert len(pattern.signature.graphlet_types) == 9


def test_patterns_have_recommendations() -> None:
    """Test that all patterns have actionable recommendations."""
    db = PatternDatabase()

    for pattern in db.all_patterns():
        # Should have at least one recommendation
        assert len(pattern.recommendations) > 0

        # Recommendations should be strings
        assert all(isinstance(rec, str) for rec in pattern.recommendations)


def test_patterns_have_characteristics() -> None:
    """Test that all patterns have characteristics."""
    db = PatternDatabase()

    for pattern in db.all_patterns():
        # Should have at least one characteristic
        assert len(pattern.characteristics) > 0

        # Characteristics should be strings
        assert all(isinstance(char, str) for char in pattern.characteristics)


def test_patterns_are_distinguishable() -> None:
    """Test that patterns have distinct signatures."""
    db = PatternDatabase()
    patterns = db.all_patterns()

    # Some patterns are intentionally similar (e.g., SEQUENTIAL and STRIDED)
    # so we allow high similarity for specific pairs
    allowed_similar_pairs = {("SEQUENTIAL", "STRIDED"), ("STRIDED", "SEQUENTIAL")}

    # Compare all pairs of patterns
    for i, p1 in enumerate(patterns):
        for p2 in patterns[i + 1 :]:
            # Signatures should be reasonably different (cosine similarity < 0.97)
            # This ensures patterns are distinguishable while allowing for natural similarity
            similarity = p1.signature.similarity(p2.signature, metric="cosine")

            # Allow some pairs to be more similar
            if (p1.name, p2.name) in allowed_similar_pairs:
                continue

            assert (
                similarity < 0.97
            ), f"{p1.name} and {p2.name} are too similar: {similarity:.3f}"


def test_pattern_signatures_non_negative() -> None:
    """Test that all signature values are non-negative."""
    db = PatternDatabase()

    for pattern in db.all_patterns():
        assert all(v >= 0 for v in pattern.signature.vector), f"{pattern.name} has negative values"
