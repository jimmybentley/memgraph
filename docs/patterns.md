# Memory Access Pattern Reference

This document describes the memory access patterns that MemGraph can detect and classify.

## Pattern Overview

| Pattern | Characteristics | Common Sources | Cache Performance |
|---------|----------------|----------------|-------------------|
| SEQUENTIAL | Consecutive addresses | Array traversal | Excellent |
| STRIDED | Fixed stride | Column-major access | Good |
| RANDOM | Unpredictable | Hash tables | Poor |
| POINTER_CHASE | Dependent loads | Linked lists | Poor |
| WORKING_SET | Small reuse set | Tight loops | Excellent |
| PRODUCER_CONSUMER | Streaming | Pipelines | Variable |

## Detailed Patterns

### SEQUENTIAL

**Description:** Linear traversal of consecutive memory addresses.

**Graph Characteristics:**
- Long chains of connected nodes
- High ratio of 2-paths and edges
- Low branching factor

**Example Code:**
```c
for (int i = 0; i < n; i++) {
    array[i] = i;
}
```

**Performance:**
- ✅ Excellent spatial locality
- ✅ Hardware prefetcher friendly
- ✅ High cache hit rates
- ✅ Optimal for SIMD operations

**Recommendations:**
- Enable hardware prefetchers (usually on by default)
- Consider software prefetch for very large strides
- Use streaming stores for write-heavy workloads
- Align data to cache line boundaries

---

### STRIDED

**Description:** Regular access pattern with fixed stride between addresses.

**Graph Characteristics:**
- Multiple disconnected chains or sparse connections
- Consistent spacing between accessed addresses
- Moderate graphlet diversity

**Example Code:**
```c
// Column-major traversal of row-major array
for (int col = 0; col < cols; col++) {
    for (int row = 0; row < rows; row++) {
        sum += matrix[row][col];  // Stride = row_width
    }
}
```

**Performance:**
- ⚠️ Moderate spatial locality
- ⚠️ Some prefetchers can adapt
- ⚠️ Cache efficiency depends on stride

**Recommendations:**
- Prefer array-of-structs over struct-of-arrays when possible
- Use loop interchange to improve access pattern
- Align data structures to cache line boundaries
- Consider streaming prefetch with stride hint

**Optimization Example:**
```c
// Before (strided)
for (int col = 0; col < cols; col++)
    for (int row = 0; row < rows; row++)
        sum += matrix[row][col];

// After (sequential)
for (int row = 0; row < rows; row++)
    for (int col = 0; col < cols; col++)
        sum += matrix[row][col];
```

---

### RANDOM

**Description:** Unpredictable memory accesses with no clear pattern.

**Graph Characteristics:**
- Sparse graph with many isolated nodes
- Low clustering coefficient
- High graphlet diversity

**Example Code:**
```c
// Hash table lookup
for (int i = 0; i < queries; i++) {
    int index = hash(keys[i]) % table_size;
    result += table[index];
}
```

**Performance:**
- ❌ Poor spatial locality
- ❌ Poor temporal locality
- ❌ Prefetching ineffective
- ❌ High cache miss rate

**Recommendations:**
- Increase cache size if possible
- Use cache-aware data structures (B-trees vs binary trees)
- Consider software prefetching if access pattern is predictable
- Batch operations to improve locality
- Use bloom filters to avoid unnecessary accesses

---

### POINTER_CHASE

**Description:** Each memory access depends on the value from the previous access.

**Graph Characteristics:**
- Long chains with sequential dependencies
- High average path length
- Low branching

**Example Code:**
```c
struct Node {
    int data;
    struct Node *next;
};

// Linked list traversal
Node *curr = head;
while (curr != NULL) {
    sum += curr->data;
    curr = curr->next;  // Depends on previous load
}
```

**Performance:**
- ❌ Impossible to prefetch effectively
- ❌ Serialized memory access
- ❌ Latency-bound performance
- ⚠️ May benefit from memory-level parallelism if multiple chains

**Recommendations:**
- Convert to array-based structures when possible
- Use pointer prefetching (limited effectiveness)
- Unroll loops to expose memory-level parallelism
- Consider cache-oblivious algorithms
- Use array-of-pointers to improve spatial locality

**Optimization Example:**
```c
// Convert linked list to array
int *array = malloc(n * sizeof(int));
int idx = 0;
Node *curr = head;
while (curr != NULL) {
    array[idx++] = curr->data;
    curr = curr->next;
}

// Now traverse array (sequential pattern)
for (int i = 0; i < n; i++) {
    sum += array[i];
}
```

---

### WORKING_SET

**Description:** Repeated access to a small set of memory locations.

**Graph Characteristics:**
- Dense subgraph with high clustering
- Many triangles and cliques
- Small number of unique nodes

**Example Code:**
```c
#define WS_SIZE 64
int working_set[WS_SIZE];

for (int iter = 0; iter < many_iterations; iter++) {
    int idx = iter % WS_SIZE;
    result += working_set[idx];
}
```

**Performance:**
- ✅ Excellent temporal locality
- ✅ Fits in cache
- ✅ Low memory bandwidth
- ✅ Predictable performance

**Recommendations:**
- Ensure working set fits in L1/L2 cache
- Minimize working set size where possible
- Use smaller data types if appropriate
- Consider cache blocking for larger computations

---

### PRODUCER_CONSUMER

**Description:** Streaming pattern where data is written once and read once.

**Graph Characteristics:**
- Bipartite-like structure
- Write followed by read pattern
- Moderate temporal distance between accesses

**Example Code:**
```c
// Producer writes to buffer
for (int i = 0; i < n; i++) {
    buffer[i] = produce(i);
}

// Consumer reads from buffer
for (int i = 0; i < n; i++) {
    consume(buffer[i]);
}
```

**Performance:**
- ✅ Good if consumer follows producer closely
- ⚠️ Depends on temporal distance
- ⚠️ May benefit from explicit cache control

**Recommendations:**
- Reduce temporal distance between producer and consumer
- Use smaller buffers to keep data in cache
- Consider double buffering for pipelined workloads
- Use streaming stores if data won't be reused

## Pattern Combinations

Real programs often exhibit multiple patterns:

**Segmented Patterns:**
```
Initialization (SEQUENTIAL) → Processing (RANDOM) → Output (SEQUENTIAL)
```

**Nested Patterns:**
```
Outer loop (SEQUENTIAL) → Inner loop (POINTER_CHASE)
```

## Detection Confidence

MemGraph reports a confidence score for pattern classification:

- **High (>70%):** Clear match, recommendations likely applicable
- **Medium (50-70%):** Probable match, verify recommendations
- **Low (<50%):** Ambiguous, may be mixed or transitioning pattern

## Further Reading

- [Interpreting Reports](interpreting.md) - How to read MemGraph output
- [Examples](/examples/) - Sample programs for each pattern
