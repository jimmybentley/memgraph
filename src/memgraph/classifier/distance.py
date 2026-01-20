"""Distance-based pattern classification."""

from dataclasses import dataclass
from typing import Optional

from memgraph.graphlets.signatures import GraphletSignature, MetricType
from memgraph.classifier.patterns import PatternDatabase, ReferencePattern


@dataclass
class ClassificationResult:
    """Result of pattern classification.

    Contains the best-matching pattern, confidence score, and all similarity scores.
    """

    pattern_name: str
    confidence: float  # 0-1, higher is more confident
    similarity: float  # Similarity to best match
    all_similarities: dict[str, float]  # All pattern similarities
    recommendations: list[str]
    characteristics: list[str]

    @property
    def is_confident(self) -> bool:
        """Returns True if classification is confident (>0.7)."""
        return self.confidence > 0.7

    @property
    def is_ambiguous(self) -> bool:
        """Returns True if multiple patterns are similarly close."""
        return self.confidence < 0.5

    def format_report(self) -> str:
        """Format a human-readable classification report.

        Returns:
            Multi-line formatted report string
        """
        lines = []
        lines.append("=" * 60)
        lines.append("PATTERN CLASSIFICATION REPORT")
        lines.append("=" * 60)
        lines.append("")

        # Best match
        lines.append(f"Best Match: {self.pattern_name}")
        lines.append(f"Confidence: {self.confidence:.2%}")
        lines.append(f"Similarity: {self.similarity:.3f}")
        lines.append("")

        # Confidence interpretation
        if self.is_confident:
            lines.append("✓ HIGH CONFIDENCE - strong pattern match")
        elif self.is_ambiguous:
            lines.append("⚠ AMBIGUOUS - multiple patterns are similar")
            lines.append("  (Consider collecting more trace data)")
        else:
            lines.append("→ MODERATE CONFIDENCE - likely match")
        lines.append("")

        # Characteristics
        lines.append("Characteristics:")
        for char in self.characteristics:
            lines.append(f"  • {char}")
        lines.append("")

        # Recommendations
        lines.append("Optimization Recommendations:")
        for rec in self.recommendations:
            lines.append(f"  {rec}")
        lines.append("")

        # All pattern similarities (ranked)
        lines.append("All Pattern Similarities:")
        sorted_patterns = sorted(
            self.all_similarities.items(), key=lambda x: x[1], reverse=True
        )
        for pname, sim in sorted_patterns:
            marker = "→" if pname == self.pattern_name else " "
            lines.append(f"  {marker} {pname:20s} {sim:.3f}")
        lines.append("")

        return "\n".join(lines)


class PatternClassifier:
    """Classify memory access patterns using distance-based matching.

    Compares graphlet signatures to reference patterns and identifies
    the closest match with confidence scoring.
    """

    def __init__(
        self,
        pattern_db: Optional[PatternDatabase] = None,
        metric: MetricType = "cosine",
        confidence_margin: float = 0.15,
    ):
        """Initialize pattern classifier.

        Args:
            pattern_db: PatternDatabase to use (creates default if None)
            metric: Distance metric to use for comparison
            confidence_margin: Margin between best and second-best for high confidence
        """
        self.pattern_db = pattern_db or PatternDatabase()
        self.metric = metric
        self.confidence_margin = confidence_margin

    def classify(self, signature: GraphletSignature) -> ClassificationResult:
        """Classify a graphlet signature.

        Args:
            signature: GraphletSignature to classify

        Returns:
            ClassificationResult with best match and confidence
        """
        patterns = self.pattern_db.all_patterns()

        if not patterns:
            raise ValueError("Pattern database is empty")

        # Compute similarities to all patterns
        similarities = {}
        for pattern in patterns:
            sim = signature.similarity(pattern.signature, metric=self.metric)
            similarities[pattern.name] = sim

        # Find best and second-best matches
        sorted_patterns = sorted(
            similarities.items(), key=lambda x: x[1], reverse=True
        )

        best_name, best_similarity = sorted_patterns[0]
        second_similarity = sorted_patterns[1][1] if len(sorted_patterns) > 1 else 0.0

        # Compute confidence based on margin
        # Confidence is high if best is significantly better than second-best
        margin = best_similarity - second_similarity
        confidence = min(1.0, margin / self.confidence_margin)

        # Get the best-matching pattern details
        best_pattern = self.pattern_db.get_pattern(best_name)
        assert best_pattern is not None  # We know it exists

        return ClassificationResult(
            pattern_name=best_name,
            confidence=confidence,
            similarity=best_similarity,
            all_similarities=similarities,
            recommendations=best_pattern.recommendations,
            characteristics=best_pattern.characteristics,
        )

    def classify_with_threshold(
        self, signature: GraphletSignature, min_similarity: float = 0.6
    ) -> Optional[ClassificationResult]:
        """Classify only if similarity exceeds threshold.

        Args:
            signature: GraphletSignature to classify
            min_similarity: Minimum similarity required for classification

        Returns:
            ClassificationResult if similarity >= threshold, None otherwise
        """
        result = self.classify(signature)

        if result.similarity >= min_similarity:
            return result
        else:
            return None

    def get_top_k_matches(
        self, signature: GraphletSignature, k: int = 3
    ) -> list[tuple[str, float]]:
        """Get top-k most similar patterns.

        Args:
            signature: GraphletSignature to compare
            k: Number of top matches to return

        Returns:
            List of (pattern_name, similarity) tuples, ranked by similarity
        """
        patterns = self.pattern_db.all_patterns()

        similarities = [
            (pattern.name, signature.similarity(pattern.signature, metric=self.metric))
            for pattern in patterns
        ]

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:k]
