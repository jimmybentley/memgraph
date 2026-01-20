"""Tests for graphlet signatures and distance metrics."""

import pytest
import numpy as np
import networkx as nx  # type: ignore

from memgraph.graphlets.definitions import GraphletType
from memgraph.graphlets.enumeration import GraphletEnumerator
from memgraph.graphlets.signatures import GraphletSignature


def test_signature_from_counts() -> None:
    """Test signature creation from counts."""
    g = nx.complete_graph(4)
    counts = GraphletEnumerator(g).count_all()

    sig = GraphletSignature.from_counts(counts)

    assert isinstance(sig.vector, np.ndarray)
    assert len(sig.vector) == 9
    assert len(sig.graphlet_types) == 9


def test_signature_normalized() -> None:
    """Test that signature vector is normalized."""
    g = nx.complete_graph(4)
    counts = GraphletEnumerator(g).count_all()

    sig = GraphletSignature.from_counts(counts)

    # Vector should sum to 1.0
    assert abs(sig.vector.sum() - 1.0) < 0.001


def test_signature_distance_cosine() -> None:
    """Test cosine distance calculation (acceptance criteria)."""
    g1 = nx.complete_graph(4)
    g2 = nx.complete_graph(4)

    counts1 = GraphletEnumerator(g1).count_all()
    counts2 = GraphletEnumerator(g2).count_all()

    sig1 = GraphletSignature.from_counts(counts1)
    sig2 = GraphletSignature.from_counts(counts2)

    # Identical graphs should have distance ~0
    distance = sig1.distance(sig2, metric="cosine")
    assert distance < 0.001


def test_signature_distance_euclidean() -> None:
    """Test Euclidean distance calculation (acceptance criteria)."""
    g1 = nx.complete_graph(4)
    g2 = nx.complete_graph(4)

    counts1 = GraphletEnumerator(g1).count_all()
    counts2 = GraphletEnumerator(g2).count_all()

    sig1 = GraphletSignature.from_counts(counts1)
    sig2 = GraphletSignature.from_counts(counts2)

    # Identical graphs should have distance ~0
    distance = sig1.distance(sig2, metric="euclidean")
    assert distance < 0.001


def test_signature_distance_manhattan() -> None:
    """Test Manhattan distance calculation (acceptance criteria)."""
    g1 = nx.complete_graph(4)
    g2 = nx.complete_graph(4)

    counts1 = GraphletEnumerator(g1).count_all()
    counts2 = GraphletEnumerator(g2).count_all()

    sig1 = GraphletSignature.from_counts(counts1)
    sig2 = GraphletSignature.from_counts(counts2)

    # Identical graphs should have distance ~0
    distance = sig1.distance(sig2, metric="manhattan")
    assert distance < 0.001


def test_signature_similarity() -> None:
    """Test similarity calculation."""
    g1 = nx.complete_graph(4)
    g2 = nx.complete_graph(4)

    counts1 = GraphletEnumerator(g1).count_all()
    counts2 = GraphletEnumerator(g2).count_all()

    sig1 = GraphletSignature.from_counts(counts1)
    sig2 = GraphletSignature.from_counts(counts2)

    # Identical graphs should have similarity ~1
    similarity = sig1.similarity(sig2, metric="cosine")
    assert similarity > 0.999


def test_signature_different_graphs() -> None:
    """Test that different graphs have different signatures."""
    g_complete = nx.complete_graph(10)
    g_path = nx.path_graph(20)

    counts_complete = GraphletEnumerator(g_complete).count_all()
    counts_path = GraphletEnumerator(g_path).count_all()

    sig_complete = GraphletSignature.from_counts(counts_complete)
    sig_path = GraphletSignature.from_counts(counts_path)

    # Different graphs should have measurable distance
    distance = sig_complete.distance(sig_path, metric="cosine")
    assert distance > 0.1

    similarity = sig_complete.similarity(sig_path, metric="cosine")
    assert similarity < 0.9


def test_signature_to_dict() -> None:
    """Test conversion to dictionary."""
    g = nx.complete_graph(4)
    counts = GraphletEnumerator(g).count_all()

    sig = GraphletSignature.from_counts(counts)
    sig_dict = sig.to_dict()

    assert isinstance(sig_dict, dict)
    assert len(sig_dict) == 9

    # All values should be floats
    for key, value in sig_dict.items():
        assert isinstance(key, str)
        assert isinstance(value, float)


def test_signature_from_dict() -> None:
    """Test creation from dictionary."""
    g = nx.complete_graph(4)
    counts = GraphletEnumerator(g).count_all()

    sig1 = GraphletSignature.from_counts(counts)
    sig_dict = sig1.to_dict()

    # Recreate from dict
    sig2 = GraphletSignature.from_dict(sig_dict)

    # Should be identical
    assert np.allclose(sig1.vector, sig2.vector)


def test_signature_round_trip() -> None:
    """Test that to_dict/from_dict round-trip preserves signature."""
    g = nx.cycle_graph(10)
    counts = GraphletEnumerator(g).count_all()

    sig1 = GraphletSignature.from_counts(counts)

    # Round trip
    sig_dict = sig1.to_dict()
    sig2 = GraphletSignature.from_dict(sig_dict)

    # Should be identical
    distance = sig1.distance(sig2, metric="cosine")
    assert distance < 0.0001


def test_signature_invalid_metric() -> None:
    """Test that invalid metric raises error."""
    g = nx.complete_graph(4)
    counts = GraphletEnumerator(g).count_all()

    sig = GraphletSignature.from_counts(counts)

    with pytest.raises(ValueError, match="Unknown metric"):
        sig.distance(sig, metric="invalid")  # type: ignore


def test_signature_zero_vector() -> None:
    """Test handling of zero vectors."""
    # Create empty signature
    zero_vec = np.zeros(9)
    sig1 = GraphletSignature(vector=zero_vec, graphlet_types=list(GraphletType))

    # Another signature
    g = nx.complete_graph(4)
    counts = GraphletEnumerator(g).count_all()
    sig2 = GraphletSignature.from_counts(counts)

    # Distance should be well-defined
    distance = sig1.distance(sig2, metric="cosine")
    assert 0 <= distance <= 2.0


def test_sequential_vs_working_set_measurably_different() -> None:
    """Sequential vs working-set traces produce measurably different signatures (acceptance criteria)."""
    from memgraph.trace.generator import generate_sequential, generate_working_set
    from memgraph.graph.builder import GraphBuilder
    from memgraph.graph.windowing import FixedWindow

    # Generate traces
    seq_trace = generate_sequential(500)
    ws_trace = generate_working_set(500, working_set_size=30, seed=42)

    # Build graphs
    builder = GraphBuilder(FixedWindow(50))
    seq_graph = builder.build(seq_trace)
    ws_graph = builder.build(ws_trace)

    # Enumerate graphlets
    seq_counts = GraphletEnumerator(seq_graph).count_all()
    ws_counts = GraphletEnumerator(ws_graph).count_all()

    # Create signatures
    seq_sig = GraphletSignature.from_counts(seq_counts)
    ws_sig = GraphletSignature.from_counts(ws_counts)

    # Signatures should be measurably different
    distance = seq_sig.distance(ws_sig, metric="cosine")
    assert distance > 0.05  # Should be noticeably different

    similarity = seq_sig.similarity(ws_sig, metric="cosine")
    assert similarity < 0.95  # Not too similar


def test_signature_cosine_distance_bounds() -> None:
    """Test that cosine distance is bounded."""
    g1 = nx.complete_graph(5)
    g2 = nx.path_graph(10)

    counts1 = GraphletEnumerator(g1).count_all()
    counts2 = GraphletEnumerator(g2).count_all()

    sig1 = GraphletSignature.from_counts(counts1)
    sig2 = GraphletSignature.from_counts(counts2)

    distance = sig1.distance(sig2, metric="cosine")

    # Cosine distance should be in [0, 2]
    assert 0 <= distance <= 2.0


def test_signature_similarity_reflexive() -> None:
    """Test that similarity(A, A) = 1.0."""
    g = nx.cycle_graph(8)
    counts = GraphletEnumerator(g).count_all()
    sig = GraphletSignature.from_counts(counts)

    similarity = sig.similarity(sig, metric="cosine")
    assert abs(similarity - 1.0) < 0.001


def test_signature_similarity_symmetric() -> None:
    """Test that similarity(A, B) = similarity(B, A)."""
    g1 = nx.complete_graph(6)
    g2 = nx.cycle_graph(12)

    counts1 = GraphletEnumerator(g1).count_all()
    counts2 = GraphletEnumerator(g2).count_all()

    sig1 = GraphletSignature.from_counts(counts1)
    sig2 = GraphletSignature.from_counts(counts2)

    sim_12 = sig1.similarity(sig2, metric="cosine")
    sim_21 = sig2.similarity(sig1, metric="cosine")

    assert abs(sim_12 - sim_21) < 0.001


def test_signature_all_metrics_agree_on_identical() -> None:
    """Test that all metrics give low distance for identical signatures."""
    g = nx.complete_graph(5)
    counts = GraphletEnumerator(g).count_all()

    sig1 = GraphletSignature.from_counts(counts)
    sig2 = GraphletSignature.from_counts(counts)

    for metric in ["cosine", "euclidean", "manhattan"]:
        distance = sig1.distance(sig2, metric=metric)  # type: ignore
        assert distance < 0.001, f"{metric} distance should be ~0 for identical"


def test_signature_vector_non_negative() -> None:
    """Test that signature vectors have non-negative components."""
    g = nx.barabasi_albert_graph(100, 3, seed=42)
    counts = GraphletEnumerator(g).count_all()

    sig = GraphletSignature.from_counts(counts)

    # All components should be non-negative
    assert np.all(sig.vector >= 0)
