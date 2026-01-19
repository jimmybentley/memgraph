"""Tests for graph builder and statistics."""

import pytest
import networkx as nx  # type: ignore
from pathlib import Path

from memgraph.graph.builder import GraphBuilder
from memgraph.graph.windowing import FixedWindow, SlidingWindow
from memgraph.graph.coarsening import Granularity
from memgraph.graph.stats import GraphStats
from memgraph.graph.serialization import save_graph, load_graph
from memgraph.trace.generator import (
    generate_sequential,
    generate_random,
    generate_working_set,
    generate_strided,
    generate_pointer_chase,
)


def test_graph_builder_basic() -> None:
    """Test basic graph building from trace."""
    trace = generate_sequential(n=50, stride=8)
    builder = GraphBuilder(FixedWindow(10), Granularity.CACHELINE)

    graph = builder.build(trace)

    assert isinstance(graph, nx.Graph)
    assert graph.number_of_nodes() > 0
    assert graph.number_of_edges() >= 0


def test_sequential_trace_produces_chain_graph() -> None:
    """Sequential access should produce path-like graph (acceptance criteria)."""
    trace = generate_sequential(100)
    graph = GraphBuilder(FixedWindow(10), Granularity.CACHELINE).build(trace)

    # Most nodes should have degree <= 2 (linear chain pattern)
    degrees = [d for _, d in graph.degree()]
    avg_degree = sum(degrees) / len(degrees) if degrees else 0

    assert avg_degree < 3  # Chain-like graph


def test_working_set_produces_dense_graph() -> None:
    """Working set should produce dense/clique-like graph (acceptance criteria)."""
    trace = generate_working_set(1000, working_set_size=20, seed=42)
    graph = GraphBuilder(FixedWindow(50), Granularity.CACHELINE).build(trace)

    stats = GraphStats.from_graph(graph)

    # High clustering indicates dense connections
    assert stats.avg_clustering > 0.3


def test_coarsening_reduces_nodes() -> None:
    """Cache-line coarsening should reduce unique nodes (acceptance criteria)."""
    trace = generate_sequential(100, stride=8)  # 8-byte stride

    graph_byte = GraphBuilder(FixedWindow(100), Granularity.BYTE).build(trace)
    graph_cl = GraphBuilder(FixedWindow(100), Granularity.CACHELINE).build(trace)

    assert graph_cl.number_of_nodes() < graph_byte.number_of_nodes()


def test_sliding_window_more_edges_than_fixed() -> None:
    """Sliding window captures more temporal relationships (acceptance criteria)."""
    trace = generate_sequential(100)

    g_fixed = GraphBuilder(FixedWindow(20), Granularity.CACHELINE).build(trace)
    g_sliding = GraphBuilder(SlidingWindow(20, step=1), Granularity.CACHELINE).build(trace)

    assert g_sliding.number_of_edges() >= g_fixed.number_of_edges()


def test_graph_builder_empty_trace() -> None:
    """Test graph builder with empty trace."""
    from memgraph.trace.models import Trace, TraceMetadata
    from pathlib import Path

    empty_trace = Trace(
        metadata=TraceMetadata(
            source=Path("<empty>"),
            format="test",
            total_accesses=0,
            unique_addresses=0,
            read_count=0,
            write_count=0,
            address_range=(0, 0)
        ),
        accesses=[]
    )

    builder = GraphBuilder(FixedWindow(10))
    graph = builder.build(empty_trace)

    assert graph.number_of_nodes() == 0
    assert graph.number_of_edges() == 0


def test_graph_builder_single_address() -> None:
    """Test graph with single unique address (no edges)."""
    from memgraph.trace.models import MemoryAccess, Trace

    # Multiple accesses to same address
    accesses = [MemoryAccess("R", 0x1000, 8, i) for i in range(20)]
    trace = Trace.from_accesses(accesses, Path("<test>"), "test")

    builder = GraphBuilder(FixedWindow(10), Granularity.CACHELINE)
    graph = builder.build(trace)

    # Should have 1 node, 0 edges (no self-loops)
    assert graph.number_of_nodes() <= 1
    assert graph.number_of_edges() == 0


def test_graph_builder_edge_weights() -> None:
    """Test that edge weights represent co-occurrence frequency."""
    trace = generate_sequential(50, stride=8)
    builder = GraphBuilder(SlidingWindow(10, step=1), Granularity.CACHELINE)

    graph = builder.build(trace)

    # All edges should have weights
    for _, _, data in graph.edges(data=True):
        assert "weight" in data
        assert data["weight"] >= 1


def test_graph_builder_min_edge_weight() -> None:
    """Test that min_edge_weight filters edges correctly."""
    trace = generate_random(100, seed=42)

    builder_min1 = GraphBuilder(FixedWindow(20), min_edge_weight=1)
    builder_min5 = GraphBuilder(FixedWindow(20), min_edge_weight=5)

    graph1 = builder_min1.build(trace)
    graph5 = builder_min5.build(trace)

    # Higher min weight should have fewer edges
    assert graph5.number_of_edges() <= graph1.number_of_edges()


def test_graph_builder_no_self_loops() -> None:
    """Test that graphs don't contain self-loops."""
    trace = generate_sequential(50)
    builder = GraphBuilder(FixedWindow(10))

    graph = builder.build(trace)

    # Check no self-loops
    for node in graph.nodes():
        assert not graph.has_edge(node, node)


def test_graph_builder_with_metadata() -> None:
    """Test build_with_metadata returns correct metadata."""
    trace = generate_sequential(100)
    builder = GraphBuilder(FixedWindow(20), Granularity.CACHELINE)

    graph, metadata = builder.build_with_metadata(trace)

    assert isinstance(graph, nx.Graph)
    assert isinstance(metadata, dict)
    assert "window_count" in metadata
    assert "total_accesses" in metadata
    assert "granularity" in metadata
    assert "strategy" in metadata

    assert metadata["total_accesses"] == 100
    assert metadata["granularity"] == "CACHELINE"
    assert metadata["strategy"] == "FixedWindow"


def test_different_patterns_produce_different_graphs() -> None:
    """Different synthetic patterns produce measurably different structures (acceptance criteria)."""
    n = 200

    # Generate traces with different patterns
    seq_trace = generate_sequential(n)
    rand_trace = generate_random(n, seed=42)
    ws_trace = generate_working_set(n, working_set_size=20, seed=42)

    # Build graphs
    builder = GraphBuilder(FixedWindow(50), Granularity.CACHELINE)
    seq_graph = builder.build(seq_trace)
    rand_graph = builder.build(rand_trace)
    ws_graph = builder.build(ws_trace)

    # Compute statistics
    seq_stats = GraphStats.from_graph(seq_graph)
    rand_stats = GraphStats.from_graph(rand_graph)
    ws_stats = GraphStats.from_graph(ws_graph)

    # Different patterns should produce measurably different graphs
    # Working set should have higher density (more edges due to reuse)
    assert ws_stats.density > seq_stats.density

    # Working set should have higher average degree
    assert ws_stats.avg_degree > seq_stats.avg_degree


def test_graph_stats_empty_graph() -> None:
    """Test GraphStats with empty graph."""
    graph = nx.Graph()
    stats = GraphStats.from_graph(graph)

    assert stats.node_count == 0
    assert stats.edge_count == 0
    assert stats.density == 0.0
    assert stats.avg_degree == 0.0
    assert stats.max_degree == 0
    assert stats.connected_components == 0
    assert stats.largest_component_size == 0
    assert stats.avg_clustering == 0.0


def test_graph_stats_single_node() -> None:
    """Test GraphStats with single node."""
    graph = nx.Graph()
    graph.add_node(1)

    stats = GraphStats.from_graph(graph)

    assert stats.node_count == 1
    assert stats.edge_count == 0
    assert stats.density == 0.0
    assert stats.avg_degree == 0.0
    assert stats.connected_components == 1
    assert stats.largest_component_size == 1


def test_graph_stats_complete_graph() -> None:
    """Test GraphStats with complete graph."""
    graph = nx.complete_graph(5)
    stats = GraphStats.from_graph(graph)

    assert stats.node_count == 5
    assert stats.edge_count == 10  # n(n-1)/2 = 5*4/2 = 10
    assert stats.density == 1.0  # Complete graph has density 1
    assert stats.avg_degree == 4.0  # Each node connected to 4 others
    assert stats.max_degree == 4
    assert stats.connected_components == 1
    assert stats.largest_component_size == 5
    assert stats.avg_clustering == 1.0  # Complete graph has clustering 1


def test_graph_stats_disconnected_components() -> None:
    """Test GraphStats with disconnected components."""
    graph = nx.Graph()

    # Component 1: 3 nodes
    graph.add_edges_from([(1, 2), (2, 3)])

    # Component 2: 2 nodes
    graph.add_edge(4, 5)

    # Component 3: 1 node
    graph.add_node(6)

    stats = GraphStats.from_graph(graph)

    assert stats.node_count == 6
    assert stats.edge_count == 3
    assert stats.connected_components == 3
    assert stats.largest_component_size == 3


def test_graph_stats_format_summary() -> None:
    """Test that format_summary produces readable output."""
    graph = nx.complete_graph(5)
    stats = GraphStats.from_graph(graph)

    summary = stats.format_summary()

    assert isinstance(summary, str)
    assert "Nodes:" in summary
    assert "Edges:" in summary
    assert "Density:" in summary
    assert "Avg Degree:" in summary


def test_save_and_load_graph_pickle(temp_dir: Path) -> None:
    """Test saving and loading graph in pickle format (acceptance criteria)."""
    trace = generate_sequential(50)
    builder = GraphBuilder(FixedWindow(10))
    original_graph = builder.build(trace)

    # Save graph
    graph_file = temp_dir / "test_graph.pkl"
    save_graph(original_graph, graph_file, format="pickle")

    assert graph_file.exists()

    # Load graph
    loaded_graph = load_graph(graph_file, format="pickle")

    assert loaded_graph.number_of_nodes() == original_graph.number_of_nodes()
    assert loaded_graph.number_of_edges() == original_graph.number_of_edges()


def test_save_and_load_graph_graphml(temp_dir: Path) -> None:
    """Test saving and loading graph in GraphML format (acceptance criteria)."""
    trace = generate_sequential(30)
    builder = GraphBuilder(FixedWindow(10))
    original_graph = builder.build(trace)

    # Save graph
    graph_file = temp_dir / "test_graph.graphml"
    save_graph(original_graph, graph_file, format="graphml")

    assert graph_file.exists()

    # Load graph
    loaded_graph = load_graph(graph_file, format="graphml")

    assert loaded_graph.number_of_nodes() == original_graph.number_of_nodes()
    assert loaded_graph.number_of_edges() == original_graph.number_of_edges()


def test_save_graph_invalid_format(temp_dir: Path) -> None:
    """Test that invalid format raises error."""
    graph = nx.Graph()
    graph.add_edge(1, 2)

    graph_file = temp_dir / "test.graph"

    with pytest.raises(ValueError, match="Unsupported format"):
        save_graph(graph, graph_file, format="invalid")


def test_load_graph_nonexistent_file() -> None:
    """Test that loading nonexistent file raises error."""
    with pytest.raises(FileNotFoundError):
        load_graph(Path("/nonexistent/file.pkl"))


def test_load_graph_auto_detect_format(temp_dir: Path) -> None:
    """Test that load_graph can auto-detect format from extension."""
    trace = generate_sequential(20)
    builder = GraphBuilder(FixedWindow(10))
    original_graph = builder.build(trace)

    # Save with .pkl extension
    graph_file = temp_dir / "test.pkl"
    save_graph(original_graph, graph_file, format="pickle")

    # Load without specifying format
    loaded_graph = load_graph(graph_file)

    assert loaded_graph.number_of_nodes() == original_graph.number_of_nodes()


def test_graph_patterns_measurably_different() -> None:
    """Test that all 5 patterns produce different graph structures."""
    n = 150

    traces = {
        "sequential": generate_sequential(n),
        "random": generate_random(n, seed=42),
        "strided": generate_strided(n),
        "pointer_chase": generate_pointer_chase(n, seed=42),
        "working_set": generate_working_set(n, seed=42),
    }

    builder = GraphBuilder(FixedWindow(30), Granularity.CACHELINE)
    stats_by_pattern = {}

    for pattern, trace in traces.items():
        graph = builder.build(trace)
        stats = GraphStats.from_graph(graph)
        stats_by_pattern[pattern] = stats

    # Check that at least some patterns have different clustering
    clusterings = [s.avg_clustering for s in stats_by_pattern.values()]
    assert len(set(clusterings)) > 1  # Not all the same

    # Working set should have highest density (most reuse)
    ws_stats = stats_by_pattern["working_set"]
    seq_stats = stats_by_pattern["sequential"]

    assert ws_stats.density > seq_stats.density


def test_graph_builder_all_granularities() -> None:
    """Test that builder works with all granularity levels."""
    # Use larger stride to span multiple pages (4KB each)
    trace = generate_sequential(100, stride=4096)

    for granularity in [Granularity.BYTE, Granularity.CACHELINE, Granularity.PAGE]:
        builder = GraphBuilder(FixedWindow(10), granularity)
        graph = builder.build(trace)

        assert graph.number_of_nodes() > 0
