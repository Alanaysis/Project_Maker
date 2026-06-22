#!/bin/bash

# WAL Project Build Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Go is installed
check_go() {
    if ! command -v go &> /dev/null; then
        print_error "Go is not installed. Please install Go first."
        exit 1
    fi
    print_info "Go version: $(go version)"
}

# Build the project
build() {
    print_info "Building WAL server..."
    mkdir -p bin
    go build -o bin/wal-server cmd/wal-server/main.go
    print_info "Build complete: bin/wal-server"
}

# Run tests
test() {
    print_info "Running tests..."
    go test -v ./test/...
    print_info "Tests complete"
}

# Run tests with coverage
test_cover() {
    print_info "Running tests with coverage..."
    go test -coverprofile=coverage.out ./test/...
    go tool cover -html=coverage.out
    print_info "Coverage report generated: coverage.out"
}

# Run the example
example() {
    print_info "Running example..."
    go run examples/usage.go
}

# Clean build artifacts
clean() {
    print_info "Cleaning build artifacts..."
    rm -rf bin/
    rm -f coverage.out
    print_info "Clean complete"
}

# Format code
fmt() {
    print_info "Formatting code..."
    go fmt ./...
    print_info "Formatting complete"
}

# Vet code
vet() {
    print_info "Vetting code..."
    go vet ./...
    print_info "Vetting complete"
}

# Show help
help() {
    echo "WAL Project Build Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  build       Build the WAL server"
    echo "  test        Run tests"
    echo "  test-cover  Run tests with coverage"
    echo "  example     Run the example"
    echo "  clean       Clean build artifacts"
    echo "  fmt         Format code"
    echo "  vet         Vet code"
    echo "  help        Show this help"
}

# Main script
check_go

case "${1:-help}" in
    build)
        build
        ;;
    test)
        test
        ;;
    test-cover)
        test_cover
        ;;
    example)
        example
        ;;
    clean)
        clean
        ;;
    fmt)
        fmt
        ;;
    vet)
        vet
        ;;
    help|*)
        help
        ;;
esac
