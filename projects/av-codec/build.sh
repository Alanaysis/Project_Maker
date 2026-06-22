#!/bin/bash
# 构建脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build"

echo "=== AV-Codec Build Script ==="

# 检查依赖
check_dependencies() {
    echo "Checking dependencies..."

    # 检查CMake
    if ! command -v cmake &> /dev/null; then
        echo "Error: cmake not found"
        echo "Install with: sudo apt install cmake"
        exit 1
    fi

    # 检查编译器
    if ! command -v g++ &> /dev/null; then
        echo "Error: g++ not found"
        echo "Install with: sudo apt install build-essential"
        exit 1
    fi

    # 检查FFmpeg开发库
    if ! pkg-config --exists libavcodec 2>/dev/null; then
        echo "Warning: FFmpeg development libraries not found"
        echo "Install with: sudo apt install libavcodec-dev libavformat-dev libavutil-dev libswscale-dev libswresample-dev"
        echo ""
        echo "Attempting to continue with manual library detection..."
    fi

    echo "Dependencies check completed"
}

# 清理构建目录
clean() {
    echo "Cleaning build directory..."
    rm -rf "${BUILD_DIR}"
    echo "Clean completed"
}

# 配置
configure() {
    echo "Configuring project..."
    mkdir -p "${BUILD_DIR}"
    cd "${BUILD_DIR}"

    cmake .. \
        -DCMAKE_BUILD_TYPE=Release \
        -DBUILD_TESTING=ON \
        -DBUILD_EXAMPLES=ON

    echo "Configuration completed"
}

# 编译
build() {
    echo "Building project..."
    cd "${BUILD_DIR}"
    make -j$(nproc)
    echo "Build completed"
}

# 测试
test() {
    echo "Running tests..."
    cd "${BUILD_DIR}"
    ctest --verbose
    echo "Tests completed"
}

# 安装
install() {
    echo "Installing..."
    cd "${BUILD_DIR}"
    make install
    echo "Installation completed"
}

# 显示帮助
help() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  clean     - Clean build directory"
    echo "  configure - Configure project"
    echo "  build     - Build project"
    echo "  test      - Run tests"
    echo "  install   - Install project"
    echo "  all       - Clean, configure, build, and test"
    echo "  help      - Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 all      # Full build and test"
    echo "  $0 build    # Just build"
    echo "  $0 test     # Run tests"
}

# 主函数
main() {
    check_dependencies

    case "${1:-all}" in
        clean)
            clean
            ;;
        configure)
            configure
            ;;
        build)
            configure
            build
            ;;
        test)
            configure
            build
            test
            ;;
        install)
            configure
            build
            install
            ;;
        all)
            clean
            configure
            build
            test
            ;;
        help|--help|-h)
            help
            ;;
        *)
            echo "Unknown command: $1"
            help
            exit 1
            ;;
    esac
}

main "$@"
