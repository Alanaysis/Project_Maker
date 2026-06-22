#!/bin/bash

# Local LLM Engine 构建脚本
# 用法: ./build.sh [选项]

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

# 默认选项
BUILD_TYPE="Release"
BUILD_TESTS="ON"
BUILD_EXAMPLES="ON"
ENABLE_AVX2="OFF"
CLEAN_BUILD="OFF"
JOBS=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--debug)
            BUILD_TYPE="Debug"
            shift
            ;;
        -r|--release)
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
        --avx2)
            ENABLE_AVX2="ON"
            shift
            ;;
        --clean)
            CLEAN_BUILD="ON"
            shift
            ;;
        -j|--jobs)
            JOBS="$2"
            shift 2
            ;;
        -h|--help)
            echo "Local LLM Engine 构建脚本"
            echo ""
            echo "用法: ./build.sh [选项]"
            echo ""
            echo "选项:"
            echo "  -d, --debug       构建 Debug 版本"
            echo "  -r, --release     构建 Release 版本 (默认)"
            echo "  --no-tests        不构建测试"
            echo "  --no-examples     不构建示例"
            echo "  --avx2            启用 AVX2 优化"
            echo "  --clean           清理构建目录"
            echo "  -j, --jobs N      并行编译数 (默认: $(nproc))"
            echo "  -h, --help        显示帮助"
            exit 0
            ;;
        *)
            print_error "未知选项: $1"
            exit 1
            ;;
    esac
done

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

print_info "Local LLM Engine 构建脚本"
print_info "=========================="

# 清理构建目录
if [ "$CLEAN_BUILD" = "ON" ]; then
    print_info "清理构建目录..."
    rm -rf build
fi

# 创建构建目录
print_info "创建构建目录..."
mkdir -p build
cd build

# 配置 CMake
print_info "配置 CMake..."
print_info "  构建类型: $BUILD_TYPE"
print_info "  构建测试: $BUILD_TESTS"
print_info "  构建示例: $BUILD_EXAMPLES"
print_info "  AVX2 优化: $ENABLE_AVX2"
print_info "  并行编译: $JOBS"

cmake .. \
    -DCMAKE_BUILD_TYPE=$BUILD_TYPE \
    -DBUILD_TESTS=$BUILD_TESTS \
    -DBUILD_EXAMPLES=$BUILD_EXAMPLES \
    -DENABLE_AVX2=$ENABLE_AVX2

# 编译
print_info "开始编译..."
cmake --build . -j $JOBS

# 运行测试
if [ "$BUILD_TESTS" = "ON" ]; then
    print_info "运行测试..."
    ctest --output-on-failure
fi

print_info "构建完成！"
print_info ""
print_info "可执行文件位于 build/ 目录:"
print_info "  - llm_engine_cli  (命令行工具)"
if [ "$BUILD_TESTS" = "ON" ]; then
    print_info "  - test_tokenizer  (Tokenizer 测试)"
    print_info "  - test_kv_cache   (KV Cache 测试)"
    print_info "  - test_sampler    (Sampler 测试)"
fi
if [ "$BUILD_EXAMPLES" = "ON" ]; then
    print_info "  - chat            (聊天示例)"
    print_info "  - benchmark       (基准测试)"
fi
print_info ""
print_info "使用示例:"
print_info "  ./llm_engine_cli --help"
print_info "  ./llm_engine_cli infer -m /path/to/model.gguf -p 'Hello'"
