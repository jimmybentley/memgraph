# MemGraph: Memory Access Pattern Analyzer via Graphlet Analysis

## Executive Summary

MemGraph is a developer tool that analyzes memory access patterns using graph-theoretic techniques (graphlets) to provide richer characterization than traditional metrics like cache miss rates or reuse distance. It transforms memory traces into temporal adjacency graphs, computes graphlet frequency distributions, and maps these signatures to known access patterns with actionable optimization recommendations.

---

## Table of Contents

1. [Motivation & Goals](#motivation--goals)
2. [High-Level Architecture](#high-level-architecture)
3. [Phase Breakdown](#phase-breakdown)
4. [Technical Specifications](#technical-specifications)
5. [Data Structures](#data-structures)
6. [API Design](#api-design)
7. [Testing Strategy](#testing-strategy)

---

## Motivation & Goals

### Problem Statement

Current memory profiling tools provide aggregate metrics (cache hit rates, bandwidth utilization, reuse distances) that tell developers *what* is happening but not *why* or *what structural pattern* causes it. A developer seeing "L1 miss rate: 45%" has limited insight into whether the problem is:
- Random pointer chasing
- Strided access with unfortunate alignment
- Working set exceeding cache size
- Temporal interleaving of independent streams

### Solution

Graphlet analysis captures **local structural patterns** in the memory access graph. Different access patterns produce distinct graphlet frequency signatures:
- **Streaming/sequential**: Long chains (path graphlets dominate)
- **Random access**: Sparse, disconnected (independent edge graphlets)
- **Pointer chasing**: Tree-like structures (star graphlets)
- **Dense working set**: Clique-like subgraphs (triangle/complete graphlets)
- **Strided access**: Regular, periodic structures

### Goals

1. **Actionable insights**: Map graphlet signatures to specific optimization recommendations
2. **Low friction**: Easy to instrument and run on existing binaries
3. **Visual & interpretable**: Produce visualizations developers can understand
4. **Extensible**: Support custom pattern definitions and plugins

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         MemGraph Pipeline                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────────────────┐ │
│  │   Tracer     │───▶│Graph Builder │───▶│ Graphlet Enumerator   │ │
│  │ (PIN/Valgrind)│    │              │    │                       │ │
│  └──────────────┘    └──────────────┘    └───────────────────────┘ │
│                                                   │                 │
│                                                   ▼                 │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────────────────┐ │
│  │   Reporter   │◀───│  Classifier  │◀───│  Signature Builder    │ │
│  │              │    │              │    │                       │ │
│  └──────────────┘    └──────────────┘    └───────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Overview

| Component | Responsibility | Input | Output |
|-----------|---------------|-------|--------|
| Tracer | Capture memory accesses from target binary | Binary + args | Raw trace file |
| Graph Builder | Convert trace to temporal adjacency graph | Trace file | NetworkX graph |
| Graphlet Enumerator | Count graphlet occurrences | Graph | Graphlet counts dict |
| Signature Builder | Normalize counts into feature vector | Counts | Signature vector |
| Classifier | Map signature to known patterns | Signature | Pattern labels + confidence |
| Reporter | Generate human-readable output | All above | Report (CLI, HTML, JSON) |

---

## Phase Breakdown

### Phase 1: Core Infrastructure & Trace Parsing
**Duration**: 1-2 days  
**Deliverables**:
- Project scaffolding (Python package structure, pyproject.toml, basic CI)
- Trace file format specification
- Trace parser that reads common formats (Valgrind lackey, PIN, simple CSV)
- Synthetic trace generator for testing
- Basic CLI skeleton using Click or Typer

**Key Files**:
```
memgraph/
├── __init__.py
├── cli.py                 # CLI entry point
├── trace/
│   ├── __init__.py
│   ├── parser.py          # Trace parsing logic
│   ├── formats.py         # Format definitions (Lackey, PIN, CSV)
│   └── generator.py       # Synthetic trace generation
└── tests/
    └── test_trace_parser.py
```

**Acceptance Criteria**:
- [ ] Can parse a Valgrind Lackey trace file
- [ ] Can generate synthetic traces for: sequential, random, strided, pointer-chase patterns
- [ ] CLI command `memgraph parse <trace_file>` outputs summary stats
- [ ] Unit tests for parser with >90% coverage

---

### Phase 2: Graph Construction
**Duration**: 1-2 days  
**Deliverables**:
- Temporal adjacency graph builder
- Configurable windowing strategies (fixed window, sliding window, adaptive)
- Address coarsening (cache-line granularity, page granularity)
- Graph statistics module
- Serialization (save/load graphs)

**Key Files**:
```
memgraph/
├── graph/
│   ├── __init__.py
│   ├── builder.py         # Core graph construction
│   ├── windowing.py       # Window strategies
│   ├── coarsening.py      # Address granularity mapping
│   └── stats.py           # Basic graph metrics
```

**Technical Details**:

*Temporal Adjacency Graph Construction*:
- Node: unique memory address (or cache line)
- Edge: (A, B) exists if A and B are accessed within `window_size` accesses of each other
- Edge weight: frequency of co-occurrence within window

*Windowing Strategies*:
1. **Fixed window**: Connect all addresses within each non-overlapping window
2. **Sliding window**: Connect addresses within a sliding window (more edges, captures transitions)
3. **Adaptive**: Window size based on temporal locality detection

*Address Coarsening*:
- Raw address → cache line (addr >> 6 for 64B lines)
- Cache line → page (addr >> 12 for 4KB pages)
- Configurable via CLI flag

**Acceptance Criteria**:
- [ ] Build graph from parsed trace
- [ ] Support all three windowing strategies
- [ ] Support cache-line and page granularity
- [ ] CLI command `memgraph build <trace> --window=100 --granularity=cacheline`
- [ ] Graph statistics: node count, edge count, density, avg degree

---

### Phase 3: Graphlet Enumeration
**Duration**: 2-3 days  
**Deliverables**:
- Efficient graphlet enumeration for 2-4 node graphlets
- Sampling-based approximation for large graphs
- Graphlet frequency distribution (GFD) computation
- Graphlet degree distribution (GDD) for node-level analysis

**Key Files**:
```
memgraph/
├── graphlets/
│   ├── __init__.py
│   ├── enumeration.py     # Exact enumeration algorithms
│   ├── sampling.py        # Approximate counting via sampling
│   ├── orbits.py          # Orbit counting for GDD
│   └── signatures.py      # GFD/GDD to feature vector
```

**Technical Details**:

*Graphlet Definitions (up to 4 nodes)*:
```
G0: ●─●           (edge)
G1: ●─●─●         (2-path)
G2: ●─●─●         (triangle)
    └─┘
G3: ●─●─●─●       (3-path)
G4: ●─●─●         (3-star)
      │
      ●
G5: ●─●─●         (4-cycle)
    │   │
    ●───●
G6: ●─●─●─●       (4-path)
G7: ●─●           (tailed triangle)
    │╲│
    ● ●
G8: ●─●           (4-clique)
    │╲│
    ●─●
... (up to 11 connected graphlets on 4 nodes)
```

*Enumeration Strategy*:
- For small graphs (<10K nodes): exact enumeration via subgraph matching
- For medium graphs (10K-100K): ESCAPE-style edge sampling
- For large graphs (>100K): MCMC sampling with convergence detection

**Acceptance Criteria**:
- [ ] Enumerate all 2-4 node connected graphlets
- [ ] Sampling mode with configurable sample size
- [ ] Output GFD as normalized vector
- [ ] CLI command `memgraph analyze <graph> --graphlets`
- [ ] Benchmark: process 50K node graph in <30 seconds

---

### Phase 4: Pattern Classification
**Duration**: 2-3 days  
**Deliverables**:
- Reference signatures for known patterns
- Distance metrics for signature comparison
- Rule-based classifier
- Optional: simple ML classifier (sklearn) trained on synthetic data
- Confidence scoring

**Key Files**:
```
memgraph/
├── classifier/
│   ├── __init__.py
│   ├── signatures.py      # Reference pattern signatures
│   ├── distance.py        # Signature comparison metrics
│   ├── rules.py           # Rule-based classification
│   └── ml.py              # Optional ML classifier
```

**Technical Details**:

*Reference Patterns*:
| Pattern | Description | Dominant Graphlets | Optimization Hint |
|---------|-------------|-------------------|-------------------|
| SEQUENTIAL | Linear traversal | G1 (2-path), G3 (3-path) | Prefetching effective |
| RANDOM | Uniform random | G0 (edge) only, low density | Reduce working set, improve locality |
| STRIDED | Regular stride | G1, periodic structure | Align to cache lines, consider blocking |
| POINTER_CHASE | Linked structures | G4 (star), tree-like | Linearize, use arrays |
| WORKING_SET | Dense reuse | G2 (triangle), G8 (clique) | Fits in cache, optimize hot paths |
| PRODUCER_CONSUMER | Two interleaved streams | Bipartite-like structure | Separate streams, pipeline |

*Classification Algorithm*:
1. Compute cosine similarity between input GFD and each reference
2. Apply threshold filtering (similarity > 0.6)
3. Rank by similarity, return top-k with confidence scores
4. For edge cases, fall back to rule-based heuristics

**Acceptance Criteria**:
- [ ] Correctly classify synthetic traces (>90% accuracy on test set)
- [ ] Return confidence scores
- [ ] Handle mixed/unknown patterns gracefully
- [ ] CLI command `memgraph classify <graph>`

---

### Phase 5: Reporting & Visualization
**Duration**: 2 days  
**Deliverables**:
- CLI report with actionable recommendations
- JSON output for programmatic consumption
- HTML report with visualizations
- Graph visualization (sampled subgraph)
- Graphlet frequency bar chart
- Timeline view (pattern changes over trace segments)

**Key Files**:
```
memgraph/
├── report/
│   ├── __init__.py
│   ├── cli_report.py      # Terminal output
│   ├── json_report.py     # JSON export
│   ├── html_report.py     # HTML generation
│   └── templates/
│       └── report.html.j2
├── visualization/
│   ├── __init__.py
│   ├── graph_viz.py       # Graph plotting
│   ├── charts.py          # Graphlet distribution charts
│   └── timeline.py        # Temporal pattern evolution
```

**Acceptance Criteria**:
- [ ] CLI report shows: pattern classification, confidence, recommendations
- [ ] JSON output includes all metrics and classifications
- [ ] HTML report renders in browser with charts
- [ ] Graph visualization shows sampled subgraph with pattern-based coloring

---

### Phase 6: End-to-End Integration & Tracing
**Duration**: 2-3 days  
**Deliverables**:
- Valgrind Lackey wrapper script
- PIN tool integration (if time permits)
- One-command workflow: `memgraph run ./my_binary --args`
- Performance benchmarks
- Documentation and examples

**Key Files**:
```
memgraph/
├── tracer/
│   ├── __init__.py
│   ├── valgrind.py        # Valgrind wrapper
│   ├── pin.py             # PIN wrapper (optional)
│   └── config.py          # Tracer configuration
├── docs/
│   ├── quickstart.md
│   ├── patterns.md
│   └── examples/
```

**Acceptance Criteria**:
- [ ] `memgraph run ./binary` produces full report
- [ ] Works on sample C programs demonstrating each pattern
- [ ] Documentation covers installation, usage, interpretation
- [ ] Benchmark results on standard workloads

---

### Phase 7: Polish & Extensions (Optional)
**Duration**: Ongoing  
**Potential Features**:
- Phase detection (segment trace, classify each segment)
- Comparative analysis (compare two runs)
- Custom pattern definitions via YAML
- VS Code extension for inline annotations
- Integration with perf/VTune for correlation with hardware counters

---

## Technical Specifications

### Trace File Format (Native)

```
# MemGraph Trace Format v1
# Fields: operation,address,size,timestamp
R,0x7fff5a8b1000,8,1
W,0x7fff5a8b1008,4,2
R,0x7fff5a8b1000,8,3
R,0x7fff5a8b2000,8,4
...
```

### Configuration File (memgraph.toml)

```toml
[trace]
format = "lackey"  # lackey, pin, csv, native
granularity = "cacheline"  # byte, cacheline, page

[graph]
window_strategy = "sliding"
window_size = 100
min_edge_weight = 1

[graphlets]
max_size = 4
sampling = true
sample_size = 100000

[classifier]
method = "cosine"  # cosine, euclidean, ml
threshold = 0.6

[report]
format = "cli"  # cli, json, html
output_dir = "./memgraph_reports"
```

---

## Data Structures

### Core Classes

```python
@dataclass
class MemoryAccess:
    """Single memory access event."""
    operation: Literal["R", "W"]
    address: int
    size: int
    timestamp: int

@dataclass  
class TraceMetadata:
    """Metadata about a trace file."""
    source: str
    format: str
    total_accesses: int
    unique_addresses: int
    time_range: tuple[int, int]

@dataclass
class GraphletCount:
    """Graphlet frequency distribution."""
    counts: dict[str, int]  # graphlet_id -> count
    total: int
    normalized: dict[str, float]  # graphlet_id -> frequency

@dataclass
class PatternMatch:
    """Classification result for a single pattern."""
    pattern: str
    confidence: float
    evidence: list[str]  # supporting graphlet features
    recommendations: list[str]

@dataclass
class AnalysisResult:
    """Complete analysis output."""
    trace_meta: TraceMetadata
    graph_stats: dict
    graphlet_counts: GraphletCount
    classifications: list[PatternMatch]
    segments: list[SegmentAnalysis] | None  # for phase detection
```

---

## API Design

### Public API

```python
from memgraph import analyze, Trace, Graph

# High-level API
result = analyze("trace.log", config="memgraph.toml")
print(result.top_pattern)
result.to_html("report.html")

# Low-level API
trace = Trace.from_file("trace.log", format="lackey")
graph = Graph.from_trace(trace, window_size=100, granularity="cacheline")
gfd = graph.compute_graphlets(max_size=4)
patterns = classify(gfd)
```

### CLI Commands

```bash
# Full pipeline
memgraph run ./binary [args]           # Trace + analyze + report
memgraph analyze trace.log             # Analyze existing trace
memgraph report analysis.json --html   # Generate report from saved analysis

# Individual stages
memgraph trace ./binary [args]         # Just trace
memgraph parse trace.log               # Parse and summarize trace
memgraph build trace.log -o graph.pkl  # Build graph
memgraph graphlets graph.pkl           # Enumerate graphlets
memgraph classify graph.pkl            # Classify pattern

# Utilities
memgraph generate --pattern=random --size=10000  # Synthetic trace
memgraph compare trace1.log trace2.log           # Comparative analysis
```

---

## Testing Strategy

### Unit Tests
- Trace parsing for each format
- Graph construction correctness
- Graphlet enumeration (verified against known small graphs)
- Classifier accuracy on synthetic patterns

### Integration Tests
- End-to-end pipeline on synthetic traces
- Round-trip serialization
- CLI command execution

### Benchmark Tests
- Graph construction time vs trace size
- Graphlet enumeration time vs graph size
- Memory usage profiling

### Validation Tests
- Run on real programs with known access patterns
- Compare classifications against ground truth
- Verify recommendations make sense

---

## Dependencies

### Required
- Python >= 3.10
- networkx >= 3.0
- numpy >= 1.24
- click >= 8.0
- rich >= 13.0 (CLI formatting)

### Optional
- matplotlib >= 3.7 (visualization)
- jinja2 >= 3.0 (HTML reports)
- scikit-learn >= 1.3 (ML classifier)
- pyvis >= 0.3 (interactive graph viz)
- valgrind (external, for tracing)

---

## References

1. Pržulj, N. (2007). Biological network comparison using graphlet degree distribution. *Bioinformatics*.
2. Ahmed, N. K., et al. (2015). Efficient graphlet counting for large networks. *ICDM*.
3. Gu, Y., et al. (2020). Neural Network-based Graph Embedding for Cross-Platform Binary Code Similarity Detection. *CCS*.
4. Intel PIN: https://www.intel.com/content/www/us/en/developer/articles/tool/pin-a-dynamic-binary-instrumentation-tool.html
5. Valgrind Lackey: https://valgrind.org/docs/manual/lk-manual.html
