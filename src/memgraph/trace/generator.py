"""Synthetic trace generation for testing and validation."""

import random
from pathlib import Path
from typing import Literal, Optional
from memgraph.trace.models import MemoryAccess, Trace


def generate_sequential(
    n: int,
    start_addr: int = 0x1000,
    stride: int = 8,
    operation: Literal["R", "W", "mixed"] = "R"
) -> Trace:
    """Generate a linear sequential access pattern.

    Args:
        n: Number of memory accesses to generate
        start_addr: Starting memory address
        stride: Byte stride between accesses
        operation: Operation type ("R", "W", or "mixed")

    Returns:
        Trace with sequential access pattern
    """
    accesses = []
    for i in range(n):
        addr = start_addr + (i * stride)
        if operation == "mixed":
            op = "R" if i % 2 == 0 else "W"
        else:
            op = operation

        accesses.append(MemoryAccess(
            operation=op,  # type: ignore
            address=addr,
            size=stride,
            timestamp=i
        ))

    return Trace.from_accesses(
        accesses,
        Path("<generated:sequential>"),
        "synthetic"
    )


def generate_random(
    n: int,
    addr_range: tuple[int, int] = (0x1000, 0x10000),
    size: int = 8,
    operation: Literal["R", "W", "mixed"] = "R",
    seed: Optional[int] = None
) -> Trace:
    """Generate a uniform random access pattern.

    Args:
        n: Number of memory accesses to generate
        addr_range: Tuple of (min_addr, max_addr)
        size: Access size in bytes
        operation: Operation type ("R", "W", or "mixed")
        seed: Random seed for reproducibility

    Returns:
        Trace with random access pattern
    """
    if seed is not None:
        random.seed(seed)

    accesses = []
    min_addr, max_addr = addr_range

    for i in range(n):
        # Align addresses to size boundary
        addr = random.randrange(min_addr, max_addr, size)

        if operation == "mixed":
            op = random.choice(["R", "W"])
        else:
            op = operation

        accesses.append(MemoryAccess(
            operation=op,  # type: ignore
            address=addr,
            size=size,
            timestamp=i
        ))

    return Trace.from_accesses(
        accesses,
        Path("<generated:random>"),
        "synthetic"
    )


def generate_strided(
    n: int,
    start_addr: int = 0x1000,
    stride: int = 64,
    count: int = 100,
    size: int = 8,
    operation: Literal["R", "W", "mixed"] = "R"
) -> Trace:
    """Generate a strided access pattern (e.g., array column traversal).

    This simulates accessing every Nth element, like iterating over columns
    in a row-major array.

    Args:
        n: Total number of memory accesses to generate
        start_addr: Starting memory address
        stride: Byte stride between accesses
        count: Number of elements in the strided pattern before wrapping
        size: Access size in bytes
        operation: Operation type ("R", "W", or "mixed")

    Returns:
        Trace with strided access pattern
    """
    accesses = []

    for i in range(n):
        # Calculate position in strided pattern
        offset = (i % count) * stride
        addr = start_addr + offset

        if operation == "mixed":
            op = "R" if i % 2 == 0 else "W"
        else:
            op = operation

        accesses.append(MemoryAccess(
            operation=op,  # type: ignore
            address=addr,
            size=size,
            timestamp=i
        ))

    return Trace.from_accesses(
        accesses,
        Path("<generated:strided>"),
        "synthetic"
    )


def generate_pointer_chase(
    n: int,
    num_nodes: int = 100,
    start_addr: int = 0x1000,
    node_size: int = 64,
    operation: Literal["R", "W", "mixed"] = "R",
    seed: Optional[int] = None
) -> Trace:
    """Generate a simulated linked list traversal pattern.

    Creates a random permutation of nodes and simulates traversing them
    in that order, like following pointers in a linked list.

    Args:
        n: Number of memory accesses to generate
        num_nodes: Number of nodes in the linked structure
        start_addr: Starting memory address for nodes
        node_size: Size of each node in bytes
        operation: Operation type ("R", "W", or "mixed")
        seed: Random seed for reproducibility

    Returns:
        Trace with pointer-chasing pattern
    """
    if seed is not None:
        random.seed(seed)

    # Create random permutation of nodes (linked list order)
    nodes = list(range(num_nodes))
    random.shuffle(nodes)

    accesses = []

    for i in range(n):
        # Follow the linked list pattern cyclically
        node_idx = nodes[i % num_nodes]
        addr = start_addr + (node_idx * node_size)

        if operation == "mixed":
            op = random.choice(["R", "W"])
        else:
            op = operation

        accesses.append(MemoryAccess(
            operation=op,  # type: ignore
            address=addr,
            size=8,  # Typically reading a pointer
            timestamp=i
        ))

    return Trace.from_accesses(
        accesses,
        Path("<generated:pointer_chase>"),
        "synthetic"
    )


def generate_working_set(
    n: int,
    working_set_size: int = 50,
    total_addresses: int = 1000,
    hot_probability: float = 0.8,
    start_addr: int = 0x1000,
    size: int = 8,
    operation: Literal["R", "W", "mixed"] = "R",
    seed: Optional[int] = None
) -> Trace:
    """Generate a pattern with dense reuse within a working set.

    Simulates temporal locality where a small working set is accessed
    frequently, with occasional accesses to a larger cold set.

    Args:
        n: Number of memory accesses to generate
        working_set_size: Number of addresses in the hot working set
        total_addresses: Total number of possible addresses
        hot_probability: Probability of accessing hot set (0.0 to 1.0)
        start_addr: Starting memory address
        size: Access size in bytes
        operation: Operation type ("R", "W", or "mixed")
        seed: Random seed for reproducibility

    Returns:
        Trace with working set pattern
    """
    if seed is not None:
        random.seed(seed)

    if working_set_size > total_addresses:
        raise ValueError("Working set size cannot exceed total addresses")

    # Define hot and cold address sets
    all_addrs = [start_addr + i * size for i in range(total_addresses)]
    hot_addrs = all_addrs[:working_set_size]
    cold_addrs = all_addrs[working_set_size:]

    accesses = []

    for i in range(n):
        # Choose from hot or cold set based on probability
        if random.random() < hot_probability and hot_addrs:
            addr = random.choice(hot_addrs)
        else:
            addr = random.choice(cold_addrs) if cold_addrs else random.choice(hot_addrs)

        if operation == "mixed":
            op = random.choice(["R", "W"])
        else:
            op = operation

        accesses.append(MemoryAccess(
            operation=op,  # type: ignore
            address=addr,
            size=size,
            timestamp=i
        ))

    return Trace.from_accesses(
        accesses,
        Path("<generated:working_set>"),
        "synthetic"
    )


# Pattern name to generator function mapping
GENERATORS = {
    "sequential": generate_sequential,
    "random": generate_random,
    "strided": generate_strided,
    "pointer_chase": generate_pointer_chase,
    "working_set": generate_working_set,
}


def get_available_patterns() -> list[str]:
    """Get list of available synthetic pattern names."""
    return list(GENERATORS.keys())
