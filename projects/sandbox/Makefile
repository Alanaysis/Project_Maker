# Sandbox Isolation Project
# Implements process sandboxing with seccomp syscall filtering

CC = gcc
CFLAGS = -Wall -Wextra -Werror -std=c11 -D_GNU_SOURCE -Iinclude
LDFLAGS =

# Directories
SRCDIR = src
BUILDDIR = build
TESTSDIR = tests
EXAMPLESDIR = examples

# Source files
SRC = $(SRCDIR)/sandbox.c
OBJ = $(BUILDDIR)/sandbox.o
LIB = $(BUILDDIR)/libsandbox.a

# Test files
TEST_SRC = $(TESTSDIR)/test_sandbox.c
TEST_BIN = $(BUILDDIR)/test_sandbox

# Example files
EXAMPLES = basic_whitelist block_network strict_sandbox
EXAMPLE_BINS = $(addprefix $(BUILDDIR)/,$(EXAMPLES))

.PHONY: all clean test examples help

all: $(LIB) examples $(TEST_BIN)

help:
	@echo "Sandbox Isolation Project"
	@echo "========================"
	@echo ""
	@echo "Targets:"
	@echo "  all       - Build library and examples (default)"
	@echo "  lib       - Build sandbox static library"
	@echo "  examples  - Build example programs"
	@echo "  test      - Build and run tests"
	@echo "  clean     - Remove build artifacts"
	@echo ""
	@echo "Examples:"
	@echo "  ./build/basic_whitelist /bin/echo Hello"
	@echo "  ./build/block_network /usr/bin/curl http://example.com"
	@echo "  ./build/strict_sandbox /bin/echo Strict mode"

# Build directories
$(BUILDDIR):
	mkdir -p $(BUILDDIR)

# Compile source
$(BUILDDIR)/sandbox.o: $(SRCDIR)/sandbox.c include/sandbox.h | $(BUILDDIR)
	$(CC) $(CFLAGS) -c $< -o $@

# Static library
$(LIB): $(OBJ)
	ar rcs $@ $^

# Examples
examples: $(EXAMPLE_BINS)

$(BUILDDIR)/basic_whitelist: $(EXAMPLESDIR)/basic_whitelist.c $(LIB) | $(BUILDDIR)
	$(CC) $(CFLAGS) $< -L$(BUILDDIR) -lsandbox -o $@

$(BUILDDIR)/block_network: $(EXAMPLESDIR)/block_network.c $(LIB) | $(BUILDDIR)
	$(CC) $(CFLAGS) $< -L$(BUILDDIR) -lsandbox -o $@

$(BUILDDIR)/strict_sandbox: $(EXAMPLESDIR)/strict_sandbox.c $(LIB) | $(BUILDDIR)
	$(CC) $(CFLAGS) $< -L$(BUILDDIR) -lsandbox -o $@

# Tests
test: $(TEST_BIN)
	@echo ""
	@echo "Running sandbox tests..."
	@echo "========================"
	$(TEST_BIN)
	@echo ""
	@echo "Note: Some tests are skipped without root privileges."
	@echo "Run 'sudo make test' for the full test suite."

$(TEST_BIN): $(TEST_SRC) $(LIB) | $(BUILDDIR)
	$(CC) $(CFLAGS) $< -L$(BUILDDIR) -lsandbox -o $@

# Clean
clean:
	rm -rf $(BUILDDIR)
