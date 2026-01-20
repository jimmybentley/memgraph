"""Tests for visualization modules."""

from pathlib import Path
import tempfile
import networkx as nx

from memgraph.visualization.graph_viz import GraphVisualizer
from memgraph.visualization.charts import ChartGenerator


def test_graph_visualizer_small_graph():
    """GraphVisualizer should handle small graphs."""
    # Create a small graph
    G = nx.Graph()
    G.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 0)])

    visualizer = GraphVisualizer()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.png', delete=False) as f:
        output_path = Path(f.name)

    try:
        visualizer.visualize(G, output_path)
        assert output_path.exists()
    finally:
        if output_path.exists():
            output_path.unlink()


def test_graph_visualizer_large_graph():
    """GraphVisualizer should sample large graphs."""
    # Create a large graph
    G = nx.barabasi_albert_graph(1000, 3, seed=42)

    visualizer = GraphVisualizer(max_nodes=100)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.png', delete=False) as f:
        output_path = Path(f.name)

    try:
        visualizer.visualize(G, output_path)
        assert output_path.exists()
    finally:
        if output_path.exists():
            output_path.unlink()


def test_graph_visualizer_empty_graph():
    """GraphVisualizer should handle empty graphs."""
    G = nx.Graph()

    visualizer = GraphVisualizer()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.png', delete=False) as f:
        output_path = Path(f.name)

    try:
        visualizer.visualize(G, output_path)
        assert output_path.exists()
    finally:
        if output_path.exists():
            output_path.unlink()


def test_chart_generator_graphlet_distribution():
    """ChartGenerator should create graphlet distribution chart."""
    chart_gen = ChartGenerator()

    graphlet_frequencies = {
        "G0": 0.3,
        "G1": 0.5,
        "G2": 0.2,
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.png', delete=False) as f:
        output_path = Path(f.name)

    try:
        chart_gen.graphlet_distribution_chart(graphlet_frequencies, output_path)
        assert output_path.exists()
    finally:
        if output_path.exists():
            output_path.unlink()


def test_chart_generator_pattern_similarity():
    """ChartGenerator should create pattern similarity chart."""
    chart_gen = ChartGenerator()

    similarities = {
        "sequential": 0.9,
        "random": 0.3,
        "strided": 0.5,
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.png', delete=False) as f:
        output_path = Path(f.name)

    try:
        chart_gen.pattern_similarity_chart(similarities, "sequential", output_path)
        assert output_path.exists()
    finally:
        if output_path.exists():
            output_path.unlink()


def test_chart_generator_empty_data():
    """ChartGenerator should handle empty data."""
    chart_gen = ChartGenerator()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.png', delete=False) as f:
        output_path = Path(f.name)

    try:
        chart_gen.graphlet_distribution_chart({}, output_path)
        assert output_path.exists()
    finally:
        if output_path.exists():
            output_path.unlink()
