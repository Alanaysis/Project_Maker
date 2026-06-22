#!/bin/bash

# 容灾数据存储系统 - 构建脚本

set -e  # 遇到错误立即退出

echo "========================================"
echo "  容灾数据存储系统 - 构建脚本"
echo "========================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查依赖
check_dependencies() {
    echo "检查依赖..."

    # 检查CMake
    if ! command -v cmake &> /dev/null; then
        echo -e "${RED}错误: 未找到CMake${NC}"
        echo "请安装CMake 3.14或更高版本"
        exit 1
    fi

    # 检查C++编译器
    if ! command -v g++ &> /dev/null && ! command -v clang++ &> /dev/null; then
        echo -e "${RED}错误: 未找到C++编译器${NC}"
        echo "请安装GCC 7+或Clang 6+"
        exit 1
    fi

    echo -e "${GREEN}依赖检查通过${NC}"
    echo ""
}

# 创建构建目录
create_build_dir() {
    echo "创建构建目录..."

    if [ -d "build" ]; then
        echo "清理旧的构建目录..."
        rm -rf build
    fi

    mkdir -p build
    cd build

    echo -e "${GREEN}构建目录创建成功${NC}"
    echo ""
}

# 配置CMake
configure_cmake() {
    echo "配置CMake..."

    cmake .. \
        -DCMAKE_BUILD_TYPE=Release \
        -DBUILD_TESTS=ON

    if [ $? -ne 0 ]; then
        echo -e "${RED}CMake配置失败${NC}"
        exit 1
    fi

    echo -e "${GREEN}CMake配置成功${NC}"
    echo ""
}

# 编译项目
build_project() {
    echo "编译项目..."

    make -j$(nproc)

    if [ $? -ne 0 ]; then
        echo -e "${RED}编译失败${NC}"
        exit 1
    fi

    echo -e "${GREEN}编译成功${NC}"
    echo ""
}

# 运行测试
run_tests() {
    echo "运行测试..."

    ctest --output-on-failure

    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}部分测试失败${NC}"
    else
        echo -e "${GREEN}所有测试通过${NC}"
    fi
    echo ""
}

# 运行示例
run_examples() {
    echo "运行示例..."

    echo ""
    echo "运行基本使用示例..."
    ./bin/basic_usage

    echo ""
    echo "========================================"
    echo ""

    echo "运行纠删码示例..."
    ./bin/erasure_coding

    echo ""
    echo "========================================"
    echo ""

    echo "运行容错机制示例..."
    ./bin/fault_tolerance

    echo ""
}

# 显示帮助
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --help        显示帮助信息"
    echo "  --build       仅编译项目"
    echo "  --test        仅运行测试"
    echo "  --examples    仅运行示例"
    echo "  --clean       清理构建目录"
    echo ""
    echo "示例:"
    echo "  $0            # 完整构建和测试"
    echo "  $0 --build    # 仅编译"
    echo "  $0 --test     # 仅测试"
    echo ""
}

# 清理构建目录
clean_build() {
    echo "清理构建目录..."
    rm -rf build
    echo -e "${GREEN}清理完成${NC}"
}

# 主函数
main() {
    # 解析参数
    case "${1:-}" in
        --help)
            show_help
            exit 0
            ;;
        --clean)
            clean_build
            exit 0
            ;;
        --build)
            check_dependencies
            create_build_dir
            configure_cmake
            build_project
            ;;
        --test)
            if [ ! -d "build" ]; then
                echo -e "${RED}错误: 请先运行构建${NC}"
                exit 1
            fi
            cd build
            run_tests
            ;;
        --examples)
            if [ ! -d "build" ]; then
                echo -e "${RED}错误: 请先运行构建${NC}"
                exit 1
            fi
            cd build
            run_examples
            ;;
        "")
            # 完整构建
            check_dependencies
            create_build_dir
            configure_cmake
            build_project
            run_tests
            run_examples
            ;;
        *)
            echo -e "${RED}未知选项: ${1}${NC}"
            show_help
            exit 1
            ;;
    esac

    echo ""
    echo "========================================"
    echo "  构建完成！"
    echo "========================================"
}

# 运行主函数
main "$@"
