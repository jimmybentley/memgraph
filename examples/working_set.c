/**
 * Working set pattern - should show WORKING_SET pattern
 *
 * This program demonstrates dense reuse within a small working set.
 * The same cache lines are accessed repeatedly, showing good temporal
 * locality.
 */

#include <stdlib.h>
#include <stdio.h>

int main() {
    int ws_size = 64;  // Small working set
    int iterations = 10000;
    int *arr = malloc(ws_size * sizeof(int));

    if (!arr) {
        fprintf(stderr, "Memory allocation failed\n");
        return 1;
    }

    // Initialize
    for (int i = 0; i < ws_size; i++) {
        arr[i] = i;
    }

    // Dense reuse within working set
    long sum = 0;
    for (int i = 0; i < iterations; i++) {
        int idx = i % ws_size;
        sum += arr[idx];
        arr[idx] = (int)(sum % 1000);
    }

    free(arr);

    // Return something to prevent optimization
    return (int)(sum % 256);
}
