"""Exact graphlet enumeration algorithms."""

import networkx as nx  # type: ignore
from itertools import combinations
from typing import Dict, Set

from memgraph.graphlets.definitions import GraphletType, GraphletCount


class GraphletEnumerator:
    """Exact graphlet enumeration for small-to-medium graphs.

    This class implements efficient algorithms for counting all connected
    graphlets up to 4 nodes in a graph.
    """

    def __init__(self, graph: nx.Graph):
        """Initialize graphlet enumerator.

        Args:
            graph: NetworkX graph to analyze
        """
        self.graph = graph
        # Pre-compute adjacency for efficiency
        self.adj: Dict[int, Set[int]] = {
            n: set(graph.neighbors(n)) for n in graph.nodes()
        }

    def count_all(self) -> GraphletCount:
        """Count all graphlets in the graph.

        Returns:
            GraphletCount with counts for all graphlet types
        """
        counts = {g: 0 for g in GraphletType}

        # Count 2-node graphlets (edges)
        counts[GraphletType.G0_EDGE] = self.graph.number_of_edges()

        # Count 3-node graphlets
        triangles, paths = self._count_3node()
        counts[GraphletType.G1_PATH] = paths
        counts[GraphletType.G2_TRIANGLE] = triangles

        # Count 4-node graphlets
        four_node_counts = self._count_4node()
        counts.update(four_node_counts)

        return GraphletCount(
            counts=counts,
            total=sum(counts.values()),
            node_count=self.graph.number_of_nodes(),
            edge_count=self.graph.number_of_edges(),
        )

    def _count_3node(self) -> tuple[int, int]:
        """Count triangles and 2-paths.

        Returns:
            Tuple of (triangle_count, path_count)
        """
        # Count triangles using NetworkX's efficient algorithm
        triangle_dict = nx.triangles(self.graph)
        triangles = sum(triangle_dict.values()) // 3

        # Count 2-paths: for each node, count pairs of neighbors that aren't connected
        paths = 0
        for node in self.graph.nodes():
            neighbors = list(self.adj[node])
            # For each pair of neighbors
            for i in range(len(neighbors)):
                for j in range(i + 1, len(neighbors)):
                    n1, n2 = neighbors[i], neighbors[j]
                    # If they're not connected, this forms a 2-path
                    if n2 not in self.adj[n1]:
                        paths += 1

        return triangles, paths

    def _count_4node(self) -> Dict[GraphletType, int]:
        """Count all 4-node graphlets.

        Returns:
            Dictionary mapping 4-node graphlet types to counts
        """
        counts = {
            GraphletType.G3_4PATH: 0,
            GraphletType.G4_STAR: 0,
            GraphletType.G5_CYCLE: 0,
            GraphletType.G6_TAILED_TRIANGLE: 0,
            GraphletType.G7_DIAMOND: 0,
            GraphletType.G8_CLIQUE: 0,
        }

        # Enumerate all 4-node combinations
        nodes = list(self.graph.nodes())
        for node_set in combinations(nodes, 4):
            # Get induced subgraph
            subgraph = self.graph.subgraph(node_set)

            # Skip if not connected
            if not nx.is_connected(subgraph):
                continue

            # Classify the graphlet
            gtype = self._classify_4node(subgraph)
            if gtype is not None:
                counts[gtype] += 1

        return counts

    def _classify_4node(self, subgraph: nx.Graph) -> GraphletType | None:
        """Classify a 4-node connected subgraph.

        Args:
            subgraph: 4-node induced subgraph to classify

        Returns:
            GraphletType or None if not classifiable
        """
        if subgraph.number_of_nodes() != 4:
            return None

        m = subgraph.number_of_edges()

        # Classify by edge count and degree sequence
        degrees = sorted([d for _, d in subgraph.degree()], reverse=True)

        if m == 3:
            # Either 4-path [2,2,1,1] or 3-star [3,1,1,1]
            if degrees[0] == 3:
                return GraphletType.G4_STAR
            else:
                return GraphletType.G3_4PATH

        elif m == 4:
            # Either 4-cycle [2,2,2,2] or tailed-triangle [2,2,2,1]
            if min(degrees) == 2:
                return GraphletType.G5_CYCLE
            else:
                return GraphletType.G6_TAILED_TRIANGLE

        elif m == 5:
            # Diamond (4-cycle with one diagonal)
            return GraphletType.G7_DIAMOND

        elif m == 6:
            # 4-clique (complete graph on 4 nodes)
            return GraphletType.G8_CLIQUE

        return None
