"""Command-line interface for MemGraph."""

from pathlib import Path
from typing import Optional
import typer  # type: ignore
from rich.console import Console  # type: ignore
from rich.table import Table  # type: ignore
from rich.panel import Panel  # type: ignore

from memgraph.trace.parser import parse_trace
from memgraph.trace.generator import GENERATORS, get_available_patterns
from memgraph.trace.formats.native import NativeParser

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


if __name__ == "__main__":
    app()
