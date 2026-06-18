#!/bin/bash

# MiniDB 构建脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    info "Checking dependencies..."

    if ! command -v cmake &> /dev/null; then
        error "cmake not found. Please install CMake 3.14+"
        exit 1
    fi

    if ! command -v g++ &> /dev/null && ! command -v clang++ &> /dev/null; then
        error "C++ compiler not found. Please install g++ or clang++"
        exit 1
    fi

    info "Dependencies OK"
}

# 清理构建目录
clean() {
    info "Cleaning build directory..."
    rm -rf build
    mkdir -p build
}

# 配置项目
configure() {
    info "Configuring project..."
    cd build

    CMAKE_BUILD_TYPE=${1:-Release}
    cmake -DCMAKE_BUILD_TYPE=$CMAKE_BUILD_TYPE ..

    cd ..
}

# 编译项目
build() {
    info "Building project..."
    cd build
    make -j$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
    cd ..
}

# 运行测试
test() {
    info "Running tests..."
    cd build
    if [ -f minidb_tests ]; then
        ./minidb_tests
    else
        warn "Test executable not found"
    fi
    cd ..
}

# 运行示例
run_example() {
    info "Running simple CRUD example..."
    cd build
    if [ -f minidb_example ]; then
        ./minidb_example
    else
        warn "Example executable not found"
    fi
    cd ..
}

# 运行并发示例
run_concurrent() {
    info "Running concurrent access example..."
    cd build
    if [ -f minidb_concurrent ]; then
        ./minidb_concurrent
    else
        warn "Concurrent example executable not found"
    fi
    cd ..
}

# 显示帮助
help() {
    echo "MiniDB Build Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  build       Build the project (default)"
    echo "  debug       Build in debug mode"
    echo "  test        Run tests"
    echo "  example     Run simple CRUD example"
    echo "  concurrent  Run concurrent access example"
    echo "  clean       Clean build directory"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0              # Build in release mode"
    echo "  $0 debug        # Build in debug mode"
    echo "  $0 test         # Build and run tests"
    echo "  $0 example      # Build and run example"
}

# 主函数
main() {
    echo "========================================"
    echo "MiniDB Build Script"
    echo "========================================"
    echo ""

    check_dependencies

    case "${1:-build}" in
        build)
            clean
            configure Release
            build
            info "Build completed successfully!"
            info "Executables are in build/ directory"
            ;;
        debug)
            clean
            configure Debug
            build
            info "Debug build completed successfully!"
            ;;
        test)
            clean
            configure Debug
            build
            test
            ;;
        example)
            clean
            configure Release
            build
            run_example
            ;;
        concurrent)
            clean
            configure Release
            build
            run_concurrent
            ;;
        clean)
            clean
            info "Clean completed"
            ;;
        help)
            help
            ;;
        *)
            error "Unknown command: $1"
            help
            exit 1
            ;;
    esac
}

main "$@"
