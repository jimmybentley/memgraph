"""Graph serialization for saving and loading graphs."""

import pickle
from pathlib import Path
from typing import Optional
import networkx as nx  # type: ignore


def save_graph(
    graph: nx.Graph,
    path: Path,
    format: str = "pickle"
) -> None:
    """Save graph to disk.

    Args:
        graph: NetworkX graph to save
        path: Output file path
        format: Serialization format ("pickle", "graphml", "edgelist")

    Raises:
        ValueError: If format is not supported
    """
    path = Path(path)
    format = format.lower()

    if format == "pickle":
        with open(path, "wb") as f:
            pickle.dump(graph, f, protocol=pickle.HIGHEST_PROTOCOL)

    elif format == "graphml":
        nx.write_graphml(graph, path)

    elif format == "edgelist":
        nx.write_edgelist(graph, path, data=["weight"])  # type: ignore[arg-type]

    else:
        raise ValueError(
            f"Unsupported format: {format}. "
            f"Supported formats: pickle, graphml, edgelist"
        )


def load_graph(path: Path, format: Optional[str] = None) -> nx.Graph:
    """Load graph from disk.

    Args:
        path: Path to graph file
        format: Serialization format. If None, auto-detect from extension.

    Returns:
        Loaded NetworkX graph

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If format is unknown or auto-detection fails
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Graph file not found: {path}")

    # Auto-detect format from extension if not specified
    if format is None:
        format = _detect_format(path)

    format = format.lower()

    if format == "pickle":
        with open(path, "rb") as f:
            graph = pickle.load(f)
            if not isinstance(graph, nx.Graph):
                raise ValueError("Loaded object is not a NetworkX graph")
            return graph

    elif format == "graphml":
        return nx.read_graphml(path)  # type: ignore[no-any-return]

    elif format == "edgelist":
        return nx.read_edgelist(path, data=[("weight", int)])  # type: ignore[no-any-return,call-overload]

    else:
        raise ValueError(
            f"Unsupported format: {format}. "
            f"Supported formats: pickle, graphml, edgelist"
        )


def _detect_format(path: Path) -> str:
    """Detect graph format from file extension.

    Args:
        path: Path to graph file

    Returns:
        Detected format string

    Raises:
        ValueError: If format cannot be detected
    """
    suffix = path.suffix.lower()

    format_map = {
        ".pkl": "pickle",
        ".pickle": "pickle",
        ".graphml": "graphml",
        ".xml": "graphml",
        ".edgelist": "edgelist",
        ".edges": "edgelist",
    }

    if suffix in format_map:
        return format_map[suffix]

    # Try pickle as default for unknown extensions
    # (most common for NetworkX graphs)
    return "pickle"
