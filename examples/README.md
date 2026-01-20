# MemGraph Example Programs

This directory contains example C programs demonstrating different memory access patterns. Each program is designed to exhibit a specific pattern that MemGraph can detect and classify.

## Building Examples

```bash
make all
```

This will compile all example programs with `-O0` (no optimization) to preserve the intended memory access patterns.

## Running Examples

### Individual Programs

Run a single example and analyze its pattern:

```bash
memgraph run ./sequential
```

### All Programs

Test all examples:

```bash
make test
```

## Example Programs

### sequential.c - SEQUENTIAL Pattern

**Description:** Linear array traversal with perfect spatial locality.

**Expected Pattern:** SEQUENTIAL

**Characteristics:**
- Consecutive memory accesses
- High cache hit rate
- Hardware prefetcher friendly

**Run:**
```bash
make run-sequential
```

### linked_list.c - POINTER_CHASE Pattern

**Description:** Linked list traversal with pointer-dependent accesses.

**Expected Pattern:** POINTER_CHASE

**Characteristics:**
- Each access depends on the previous value
- Poor spatial locality
- Difficult to prefetch

**Run:**
```bash
make run-linked_list
```

### working_set.c - WORKING_SET Pattern

**Description:** Small working set with high temporal locality.

**Expected Pattern:** WORKING_SET

**Characteristics:**
- Dense reuse of same memory locations
- Excellent cache performance
- Small footprint

**Run:**
```bash
make run-working_set
```

### random_access.c - RANDOM Pattern

**Description:** Pseudo-random memory accesses.

**Expected Pattern:** RANDOM

**Characteristics:**
- Unpredictable access pattern
- Poor cache performance
- Ineffective prefetching

**Run:**
```bash
make run-random_access
```

### strided.c - STRIDED Pattern

**Description:** Fixed stride access (column-major array traversal).

**Expected Pattern:** STRIDED

**Characteristics:**
- Regular but non-sequential pattern
- Predictable stride
- Some prefetchers can adapt

**Run:**
```bash
make run-strided
```

## Output Formats

Generate different report formats:

```bash
# Terminal output (default)
memgraph run ./sequential

# JSON report
memgraph run ./sequential --report=json -o result.json

# HTML report
memgraph run ./sequential --report=html -o report.html
```

## Customization

Adjust analysis parameters:

```bash
# Different window size
memgraph run ./sequential --window-size=200

# Different granularity
memgraph run ./sequential --granularity=page

# Keep trace file
memgraph run ./sequential --keep-trace --trace-output=trace.log
```

## Requirements

- GCC or compatible C compiler
- Valgrind (for tracing)
- MemGraph

## Platform Notes

- **Linux:** Full support, works best
- **macOS:** Valgrind support limited on recent versions
- **Windows:** Use WSL or generate traces elsewhere

## Troubleshooting

### Valgrind not found

Install Valgrind:

```bash
# Ubuntu/Debian
sudo apt install valgrind

# macOS
brew install valgrind

# Fedora
sudo dnf install valgrind
```

### Compilation errors

Make sure you have a C compiler installed:

```bash
# Ubuntu/Debian
sudo apt install build-essential

# macOS
xcode-select --install
```

### Pattern not detected correctly

Try adjusting the window size:
```bash
memgraph run ./program --window-size=100
```

Or use a different granularity:
```bash
memgraph run ./program --granularity=byte
```
