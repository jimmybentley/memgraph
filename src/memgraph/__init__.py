"""MemGraph - Memory access pattern analysis using graphlet analysis."""

from pathlib import Path
from datetime import datetime

__version__ = "0.1.0"

# Import key classes for easy access
from memgraph.trace.parser import parse_trace
from memgraph.graph.builder import GraphBuilder
from memgraph.graph.windowing import FixedWindow, SlidingWindow, AdaptiveWindow
from memgraph.graph.coarsening import Granularity
from memgraph.graph.stats import GraphStats
from memgraph.graphlets.enumeration import GraphletEnumerator
from memgraph.graphlets.sampling import GraphletSampler
from memgraph.graphlets.signatures import GraphletSignature
from memgraph.classifier.distance import PatternClassifier
from memgraph.report.result import AnalysisResult

__all__ = [
    "__version__",
    "analyze",
    "parse_trace",
    "GraphBuilder",
    "FixedWindow",
    "SlidingWindow",
    "AdaptiveWindow",
    "Granularity",
    "GraphletEnumerator",
    "GraphletSampler",
    "GraphletSignature",
    "PatternClassifier",
    "AnalysisResult",
]


def analyze(
    trace_path: str | Path,
    window_size: int = 100,
    window_strategy: str = "fixed",
    granularity: str = "cacheline",
    sample: bool = False,
    num_samples: int = 100000,
    metric: str = "cosine",
    trace_format: str | None = None,
) -> AnalysisResult:
    """
    Analyze a memory trace file and classify its access pattern.

    This is the high-level API that runs the full pipeline:
    trace parsing → graph construction → graphlet enumeration → classification.

    Args:
        trace_path: Path to trace file (Lackey, CSV, or native format)
        window_size: Temporal window size for graph construction (default: 100)
        window_strategy: Window strategy - "fixed", "sliding", or "adaptive" (default: "fixed")
        granularity: Address granularity - "byte", "cacheline", or "page" (default: "cacheline")
        sample: Use sampling for graphlet enumeration (default: False, auto-enabled for large graphs)
        num_samples: Number of samples if sampling (default: 100000)
        metric: Distance metric - "cosine", "euclidean", or "manhattan" (default: "cosine")
        trace_format: Trace format - "lackey", "csv", or "native" (default: auto-detect)

    Returns:
        AnalysisResult containing classification, confidence, recommendations, and full statistics

    Raises:
        FileNotFoundError: If trace file doesn't exist
        ValueError: If invalid parameters provided

    Example:
        >>> result = analyze("trace.log")
        >>> print(result.detected_pattern)
        'SEQUENTIAL'
        >>> print(result.confidence)
        0.873
        >>> for rec in result.recommendations:
        ...     print(f"  • {rec}")

    Example with options:
        >>> result = analyze(
        ...     "large_trace.log",
        ...     window_size=200,
        ...     granularity="page",
        ...     sample=True
        ... )
        >>> print(f"Pattern: {result.detected_pattern} ({result.confidence:.1%} confidence)")
    """
    trace_path = Path(trace_path)

    if not trace_path.exists():
        raise FileNotFoundError(f"Trace file not found: {trace_path}")

    # Parse trace
    trace = parse_trace(trace_path, format=trace_format)

    # Select window strategy
    window_strategy = window_strategy.lower()
    if window_strategy == "fixed":
        strategy = FixedWindow(size=window_size)
    elif window_strategy == "sliding":
        strategy = SlidingWindow(size=window_size, step=1)
    elif window_strategy == "adaptive":
        strategy = AdaptiveWindow(base_size=window_size)
    else:
        raise ValueError(
            f"Unknown window strategy: {window_strategy}. "
            f"Must be one of: fixed, sliding, adaptive"
        )

    # Select granularity
    granularity = granularity.lower()
    granularity_map = {
        "byte": Granularity.BYTE,
        "cacheline": Granularity.CACHELINE,
        "page": Granularity.PAGE,
    }
    if granularity not in granularity_map:
        raise ValueError(
            f"Unknown granularity: {granularity}. "
            f"Must be one of: byte, cacheline, page"
        )
    gran = granularity_map[granularity]

    # Build graph
    builder = GraphBuilder(window_strategy=strategy, granularity=gran)
    graph = builder.build(trace)

    # Compute graph stats
    graph_stats = GraphStats.from_graph(graph)

    # Enumerate graphlets (auto-enable sampling for large graphs)
    if sample or graph.number_of_nodes() > 5000:
        sampler = GraphletSampler(graph)
        counts = sampler.sample_count(num_samples=num_samples)
    else:
        enumerator = GraphletEnumerator(graph)
        counts = enumerator.count_all()

    signature = GraphletSignature.from_counts(counts)

    # Classify pattern
    metric = metric.lower()
    if metric not in ("cosine", "euclidean", "manhattan"):
        raise ValueError(
            f"Unknown metric: {metric}. "
            f"Must be one of: cosine, euclidean, manhattan"
        )

    classifier = PatternClassifier(metric=metric)  # type: ignore
    classification = classifier.classify(signature)

    # Build and return result
    return AnalysisResult(
        trace_source=str(trace_path),
        analysis_timestamp=datetime.now(),
        memgraph_version=__version__,
        total_accesses=trace.metadata.total_accesses,
        unique_addresses=trace.metadata.unique_addresses,
        read_count=trace.metadata.read_count,
        write_count=trace.metadata.write_count,
        node_count=graph.number_of_nodes(),
        edge_count=graph.number_of_edges(),
        density=graph_stats.density,
        avg_degree=graph_stats.avg_degree,
        avg_clustering=graph_stats.avg_clustering,
        graphlet_counts=counts.to_dict(),
        graphlet_frequencies=signature.to_dict(),
        detected_pattern=classification.pattern_name,
        confidence=classification.confidence,
        all_similarities=classification.all_similarities,
        recommendations=classification.recommendations,
        window_strategy=window_strategy,
        window_size=window_size,
        granularity=granularity,
    )
