#!/bin/bash

# C++11/14 新特性项目构建脚本

set -e  # 遇到错误立即退出

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
    print_info "检查依赖..."

    # 检查 CMake
    if ! command -v cmake &> /dev/null; then
        print_error "CMake 未安装"
        exit 1
    fi

    # 检查编译器
    if command -v g++ &> /dev/null; then
        COMPILER="g++"
        COMPILER_VERSION=$(g++ --version | head -n1)
    elif command -v clang++ &> /dev/null; then
        COMPILER="clang++"
        COMPILER_VERSION=$(clang++ --version | head -n1)
    else
        print_error "未找到 C++ 编译器"
        exit 1
    fi

    print_info "编译器: $COMPILER_VERSION"
    print_info "CMake 版本: $(cmake --version | head -n1)"
}

# 创建构建目录
create_build_dir() {
    BUILD_DIR="build"

    if [ -d "$BUILD_DIR" ]; then
        print_warn "构建目录已存在，将清理..."
        rm -rf "$BUILD_DIR"
    fi

    mkdir -p "$BUILD_DIR"
    print_info "创建构建目录: $BUILD_DIR"
}

# 配置 CMake
configure_cmake() {
    print_info "配置 CMake..."
    cd "$BUILD_DIR"
    cmake .. -DCMAKE_BUILD_TYPE=Release
    cd ..
}

# 编译项目
build_project() {
    print_info "编译项目..."
    cd "$BUILD_DIR"
    make -j$(nproc)
    cd ..
}

# 运行测试
run_tests() {
    print_info "运行测试..."
    cd "$BUILD_DIR"
    ctest --output-on-failure
    cd ..
}

# 运行示例
run_examples() {
    print_info "运行示例..."

    EXAMPLES=(
        "01_move_semantics"
        "02_lambda"
        "03_smart_pointers"
        "04_threads"
        "05_variadic_templates"
        "06_constexpr"
        "07_auto_decltype"
        "08_range_for"
        "09_initializer_list"
    )

    for example in "${EXAMPLES[@]}"; do
        echo ""
        echo "========================================"
        echo "运行示例: $example"
        echo "========================================"
        if [ -f "build/$example" ]; then
            ./build/$example
        else
            print_warn "示例 $example 不存在"
        fi
    done
}

# 运行主程序
run_main() {
    print_info "运行主程序..."
    if [ -f "build/main" ]; then
        ./build/main
    else
        print_error "主程序不存在"
        exit 1
    fi
}

# 清理构建文件
clean() {
    print_info "清理构建文件..."
    rm -rf build
    print_info "清理完成"
}

# 显示帮助
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  build     编译项目（默认）"
    echo "  test      运行测试"
    echo "  examples  运行所有示例"
    echo "  main      运行主程序"
    echo "  clean     清理构建文件"
    echo "  all       编译、测试并运行示例"
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0          # 编译项目"
    echo "  $0 test     # 运行测试"
    echo "  $0 examples # 运行示例"
    echo "  $0 all      # 完整流程"
}

# 主函数
main() {
    # 切换到脚本所在目录
    cd "$(dirname "$0")"

    # 检查依赖
    check_dependencies

    # 解析参数
    case "${1:-build}" in
        build)
            create_build_dir
            configure_cmake
            build_project
            print_info "编译完成！"
            ;;
        test)
            if [ ! -d "build" ]; then
                create_build_dir
                configure_cmake
                build_project
            fi
            run_tests
            ;;
        examples)
            if [ ! -d "build" ]; then
                create_build_dir
                configure_cmake
                build_project
            fi
            run_examples
            ;;
        main)
            if [ ! -d "build" ]; then
                create_build_dir
                configure_cmake
                build_project
            fi
            run_main
            ;;
        clean)
            clean
            ;;
        all)
            create_build_dir
            configure_cmake
            build_project
            run_tests
            run_examples
            ;;
        help)
            show_help
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"
