CC = gcc
CFLAGS = -O0 -g  # No optimization to preserve access patterns
PROGRAMS = sequential linked_list working_set random_access strided

.PHONY: all clean test

all: $(PROGRAMS)

%: %.c
	$(CC) $(CFLAGS) -o $@ $<

clean:
	rm -f $(PROGRAMS)

# Test all examples with memgraph (requires memgraph installed)
test: all
	@echo "Testing all example programs with memgraph..."
	@for prog in $(PROGRAMS); do \
		echo ""; \
		echo "======================================"; \
		echo "Testing: $$prog"; \
		echo "======================================"; \
		memgraph run ./$$prog --window-size=50; \
	done

# Run examples individually
run-%: %
	memgraph run ./$< --window-size=50
