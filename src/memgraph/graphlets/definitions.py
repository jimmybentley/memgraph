"""Graphlet type definitions and data structures."""

from dataclasses import dataclass
from enum import Enum


class GraphletType(Enum):
    """All connected graphlets up to 4 nodes.

    Graphlet patterns:
    - 2-node: 1 type (edge)
    - 3-node: 2 types (path, triangle)
    - 4-node: 6 types (path, star, cycle, tailed-triangle, diamond, clique)
    """

    # 2-node graphlets
    G0_EDGE = 0

    # 3-node graphlets
    G1_PATH = 1
    G2_TRIANGLE = 2

    # 4-node graphlets
    G3_4PATH = 3
    G4_STAR = 4
    G5_CYCLE = 5
    G6_TAILED_TRIANGLE = 6
    G7_DIAMOND = 7
    G8_CLIQUE = 8

    @property
    def name_str(self) -> str:
        """Get human-readable name for this graphlet type."""
        names = {
            GraphletType.G0_EDGE: "edge",
            GraphletType.G1_PATH: "2-path",
            GraphletType.G2_TRIANGLE: "triangle",
            GraphletType.G3_4PATH: "4-path",
            GraphletType.G4_STAR: "3-star",
            GraphletType.G5_CYCLE: "4-cycle",
            GraphletType.G6_TAILED_TRIANGLE: "tailed-triangle",
            GraphletType.G7_DIAMOND: "diamond",
            GraphletType.G8_CLIQUE: "4-clique",
        }
        return names[self]

    @property
    def size(self) -> int:
        """Get the number of nodes in this graphlet."""
        if self == GraphletType.G0_EDGE:
            return 2
        elif self in (GraphletType.G1_PATH, GraphletType.G2_TRIANGLE):
            return 3
        else:
            return 4


@dataclass
class GraphletCount:
    """Container for graphlet enumeration results."""

    counts: dict[GraphletType, int]
    total: int
    node_count: int
    edge_count: int

    @property
    def normalized(self) -> dict[GraphletType, float]:
        """Return frequency distribution (normalized to sum to 1).

        Returns:
            Dictionary mapping graphlet types to their frequencies
        """
        if self.total == 0:
            return {g: 0.0 for g in GraphletType}
        return {g: c / self.total for g, c in self.counts.items()}

    def to_vector(self) -> list[float]:
        """Return as fixed-order feature vector.

        Returns:
            List of 9 frequencies in GraphletType enum order
        """
        normalized = self.normalized
        return [normalized[g] for g in GraphletType]

    def to_dict(self) -> dict[str, int]:
        """Return graphlet counts as a dictionary with string keys.

        Returns:
            Dictionary mapping graphlet names to counts
        """
        return {g.name: self.counts[g] for g in GraphletType}

    def format_summary(self) -> str:
        """Format graphlet counts as a human-readable summary.

        Returns:
            Multi-line string with formatted counts and frequencies
        """
        lines = [f"Total graphlets: {self.total:,}"]
        lines.append(f"Graph: {self.node_count:,} nodes, {self.edge_count:,} edges")
        lines.append("")
        lines.append("Graphlet counts:")

        normalized = self.normalized

        for gtype in GraphletType:
            count = self.counts.get(gtype, 0)
            freq = normalized.get(gtype, 0.0)
            name = gtype.name_str
            lines.append(f"  {gtype.name:20} ({name:20}): {count:10,}  ({freq:7.2%})")

        # Find dominant graphlet
        if self.total > 0:
            max_type = max(self.counts.items(), key=lambda x: x[1])
            lines.append("")
            lines.append(f"Dominant: {max_type[0].name_str} ({max_type[1]:,} occurrences)")

        return "\n".join(lines)
