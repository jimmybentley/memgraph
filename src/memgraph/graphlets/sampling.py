"""Sampling-based graphlet approximation for large graphs."""

import random
import networkx as nx  # type: ignore
from typing import Set, Optional

from memgraph.graphlets.definitions import GraphletType, GraphletCount


class GraphletSampler:
    """Approximate graphlet counting via random sampling.

    For large graphs where exact enumeration is too expensive, this class
    uses sampling to estimate graphlet frequencies.
    """

    def __init__(self, graph: nx.Graph, seed: int = 42):
        """Initialize graphlet sampler.

        Args:
            graph: NetworkX graph to analyze
            seed: Random seed for reproducibility
        """
        self.graph = graph
        self.rng = random.Random(seed)
        self.adj = {n: set(graph.neighbors(n)) for n in graph.nodes()}

    def sample_count(
        self, num_samples: int = 100000, graphlet_size: int = 4
    ) -> GraphletCount:
        """Estimate graphlet counts via random sampling.

        Args:
            num_samples: Number of samples to take
            graphlet_size: Size of graphlets to sample (3 or 4)

        Returns:
            GraphletCount with estimated counts
        """
        if graphlet_size not in (3, 4):
            raise ValueError("graphlet_size must be 3 or 4")

        sample_counts = {g: 0 for g in GraphletType}
        edges = list(self.graph.edges())

        if not edges:
            return GraphletCount(
                counts=sample_counts,
                total=0,
                node_count=self.graph.number_of_nodes(),
                edge_count=0,
            )

        successful_samples = 0

        for _ in range(num_samples):
            # Sample a random edge
            u, v = self.rng.choice(edges)

            # Try to extend to desired size
            if graphlet_size == 3:
                subgraph_nodes = self._extend_to_3node(u, v)
            else:
                subgraph_nodes = self._extend_to_4node(u, v)

            if subgraph_nodes is None:
                continue

            # Classify the induced subgraph
            gtype = self._classify_subgraph(subgraph_nodes)
            if gtype is not None:
                sample_counts[gtype] += 1
                successful_samples += 1

        # Scale counts based on sampling
        return self._scale_counts(sample_counts, successful_samples)

    def _extend_to_3node(self, u: int, v: int) -> Optional[Set[int]]:
        """Extend an edge to a 3-node connected subgraph.

        Args:
            u, v: Edge endpoints

        Returns:
            Set of 3 nodes forming connected subgraph, or None
        """
        # Get neighbors of both endpoints
        candidates = (self.adj[u] | self.adj[v]) - {u, v}

        if not candidates:
            return None

        # Pick a random third node
        w = self.rng.choice(list(candidates))
        return {u, v, w}

    def _extend_to_4node(self, u: int, v: int) -> Optional[Set[int]]:
        """Extend an edge to a 4-node connected subgraph.

        Args:
            u, v: Edge endpoints

        Returns:
            Set of 4 nodes forming connected subgraph, or None
        """
        nodes = {u, v}
        candidates = (self.adj[u] | self.adj[v]) - nodes

        if not candidates:
            return None

        # Add a third node
        w = self.rng.choice(list(candidates))
        nodes.add(w)

        # Find candidates for fourth node (connected to at least one existing node)
        candidates = (self.adj[u] | self.adj[v] | self.adj[w]) - nodes

        if not candidates:
            return None

        # Add fourth node
        x = self.rng.choice(list(candidates))
        nodes.add(x)

        # Check if resulting subgraph is connected
        subgraph = self.graph.subgraph(nodes)
        if not nx.is_connected(subgraph):
            return None

        return nodes

    def _classify_subgraph(self, nodes: Set[int]) -> Optional[GraphletType]:
        """Classify a sampled subgraph by graphlet type.

        Args:
            nodes: Set of node IDs forming the subgraph

        Returns:
            GraphletType or None if not classifiable
        """
        subgraph = self.graph.subgraph(nodes)
        n = len(nodes)
        m = subgraph.number_of_edges()

        if n == 2:
            return GraphletType.G0_EDGE

        elif n == 3:
            if m == 3:
                return GraphletType.G2_TRIANGLE
            elif m == 2:
                return GraphletType.G1_PATH
            else:
                return None

        elif n == 4:
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
                return GraphletType.G7_DIAMOND

            elif m == 6:
                return GraphletType.G8_CLIQUE

        return None

    def _scale_counts(
        self, sample_counts: dict[GraphletType, int], num_samples: int
    ) -> GraphletCount:
        """Scale sample counts to estimate total counts.

        Args:
            sample_counts: Raw counts from sampling
            num_samples: Number of successful samples

        Returns:
            GraphletCount with scaled estimates
        """
        # For now, use raw sample counts (they represent frequencies)
        # In a more sophisticated version, we'd estimate total counts
        # based on the sampling probability

        return GraphletCount(
            counts=sample_counts,
            total=sum(sample_counts.values()),
            node_count=self.graph.number_of_nodes(),
            edge_count=self.graph.number_of_edges(),
        )
