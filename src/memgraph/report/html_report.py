"""HTML report generator with embedded charts."""

from jinja2 import Environment, PackageLoader
from pathlib import Path
import base64
import io

from memgraph.report.result import AnalysisResult


class HTMLReporter:
    """Standalone HTML report with embedded charts."""

    def __init__(self):
        self.env = Environment(
            loader=PackageLoader('memgraph.report', 'templates'),
            autoescape=True
        )

    def report(self, result: AnalysisResult, output_path: Path) -> None:
        """Generate standalone HTML report."""
        # Generate chart images as base64
        graphlet_chart = self._generate_graphlet_chart(result)
        similarity_chart = self._generate_similarity_chart(result)

        template = self.env.get_template('report.html.j2')
        html = template.render(
            result=result,
            graphlet_chart_b64=graphlet_chart,
            similarity_chart_b64=similarity_chart,
            generated_at=result.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S')
        )

        output_path.write_text(html)

    def _generate_graphlet_chart(self, result: AnalysisResult) -> str:
        """Generate graphlet bar chart as base64 PNG."""
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(10, 5))

        if result.graphlet_frequencies:
            names = list(result.graphlet_frequencies.keys())
            freqs = list(result.graphlet_frequencies.values())

            bars = ax.bar(names, freqs, color='steelblue')
            ax.set_ylabel('Frequency')
            ax.set_xlabel('Graphlet Type')
            ax.set_title('Graphlet Frequency Distribution')
            plt.xticks(rotation=45, ha='right')
        else:
            ax.text(0.5, 0.5, 'No graphlet data available',
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Graphlet Frequency Distribution')

        plt.tight_layout()

        # Convert to base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)

        return b64

    def _generate_similarity_chart(self, result: AnalysisResult) -> str:
        """Generate horizontal bar chart of pattern similarities."""
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(8, 4))

        if result.all_similarities:
            # Sort by similarity
            sorted_items = sorted(result.all_similarities.items(), key=lambda x: x[1])
            names = [x[0] for x in sorted_items]
            sims = [x[1] for x in sorted_items]

            colors = ['green' if n == result.detected_pattern else 'steelblue' for n in names]

            ax.barh(names, sims, color=colors)
            ax.set_xlabel('Similarity')
            ax.set_title('Pattern Similarity Scores')
            ax.set_xlim(0, 1)
        else:
            ax.text(0.5, 0.5, 'No similarity data available',
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Pattern Similarity Scores')

        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)

        return b64
