# MiniContainer Makefile

# 变量
BINARY=minicontainer
VERSION=0.2.0
GO=go
GOFLAGS=-v

# 默认目标
.PHONY: all
all: build

# 编译
.PHONY: build
build:
	$(GO) build $(GOFLAGS) -o $(BINARY) ./cmd/minicontainer/

# 测试
.PHONY: test
test:
	$(GO) test $(GOFLAGS) ./tests/...

# 测试容器模块
.PHONY: test-container
test-container:
	$(GO) test $(GOFLAGS) ./tests/ -run TestContainer

# 测试镜像模块
.PHONY: test-image
test-image:
	$(GO) test $(GOFLAGS) ./tests/ -run TestImage

# 测试网络模块
.PHONY: test-network
test-network:
	$(GO) test $(GOFLAGS) ./tests/ -run TestNetwork\|TestIP\|TestNewNetwork

# 测试 Cgroup 模块
.PHONY: test-cgroup
test-cgroup:
	$(GO) test $(GOFLAGS) ./tests/ -run TestCgroup\|TestResource

# 测试存储模块
.PHONY: test-storage
test-storage:
	$(GO) test $(GOFLAGS) ./tests/ -run TestStorage\|TestMount

# 清理
.PHONY: clean
clean:
	rm -f $(BINARY)
	rm -rf /var/lib/minicontainer

# 安装
.PHONY: install
install: build
	cp $(BINARY) /usr/local/bin/

# 卸载
.PHONY: uninstall
uninstall:
	rm -f /usr/local/bin/$(BINARY)

# 运行示例
.PHONY: example
example: build
	sudo ./$(BINARY) run --name example alpine /bin/sh

# 检查依赖
.PHONY: deps
deps:
	$(GO) mod tidy

# 格式化代码
.PHONY: fmt
fmt:
	$(GO) fmt ./...

# 代码检查
.PHONY: vet
vet:
	$(GO) vet ./...

# 生成文档
.PHONY: docs
docs:
	godoc -http=:6060

# 帮助
.PHONY: help
help:
	@echo "MiniContainer - 轻量级容器运行时"
	@echo ""
	@echo "用法:"
	@echo "  make [target]"
	@echo ""
	@echo "目标:"
	@echo "  all            编译所有（默认）"
	@echo "  build          编译二进制文件"
	@echo "  test           运行所有测试"
	@echo "  test-container 运行容器测试"
	@echo "  test-image     运行镜像测试"
	@echo "  test-network   运行网络测试"
	@echo "  test-cgroup    运行 Cgroup 测试"
	@echo "  test-storage   运行存储测试"
	@echo "  clean          清理编译产物"
	@echo "  install        安装到系统"
	@echo "  uninstall      从系统卸载"
	@echo "  example        运行示例"
	@echo "  deps           检查依赖"
	@echo "  fmt            格式化代码"
	@echo "  vet            代码检查"
	@echo "  docs           生成文档"
	@echo "  help           显示帮助"
