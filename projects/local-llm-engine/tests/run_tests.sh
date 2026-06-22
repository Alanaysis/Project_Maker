#!/bin/bash

# 测试运行脚本

set -e

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# 检查构建目录
BUILD_DIR="build"
if [ ! -d "$BUILD_DIR" ]; then
    print_info "构建目录不存在，开始构建..."
    mkdir -p $BUILD_DIR
    cd $BUILD_DIR
    cmake .. -DCMAKE_BUILD_TYPE=Debug
    make -j$(nproc)
    cd ..
fi

# 运行测试
print_info "运行测试..."

# 测试 Tokenizer
print_info "运行 Tokenizer 测试..."
if ./$BUILD_DIR/test_tokenizer; then
    print_pass "Tokenizer 测试通过"
else
    print_fail "Tokenizer 测试失败"
    exit 1
fi

# 测试 KV Cache
print_info "运行 KV Cache 测试..."
if ./$BUILD_DIR/test_kv_cache; then
    print_pass "KV Cache 测试通过"
else
    print_fail "KV Cache 测试失败"
    exit 1
fi

# 测试 Sampler
print_info "运行 Sampler 测试..."
if ./$BUILD_DIR/test_sampler; then
    print_pass "Sampler 测试通过"
else
    print_fail "Sampler 测试失败"
    exit 1
fi

print_info "所有测试通过！"
