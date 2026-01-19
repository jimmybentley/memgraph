"""Graph builder for constructing temporal adjacency graphs from traces."""

from collections import defaultdict
import networkx as nx  # type: ignore
from typing import Optional

from memgraph.trace.models import Trace, MemoryAccess
from memgraph.graph.windowing import WindowStrategy, FixedWindow
from memgraph.graph.coarsening import Granularity, coarsen_address


class GraphBuilder:
    """Build temporal adjacency graphs from memory traces.

    A temporal adjacency graph represents co-occurrence relationships between
    memory addresses within temporal windows. Nodes are memory addresses (or
    coarsened addresses), and edges connect addresses that appear together
    within a window. Edge weights represent co-occurrence frequency.
    """

    def __init__(
        self,
        window_strategy: Optional[WindowStrategy] = None,
        granularity: Granularity = Granularity.CACHELINE,
        min_edge_weight: int = 1
    ):
        """Initialize graph builder.

        Args:
            window_strategy: Strategy for windowing the trace.
                Defaults to FixedWindow(100).
            granularity: Address coarsening granularity.
                Defaults to CACHELINE (64 bytes).
            min_edge_weight: Minimum edge weight to include in graph.
                Edges with weight < min_edge_weight are filtered out.
        """
        self.window_strategy = window_strategy or FixedWindow(100)
        self.granularity = granularity
        self.min_edge_weight = min_edge_weight

    def build(self, trace: Trace) -> nx.Graph:
        """Build temporal adjacency graph from trace.

        Args:
            trace: Memory trace to convert to graph

        Returns:
            NetworkX undirected graph where:
            - Nodes are (coarsened) memory addresses
            - Edges connect addresses that co-occur within windows
            - Edge weights represent co-occurrence frequency
        """
        # Track edge weights (co-occurrence counts)
        edge_weights: dict[tuple[int, int], int] = defaultdict(int)

        # Process each window
        for window in self.window_strategy.windows(trace.accesses):
            self._process_window(window, edge_weights)

        # Build NetworkX graph
        graph = self._create_graph(edge_weights)

        return graph

    def _process_window(
        self,
        window: list[MemoryAccess],
        edge_weights: dict[tuple[int, int], int]
    ) -> None:
        """Process a single window and update edge weights.

        Args:
            window: Window of memory accesses
            edge_weights: Dictionary tracking edge co-occurrence counts
        """
        # Get unique coarsened addresses in this window
        addresses = set()
        for access in window:
            coarsened = coarsen_address(access.address, self.granularity)
            addresses.add(coarsened)

        # Skip windows with 0 or 1 unique addresses
        if len(addresses) <= 1:
            return

        # Create edges between all pairs in window (clique)
        addresses_list = sorted(addresses)
        for i in range(len(addresses_list)):
            for j in range(i + 1, len(addresses_list)):
                addr1, addr2 = addresses_list[i], addresses_list[j]
                # Store edges with smaller address first (canonical form)
                edge = (addr1, addr2)
                edge_weights[edge] += 1

    def _create_graph(
        self,
        edge_weights: dict[tuple[int, int], int]
    ) -> nx.Graph:
        """Create NetworkX graph from edge weights.

        Args:
            edge_weights: Dictionary of edge -> weight

        Returns:
            NetworkX undirected graph
        """
        graph = nx.Graph()

        # Add edges with weights >= min_edge_weight
        for (node1, node2), weight in edge_weights.items():
            if weight >= self.min_edge_weight:
                graph.add_edge(node1, node2, weight=weight)

        return graph

    def build_with_metadata(self, trace: Trace) -> tuple[nx.Graph, dict]:
        """Build graph and return additional metadata.

        Args:
            trace: Memory trace to convert to graph

        Returns:
            Tuple of (graph, metadata_dict) where metadata includes:
            - window_count: Number of windows processed
            - total_accesses: Total memory accesses in trace
            - granularity: Coarsening granularity used
            - strategy: Window strategy name
        """
        graph = self.build(trace)

        metadata = {
            "window_count": sum(1 for _ in self.window_strategy.windows(trace.accesses)),
            "total_accesses": len(trace.accesses),
            "granularity": self.granularity.name,
            "strategy": self.window_strategy.__class__.__name__,
        }

        return graph, metadata
