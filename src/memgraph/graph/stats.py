"""Graph statistics computation."""

from dataclasses import dataclass
import networkx as nx  # type: ignore


@dataclass
class GraphStats:
    """Statistics for a temporal adjacency graph."""

    node_count: int
    edge_count: int
    density: float              # edges / possible_edges
    avg_degree: float
    max_degree: int
    connected_components: int
    largest_component_size: int
    avg_clustering: float       # clustering coefficient

    @classmethod
    def from_graph(cls, graph: nx.Graph) -> "GraphStats":
        """Compute statistics from a NetworkX graph.

        Args:
            graph: NetworkX graph to analyze

        Returns:
            GraphStats object with computed metrics
        """
        node_count = graph.number_of_nodes()
        edge_count = graph.number_of_edges()

        # Compute density
        if node_count <= 1:
            density = 0.0
        else:
            max_edges = node_count * (node_count - 1) / 2
            density = edge_count / max_edges if max_edges > 0 else 0.0

        # Compute degree statistics
        if node_count > 0:
            degrees = [degree for _, degree in graph.degree()]
            avg_degree = sum(degrees) / len(degrees)
            max_degree = max(degrees) if degrees else 0
        else:
            avg_degree = 0.0
            max_degree = 0

        # Compute connected components
        components = list(nx.connected_components(graph))
        connected_components = len(components)
        largest_component_size = len(max(components, key=len)) if components else 0

        # Compute average clustering coefficient
        if node_count > 0:
            try:
                avg_clustering = nx.average_clustering(graph)
            except ZeroDivisionError:
                # Can happen for graphs with no triangles
                avg_clustering = 0.0
        else:
            avg_clustering = 0.0

        return cls(
            node_count=node_count,
            edge_count=edge_count,
            density=density,
            avg_degree=avg_degree,
            max_degree=max_degree,
            connected_components=connected_components,
            largest_component_size=largest_component_size,
            avg_clustering=avg_clustering,
        )

    def format_summary(self) -> str:
        """Format statistics as a human-readable summary.

        Returns:
            Multi-line string with formatted statistics
        """
        lines = [
            f"Nodes: {self.node_count:,}",
            f"Edges: {self.edge_count:,}",
            f"Density: {self.density:.4f}",
            f"Avg Degree: {self.avg_degree:.2f}",
            f"Max Degree: {self.max_degree}",
            f"Connected Components: {self.connected_components}",
        ]

        if self.node_count > 0:
            pct = (self.largest_component_size / self.node_count) * 100
            lines.append(
                f"Largest Component: {self.largest_component_size:,} nodes ({pct:.1f}%)"
            )
        else:
            lines.append("Largest Component: 0 nodes")

        lines.append(f"Avg Clustering: {self.avg_clustering:.4f}")

        return "\n".join(lines)
