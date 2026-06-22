.PHONY: build test run examples clean docs

# Build the project
build:
	cargo build

# Build release version
release:
	cargo build --release

# Run all tests
test:
	cargo test

# Run tests with output
test-verbose:
	cargo test -- --nocapture

# Run the main server
run:
	cargo run

# Run examples
example-simple:
	cargo run --example simple_server

example-calculator:
	cargo run --example calculator_tool

example-client:
	cargo run --example client_example

example-builtin:
	cargo run --example builtin_tools

# Generate documentation
docs:
	cargo doc --open

# Check code
check:
	cargo check
	cargo clippy

# Format code
fmt:
	cargo fmt

# Clean build artifacts
clean:
	cargo clean

# Run all checks
all: fmt check test

# Help
help:
	@echo "Available targets:"
	@echo "  build          - Build the project"
	@echo "  release        - Build release version"
	@echo "  test           - Run all tests"
	@echo "  test-verbose   - Run tests with output"
	@echo "  run            - Run the main server"
	@echo "  example-simple - Run simple server example"
	@echo "  example-calculator - Run calculator example"
	@echo "  example-client - Run client example"
	@echo "  example-builtin - Run builtin tools example"
	@echo "  docs           - Generate documentation"
	@echo "  check          - Check code with clippy"
	@echo "  fmt            - Format code"
	@echo "  clean          - Clean build artifacts"
	@echo "  all            - Run fmt, check, and test"
	@echo "  help           - Show this help"
