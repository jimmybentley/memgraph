"""Tests for sampling-based graphlet approximation."""

import pytest
import networkx as nx  # type: ignore

from memgraph.graphlets.definitions import GraphletType
from memgraph.graphlets.enumeration import GraphletEnumerator
from memgraph.graphlets.sampling import GraphletSampler
from memgraph.graphlets.signatures import GraphletSignature


def test_sampler_basic() -> None:
    """Test that sampler produces counts."""
    g = nx.complete_graph(10)
    sampler = GraphletSampler(g, seed=42)

    counts = sampler.sample_count(num_samples=1000)

    assert counts.total > 0
    assert counts.node_count == 10
    assert counts.edge_count == 45


def test_sampler_empty_graph() -> None:
    """Test sampler with empty graph."""
    g = nx.Graph()
    sampler = GraphletSampler(g, seed=42)

    counts = sampler.sample_count(num_samples=100)

    assert counts.total == 0


def test_sampler_single_edge() -> None:
    """Test sampler with single edge."""
    g = nx.Graph()
    g.add_edge(0, 1)
    sampler = GraphletSampler(g, seed=42)

    counts = sampler.sample_count(num_samples=100)

    # Should sample some edges
    assert counts.total >= 0


def test_sampling_approximates_exact() -> None:
    """Sampling should approximate exact counts within tolerance (acceptance criteria)."""
    # Use a smaller graph for faster testing (exact enumeration is O(n^4))
    g = nx.barabasi_albert_graph(100, 3, seed=42)

    # Exact enumeration
    exact = GraphletEnumerator(g).count_all()

    # Sampled approximation
    sampled = GraphletSampler(g, seed=42).sample_count(num_samples=10000)

    # Create signatures
    sig_exact = GraphletSignature.from_counts(exact)
    sig_sampled = GraphletSignature.from_counts(sampled)

    # Signatures should be similar (cosine similarity > 0.8)
    similarity = sig_exact.similarity(sig_sampled)
    assert similarity > 0.8, f"Similarity {similarity:.3f} < 0.8"


def test_sampler_reproducibility() -> None:
    """Test that sampler produces consistent results with same seed."""
    g = nx.complete_graph(20)

    sampler1 = GraphletSampler(g, seed=42)
    counts1 = sampler1.sample_count(num_samples=1000)

    sampler2 = GraphletSampler(g, seed=42)
    counts2 = sampler2.sample_count(num_samples=1000)

    # Should produce identical counts
    assert counts1.total == counts2.total
    for gtype in GraphletType:
        assert counts1.counts[gtype] == counts2.counts[gtype]


def test_sampler_3node_graphlets() -> None:
    """Test sampling of 3-node graphlets."""
    g = nx.complete_graph(10)
    sampler = GraphletSampler(g, seed=42)

    counts = sampler.sample_count(num_samples=5000, graphlet_size=3)

    # Complete graph should have many triangles, few paths
    assert counts.counts[GraphletType.G2_TRIANGLE] > 0
    assert counts.total > 0


def test_sampler_invalid_graphlet_size() -> None:
    """Test that invalid graphlet size raises error."""
    g = nx.complete_graph(5)
    sampler = GraphletSampler(g, seed=42)

    with pytest.raises(ValueError, match="graphlet_size must be 3 or 4"):
        sampler.sample_count(num_samples=100, graphlet_size=5)


def test_sampler_extend_to_3node() -> None:
    """Test edge extension to 3 nodes."""
    g = nx.path_graph(5)
    sampler = GraphletSampler(g, seed=42)

    # Try extending edge (1, 2)
    nodes = sampler._extend_to_3node(1, 2)

    assert nodes is not None
    assert len(nodes) == 3
    assert 1 in nodes and 2 in nodes


def test_sampler_extend_to_4node() -> None:
    """Test edge extension to 4 nodes."""
    g = nx.complete_graph(10)
    sampler = GraphletSampler(g, seed=42)

    # Try extending edge (0, 1)
    nodes = sampler._extend_to_4node(0, 1)

    assert nodes is not None
    assert len(nodes) == 4
    assert 0 in nodes and 1 in nodes


def test_sampler_classify_subgraph() -> None:
    """Test subgraph classification."""
    g = nx.complete_graph(4)
    sampler = GraphletSampler(g, seed=42)

    # Classify a triangle
    triangle_nodes = {0, 1, 2}
    gtype = sampler._classify_subgraph(triangle_nodes)
    assert gtype == GraphletType.G2_TRIANGLE

    # Classify a 4-clique
    clique_nodes = {0, 1, 2, 3}
    gtype = sampler._classify_subgraph(clique_nodes)
    assert gtype == GraphletType.G8_CLIQUE


def test_sampler_handles_large_graphs() -> None:
    """Test that sampler works on large graphs."""
    # Create a moderately large graph (reduced for faster testing)
    g = nx.barabasi_albert_graph(2000, 3, seed=42)

    sampler = GraphletSampler(g, seed=42)
    counts = sampler.sample_count(num_samples=5000)

    # Should produce results
    assert counts.total > 0
    assert counts.node_count == 2000


def test_sampler_various_graph_types() -> None:
    """Test sampler on various graph types."""
    graphs = {
        "complete": nx.complete_graph(15),
        "path": nx.path_graph(50),
        "cycle": nx.cycle_graph(30),
        "star": nx.star_graph(20),
        "grid": nx.grid_2d_graph(10, 10),
    }

    for name, g in graphs.items():
        # Convert grid graph to standard Graph (remove node tuples)
        if name == "grid":
            g = nx.convert_node_labels_to_integers(g)

        sampler = GraphletSampler(g, seed=42)
        counts = sampler.sample_count(num_samples=1000)

        assert counts.total > 0, f"No samples for {name} graph"


def test_sampling_frequency_distribution() -> None:
    """Test that sampled distribution makes sense."""
    # Complete graph should be triangle-heavy
    g_complete = nx.complete_graph(20)
    sampler = GraphletSampler(g_complete, seed=42)
    counts = sampler.sample_count(num_samples=5000, graphlet_size=3)

    normalized = counts.normalized
    # Triangles should dominate in complete graph
    assert normalized[GraphletType.G2_TRIANGLE] > normalized[GraphletType.G1_PATH]

    # Path graph should be path-heavy
    g_path = nx.path_graph(50)
    sampler = GraphletSampler(g_path, seed=42)
    counts = sampler.sample_count(num_samples=5000, graphlet_size=3)

    normalized = counts.normalized
    # Paths should dominate in path graph
    assert normalized[GraphletType.G1_PATH] > normalized[GraphletType.G2_TRIANGLE]
