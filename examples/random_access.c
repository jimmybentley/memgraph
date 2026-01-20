/**
 * Random access pattern - should show RANDOM pattern
 *
 * This program demonstrates random memory accesses with poor spatial
 * and temporal locality. Prefetchers and caches will struggle with
 * this pattern.
 */

#include <stdlib.h>
#include <stdio.h>

int main() {
    int n = 1000;
    int accesses = 10000;
    int *arr = malloc(n * sizeof(int));

    if (!arr) {
        fprintf(stderr, "Memory allocation failed\n");
        return 1;
    }

    // Initialize
    for (int i = 0; i < n; i++) {
        arr[i] = i;
    }

    // Random accesses (LCG for reproducibility)
    unsigned int seed = 12345;
    long sum = 0;
    for (int i = 0; i < accesses; i++) {
        // Linear Congruential Generator
        seed = seed * 1103515245 + 12345;
        int idx = (seed >> 16) % n;
        sum += arr[idx];
    }

    free(arr);

    // Return something to prevent optimization
    return (int)(sum % 256);
}
