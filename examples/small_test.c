/**
 * Small test program for quick testing
 */

#include <stdlib.h>

int main() {
    int n = 100;
    int *arr = malloc(n * sizeof(int));

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
    return (int)(sum % 256);
}
