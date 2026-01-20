/**
 * Strided access pattern - should show STRIDED pattern
 *
 * This program demonstrates strided memory access, typical of
 * column-major traversal of row-major arrays or accessing
 * specific fields in arrays of structs.
 */

#include <stdlib.h>
#include <stdio.h>

#define ROWS 100
#define COLS 100

int main() {
    // Allocate 2D array (row-major in C)
    int **matrix = malloc(ROWS * sizeof(int *));
    if (!matrix) {
        fprintf(stderr, "Memory allocation failed\n");
        return 1;
    }

    for (int i = 0; i < ROWS; i++) {
        matrix[i] = malloc(COLS * sizeof(int));
        if (!matrix[i]) {
            fprintf(stderr, "Memory allocation failed\n");
            return 1;
        }
    }

    // Initialize
    for (int i = 0; i < ROWS; i++) {
        for (int j = 0; j < COLS; j++) {
            matrix[i][j] = i * COLS + j;
        }
    }

    // Column-major traversal (strided access)
    long sum = 0;
    for (int j = 0; j < COLS; j++) {
        for (int i = 0; i < ROWS; i++) {
            sum += matrix[i][j];
        }
    }

    // Cleanup
    for (int i = 0; i < ROWS; i++) {
        free(matrix[i]);
    }
    free(matrix);

    // Return something to prevent optimization
    return (int)(sum % 256);
}
