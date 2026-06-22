.PHONY: build run test clean fmt vet docs help

# Default target
all: build

# Build the CDN server
build:
	@echo "Building CDN server..."
	go build -o bin/cdn-server cmd/cdn-server/main.go
	@echo "Build complete: bin/cdn-server"

# Run the CDN server
run: build
	@echo "Starting CDN server..."
	./bin/cdn-server -addr :8080 -origin http://localhost:9090

# Run with custom options
run-custom: build
	@echo "Starting CDN server with custom options..."
	./bin/cdn-server -addr $(ADDR) -origin $(ORIGIN) -ttl $(TTL)

# Run tests
test:
	@echo "Running tests..."
	go test -v ./...

# Run tests with coverage
test-coverage:
	@echo "Running tests with coverage..."
	go test -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out -o coverage.html
	@echo "Coverage report: coverage.html"

# Run benchmarks
bench:
	@echo "Running benchmarks..."
	go test -bench=. ./...

# Format code
fmt:
	@echo "Formatting code..."
	go fmt ./...

# Run static analysis
vet:
	@echo "Running static analysis..."
	go vet ./...

# Run linter (requires golangci-lint)
lint:
	@echo "Running linter..."
	golangci-lint run

# Clean build artifacts
clean:
	@echo "Cleaning..."
	rm -rf bin/
	rm -f coverage.out coverage.html

# Generate documentation
docs:
	@echo "Generating documentation..."
	godoc -http=:6060

# Install dependencies
deps:
	@echo "Installing dependencies..."
	go mod tidy

# Run example origin server
origin:
	@echo "Starting example origin server..."
	go run examples/origin-server.go

# Help
help:
	@echo "Available targets:"
	@echo "  build         - Build the CDN server"
	@echo "  run           - Build and run the CDN server"
	@echo "  run-custom    - Run with custom options (ADDR, ORIGIN, TTL)"
	@echo "  test          - Run tests"
	@echo "  test-coverage - Run tests with coverage report"
	@echo "  bench         - Run benchmarks"
	@echo "  fmt           - Format code"
	@echo "  vet           - Run static analysis"
	@echo "  lint          - Run linter"
	@echo "  clean         - Clean build artifacts"
	@echo "  docs          - Generate documentation"
	@echo "  deps          - Install dependencies"
	@echo "  origin        - Run example origin server"
	@echo "  help          - Show this help"