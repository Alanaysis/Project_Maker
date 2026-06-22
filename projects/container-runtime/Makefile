# MiniContainer Makefile

# 变量
BINARY=minicontainer
VERSION=0.1.0
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
	$(GO) test $(GOFLAGS) ./...

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
.PHONY: lint
lint:
	golangci-lint run ./...

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
	@echo "  all        编译所有（默认）"
	@echo "  build      编译二进制文件"
	@echo "  test       运行测试"
	@echo "  clean      清理编译产物"
	@echo "  install    安装到系统"
	@echo "  uninstall  从系统卸载"
	@echo "  example    运行示例"
	@echo "  deps       检查依赖"
	@echo "  fmt        格式化代码"
	@echo "  lint       代码检查"
	@echo "  docs       生成文档"
	@echo "  help       显示帮助"
