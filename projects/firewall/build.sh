#!/bin/bash

# 防火墙项目构建脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# 检查依赖
check_dependencies() {
    print_info "Checking dependencies..."

    # 检查编译器
    if ! command -v gcc &> /dev/null; then
        print_error "GCC not found. Please install gcc."
        exit 1
    fi

    # 检查 pkg-config
    if ! command -v pkg-config &> /dev/null; then
        print_warn "pkg-config not found. Some features may not work."
    fi

    # 检查 libnetfilter_queue
    if ! pkg-config --exists libnetfilter_queue 2>/dev/null; then
        print_warn "libnetfilter_queue not found. Install with:"
        print_warn "  sudo apt-get install libnetfilter-queue-dev"
    fi

    # 检查 libpcap
    if ! pkg-config --exists libpcap 2>/dev/null; then
        print_warn "libpcap not found. Install with:"
        print_warn "  sudo apt-get install libpcap-dev"
    fi

    print_info "Dependencies check complete."
}

# 创建构建目录
create_build_dir() {
    if [ ! -d "build" ]; then
        print_info "Creating build directory..."
        mkdir -p build
    fi
}

# 编译主程序
build_main() {
    print_info "Building firewall..."

    gcc -Wall -Wextra -g -O2 \
        -I include \
        -c src/main.c -o build/main.o

    gcc -Wall -Wextra -g -O2 \
        -I include \
        -c src/packet.c -o build/packet.o

    gcc -Wall -Wextra -g -O2 \
        -I include \
        -c src/rules.c -o build/rules.o

    gcc -Wall -Wextra -g -O2 \
        -I include \
        -c src/state.c -o build/state.o

    gcc -Wall -Wextra -g -O2 \
        -I include \
        -c src/ids.c -o build/ids.o

    gcc -Wall -Wextra -g -O2 \
        -I include \
        -c src/logger.c -o build/logger.o

    gcc build/main.o build/packet.o build/rules.o \
        build/state.o build/ids.o build/logger.o \
        -o build/firewall -lpthread

    print_info "Firewall built successfully."
}

# 编译测试
build_tests() {
    print_info "Building tests..."

    # 包解析测试
    gcc -Wall -Wextra -g -O2 \
        -I include \
        -c tests/test_packet.c -o build/test_packet.o

    gcc build/test_packet.o build/packet.o \
        -o build/test_packet -lpthread

    # 规则引擎测试
    gcc -Wall -Wextra -g -O2 \
        -I include \
        -c tests/test_rules.c -o build/test_rules.o

    gcc build/test_rules.o build/rules.o build/packet.o \
        -o build/test_rules -lpthread

    # 状态管理测试
    gcc -Wall -Wextra -g -O2 \
        -I include \
        -c tests/test_state.c -o build/test_state.o

    gcc build/test_state.o build/state.o build/packet.o \
        -o build/test_state -lpthread

    # IDS 测试
    gcc -Wall -Wextra -g -O2 \
        -I include \
        -c tests/test_ids.c -o build/test_ids.o

    gcc build/test_ids.o build/ids.o build/packet.o \
        -o build/test_ids -lpthread

    print_info "Tests built successfully."
}

# 编译示例
build_examples() {
    print_info "Building examples..."

    gcc -Wall -Wextra -g -O2 \
        -I include \
        -c examples/simple_filter.c -o build/simple_filter.o

    gcc build/simple_filter.o build/rules.o build/packet.o \
        -o build/simple_filter -lpthread

    print_info "Examples built successfully."
}

# 运行测试
run_tests() {
    print_info "Running tests..."

    echo ""
    echo "=== Running Packet Tests ==="
    ./build/test_packet

    echo ""
    echo "=== Running Rules Tests ==="
    ./build/test_rules

    echo ""
    echo "=== Running State Tests ==="
    ./build/test_state

    echo ""
    echo "=== Running IDS Tests ==="
    ./build/test_ids

    print_info "All tests completed."
}

# 清理构建文件
clean() {
    print_info "Cleaning build files..."
    rm -rf build
    print_info "Clean complete."
}

# 显示帮助
show_help() {
    echo "Firewall Build Script"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  build     - Build everything (default)"
    echo "  test      - Build and run tests"
    echo "  clean     - Remove build files"
    echo "  help      - Show this help"
}

# 主函数
main() {
    case "${1:-build}" in
        build)
            check_dependencies
            create_build_dir
            build_main
            build_tests
            build_examples
            print_info "Build complete!"
            ;;
        test)
            check_dependencies
            create_build_dir
            build_main
            build_tests
            run_tests
            ;;
        clean)
            clean
            ;;
        help)
            show_help
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
