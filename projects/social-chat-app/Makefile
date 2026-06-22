.PHONY: all build run test clean tidy

APP_NAME=chat-server
CLIENT_NAME=chat-client
BUILD_DIR=./bin

all: build

# Install dependencies
tidy:
	go mod tidy

# Build server and client
build: tidy
	@echo "Building $(APP_NAME) and $(CLIENT_NAME)..."
	@mkdir -p $(BUILD_DIR)
	CGO_ENABLED=1 go build -o $(BUILD_DIR)/$(APP_NAME) ./cmd/server
	CGO_ENABLED=1 go build -o $(BUILD_DIR)/$(CLIENT_NAME) ./cmd/client
	@echo "Build complete: $(BUILD_DIR)/$(APP_NAME), $(BUILD_DIR)/$(CLIENT_NAME)"

# Build server only
build-server: tidy
	@mkdir -p $(BUILD_DIR)
	CGO_ENABLED=1 go build -o $(BUILD_DIR)/$(APP_NAME) ./cmd/server
	@echo "Server built: $(BUILD_DIR)/$(APP_NAME)"

# Build client only
build-client: tidy
	@mkdir -p $(BUILD_DIR)
	CGO_ENABLED=1 go build -o $(BUILD_DIR)/$(CLIENT_NAME) ./cmd/client
	@echo "Client built: $(BUILD_DIR)/$(CLIENT_NAME)"

# Run server
run: build-server
	@mkdir -p data
	./$(BUILD_DIR)/$(APP_NAME)

# Run server in development mode
dev:
	@mkdir -p data
	go run ./cmd/server

# Run tests
test:
	go test -v ./tests/...

# Run tests with coverage
test-cover:
	go test -v -coverprofile=coverage.out ./tests/...
	go tool cover -func=coverage.out
	@rm -f coverage.out

# Clean build artifacts
clean:
	rm -rf $(BUILD_DIR) data *.db coverage.out

# Format code
fmt:
	go fmt ./...

# Lint
lint:
	golangci-lint run ./...

# Help
help:
	@echo "Available targets:"
	@echo "  make build        - Build server and client"
	@echo "  make build-server - Build server only"
	@echo "  make build-client - Build client only"
	@echo "  make run          - Build and run server"
	@echo "  make dev          - Run server in development mode"
	@echo "  make test         - Run all tests"
	@echo "  make test-cover   - Run tests with coverage"
	@echo "  make clean        - Remove build artifacts"
	@echo "  make fmt          - Format code"
	@echo "  make lint         - Lint code"
	@echo "  make tidy         - Install dependencies"
	@echo "  make help         - Show this help"
