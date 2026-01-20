"""Chart generation utilities for MemGraph."""

from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from typing import Dict

from memgraph.visualization.colors import PATTERN_COLORS


class ChartGenerator:
    """Generate various charts for analysis results."""

    def __init__(self):
        pass

    def graphlet_distribution_chart(
        self,
        graphlet_frequencies: Dict[str, float],
        output_path: Path | None = None,
        title: str = "Graphlet Frequency Distribution"
    ) -> None:
        """Generate graphlet distribution bar chart."""
        fig, ax = plt.subplots(figsize=(10, 5))

        if graphlet_frequencies:
            names = list(graphlet_frequencies.keys())
            freqs = list(graphlet_frequencies.values())

            ax.bar(names, freqs, color='steelblue')
            ax.set_ylabel('Frequency')
            ax.set_xlabel('Graphlet Type')
            ax.set_title(title)
            plt.xticks(rotation=45, ha='right')
        else:
            ax.text(0.5, 0.5, 'No data available',
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title(title)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
        else:
            plt.show()

        plt.close(fig)

    def pattern_similarity_chart(
        self,
        similarities: Dict[str, float],
        detected_pattern: str,
        output_path: Path | None = None,
        title: str = "Pattern Similarity Scores"
    ) -> None:
        """Generate horizontal bar chart of pattern similarities."""
        fig, ax = plt.subplots(figsize=(8, 4))

        if similarities:
            # Sort by similarity
            sorted_items = sorted(similarities.items(), key=lambda x: x[1])
            names = [x[0] for x in sorted_items]
            sims = [x[1] for x in sorted_items]

            colors = ['green' if n == detected_pattern else 'steelblue' for n in names]

            ax.barh(names, sims, color=colors)
            ax.set_xlabel('Similarity')
            ax.set_title(title)
            ax.set_xlim(0, 1)
        else:
            ax.text(0.5, 0.5, 'No data available',
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title(title)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
        else:
            plt.show()

        plt.close(fig)
