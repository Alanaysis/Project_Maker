#!/bin/bash

# VR Application 构建脚本
# 用法: ./build.sh [选项]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 默认选项
BUILD_TYPE="Release"
BUILD_TESTS="ON"
BUILD_EXAMPLES="ON"
USE_OPENXR="OFF"
CLEAN_BUILD=false
JOBS=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --debug)
            BUILD_TYPE="Debug"
            shift
            ;;
        --release)
            BUILD_TYPE="Release"
            shift
            ;;
        --no-tests)
            BUILD_TESTS="OFF"
            shift
            ;;
        --no-examples)
            BUILD_EXAMPLES="OFF"
            shift
            ;;
        --openxr)
            USE_OPENXR="ON"
            shift
            ;;
        --clean)
            CLEAN_BUILD=true
            shift
            ;;
        --jobs)
            JOBS="$2"
            shift 2
            ;;
        --help)
            echo "VR Application 构建脚本"
            echo ""
            echo "用法: ./build.sh [选项]"
            echo ""
            echo "选项:"
            echo "  --debug          构建 Debug 版本"
            echo "  --release        构建 Release 版本（默认）"
            echo "  --no-tests       不构建测试"
            echo "  --no-examples    不构建示例"
            echo "  --openxr         启用 OpenXR 支持"
            echo "  --clean          清理构建目录"
            echo "  --jobs N         并行编译任务数"
            echo "  --help           显示此帮助信息"
            echo ""
            echo "示例:"
            echo "  ./build.sh                    # 默认 Release 构建"
            echo "  ./build.sh --debug            # Debug 构建"
            echo "  ./build.sh --clean --release  # 清理后重新构建"
            exit 0
            ;;
        *)
            print_error "未知选项: $1"
            exit 1
            ;;
    esac
done

# 打印配置信息
print_info "=== VR Application 构建配置 ==="
print_info "构建类型: $BUILD_TYPE"
print_info "构建测试: $BUILD_TESTS"
print_info "构建示例: $BUILD_EXAMPLES"
print_info "OpenXR: $USE_OPENXR"
print_info "并行任务: $JOBS"
print_info "================================"
echo ""

# 检查依赖
print_info "检查依赖..."

check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "未找到 $1，请先安装"
        return 1
    fi
    return 0
}

# 检查必需的工具
check_command cmake || exit 1
check_command g++ || check_command clang++ || exit 1

# 检查库（简化检查）
print_info "注意：请确保已安装以下依赖："
print_info "  - OpenGL 开发库"
print_info "  - GLFW3"
print_info "  - GLEW"
print_info "  - GLM"
echo ""

# 进入项目目录
cd "$(dirname "$0")"
PROJECT_DIR=$(pwd)

# 清理构建目录
if [ "$CLEAN_BUILD" = true ]; then
    print_info "清理构建目录..."
    rm -rf build
fi

# 创建构建目录
print_info "创建构建目录..."
mkdir -p build
cd build

# 配置项目
print_info "配置项目..."
cmake .. \
    -DCMAKE_BUILD_TYPE=$BUILD_TYPE \
    -DBUILD_TESTS=$BUILD_TESTS \
    -DBUILD_EXAMPLES=$BUILD_EXAMPLES \
    -DUSE_OPENXR=$USE_OPENXR

if [ $? -ne 0 ]; then
    print_error "CMake 配置失败"
    exit 1
fi

# 编译项目
print_info "编译项目..."
cmake --build . --config $BUILD_TYPE -j $JOBS

if [ $? -ne 0 ]; then
    print_error "编译失败"
    exit 1
fi

echo ""
print_success "构建成功！"
echo ""

# 显示生成的文件
print_info "生成的可执行文件："
if [ -f "bin/vr_application" ]; then
    echo "  - bin/vr_application"
fi
if [ -f "bin/examples/basic_scene" ]; then
    echo "  - bin/examples/basic_scene"
fi

echo ""

# 运行测试（如果启用）
if [ "$BUILD_TESTS" = "ON" ]; then
    print_info "运行测试..."
    ctest --output-on-failure
    echo ""
fi

print_info "构建完成！"
print_info "可执行文件位于 build/bin/ 目录"