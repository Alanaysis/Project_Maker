#!/bin/bash

# MiniContainer 构建脚本

set -e

echo "=== MiniContainer 构建脚本 ==="

# 检查 Go 环境
echo "检查 Go 环境..."
if ! command -v go &> /dev/null; then
    echo "错误: Go 未安装"
    exit 1
fi

GO_VERSION=$(go version | awk '{print $3}')
echo "Go 版本: $GO_VERSION"

# 编译项目
echo ""
echo "编译项目..."
go build -o minicontainer ./cmd/minicontainer/

if [ $? -eq 0 ]; then
    echo "编译成功!"
    echo "可执行文件: ./minicontainer"
else
    echo "编译失败!"
    exit 1
fi

# 运行测试
echo ""
echo "运行测试..."
go test ./...

if [ $? -eq 0 ]; then
    echo "测试通过!"
else
    echo "测试失败!"
    exit 1
fi

echo ""
echo "=== 构建完成 ==="
echo ""
echo "使用方法:"
echo "  sudo ./minicontainer run --name test alpine /bin/sh"
echo "  sudo ./minicontainer ps"
echo "  sudo ./minicontainer images"
