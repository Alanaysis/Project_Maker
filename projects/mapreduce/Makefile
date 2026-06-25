.PHONY: build test clean run lint help

# 默认目标
all: build

# 帮助信息
help:
	@echo "Usage:"
	@echo "  make build       - Build coordinator and worker"
	@echo "  make test        - Run tests"
	@echo "  make clean       - Clean build artifacts"
	@echo "  make run         - Run wordcount example"
	@echo "  make lint        - Run linter"
	@echo "  make benchmark   - Run benchmarks"

# 编译
build: build-coordinator build-worker

build-coordinator:
	go build -o bin/coordinator ./cmd/coordinator

build-worker:
	go build -o bin/worker ./cmd/worker

# 测试
test:
	go test -race -v ./...

test-cover:
	go test -race -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out -o coverage.html

# 清理
clean:
	rm -rf bin/ tmp/ mr-out-* coverage.out coverage.html

# 运行示例
run: build
	@echo "Starting Coordinator..."
	@./bin/coordinator -port 8888 -nreduce 3 testdata/pg-*.txt &
	@sleep 2
	@echo "Starting Workers..."
	@./bin/worker -coordinator localhost:8888 -app wordcount &
	@./bin/worker -coordinator localhost:8888 -app wordcount &
	@echo "Waiting for completion..."
	@wait
	@echo "Results:"
	@cat mr-out-* | sort | head -20

# 代码检查
lint:
	go vet ./...
	golangci-lint run ./...

# 基准测试
benchmark:
	go test -bench=. ./...

# Docker 构建
docker:
	docker build -t mapreduce .

# 格式化代码
fmt:
	go fmt ./...

# 静态分析
staticcheck:
	staticcheck ./...

# 依赖检查
deps:
	go mod tidy
	go mod verify
