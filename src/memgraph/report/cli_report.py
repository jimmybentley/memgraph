"""Rich-based CLI reporter for terminal output."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import box

from memgraph.report.result import AnalysisResult


class CLIReporter:
    """Rich-based terminal report."""

    def __init__(self, console: Console | None = None):
        self.console = console or Console()

    def report(self, result: AnalysisResult) -> None:
        """Print full analysis report to terminal."""
        self.console.print()
        self._print_header(result)
        self._print_trace_stats(result)
        self._print_graph_stats(result)
        self._print_graphlet_distribution(result)
        self._print_classification(result)
        self._print_recommendations(result)
        self.console.print()

    def _print_header(self, result: AnalysisResult):
        """Print report header."""
        self.console.print(Panel(
            f"[bold blue]MemGraph Analysis Report[/bold blue]\n"
            f"Source: {result.trace_source}\n"
            f"Generated: {result.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            box=box.DOUBLE
        ))

    def _print_trace_stats(self, result: AnalysisResult):
        """Print trace statistics."""
        table = Table(title="Trace Statistics", box=box.SIMPLE)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right", style="green")

        total = result.total_accesses
        table.add_row("Total Accesses", f"{total:,}")
        table.add_row("Unique Addresses", f"{result.unique_addresses:,}")

        read_pct = (result.read_count / total * 100) if total > 0 else 0
        write_pct = (result.write_count / total * 100) if total > 0 else 0

        table.add_row("Reads", f"{result.read_count:,} ({read_pct:.1f}%)")
        table.add_row("Writes", f"{result.write_count:,} ({write_pct:.1f}%)")

        self.console.print(table)

    def _print_graph_stats(self, result: AnalysisResult):
        """Print graph statistics."""
        table = Table(title="Graph Statistics", box=box.SIMPLE)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right", style="green")

        table.add_row("Nodes", f"{result.node_count:,}")
        table.add_row("Edges", f"{result.edge_count:,}")
        table.add_row("Density", f"{result.density:.4f}")
        table.add_row("Avg Degree", f"{result.avg_degree:.2f}")
        table.add_row("Avg Clustering", f"{result.avg_clustering:.4f}")

        self.console.print(table)

    def _print_graphlet_distribution(self, result: AnalysisResult):
        """Print graphlet frequencies as horizontal bar chart."""
        table = Table(title="Graphlet Distribution", box=box.SIMPLE)
        table.add_column("Graphlet", style="cyan")
        table.add_column("Count", justify="right")
        table.add_column("Frequency", justify="right")
        table.add_column("", width=30)  # Bar

        max_freq = max(result.graphlet_frequencies.values()) if result.graphlet_frequencies else 1

        for gtype, freq in sorted(result.graphlet_frequencies.items()):
            count = result.graphlet_counts.get(gtype, 0)
            bar_len = int((freq / max_freq) * 25) if max_freq > 0 else 0
            bar = "█" * bar_len
            table.add_row(gtype, f"{count:,}", f"{freq:.3f}", f"[green]{bar}[/green]")

        self.console.print(table)

    def _print_classification(self, result: AnalysisResult):
        """Print classification results with similarity ranking."""
        # Pattern with confidence
        confidence_color = "green" if result.confidence > 0.7 else "yellow" if result.confidence > 0.5 else "red"

        panel_content = f"[bold]{result.detected_pattern}[/bold]\n"
        panel_content += f"Confidence: [{confidence_color}]{result.confidence:.1%}[/{confidence_color}]\n\n"

        # Similarity ranking
        panel_content += "Pattern Similarities:\n"
        for pattern, sim in sorted(result.all_similarities.items(), key=lambda x: -x[1]):
            bar_len = int(sim * 20)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            marker = " ◄" if pattern == result.detected_pattern else ""
            panel_content += f"  {pattern:18} {sim:.1%} {bar}{marker}\n"

        self.console.print(Panel(panel_content, title="Pattern Classification", box=box.ROUNDED))

    def _print_recommendations(self, result: AnalysisResult):
        """Print optimization recommendations."""
        if not result.recommendations:
            rec_text = "  No specific recommendations."
        else:
            rec_text = "\n".join(f"  • {r}" for r in result.recommendations)

        self.console.print(Panel(rec_text, title="Recommendations", box=box.ROUNDED, border_style="green"))
