#!/bin/bash

# MiniContainer 构建脚本
# 用法: ./build.sh [command]
# 命令:
#   build   - 编译项目
#   test    - 运行测试
#   clean   - 清理编译产物
#   install - 安装到系统
#   all     - 编译并测试

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目配置
BINARY=minicontainer
VERSION=0.2.0
GO=go

# 打印带颜色的消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 编译
build() {
    print_info "编译 MiniContainer v${VERSION}..."
    $GO build -v -o $BINARY ./cmd/minicontainer/
    if [ $? -eq 0 ]; then
        print_info "编译成功: ./$BINARY"
    else
        print_error "编译失败"
        exit 1
    fi
}

# 测试
test() {
    print_info "运行测试..."
    $GO test -v ./tests/...
    if [ $? -eq 0 ]; then
        print_info "测试通过"
    else
        print_error "测试失败"
        exit 1
    fi
}

# 清理
clean() {
    print_info "清理编译产物..."
    rm -f $BINARY
    rm -rf /var/lib/minicontainer
    print_info "清理完成"
}

# 安装
install() {
    build
    print_info "安装到 /usr/local/bin/..."
    sudo cp $BINARY /usr/local/bin/
    print_info "安装完成"
}

# 卸载
uninstall() {
    print_info "从系统卸载..."
    sudo rm -f /usr/local/bin/$BINARY
    print_info "卸载完成"
}

# 运行示例
example() {
    build
    print_info "运行示例容器..."
    sudo ./$BINARY run --name example alpine /bin/sh
}

# 检查依赖
deps() {
    print_info "检查依赖..."
    $GO mod tidy
    print_info "依赖检查完成"
}

# 格式化代码
fmt() {
    print_info "格式化代码..."
    $GO fmt ./...
    print_info "格式化完成"
}

# 代码检查
vet() {
    print_info "代码检查..."
    $GO vet ./...
    print_info "代码检查完成"
}

# 显示帮助
help() {
    echo "MiniContainer - 轻量级容器运行时"
    echo ""
    echo "用法: ./build.sh [command]"
    echo ""
    echo "命令:"
    echo "  build     编译项目"
    echo "  test      运行测试"
    echo "  clean     清理编译产物"
    echo "  install   安装到系统"
    echo "  uninstall 从系统卸载"
    echo "  example   运行示例"
    echo "  deps      检查依赖"
    echo "  fmt       格式化代码"
    echo "  vet       代码检查"
    echo "  all       编译并测试"
    echo "  help      显示帮助"
}

# 主逻辑
case "${1:-all}" in
    build)
        build
        ;;
    test)
        test
        ;;
    clean)
        clean
        ;;
    install)
        install
        ;;
    uninstall)
        uninstall
        ;;
    example)
        example
        ;;
    deps)
        deps
        ;;
    fmt)
        fmt
        ;;
    vet)
        vet
        ;;
    all)
        build
        test
        ;;
    help)
        help
        ;;
    *)
        print_error "未知命令: $1"
        help
        exit 1
        ;;
esac
