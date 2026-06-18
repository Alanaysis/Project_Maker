.PHONY: all build run test clean

# 变量
APP_NAME=chat-server
BUILD_DIR=./bin
MAIN_PATH=./cmd/server

# 默认目标
all: build

# 编译
build:
	@echo "Building $(APP_NAME)..."
	@mkdir -p $(BUILD_DIR)
	go build -o $(BUILD_DIR)/$(APP_NAME) $(MAIN_PATH)
	@echo "Build complete: $(BUILD_DIR)/$(APP_NAME)"

# 运行
run:
	@echo "Starting server..."
	go run $(MAIN_PATH)

# 测试
test:
	@echo "Running tests..."
	go test -v ./...

# 清理
clean:
	@echo "Cleaning..."
	@rm -rf $(BUILD_DIR)
	@rm -rf ./data
	@echo "Clean complete"

# 安装依赖
deps:
	@echo "Installing dependencies..."
	go mod tidy

# 格式化代码
fmt:
	@echo "Formatting code..."
	go fmt ./...

# 代码检查
lint:
	@echo "Running linter..."
	golangci-lint run

# 生成文档
docs:
	@echo "Documentation is in the docs/ directory"

# 帮助
help:
	@echo "Available targets:"
	@echo "  all     - Build the application (default)"
	@echo "  build   - Build the application"
	@echo "  run     - Run the server"
	@echo "  test    - Run tests"
	@echo "  clean   - Clean build artifacts"
	@echo "  deps    - Install dependencies"
	@echo "  fmt     - Format code"
	@echo "  lint    - Run linter"
	@echo "  docs    - Show documentation location"
	@echo "  help    - Show this help"