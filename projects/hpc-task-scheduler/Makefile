.PHONY: build run test clean lint

# 编译
build:
	go build -o bin/server ./cmd/server

# 运行
run: build
	./bin/server

# 测试
test:
	go test ./... -v

# 清理
clean:
	rm -rf bin/

# 代码检查
lint:
	golangci-lint run ./...

# 帮助
help:
	@echo "Available targets:"
	@echo "  build   - Build the server binary"
	@echo "  run     - Build and run the server"
	@echo "  test    - Run all tests"
	@echo "  clean   - Remove build artifacts"
	@echo "  lint    - Run linter"
