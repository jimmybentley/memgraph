# MemGraph Quickstart

## Installation

### Install MemGraph

```bash
pip install memgraph
```

### Install Valgrind (required for tracing)

```bash
# Ubuntu/Debian
sudo apt install valgrind

# macOS
brew install valgrind

# Fedora
sudo dnf install valgrind
```

**Note:** Valgrind support on macOS ARM (M1/M2/M3) is limited. Consider using a Linux VM or Docker for best results.

## Basic Usage

### Analyze Any Binary

The simplest way to use MemGraph is with the `run` command:

```bash
memgraph run ./your_program
```

This will:
1. Run your program under Valgrind to capture memory accesses
2. Build a temporal adjacency graph from the trace
3. Analyze graphlet patterns
4. Classify the access pattern
5. Show recommendations

### Example Output

```
Step 1/5: Tracing binary with Valgrind
  → Trace saved to: /tmp/memgraph_abc123.trace
Step 2/5: Parsing trace
  → Loaded 15,432 memory accesses
Step 3/5: Building graph (fixed window, cacheline)
  → Graph: 1,234 nodes, 2,345 edges
Step 4/5: Computing graphlet signature
  → Enumerated 5,678 graphlets
Step 5/5: Classifying pattern

╔══════════════════════════════════════════════╗
║ MemGraph Analysis Report                     ║
║ Source: ./your_program                        ║
║ Generated: 2024-01-20 10:30:45               ║
╚══════════════════════════════════════════════╝

╭─────────── Pattern Classification ───────────╮
│ Detected Pattern: SEQUENTIAL                 │
│ Confidence: 87.3%                            │
├──────────────────────────────────────────────┤
│ Recommendations:                             │
│   • Hardware prefetching should be effective  │
│   • Consider software prefetch hints          │
╰──────────────────────────────────────────────╯
```

## Output Formats

### Terminal (CLI) - Default

```bash
memgraph run ./program
```

Best for: Interactive analysis, quick feedback

### JSON - For CI/Scripts

```bash
memgraph run ./program --report=json -o results.json
```

Best for: Automation, regression tracking, CI/CD pipelines

### HTML - Shareable Reports

```bash
memgraph run ./program --report=html -o report.html
```

Best for: Sharing with team, documentation, archiving

## Common Options

### Pass Arguments to Your Program

```bash
memgraph run ./program arg1 arg2 --with-flag
```

### Adjust Analysis Parameters

```bash
# Use different window size
memgraph run ./program --window-size=200

# Use different granularity
memgraph run ./program --granularity=page

# Use sampling for large programs
memgraph run ./program --sample
```

### Keep Trace File

```bash
# Keep trace in temp directory
memgraph run ./program --keep-trace

# Save trace to specific location
memgraph run ./program --trace-output=my_trace.log
```

## Analyzing Existing Traces

If you already have a Valgrind Lackey trace:

```bash
memgraph analyze trace.log
```

## Example Programs

Try the included examples to see different patterns:

```bash
cd examples
make all
memgraph run ./sequential
memgraph run ./linked_list
memgraph run ./random_access
```

## Next Steps

- Read [Pattern Reference](patterns.md) to understand different patterns
- Learn [How to Interpret Reports](interpreting.md)
- Check [Troubleshooting](troubleshooting.md) if you encounter issues

## Quick Tips

1. **Start with small inputs** - Tracing adds overhead (10-100x slowdown)
2. **Use sampling for large programs** - Add `--sample` flag
3. **Compile with -O0** - Optimizations can obscure access patterns
4. **Check Valgrind version** - Run `valgrind --version` (need 3.10+)

## Platform-Specific Notes

### Linux
Full support, recommended platform.

### macOS (Intel)
Works but Valgrind may be slower.

### macOS (ARM)
Valgrind not supported. Options:
- Use Docker with Linux image
- Generate traces on Linux, analyze anywhere
- Use alternative tools (Intel PIN, DTrace)

### Windows
Not directly supported. Options:
- Use WSL2 (Windows Subsystem for Linux)
- Use Docker
- Use Dr. Memory as alternative tracer
