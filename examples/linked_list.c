/**
 * Linked list traversal - should show POINTER_CHASE pattern
 *
 * This program demonstrates a pointer-chasing access pattern typical
 * of linked data structures. Each access depends on the previous one,
 * making prefetching difficult.
 */

#include <stdlib.h>
#include <stdio.h>

struct Node {
    int value;
    struct Node *next;
};

int main() {
    int n = 1000;

    // Build linked list
    struct Node *head = malloc(sizeof(struct Node));
    if (!head) {
        fprintf(stderr, "Memory allocation failed\n");
        return 1;
    }

    struct Node *curr = head;
    for (int i = 0; i < n; i++) {
        curr->value = i;
        curr->next = malloc(sizeof(struct Node));
        if (!curr->next && i < n - 1) {
            fprintf(stderr, "Memory allocation failed\n");
            return 1;
        }
        curr = curr->next;
    }
    curr->next = NULL;

    // Traverse
    long sum = 0;
    curr = head;
    while (curr != NULL) {
        sum += curr->value;
        struct Node *temp = curr;
        curr = curr->next;
        free(temp);
    }

    // Return something to prevent optimization
    return (int)(sum % 256);
}
