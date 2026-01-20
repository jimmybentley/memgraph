"""Graph visualization module for MemGraph."""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import networkx as nx
from pathlib import Path

from memgraph.visualization.colors import NODE_COLOR, EDGE_COLOR


class GraphVisualizer:
    """Visualize memory access graphs."""

    def __init__(self, max_nodes: int = 500):
        self.max_nodes = max_nodes

    def visualize(
        self,
        graph: nx.Graph,
        output_path: Path | None = None,
        title: str = "Memory Access Graph"
    ) -> None:
        """Visualize graph (sampled if too large)."""
        # Sample if too large
        if graph.number_of_nodes() > self.max_nodes:
            nodes = list(graph.nodes())[:self.max_nodes]
            graph = graph.subgraph(nodes)
            title = f"{title} (sampled {self.max_nodes} nodes)"

        fig, ax = plt.subplots(figsize=(12, 12))

        if graph.number_of_nodes() > 0:
            # Layout - use spring layout for all graphs
            # For larger graphs, reduce iterations for speed
            iterations = 50 if graph.number_of_nodes() < 100 else 20
            pos = nx.spring_layout(graph, seed=42, k=2/max(1, len(graph.nodes())**0.5), iterations=iterations)

            # Draw
            nx.draw_networkx_edges(graph, pos, alpha=0.3, edge_color=EDGE_COLOR, ax=ax)
            nx.draw_networkx_nodes(graph, pos, node_size=20, node_color=NODE_COLOR, ax=ax)

            ax.set_title(title)
            ax.axis('off')
        else:
            ax.text(0.5, 0.5, 'Empty graph',
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title(title)
            ax.axis('off')

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
        else:
            plt.show()

        plt.close(fig)

    def visualize_with_labels(
        self,
        graph: nx.Graph,
        output_path: Path | None = None,
        title: str = "Memory Access Graph"
    ) -> None:
        """Visualize graph with node labels (only for small graphs)."""
        if graph.number_of_nodes() > 50:
            raise ValueError("Graph too large for labeled visualization (max 50 nodes)")

        fig, ax = plt.subplots(figsize=(12, 12))

        if graph.number_of_nodes() > 0:
            # Layout
            pos = nx.spring_layout(graph, seed=42)

            # Draw
            nx.draw_networkx_edges(graph, pos, alpha=0.3, edge_color=EDGE_COLOR, ax=ax)
            nx.draw_networkx_nodes(graph, pos, node_size=300, node_color=NODE_COLOR, ax=ax)
            nx.draw_networkx_labels(graph, pos, font_size=8, font_color='white', ax=ax)

            ax.set_title(title)
            ax.axis('off')
        else:
            ax.text(0.5, 0.5, 'Empty graph',
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title(title)
            ax.axis('off')

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
        else:
            plt.show()

        plt.close(fig)
