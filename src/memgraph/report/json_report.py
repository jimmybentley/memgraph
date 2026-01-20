"""JSON export reporter for CI/tooling integration."""

from pathlib import Path
import json

from memgraph.report.result import AnalysisResult


class JSONReporter:
    """JSON export for CI/tooling integration."""

    def report(self, result: AnalysisResult, path: Path | None = None) -> str:
        """Export to JSON. Optionally write to file."""
        json_str = result.to_json(indent=2)

        if path:
            path.write_text(json_str)

        return json_str

    def report_minimal(self, result: AnalysisResult) -> str:
        """Export minimal JSON (just classification + recommendations)."""
        minimal = {
            "pattern": result.detected_pattern,
            "confidence": result.confidence,
            "recommendations": result.recommendations
        }
        return json.dumps(minimal, indent=2)
