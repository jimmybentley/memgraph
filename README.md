# MemGraph

**Analyze memory access patterns using graph theory**

MemGraph transforms memory traces into temporal adjacency graphs and uses graphlet analysis to classify access patterns, giving you actionable optimization recommendations beyond simple cache miss rates.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Why MemGraph?

Traditional profilers tell you **what** (45% cache miss rate) but not **why** or **what to do about it**.

MemGraph identifies **structural patterns** in your memory accesses:

| Pattern | What It Means | MemGraph Recommendation |
|---------|--------------|------------------------|
| SEQUENTIAL | Linear array traversal | Hardware prefetching effective |
| RANDOM | Hash tables, pointer-heavy | Reduce working set, batch accesses |
| POINTER_CHASE | Linked lists, trees | Linearize to array representation |
| WORKING_SET | Dense reuse, hot loops | Excellent cache behavior |
| STRIDED | Column-major, struct fields | Align to cache lines, consider SoA |

## Quick Start

```bash
# Install
pip install memgraph

# Analyze any binary (requires Valgrind)
memgraph run ./your_program

# Or analyze an existing trace
memgraph analyze trace.log --report=html -o report.html
```

## Example Output

```
╭─────────────────── Pattern Analysis ───────────────────╮
│ Detected Pattern: SEQUENTIAL                           │
│ Confidence: 87.3%                                      │
├────────────────────────────────────────────────────────┤
│ Recommendations:                                       │
│   • Hardware prefetching should be effective           │
│   • Consider software prefetch hints for large strides │
│   • Loop tiling may help if working set exceeds cache  │
╰────────────────────────────────────────────────────────╯
```

## How It Works

1. **Trace** memory accesses (via Valgrind Lackey)
2. **Build** a temporal adjacency graph (addresses as nodes, co-occurrence as edges)
3. **Count** graphlet patterns (small subgraph motifs)
4. **Classify** against known pattern signatures
5. **Report** with actionable recommendations

```
Memory Trace → Graph → Graphlets → Classification → Recommendations
```

## Installation

```bash
# From source
git clone https://github.com/jimmybentley/memgraph
cd memgraph
pip install -e ".[dev]"

# Valgrind (required for tracing)
# Ubuntu/Debian:
sudo apt install valgrind
# macOS (Intel only):
brew install valgrind
```

## Usage

### One-Command Analysis

```bash
# Trace and analyze a binary
memgraph run ./my_program

# With arguments
memgraph run ./benchmark arg1 arg2

# HTML report
memgraph run ./program --report=html -o report.html

# JSON for CI integration
memgraph run ./program --report=json -o results.json
```

### Step-by-Step

```bash
# Generate trace manually
valgrind --tool=lackey --trace-mem=yes ./program 2>&1 | grep -E '^ *(L|S|M) ' > trace.log

# Analyze
memgraph analyze trace.log

# Or step by step
memgraph parse trace.log                    # View trace stats
memgraph build trace.log -o graph.pkl       # Build graph
memgraph graphlets graph.pkl                # Analyze graphlets
memgraph classify graph.pkl                 # Classify pattern
```

### Python API

```python
from memgraph import analyze

# High-level API
result = analyze("trace.log")
print(result.detected_pattern)  # "SEQUENTIAL"
print(result.recommendations)

# Low-level API
from memgraph.trace import parse_trace
from memgraph.graph import GraphBuilder, SlidingWindow, Granularity
from memgraph.graphlets import GraphletEnumerator, GraphletSignature
from memgraph.classifier import PatternClassifier

trace = parse_trace("trace.log", format="lackey")
graph = GraphBuilder(
    window_strategy=SlidingWindow(100),
    granularity=Granularity.CACHELINE
).build(trace)
counts = GraphletEnumerator(graph).count_all()
signature = GraphletSignature.from_counts(counts)
result = PatternClassifier().classify(signature)
```

## Supported Patterns

| Pattern | Graphlet Signature | Typical Cause |
|---------|-------------------|---------------|
| SEQUENTIAL | High edges + 2-paths | Array iteration, streaming |
| RANDOM | Edge-dominated, sparse | Hash tables, pointer graphs |
| STRIDED | Periodic structure | Column-major access, struct fields |
| POINTER_CHASE | Elevated 3-stars | Linked lists, trees |
| WORKING_SET | High triangles/cliques | Hot loops, small caches |
| PRODUCER_CONSUMER | Bipartite-like | Pipelines, queues |

See [docs/patterns.md](docs/patterns.md) for detailed pattern reference.

## Configuration

```bash
# Window size (default: 100)
memgraph run ./program --window-size=200

# Address granularity: byte, cacheline (default), page
memgraph run ./program --granularity=page

# Keep trace file for later analysis
memgraph run ./program --keep-trace

# Use sampling for large graphs
memgraph run ./program --sample --num-samples=50000
```

## Example Programs

Try the included examples to see different patterns:

```bash
cd examples
make all

# Run individual examples
memgraph run ./sequential
memgraph run ./linked_list
memgraph run ./random_access
memgraph run ./working_set
memgraph run ./strided

# Run all tests
make test
```

## How Graphlets Work

Graphlets are small induced subgraph patterns. MemGraph counts 9 types (2-4 nodes):

```
G0: ●─●           (edge)
G1: ●─●─●         (2-path)
G2: △             (triangle)
G3: ●─●─●─●       (4-path)
G4: ●─●─●         (3-star)
      │
      ●
G5: ●─●─●─●       (4-cycle, square)
    │     │
    ●─────●
G6: △─●           (tailed triangle)
G7: ◇             (diamond)
G8: ▲             (4-clique, tetrahedron)
```

Different access patterns produce distinct graphlet frequency distributions, which enables classification.

**Key Insight:** Sequential access creates long chains (edges, 2-paths). Random access creates sparse isolated connections. Pointer chasing creates star patterns. Dense reuse creates triangles and cliques.

## Documentation

- [Quickstart Guide](docs/quickstart.md) - Installation and basic usage
- [Pattern Reference](docs/patterns.md) - Detailed pattern descriptions with examples
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions
- [Examples](examples/README.md) - Sample C programs for each pattern

## Requirements

- Python 3.10+
- Valgrind (for tracing)
- Linux recommended (Valgrind has limited macOS support, no ARM support)

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# With coverage
pytest --cov=memgraph --cov-report=term-missing

# Type checking
mypy src/memgraph

# Run specific test
pytest tests/test_classifier.py
```

## Architecture

```
src/memgraph/
├── trace/          # Trace parsing (Lackey, CSV, Native formats)
├── graph/          # Graph construction and windowing strategies
├── graphlets/      # Graphlet enumeration and signatures
├── classifier/     # Pattern classification and reference patterns
├── report/         # CLI, JSON, and HTML report generation
├── visualization/  # Graph and chart visualization
├── tracer/         # Valgrind integration
└── cli.py          # Command-line interface
```

## Citation

If you use MemGraph in research:

```bibtex
@software{memgraph2025,
  author = {Bentley, James},
  title = {MemGraph: Memory Access Pattern Analysis via Graphlets},
  year = {2025},
  url = {https://github.com/jimmybentley/memgraph}
}
```

## License

MIT License - see [LICENSE](LICENSE)

## Acknowledgments

- Graphlet analysis inspired by biological network analysis (Pržulj, 2007)
- Built with [NetworkX](https://networkx.org/), [Rich](https://rich.readthedocs.io/), [Typer](https://typer.tiangolo.com/)
- Valgrind Lackey tool for memory tracing

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Roadmap

Completed phases:
- Phase 1: Trace parsing ✓
- Phase 2: Graph construction ✓
- Phase 3: Graphlet enumeration ✓
- Phase 4: Pattern classification ✓
- Phase 5: Reporting & visualization ✓
- Phase 6: Valgrind integration ✓

Potential future enhancements:
- Phase detection (segment trace, classify each segment)
- Intel PIN support (faster than Valgrind)
- VS Code extension
- Comparative analysis (diff two runs)
- Cache simulation integration
