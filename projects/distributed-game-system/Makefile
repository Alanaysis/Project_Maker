.PHONY: all build clean test run-server run-client proto

# 默认目标
all: build

# 编译所有
build: proto
	go build -o bin/server ./cmd/server
	go build -o bin/client ./cmd/client

# 编译服务器
build-server:
	go build -o bin/server ./cmd/server

# 编译客户端
build-client:
	go build -o bin/client ./cmd/client

# 生成 Protobuf 代码
proto:
	protoc --go_out=. --go_opt=paths=source_relative proto/*.proto

# 运行测试
test:
	go test ./... -v

# 运行测试并显示覆盖率
test-cover:
	go test ./... -coverprofile=coverage.out
	go tool cover -html=coverage.out

# 运行服务器
run-server: build-server
	./bin/server

# 运行客户端
run-client: build-client
	./bin/client

# 清理
clean:
	rm -rf bin/
	rm -f coverage.out

# 格式化代码
fmt:
	go fmt ./...

# 代码检查
lint:
	golint ./...
	go vet ./...

# 依赖管理
deps:
	go mod tidy

# 帮助
help:
	@echo "Available targets:"
	@echo "  all          - Build everything"
	@echo "  build        - Build server and client"
	@echo "  build-server - Build server only"
	@echo "  build-client - Build client only"
	@echo "  proto        - Generate protobuf code"
	@echo "  test         - Run tests"
	@echo "  test-cover   - Run tests with coverage"
	@echo "  run-server   - Build and run server"
	@echo "  run-client   - Build and run client"
	@echo "  clean        - Clean build artifacts"
	@echo "  fmt          - Format code"
	@echo "  lint         - Run linter"
	@echo "  deps         - Manage dependencies"
