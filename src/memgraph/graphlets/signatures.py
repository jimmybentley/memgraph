"""Graphlet signatures and distance metrics."""

import numpy as np  # type: ignore
from dataclasses import dataclass
from typing import Literal

from memgraph.graphlets.definitions import GraphletType, GraphletCount


MetricType = Literal["cosine", "euclidean", "manhattan"]


@dataclass
class GraphletSignature:
    """Normalized graphlet frequency distribution.

    This represents a graph's "fingerprint" based on its graphlet frequencies,
    which can be compared to other graphs using various distance metrics.
    """

    vector: np.ndarray  # Shape: (9,) for 9 graphlet types
    graphlet_types: list[GraphletType]

    @classmethod
    def from_counts(cls, counts: GraphletCount) -> "GraphletSignature":
        """Create signature from raw graphlet counts.

        Args:
            counts: GraphletCount object with raw counts

        Returns:
            GraphletSignature with normalized frequency vector
        """
        vec = np.array(counts.to_vector(), dtype=np.float64)

        # L1 normalize (ensure it sums to 1)
        vec_sum = vec.sum()
        if vec_sum > 0:
            vec = vec / vec_sum

        return cls(vector=vec, graphlet_types=list(GraphletType))

    def distance(self, other: "GraphletSignature", metric: MetricType = "cosine") -> float:
        """Compute distance to another signature.

        Args:
            other: Another GraphletSignature to compare to
            metric: Distance metric to use

        Returns:
            Distance value (0 = identical, higher = more different)
        """
        if metric == "cosine":
            # Cosine distance: 1 - cosine_similarity
            dot = np.dot(self.vector, other.vector)
            norm_self = np.linalg.norm(self.vector)
            norm_other = np.linalg.norm(other.vector)
            norm_product = norm_self * norm_other

            if norm_product == 0:
                return 1.0  # Completely different

            cosine_sim = dot / norm_product
            # Clamp to [-1, 1] to handle numerical errors
            cosine_sim = np.clip(cosine_sim, -1.0, 1.0)
            return float(1.0 - cosine_sim)

        elif metric == "euclidean":
            # Euclidean distance
            return float(np.linalg.norm(self.vector - other.vector))

        elif metric == "manhattan":
            # Manhattan (L1) distance
            return float(np.sum(np.abs(self.vector - other.vector)))

        else:
            raise ValueError(
                f"Unknown metric: {metric}. "
                f"Supported: cosine, euclidean, manhattan"
            )

    def similarity(self, other: "GraphletSignature", metric: MetricType = "cosine") -> float:
        """Compute similarity to another signature.

        Args:
            other: Another GraphletSignature to compare to
            metric: Distance metric to use

        Returns:
            Similarity value (1 = identical, 0 = completely different)
        """
        if metric == "cosine":
            # For cosine, similarity is 1 - distance
            return 1.0 - self.distance(other, metric)
        elif metric in ("euclidean", "manhattan"):
            # For unbounded metrics, convert distance to similarity
            # Using exponential decay: sim = exp(-distance)
            dist = self.distance(other, metric)
            return float(np.exp(-dist))
        else:
            raise ValueError(f"Unknown metric: {metric}")

    def to_dict(self) -> dict[str, float]:
        """Convert signature to dictionary for serialization.

        Returns:
            Dictionary mapping graphlet names to frequencies
        """
        return {
            gtype.name: float(self.vector[i])
            for i, gtype in enumerate(self.graphlet_types)
        }

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> "GraphletSignature":
        """Create signature from dictionary.

        Args:
            data: Dictionary mapping graphlet names to frequencies

        Returns:
            GraphletSignature reconstructed from dict
        """
        graphlet_types = list(GraphletType)
        vector = np.zeros(len(graphlet_types), dtype=np.float64)

        for i, gtype in enumerate(graphlet_types):
            if gtype.name in data:
                vector[i] = data[gtype.name]

        return cls(vector=vector, graphlet_types=graphlet_types)
