#!/bin/bash

# 社交聊天系统测试脚本

set -e

echo "=== 社交聊天系统测试脚本 ==="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Go 是否安装
if ! command -v go &> /dev/null; then
    echo -e "${RED}错误: Go 未安装${NC}"
    echo "请先安装 Go: https://go.dev/dl/"
    exit 1
fi

echo -e "${GREEN}✓ Go 已安装${NC}"

# 安装依赖
echo ""
echo "安装依赖..."
go mod tidy
echo -e "${GREEN}✓ 依赖安装完成${NC}"

# 运行测试
echo ""
echo "运行单元测试..."
go test -v ./tests/...
echo -e "${GREEN}✓ 测试通过${NC}"

# 编译项目
echo ""
echo "编译项目..."
go build -o bin/chat-server ./cmd/server
echo -e "${GREEN}✓ 编译成功${NC}"

# 创建数据目录
mkdir -p data logs

echo ""
echo -e "${YELLOW}=== 测试完成 ===${NC}"
echo ""
echo "下一步:"
echo "1. 启动服务器: go run ./cmd/server"
echo "2. 注册用户:   go run ./examples/register_and_login.go register alice password123"
echo "3. 启动聊天:   go run ./examples/client.go ws://localhost:8080/ws <token>"
echo ""
echo "更多信息请查看 examples/README.md"