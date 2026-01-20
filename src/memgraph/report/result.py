"""Analysis result container for MemGraph."""

from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import json


@dataclass
class AnalysisResult:
    """Complete analysis output - input to all reporters."""

    # Metadata
    trace_source: str
    analysis_timestamp: datetime
    memgraph_version: str

    # Trace stats
    total_accesses: int
    unique_addresses: int
    read_count: int
    write_count: int

    # Graph stats
    node_count: int
    edge_count: int
    density: float
    avg_degree: float
    avg_clustering: float

    # Graphlet analysis
    graphlet_counts: dict[str, int]
    graphlet_frequencies: dict[str, float]

    # Classification
    detected_pattern: str
    confidence: float
    all_similarities: dict[str, float]
    recommendations: list[str]

    # Configuration used
    window_strategy: str
    window_size: int
    granularity: str

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        d = asdict(self)
        d['analysis_timestamp'] = self.analysis_timestamp.isoformat()
        return d

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> "AnalysisResult":
        """Deserialize from JSON."""
        d = json.loads(json_str)
        d['analysis_timestamp'] = datetime.fromisoformat(d['analysis_timestamp'])
        return cls(**d)

    @classmethod
    def from_dict(cls, d: dict) -> "AnalysisResult":
        """Deserialize from dict."""
        if isinstance(d['analysis_timestamp'], str):
            d['analysis_timestamp'] = datetime.fromisoformat(d['analysis_timestamp'])
        return cls(**d)
