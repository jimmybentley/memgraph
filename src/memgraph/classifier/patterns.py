"""Reference pattern definitions for classification."""

from dataclasses import dataclass
import numpy as np

from memgraph.graphlets.signatures import GraphletSignature
from memgraph.graphlets.definitions import GraphletType


@dataclass
class ReferencePattern:
    """A known memory access pattern with its graphlet signature."""

    name: str
    description: str
    signature: GraphletSignature
    characteristics: list[str]
    recommendations: list[str]


class PatternDatabase:
    """Database of reference patterns for classification.

    Contains canonical graphlet signatures for known memory access patterns,
    along with their characteristics and optimization recommendations.
    """

    def __init__(self) -> None:
        """Initialize pattern database with built-in patterns."""
        self.patterns: dict[str, ReferencePattern] = {}
        self._load_builtin_patterns()

    def _load_builtin_patterns(self) -> None:
        """Load built-in reference patterns."""

        # SEQUENTIAL: Linear traversal (array iteration)
        # Dominated by edges and 2-paths (chain structure)
        self.add_pattern(
            ReferencePattern(
                name="SEQUENTIAL",
                description="Linear sequential access (array traversal, streaming)",
                signature=GraphletSignature(
                    vector=np.array(
                        [
                            0.40,  # G0: edge - high (chain has many edges)
                            0.35,  # G1: 2-path - high (consecutive triplets)
                            0.02,  # G2: triangle - very low
                            0.15,  # G3: 4-path - moderate
                            0.03,  # G4: 3-star - low
                            0.02,  # G5: 4-cycle - very low
                            0.02,  # G6: tailed-triangle - very low
                            0.01,  # G7: diamond - very low
                            0.00,  # G8: 4-clique - none
                        ],
                        dtype=np.float64,
                    ),
                    graphlet_types=list(GraphletType),
                ),
                characteristics=[
                    "High edge and 2-path frequency",
                    "Very low triangle/clique content",
                    "Linear chain structure",
                ],
                recommendations=[
                    "✓ Hardware prefetching should be effective",
                    "✓ Consider software prefetch hints for large strides",
                    "✓ Good candidate for streaming stores if write-heavy",
                    "✓ Loop tiling may help if working set exceeds cache",
                ],
            )
        )

        # RANDOM: Uniform random access
        # Low density, mostly isolated edges
        self.add_pattern(
            ReferencePattern(
                name="RANDOM",
                description="Uniform random access (hash tables, pointer-heavy code)",
                signature=GraphletSignature(
                    vector=np.array(
                        [
                            0.70,  # G0: edge - very high (sparse connections)
                            0.15,  # G1: 2-path - low
                            0.02,  # G2: triangle - very low
                            0.08,  # G3: 4-path - low
                            0.03,  # G4: 3-star - low
                            0.01,  # G5: 4-cycle - very low
                            0.01,  # G6: tailed-triangle - very low
                            0.00,  # G7: diamond - none
                            0.00,  # G8: 4-clique - none
                        ],
                        dtype=np.float64,
                    ),
                    graphlet_types=list(GraphletType),
                ),
                characteristics=[
                    "Edge-dominated (sparse graph)",
                    "Very low clustering",
                    "High unique address count relative to accesses",
                ],
                recommendations=[
                    "⚠ Prefetching will be ineffective",
                    "→ Reduce working set size if possible",
                    "→ Consider cache-oblivious data structures",
                    "→ Batch accesses to improve spatial locality",
                    "→ Profile for TLB misses (may be page-bound)",
                ],
            )
        )

        # STRIDED: Regular stride pattern
        # Similar to sequential but may have gaps
        self.add_pattern(
            ReferencePattern(
                name="STRIDED",
                description="Regular strided access (column-major, struct fields)",
                signature=GraphletSignature(
                    vector=np.array(
                        [
                            0.45,  # G0: edge - high
                            0.30,  # G1: 2-path - moderate-high
                            0.03,  # G2: triangle - low
                            0.12,  # G3: 4-path - moderate
                            0.05,  # G4: 3-star - low
                            0.02,  # G5: 4-cycle - low
                            0.02,  # G6: tailed-triangle - low
                            0.01,  # G7: diamond - very low
                            0.00,  # G8: 4-clique - none
                        ],
                        dtype=np.float64,
                    ),
                    graphlet_types=list(GraphletType),
                ),
                characteristics=[
                    "Similar to sequential but with periodic structure",
                    "Moderate path content",
                    "Consistent stride in address differences",
                ],
                recommendations=[
                    "→ Align data structures to cache line boundaries",
                    "→ Consider array-of-structs → struct-of-arrays transform",
                    "→ Use streaming prefetch with stride hint",
                    "→ Loop interchange may improve cache utilization",
                ],
            )
        )

        # POINTER_CHASE: Linked structure traversal
        # Star patterns from hub nodes (e.g., list head)
        self.add_pattern(
            ReferencePattern(
                name="POINTER_CHASE",
                description="Linked structure traversal (lists, trees, graphs)",
                signature=GraphletSignature(
                    vector=np.array(
                        [
                            0.28,  # G0: edge - lower than sequential
                            0.18,  # G1: 2-path - lower than sequential
                            0.08,  # G2: triangle - higher (back-edges)
                            0.12,  # G3: 4-path - moderate
                            0.20,  # G4: 3-star - strongly elevated (hub nodes)
                            0.05,  # G5: 4-cycle - low
                            0.06,  # G6: tailed-triangle - moderate
                            0.03,  # G7: diamond - low
                            0.00,  # G8: 4-clique - none
                        ],
                        dtype=np.float64,
                    ),
                    graphlet_types=list(GraphletType),
                ),
                characteristics=[
                    "Elevated 3-star content (hub/spoke pattern)",
                    "Tree-like structure",
                    "Low clustering coefficient",
                ],
                recommendations=[
                    "⚠ Hardware prefetching ineffective",
                    "→ Linearize: convert to array-based representation",
                    "→ Consider B-tree instead of binary tree",
                    "→ Use software prefetch if next pointer is predictable",
                    "→ Cache-oblivious layout (van Emde Boas)",
                ],
            )
        )

        # WORKING_SET: Dense reuse within small set
        # High triangle/clique content
        self.add_pattern(
            ReferencePattern(
                name="WORKING_SET",
                description="Dense reuse within working set (hot loops, caches)",
                signature=GraphletSignature(
                    vector=np.array(
                        [
                            0.15,  # G0: edge - low (edges part of larger structures)
                            0.15,  # G1: 2-path - low
                            0.20,  # G2: triangle - high
                            0.10,  # G3: 4-path - low
                            0.08,  # G4: 3-star - moderate
                            0.10,  # G5: 4-cycle - moderate
                            0.10,  # G6: tailed-triangle - moderate
                            0.08,  # G7: diamond - moderate
                            0.04,  # G8: 4-clique - present
                        ],
                        dtype=np.float64,
                    ),
                    graphlet_types=list(GraphletType),
                ),
                characteristics=[
                    "High triangle and clique content",
                    "High clustering coefficient",
                    "Small number of unique addresses",
                ],
                recommendations=[
                    "✓ Excellent cache behavior - working set fits",
                    "✓ Consider pinning hot data in L1/L2",
                    "→ Focus optimization on computation, not memory",
                    "→ Verify alignment for SIMD if applicable",
                ],
            )
        )

        # PRODUCER_CONSUMER: Two interleaved streams
        self.add_pattern(
            ReferencePattern(
                name="PRODUCER_CONSUMER",
                description="Two interleaved access streams (pipelines, queues)",
                signature=GraphletSignature(
                    vector=np.array(
                        [
                            0.30,  # G0: edge - moderate
                            0.25,  # G1: 2-path - moderate
                            0.05,  # G2: triangle - low
                            0.20,  # G3: 4-path - elevated
                            0.10,  # G4: 3-star - moderate
                            0.05,  # G5: 4-cycle - low-moderate
                            0.03,  # G6: tailed-triangle - low
                            0.02,  # G7: diamond - low
                            0.00,  # G8: 4-clique - none
                        ],
                        dtype=np.float64,
                    ),
                    graphlet_types=list(GraphletType),
                ),
                characteristics=[
                    "Bipartite-like structure",
                    "Two distinct address regions",
                    "Alternating access pattern",
                ],
                recommendations=[
                    "→ Separate streams into distinct cache regions",
                    "→ Use non-temporal stores for producer if consumer is delayed",
                    "→ Consider double-buffering",
                    "→ Align producer/consumer boundaries to cache lines",
                ],
            )
        )

    def add_pattern(self, pattern: ReferencePattern) -> None:
        """Add a pattern to the database.

        Args:
            pattern: ReferencePattern to add
        """
        self.patterns[pattern.name] = pattern

    def get_pattern(self, name: str) -> ReferencePattern | None:
        """Retrieve a pattern by name.

        Args:
            name: Pattern name

        Returns:
            ReferencePattern if found, None otherwise
        """
        return self.patterns.get(name)

    def all_patterns(self) -> list[ReferencePattern]:
        """Return all patterns.

        Returns:
            List of all ReferencePattern objects
        """
        return list(self.patterns.values())

    def pattern_names(self) -> list[str]:
        """Return all pattern names.

        Returns:
            List of pattern name strings
        """
        return list(self.patterns.keys())
