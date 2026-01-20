"""Command-line interface for MemGraph."""

from pathlib import Path
from typing import Optional
from datetime import datetime
import typer  # type: ignore
from rich.console import Console  # type: ignore
from rich.table import Table  # type: ignore
from rich.panel import Panel  # type: ignore

from memgraph.trace.parser import parse_trace
from memgraph.trace.generator import GENERATORS, get_available_patterns
from memgraph.trace.formats.native import NativeParser
from memgraph.graph.builder import GraphBuilder
from memgraph.graph.windowing import WindowStrategy, FixedWindow, SlidingWindow, AdaptiveWindow
from memgraph.graph.coarsening import Granularity
from memgraph.graph.stats import GraphStats
from memgraph.graph.serialization import save_graph, load_graph
from memgraph.graphlets.enumeration import GraphletEnumerator
from memgraph.graphlets.sampling import GraphletSampler
from memgraph.graphlets.signatures import GraphletSignature
from memgraph.classifier.patterns import PatternDatabase
from memgraph.classifier.distance import PatternClassifier
from memgraph.report.result import AnalysisResult
from memgraph.report.cli_report import CLIReporter
from memgraph.report.json_report import JSONReporter
from memgraph.report.html_report import HTMLReporter
from memgraph import __version__

app = typer.Typer(
    name="memgraph",
    help="Memory access pattern analysis using graphlet analysis",
    add_completion=False,
)
console = Console()


@app.command()
def parse(
    trace_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        help="Path to trace file"
    ),
    format: Optional[str] = typer.Option(
        None,
        "--format",
        "-f",
        help="Trace format (native, lackey, csv). Auto-detected if not specified."
    ),
) -> None:
    """Parse a trace file and display summary statistics."""
    try:
        # Parse the trace
        trace = parse_trace(trace_file, format=format)

        # Create a rich table for the summary
        meta = trace.metadata

        # Calculate percentages
        read_pct = (meta.read_count / meta.total_accesses * 100) if meta.total_accesses > 0 else 0
        write_pct = (meta.write_count / meta.total_accesses * 100) if meta.total_accesses > 0 else 0

        # Format the summary
        summary_lines = [
            f"[cyan]Source:[/cyan] {meta.source}",
            f"[cyan]Format:[/cyan] {meta.format}",
            f"[cyan]Total accesses:[/cyan] {meta.total_accesses:,}",
            f"[cyan]Unique addresses:[/cyan] {meta.unique_addresses:,}",
            f"[cyan]Reads:[/cyan] {meta.read_count:,} ({read_pct:.1f}%)",
            f"[cyan]Writes:[/cyan] {meta.write_count:,} ({write_pct:.1f}%)",
            f"[cyan]Address range:[/cyan] {hex(meta.address_range[0])} - {hex(meta.address_range[1])}",
        ]

        # Create panel
        panel = Panel(
            "\n".join(summary_lines),
            title="[bold]Trace Summary[/bold]",
            border_style="green",
            padding=(1, 2),
        )

        console.print(panel)

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def generate(
    pattern: str = typer.Argument(
        ...,
        help=f"Pattern type: {', '.join(get_available_patterns())}"
    ),
    size: int = typer.Option(
        1000,
        "--size",
        "-n",
        help="Number of memory accesses to generate"
    ),
    output: Path = typer.Option(
        ...,
        "--output",
        "-o",
        help="Output file path"
    ),
    start_addr: int = typer.Option(
        0x1000,
        "--start-addr",
        help="Starting memory address (hex or decimal)"
    ),
    stride: int = typer.Option(
        8,
        "--stride",
        help="Stride for sequential/strided patterns"
    ),
    seed: Optional[int] = typer.Option(
        None,
        "--seed",
        help="Random seed for reproducibility"
    ),
) -> None:
    """Generate a synthetic trace with the specified pattern."""
    try:
        # Validate pattern
        if pattern not in GENERATORS:
            console.print(
                f"[red]Error:[/red] Unknown pattern '{pattern}'. "
                f"Available: {', '.join(get_available_patterns())}"
            )
            raise typer.Exit(1)

        # Generate trace based on pattern
        generator = GENERATORS[pattern]

        # Call generator with appropriate parameters
        if pattern == "sequential":
            trace = generator(n=size, start_addr=start_addr, stride=stride)  # type: ignore
        elif pattern == "random":
            trace = generator(n=size, seed=seed)  # type: ignore
        elif pattern == "strided":
            trace = generator(n=size, start_addr=start_addr, stride=stride)  # type: ignore
        elif pattern == "pointer_chase":
            trace = generator(n=size, start_addr=start_addr, seed=seed)  # type: ignore
        elif pattern == "working_set":
            trace = generator(n=size, start_addr=start_addr, seed=seed)  # type: ignore
        else:
            # Fallback
            trace = generator(n=size)  # type: ignore

        # Write trace to file in native format
        parser = NativeParser()
        parser.write(trace, output)

        console.print(
            f"[green]✓[/green] Generated {size:,} memory accesses "
            f"with pattern '{pattern}' → {output}"
        )

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def formats() -> None:
    """List supported trace formats."""
    table = Table(title="Supported Trace Formats")

    table.add_column("Format", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    table.add_column("Example", style="dim")

    table.add_row(
        "native",
        "MemGraph native format",
        "R,0x1000,8,1"
    )
    table.add_row(
        "lackey",
        "Valgrind Lackey format",
        " L 7ff000398,8"
    )
    table.add_row(
        "csv",
        "Simple CSV format",
        "R,0x1000,8"
    )

    console.print(table)


@app.command()
def patterns() -> None:
    """List available synthetic trace patterns."""
    table = Table(title="Available Synthetic Patterns")

    table.add_column("Pattern", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")

    table.add_row(
        "sequential",
        "Linear sequential access pattern"
    )
    table.add_row(
        "random",
        "Uniform random access pattern"
    )
    table.add_row(
        "strided",
        "Strided access (e.g., array column traversal)"
    )
    table.add_row(
        "pointer_chase",
        "Simulated linked list traversal"
    )
    table.add_row(
        "working_set",
        "Dense reuse within a working set"
    )

    console.print(table)


@app.command()
def build(
    trace_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        help="Path to trace file"
    ),
    output: Path = typer.Option(
        ...,
        "--output",
        "-o",
        help="Output graph file path"
    ),
    window: str = typer.Option(
        "fixed",
        "--window",
        "-w",
        help="Window strategy: fixed, sliding, adaptive"
    ),
    window_size: int = typer.Option(
        100,
        "--window-size",
        help="Window size (number of accesses)"
    ),
    step: int = typer.Option(
        1,
        "--step",
        help="Step size for sliding window"
    ),
    granularity: str = typer.Option(
        "cacheline",
        "--granularity",
        "-g",
        help="Address granularity: byte, cacheline, page"
    ),
    min_weight: int = typer.Option(
        1,
        "--min-weight",
        help="Minimum edge weight to include"
    ),
    show_stats: bool = typer.Option(
        False,
        "--stats",
        help="Display graph statistics after building"
    ),
    trace_format: Optional[str] = typer.Option(
        None,
        "--format",
        "-f",
        help="Trace format (auto-detect if not specified)"
    ),
) -> None:
    """Build a temporal adjacency graph from a trace file."""
    try:
        # Parse trace
        console.print(f"[cyan]Parsing trace:[/cyan] {trace_file}")
        trace = parse_trace(trace_file, format=trace_format)
        console.print(f"  Loaded {len(trace):,} memory accesses")

        # Select window strategy
        window = window.lower()
        strategy: WindowStrategy
        if window == "fixed":
            strategy = FixedWindow(size=window_size)
        elif window == "sliding":
            strategy = SlidingWindow(size=window_size, step=step)
        elif window == "adaptive":
            strategy = AdaptiveWindow(base_size=window_size)
        else:
            console.print(f"[red]Error:[/red] Unknown window strategy: {window}")
            console.print("Available: fixed, sliding, adaptive")
            raise typer.Exit(1)

        # Select granularity
        granularity_map = {
            "byte": Granularity.BYTE,
            "cacheline": Granularity.CACHELINE,
            "page": Granularity.PAGE,
        }
        granularity = granularity.lower()
        if granularity not in granularity_map:
            console.print(f"[red]Error:[/red] Unknown granularity: {granularity}")
            console.print("Available: byte, cacheline, page")
            raise typer.Exit(1)

        gran = granularity_map[granularity]

        # Build graph
        console.print(f"[cyan]Building graph:[/cyan] {window} window, {granularity} granularity")
        builder = GraphBuilder(
            window_strategy=strategy,
            granularity=gran,
            min_edge_weight=min_weight
        )
        graph = builder.build(trace)

        # Save graph
        save_graph(graph, output)
        console.print(f"[green]✓[/green] Graph saved to: {output}")

        # Show statistics if requested
        if show_stats:
            stats = GraphStats.from_graph(graph)
            summary_lines = stats.format_summary().split("\n")

            panel = Panel(
                "\n".join(summary_lines),
                title="[bold]Graph Statistics[/bold]",
                border_style="green",
                padding=(1, 2),
            )
            console.print(panel)

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def stats(
    graph_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        help="Path to graph file"
    ),
) -> None:
    """Display statistics for a saved graph."""
    try:
        # Load graph
        console.print(f"[cyan]Loading graph:[/cyan] {graph_file}")
        graph = load_graph(graph_file)

        # Compute statistics
        graph_stats = GraphStats.from_graph(graph)

        # Display statistics
        summary_lines = graph_stats.format_summary().split("\n")

        panel = Panel(
            "\n".join(summary_lines),
            title="[bold]Graph Statistics[/bold]",
            border_style="green",
            padding=(1, 2),
        )

        console.print(panel)

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def graphlets(
    graph_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        help="Path to graph file"
    ),
    sample: bool = typer.Option(
        False,
        "--sample",
        help="Use sampling for large graphs"
    ),
    num_samples: int = typer.Option(
        100000,
        "--num-samples",
        help="Number of samples (if using sampling)"
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Save signature to JSON file"
    ),
) -> None:
    """Enumerate graphlets and compute signature for a graph."""
    try:
        # Load graph
        console.print(f"[cyan]Loading graph:[/cyan] {graph_file}")
        graph = load_graph(graph_file)

        # Enumerate graphlets
        if sample:
            console.print(f"[cyan]Sampling graphlets:[/cyan] {num_samples:,} samples")
            sampler = GraphletSampler(graph)
            counts = sampler.sample_count(num_samples=num_samples)
            method = f"sampling ({num_samples:,} samples)"
        else:
            console.print("[cyan]Enumerating graphlets:[/cyan] exact")
            enumerator = GraphletEnumerator(graph)
            counts = enumerator.count_all()
            method = "exact enumeration"

        # Create signature
        signature = GraphletSignature.from_counts(counts)

        # Display results
        lines = [
            f"Method: {method}",
            "",
            counts.format_summary(),
        ]

        panel = Panel(
            "\n".join(lines),
            title="[bold]Graphlet Analysis[/bold]",
            border_style="green",
            padding=(1, 2),
        )
        console.print(panel)

        # Save signature if requested
        if output:
            import json
            with open(output, "w") as f:
                json.dump(signature.to_dict(), f, indent=2)
            console.print(f"[green]✓[/green] Signature saved to: {output}")

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def compare(
    graph1_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        help="Path to first graph file"
    ),
    graph2_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        help="Path to second graph file"
    ),
    metric: str = typer.Option(
        "cosine",
        "--metric",
        "-m",
        help="Distance metric: cosine, euclidean, manhattan"
    ),
    sample: bool = typer.Option(
        False,
        "--sample",
        help="Use sampling for large graphs"
    ),
    num_samples: int = typer.Option(
        100000,
        "--num-samples",
        help="Number of samples (if using sampling)"
    ),
) -> None:
    """Compare two graphs based on their graphlet signatures."""
    try:
        # Validate metric
        metric = metric.lower()
        if metric not in ("cosine", "euclidean", "manhattan"):
            console.print(f"[red]Error:[/red] Unknown metric: {metric}")
            console.print("Available: cosine, euclidean, manhattan")
            raise typer.Exit(1)

        # Load graphs
        console.print(f"[cyan]Loading graphs...[/cyan]")
        graph1 = load_graph(graph1_file)
        graph2 = load_graph(graph2_file)

        # Enumerate graphlets for both graphs
        if sample:
            console.print(f"[cyan]Sampling graphlets:[/cyan] {num_samples:,} samples each")
            sampler1 = GraphletSampler(graph1)
            sampler2 = GraphletSampler(graph2)
            counts1 = sampler1.sample_count(num_samples=num_samples)
            counts2 = sampler2.sample_count(num_samples=num_samples)
        else:
            console.print("[cyan]Enumerating graphlets...[/cyan]")
            counts1 = GraphletEnumerator(graph1).count_all()
            counts2 = GraphletEnumerator(graph2).count_all()

        # Create signatures
        sig1 = GraphletSignature.from_counts(counts1)
        sig2 = GraphletSignature.from_counts(counts2)

        # Compute distance and similarity
        distance = sig1.distance(sig2, metric=metric)  # type: ignore
        similarity = sig1.similarity(sig2, metric=metric)  # type: ignore

        # Display results
        lines = [
            f"Graph 1: {graph1.number_of_nodes():,} nodes, {graph1.number_of_edges():,} edges",
            f"Graph 2: {graph2.number_of_nodes():,} nodes, {graph2.number_of_edges():,} edges",
            "",
            f"Metric: {metric}",
            f"Distance: {distance:.4f}",
            f"Similarity: {similarity:.4f}",
            "",
        ]

        # Add interpretation
        if metric == "cosine":
            if similarity > 0.9:
                interpretation = "Very similar"
            elif similarity > 0.7:
                interpretation = "Moderately similar"
            elif similarity > 0.5:
                interpretation = "Somewhat similar"
            else:
                interpretation = "Quite different"
            lines.append(f"Interpretation: {interpretation}")

        panel = Panel(
            "\n".join(lines),
            title="[bold]Graph Comparison[/bold]",
            border_style="green",
            padding=(1, 2),
        )
        console.print(panel)

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def classify(
    graph_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        help="Path to graph file"
    ),
    sample: bool = typer.Option(
        False,
        "--sample",
        help="Use sampling for large graphs"
    ),
    num_samples: int = typer.Option(
        100000,
        "--num-samples",
        help="Number of samples (if using sampling)"
    ),
    metric: str = typer.Option(
        "cosine",
        "--metric",
        "-m",
        help="Distance metric: cosine, euclidean, manhattan"
    ),
    min_similarity: float = typer.Option(
        0.0,
        "--min-similarity",
        help="Minimum similarity threshold (0.0-1.0)"
    ),
) -> None:
    """Classify a graph's memory access pattern."""
    try:
        # Validate metric
        metric = metric.lower()
        if metric not in ("cosine", "euclidean", "manhattan"):
            console.print(f"[red]Error:[/red] Unknown metric: {metric}")
            console.print("Available: cosine, euclidean, manhattan")
            raise typer.Exit(1)

        # Load graph
        console.print(f"[cyan]Loading graph:[/cyan] {graph_file}")
        graph = load_graph(graph_file)

        # Enumerate graphlets
        if sample:
            console.print(f"[cyan]Sampling graphlets:[/cyan] {num_samples:,} samples")
            sampler = GraphletSampler(graph)
            counts = sampler.sample_count(num_samples=num_samples)
        else:
            console.print("[cyan]Enumerating graphlets:[/cyan] exact")
            enumerator = GraphletEnumerator(graph)
            counts = enumerator.count_all()

        # Create signature
        signature = GraphletSignature.from_counts(counts)

        # Classify pattern
        console.print(f"[cyan]Classifying pattern:[/cyan] {metric} metric")
        classifier = PatternClassifier(metric=metric)  # type: ignore

        if min_similarity > 0:
            result = classifier.classify_with_threshold(signature, min_similarity)
            if result is None:
                console.print(
                    f"[yellow]Warning:[/yellow] No pattern matched with "
                    f"similarity >= {min_similarity:.2f}"
                )
                raise typer.Exit(0)
        else:
            result = classifier.classify(signature)

        # Display classification report
        console.print("")
        console.print(result.format_report())

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def analyze(
    trace_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        help="Path to trace file"
    ),
    window: str = typer.Option(
        "fixed",
        "--window",
        "-w",
        help="Window strategy: fixed, sliding, adaptive"
    ),
    window_size: int = typer.Option(
        100,
        "--window-size",
        help="Window size (number of accesses)"
    ),
    granularity: str = typer.Option(
        "cacheline",
        "--granularity",
        "-g",
        help="Address granularity: byte, cacheline, page"
    ),
    sample: bool = typer.Option(
        False,
        "--sample",
        help="Use sampling for graphlet enumeration"
    ),
    num_samples: int = typer.Option(
        100000,
        "--num-samples",
        help="Number of samples (if using sampling)"
    ),
    metric: str = typer.Option(
        "cosine",
        "--metric",
        "-m",
        help="Distance metric: cosine, euclidean, manhattan"
    ),
    trace_format: Optional[str] = typer.Option(
        None,
        "--format",
        "-f",
        help="Trace format (auto-detect if not specified)"
    ),
    report: str = typer.Option(
        "cli",
        "--report",
        "-r",
        help="Report format: cli, json, html"
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file for json/html reports"
    ),
) -> None:
    """End-to-end analysis: parse trace, build graph, and classify pattern."""
    try:
        # Validate report format
        report = report.lower()
        if report not in ("cli", "json", "html"):
            console.print(f"[red]Error:[/red] Unknown report format: {report}")
            console.print("Available: cli, json, html")
            raise typer.Exit(1)

        # Validate output requirement
        if report in ("json", "html") and output is None:
            console.print(f"[red]Error:[/red] --output is required for {report} format")
            raise typer.Exit(1)

        # Validate metric
        metric = metric.lower()
        if metric not in ("cosine", "euclidean", "manhattan"):
            console.print(f"[red]Error:[/red] Unknown metric: {metric}")
            console.print("Available: cosine, euclidean, manhattan")
            raise typer.Exit(1)

        # Parse trace
        console.print(f"[cyan]Step 1/4: Parsing trace[/cyan] {trace_file}")
        trace = parse_trace(trace_file, format=trace_format)
        console.print(f"  → Loaded {len(trace):,} memory accesses")

        # Select window strategy
        window = window.lower()
        strategy: WindowStrategy
        if window == "fixed":
            strategy = FixedWindow(size=window_size)
        elif window == "sliding":
            strategy = SlidingWindow(size=window_size, step=1)
        elif window == "adaptive":
            strategy = AdaptiveWindow(base_size=window_size)
        else:
            console.print(f"[red]Error:[/red] Unknown window strategy: {window}")
            console.print("Available: fixed, sliding, adaptive")
            raise typer.Exit(1)

        # Select granularity
        granularity_map = {
            "byte": Granularity.BYTE,
            "cacheline": Granularity.CACHELINE,
            "page": Granularity.PAGE,
        }
        granularity = granularity.lower()
        if granularity not in granularity_map:
            console.print(f"[red]Error:[/red] Unknown granularity: {granularity}")
            console.print("Available: byte, cacheline, page")
            raise typer.Exit(1)

        gran = granularity_map[granularity]

        # Build graph
        console.print(f"[cyan]Step 2/4: Building graph[/cyan] ({window} window, {granularity})")
        builder = GraphBuilder(window_strategy=strategy, granularity=gran)
        graph = builder.build(trace)
        console.print(f"  → Graph: {graph.number_of_nodes():,} nodes, {graph.number_of_edges():,} edges")

        # Compute graph stats
        graph_stats = GraphStats.from_graph(graph)

        # Enumerate graphlets
        console.print(f"[cyan]Step 3/4: Computing graphlet signature[/cyan]")
        if sample:
            sampler = GraphletSampler(graph)
            counts = sampler.sample_count(num_samples=num_samples)
            console.print(f"  → Sampled {num_samples:,} graphlets")
        else:
            enumerator = GraphletEnumerator(graph)
            counts = enumerator.count_all()
            console.print(f"  → Enumerated {counts.total:,} graphlets")

        signature = GraphletSignature.from_counts(counts)

        # Classify pattern
        console.print(f"[cyan]Step 4/4: Classifying pattern[/cyan]")
        classifier = PatternClassifier(metric=metric)  # type: ignore
        classification = classifier.classify(signature)

        # Build AnalysisResult
        analysis_result = AnalysisResult(
            trace_source=str(trace_file),
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
            window_strategy=window,
            window_size=window_size,
            granularity=granularity,
        )

        # Generate report
        console.print("")
        if report == "cli":
            reporter = CLIReporter(console)
            reporter.report(analysis_result)
        elif report == "json":
            reporter = JSONReporter()
            reporter.report(analysis_result, output)
            console.print(f"[green]✓[/green] JSON report saved to: {output}")
        elif report == "html":
            console.print("[cyan]Generating HTML report...[/cyan]")
            reporter = HTMLReporter()
            reporter.report(analysis_result, output)  # type: ignore
            console.print(f"[green]✓[/green] HTML report saved to: {output}")

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def report(
    result_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        help="Path to JSON analysis result file"
    ),
    format: str = typer.Option(
        "cli",
        "--format",
        "-f",
        help="Report format: cli, html"
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file for html report"
    ),
) -> None:
    """Generate a report from a saved JSON analysis result."""
    try:
        # Validate format
        format = format.lower()
        if format not in ("cli", "html"):
            console.print(f"[red]Error:[/red] Unknown format: {format}")
            console.print("Available: cli, html")
            raise typer.Exit(1)

        # Validate output requirement
        if format == "html" and output is None:
            console.print(f"[red]Error:[/red] --output is required for html format")
            raise typer.Exit(1)

        # Load result
        console.print(f"[cyan]Loading analysis result:[/cyan] {result_file}")
        result_json = result_file.read_text()
        analysis_result = AnalysisResult.from_json(result_json)

        # Generate report
        if format == "cli":
            reporter = CLIReporter(console)
            reporter.report(analysis_result)
        elif format == "html":
            console.print("[cyan]Generating HTML report...[/cyan]")
            reporter = HTMLReporter()
            reporter.report(analysis_result, output)  # type: ignore
            console.print(f"[green]✓[/green] HTML report saved to: {output}")

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
