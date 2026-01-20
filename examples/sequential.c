/**
 * Sequential array traversal - should show SEQUENTIAL pattern
 *
 * This program demonstrates a classic sequential memory access pattern
 * by traversing an array in order. Hardware prefetchers should handle
 * this pattern very efficiently.
 */

#include <stdlib.h>
#include <stdio.h>

int main() {
    int n = 10000;
    int *arr = malloc(n * sizeof(int));

    if (!arr) {
        fprintf(stderr, "Memory allocation failed\n");
        return 1;
    }

    // Sequential write
    for (int i = 0; i < n; i++) {
        arr[i] = i;
    }

    // Sequential read
    long sum = 0;
    for (int i = 0; i < n; i++) {
        sum += arr[i];
    }

    free(arr);

    // Return something to prevent optimization
    return (int)(sum % 256);
}
