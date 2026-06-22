.PHONY: build test clean run help

# Default target
all: build

# Build the WAL server
build:
	@echo "Building WAL server..."
	go build -o bin/wal-server cmd/wal-server/main.go
	@echo "Build complete: bin/wal-server"

# Run tests
test:
	@echo "Running tests..."
	go test -v ./test/...

# Run tests with coverage
test-cover:
	@echo "Running tests with coverage..."
	go test -coverprofile=coverage.out ./test/...
	go tool cover -html=coverage.out

# Run the WAL server
run: build
	@echo "Running WAL server..."
	./bin/wal-server

# Run the example
example:
	@echo "Running example..."
	go run examples/usage.go

# Clean build artifacts
clean:
	@echo "Cleaning..."
	rm -rf bin/
	rm -f coverage.out
	@echo "Clean complete"

# Format code
fmt:
	@echo "Formatting code..."
	go fmt ./...

# Lint code
lint:
	@echo "Linting code..."
	golint ./...

# Vet code
vet:
	@echo "Vetting code..."
	go vet ./...

# Show help
help:
	@echo "Available targets:"
	@echo "  build       - Build the WAL server"
	@echo "  test        - Run tests"
	@echo "  test-cover  - Run tests with coverage"
	@echo "  run         - Build and run the WAL server"
	@echo "  example     - Run the example"
	@echo "  clean       - Clean build artifacts"
	@echo "  fmt         - Format code"
	@echo "  lint        - Lint code"
	@echo "  vet         - Vet code"
	@echo "  help        - Show this help"
