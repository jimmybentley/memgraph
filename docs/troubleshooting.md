# Troubleshooting Guide

## Common Issues

### Valgrind Not Found

**Error:**
```
Error: Valgrind not found. Install with:
  Ubuntu/Debian: sudo apt install valgrind
```

**Solution:**

Install Valgrind for your platform:

```bash
# Ubuntu/Debian
sudo apt install valgrind

# macOS (Intel only)
brew install valgrind

# Fedora/RHEL
sudo dnf install valgrind
```

**Note:** Valgrind is not available for macOS ARM (M1/M2/M3). Use Docker with a Linux image or WSL2 on Windows.

---

### Trace File Empty

**Error:**
```
TracingError: Trace file is empty. The program may have:
  - Crashed or exited immediately
  - Not performed any memory accesses
```

**Solutions:**

1. **Program crashes:** Run manually to debug:
   ```bash
   valgrind --tool=lackey --trace-mem=yes ./program
   ```

2. **Program exits too quickly:** Add more operations or increase input size

3. **No memory accesses:** Ensure your program actually accesses memory (not just CPU-bound)

---

### Pattern Confidence Low

**Issue:** MemGraph reports low confidence (<50%) for pattern classification.

**Causes:**
- Mixed access patterns
- Small trace size
- Transitional behavior
- Wrong window size

**Solutions:**

1. **Increase window size:**
   ```bash
   memgraph run ./program --window-size=200
   ```

2. **Try different granularity:**
   ```bash
   memgraph run ./program --granularity=page
   ```

3. **Increase program input size** to get more accesses

4. **Accept that the program has mixed patterns** - this is useful information!

---

### Performance Issues

#### Tracing Too Slow

**Issue:** Valgrind adds 10-100x slowdown.

**Solutions:**

1. **Use smaller inputs** for testing
2. **Set timeout:**
   ```bash
   memgraph run ./program --timeout=300
   ```
3. **Profile a specific phase** rather than full program

#### Analysis Too Slow

**Issue:** Graph construction or graphlet enumeration takes too long.

**Solutions:**

1. **Use sampling:**
   ```bash
   memgraph run ./program --sample --num-samples=50000
   ```

2. **Increase granularity:**
   ```bash
   memgraph run ./program --granularity=page
   ```

3. **Reduce window size:**
   ```bash
   memgraph run ./program --window-size=50
   ```

---

### Compiler Optimizations

**Issue:** Optimizations change access pattern.

**Solution:** Compile with `-O0` to preserve intended pattern:

```bash
gcc -O0 -g program.c -o program
```

For production analysis, use actual optimization level but interpret results in context.

---

### Memory Access Not Captured

**Issue:** Some memory accesses seem missing from analysis.

**Possible Causes:**

1. **Register optimization:** Compiler kept values in registers
   - Solution: Use `-O0` or `volatile` keyword

2. **Stack accesses filtered:** MemGraph may focus on heap accesses
   - Check trace file manually

3. **Instruction fetches:** Disabled by default
   - Enable if needed (usually not useful for data pattern analysis)

---

### macOS ARM (M1/M2/M3) Support

**Issue:** Valgrind not available for ARM Macs.

**Solutions:**

1. **Use Docker:**
   ```bash
   docker run -it --rm -v $(pwd):/work ubuntu:22.04
   apt update && apt install -y valgrind gcc python3 pip
   pip install memgraph
   ```

2. **Use WSL2** (if you also have Windows)

3. **Generate traces on Linux**, analyze anywhere:
   ```bash
   # On Linux machine
   memgraph run ./program --keep-trace --trace-output=trace.log

   # Copy trace.log to Mac
   # On Mac
   memgraph analyze trace.log
   ```

4. **Use alternative tracers** (Intel PIN, DTrace) - requires custom integration

---

### Graph Too Small/Large

#### Graph Too Small

**Issue:** Only a few nodes in graph.

**Causes:**
- Very small program
- High granularity (page-level)
- Large window size

**Solutions:**
- Use `--granularity=byte` or `--granularity=cacheline`
- Decrease window size
- Run program with larger input

#### Graph Too Large

**Issue:** Millions of nodes, analysis very slow.

**Solutions:**
- Use `--granularity=page`
- Increase window size
- Enable sampling: `--sample`
- Analyze only part of execution

---

### CI/CD Integration

#### Reproducibility

**Issue:** Results vary between runs.

**Solutions:**
- Use fixed random seeds in your program
- Use `--window-size` consistently
- Ensure consistent build flags

#### Automated Thresholds

Example CI check:

```bash
# Run analysis
memgraph run ./program --report=json -o result.json

# Check confidence threshold
confidence=$(jq '.confidence' result.json)
if (( $(echo "$confidence < 0.7" | bc -l) )); then
    echo "Low confidence: $confidence"
    exit 1
fi

# Check for undesired pattern
pattern=$(jq -r '.detected_pattern' result.json)
if [ "$pattern" = "RANDOM" ]; then
    echo "Warning: Random access detected"
    exit 1
fi
```

---

### Getting Help

1. **Check verbose output:**
   ```bash
   memgraph run ./program --verbose
   ```

2. **Run Valgrind manually** to debug tracing:
   ```bash
   valgrind --tool=lackey --trace-mem=yes ./program 2>&1 | head
   ```

3. **Examine trace file:**
   ```bash
   memgraph run ./program --keep-trace
   cat /tmp/memgraph_*.trace | head -20
   ```

4. **File an issue:**
   [https://github.com/jimmybentley/memgraph/issues](https://github.com/jimmybentley/memgraph/issues)

## Debugging Checklist

- [ ] Valgrind installed and working: `valgrind --version`
- [ ] Program compiles: `gcc program.c -o program`
- [ ] Program runs: `./program`
- [ ] Program makes memory accesses (not just CPU-bound)
- [ ] Using appropriate window size for program scale
- [ ] Compiled with `-O0` if studying specific pattern
- [ ] Enough trace data (>1000 accesses recommended)

## Platform-Specific Issues

### Linux

Generally works well. If issues:
- Ensure Valgrind 3.10+ installed
- Check kernel compatibility (old kernels may have issues)

### macOS Intel

- Valgrind may be slower than on Linux
- Some macOS-specific libraries may cause issues
- Consider using Docker for consistency

### Windows/WSL2

- WSL2 generally works well
- Ensure WSL2 is Ubuntu 20.04+ or Debian 11+
- File system performance: keep files in Linux filesystem, not /mnt/c/

## Advanced Debugging

### Enable Valgrind Verbose Output

```bash
valgrind --tool=lackey --trace-mem=yes -v ./program
```

### Inspect Graph Structure

```bash
# Save graph
memgraph build trace.log -o graph.pkl --stats

# Examine in Python
python3
>>> import pickle
>>> import networkx as nx
>>> with open('graph.pkl', 'rb') as f:
...     graph = pickle.load(f)
>>> print(f"Nodes: {graph.number_of_nodes()}")
>>> print(f"Edges: {graph.number_of_edges()}")
```

### Compare Different Settings

```bash
# Try different parameters
memgraph run ./program --window-size=50 -o report1.html --report=html
memgraph run ./program --window-size=200 -o report2.html --report=html
# Compare reports
```
