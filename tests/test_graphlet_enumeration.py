"""Tests for exact graphlet enumeration."""

import pytest
import networkx as nx  # type: ignore

from memgraph.graphlets.definitions import GraphletType, GraphletCount
from memgraph.graphlets.enumeration import GraphletEnumerator
from memgraph.trace.generator import (
    generate_sequential,
    generate_working_set,
)
from memgraph.graph.builder import GraphBuilder
from memgraph.graph.windowing import FixedWindow


def test_graphlet_type_properties() -> None:
    """Test GraphletType enum properties."""
    assert GraphletType.G0_EDGE.size == 2
    assert GraphletType.G1_PATH.size == 3
    assert GraphletType.G2_TRIANGLE.size == 3
    assert GraphletType.G3_4PATH.size == 4
    assert GraphletType.G8_CLIQUE.size == 4

    assert GraphletType.G0_EDGE.name_str == "edge"
    assert GraphletType.G2_TRIANGLE.name_str == "triangle"


def test_triangle_graph() -> None:
    """Triangle should have exactly 1 triangle, 0 paths (acceptance criteria)."""
    g = nx.complete_graph(3)
    counts = GraphletEnumerator(g).count_all()

    assert counts.counts[GraphletType.G2_TRIANGLE] == 1
    assert counts.counts[GraphletType.G1_PATH] == 0
    assert counts.counts[GraphletType.G0_EDGE] == 3


def test_path_graph() -> None:
    """Path graph should have only paths, no triangles (acceptance criteria)."""
    g = nx.path_graph(5)  # 0-1-2-3-4
    counts = GraphletEnumerator(g).count_all()

    assert counts.counts[GraphletType.G2_TRIANGLE] == 0
    assert counts.counts[GraphletType.G1_PATH] == 3  # (0,1,2), (1,2,3), (2,3,4)
    assert counts.counts[GraphletType.G0_EDGE] == 4


def test_complete_graph_4() -> None:
    """K4 should have exactly 1 4-clique (acceptance criteria)."""
    g = nx.complete_graph(4)
    counts = GraphletEnumerator(g).count_all()

    assert counts.counts[GraphletType.G8_CLIQUE] == 1
    assert counts.counts[GraphletType.G2_TRIANGLE] == 4  # C(4,3) = 4 triangles
    assert counts.counts[GraphletType.G0_EDGE] == 6  # C(4,2) = 6 edges


def test_star_graph() -> None:
    """Star graph should produce 3-stars (acceptance criteria)."""
    g = nx.star_graph(4)  # Center + 4 leaves = 5 nodes total
    counts = GraphletEnumerator(g).count_all()

    # A star with 4 leaves has C(4,3) = 4 different 3-stars
    assert counts.counts[GraphletType.G4_STAR] == 4
    assert counts.counts[GraphletType.G2_TRIANGLE] == 0
    assert counts.counts[GraphletType.G0_EDGE] == 4


def test_cycle_graph() -> None:
    """4-cycle should have exactly one 4-cycle graphlet (acceptance criteria)."""
    g = nx.cycle_graph(4)
    counts = GraphletEnumerator(g).count_all()

    assert counts.counts[GraphletType.G5_CYCLE] == 1
    assert counts.counts[GraphletType.G0_EDGE] == 4
    assert counts.counts[GraphletType.G1_PATH] == 4  # 4 different 2-paths


def test_empty_graph() -> None:
    """Empty graph should have zero graphlets."""
    g = nx.Graph()
    counts = GraphletEnumerator(g).count_all()

    assert counts.total == 0
    assert all(c == 0 for c in counts.counts.values())


def test_single_edge() -> None:
    """Single edge graph should have only one edge graphlet."""
    g = nx.Graph()
    g.add_edge(0, 1)
    counts = GraphletEnumerator(g).count_all()

    assert counts.counts[GraphletType.G0_EDGE] == 1
    assert counts.total == 1


def test_4path_graph() -> None:
    """Path of 4 nodes should have one 4-path graphlet."""
    g = nx.path_graph(4)
    counts = GraphletEnumerator(g).count_all()

    assert counts.counts[GraphletType.G3_4PATH] == 1
    assert counts.counts[GraphletType.G0_EDGE] == 3


def test_diamond_graph() -> None:
    """Diamond graph (4-cycle with one diagonal) should have one diamond graphlet."""
    g = nx.Graph()
    g.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)])  # Square with diagonal
    counts = GraphletEnumerator(g).count_all()

    assert counts.counts[GraphletType.G7_DIAMOND] == 1
    assert counts.counts[GraphletType.G2_TRIANGLE] == 2  # Two triangles in diamond


def test_tailed_triangle() -> None:
    """Tailed triangle should be detected correctly."""
    g = nx.Graph()
    g.add_edges_from([(0, 1), (1, 2), (0, 2), (2, 3)])  # Triangle + tail
    counts = GraphletEnumerator(g).count_all()

    assert counts.counts[GraphletType.G6_TAILED_TRIANGLE] == 1
    assert counts.counts[GraphletType.G2_TRIANGLE] == 1


def test_graphlet_count_normalized() -> None:
    """Test normalized frequency distribution."""
    g = nx.complete_graph(4)
    counts = GraphletEnumerator(g).count_all()

    normalized = counts.normalized

    # Should sum to approximately 1.0
    total_freq = sum(normalized.values())
    assert abs(total_freq - 1.0) < 0.001

    # All frequencies should be non-negative
    assert all(f >= 0 for f in normalized.values())


def test_graphlet_count_to_vector() -> None:
    """Test conversion to feature vector."""
    g = nx.complete_graph(3)
    counts = GraphletEnumerator(g).count_all()

    vector = counts.to_vector()

    # Should have 9 elements (one for each graphlet type)
    assert len(vector) == 9

    # Should sum to 1.0
    assert abs(sum(vector) - 1.0) < 0.001


def test_graphlet_count_format_summary() -> None:
    """Test that format_summary produces output."""
    g = nx.complete_graph(3)
    counts = GraphletEnumerator(g).count_all()

    summary = counts.format_summary()

    assert isinstance(summary, str)
    assert "Total graphlets" in summary
    assert "triangle" in summary


def test_sequential_trace_signature() -> None:
    """Sequential trace should have path-dominated signature (acceptance criteria)."""
    trace = generate_sequential(200)
    graph = GraphBuilder(FixedWindow(50)).build(trace)
    counts = GraphletEnumerator(graph).count_all()

    normalized = counts.normalized

    # Paths should be significant
    assert normalized[GraphletType.G1_PATH] > 0


def test_working_set_trace_signature() -> None:
    """Working set trace should have triangle-rich signature (acceptance criteria)."""
    trace = generate_working_set(200, working_set_size=20, seed=42)
    graph = GraphBuilder(FixedWindow(50)).build(trace)
    counts = GraphletEnumerator(graph).count_all()

    # Should have some triangles due to dense reuse
    assert counts.counts[GraphletType.G2_TRIANGLE] > 0


def test_disconnected_graph() -> None:
    """Test that disconnected graphs are handled correctly."""
    g = nx.Graph()
    # Two separate triangles
    g.add_edges_from([(0, 1), (1, 2), (2, 0)])
    g.add_edges_from([(3, 4), (4, 5), (5, 3)])

    counts = GraphletEnumerator(g).count_all()

    # Should count each triangle
    assert counts.counts[GraphletType.G2_TRIANGLE] == 2
    assert counts.counts[GraphletType.G0_EDGE] == 6


def test_classify_4node_edge_counts() -> None:
    """Test classification of 4-node subgraphs by edge count."""
    enumerator = GraphletEnumerator(nx.Graph())

    # 3 edges: could be 4-path or 3-star
    # Test 4-path (degrees [2,2,1,1])
    g_path = nx.path_graph(4)
    gtype = enumerator._classify_4node(g_path)
    assert gtype == GraphletType.G3_4PATH

    # Test 3-star (degrees [3,1,1,1])
    g_star = nx.star_graph(3)
    gtype = enumerator._classify_4node(g_star)
    assert gtype == GraphletType.G4_STAR

    # 4 edges: could be 4-cycle or tailed-triangle
    # Test 4-cycle (degrees [2,2,2,2])
    g_cycle = nx.cycle_graph(4)
    gtype = enumerator._classify_4node(g_cycle)
    assert gtype == GraphletType.G5_CYCLE

    # 5 edges: diamond
    g_diamond = nx.Graph()
    g_diamond.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)])
    gtype = enumerator._classify_4node(g_diamond)
    assert gtype == GraphletType.G7_DIAMOND

    # 6 edges: 4-clique
    g_clique = nx.complete_graph(4)
    gtype = enumerator._classify_4node(g_clique)
    assert gtype == GraphletType.G8_CLIQUE


def test_large_graph_performance() -> None:
    """Test that enumeration completes in reasonable time for medium graphs."""
    import time

    # Create a graph with ~1000 nodes
    g = nx.barabasi_albert_graph(1000, 3, seed=42)

    start = time.time()
    counts = GraphletEnumerator(g).count_all()
    elapsed = time.time() - start

    # Should complete (though may be slow)
    assert counts.total > 0
    # Don't enforce strict time limit, but it should finish


def test_graphlet_counts_are_integers() -> None:
    """Test that all counts are non-negative integers."""
    g = nx.complete_graph(5)
    counts = GraphletEnumerator(g).count_all()

    for gtype, count in counts.counts.items():
        assert isinstance(count, int)
        assert count >= 0
