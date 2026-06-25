#!/bin/bash
# 运行所有基准测试

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_DIR/build"

echo "========================================"
echo "  C++ 性能优化技巧 - 基准测试"
echo "========================================"
echo ""

# 检查构建目录
if [ ! -d "$BUILD_DIR" ]; then
    echo "创建构建目录..."
    mkdir -p "$BUILD_DIR"
    cd "$BUILD_DIR"
    cmake -DCMAKE_BUILD_TYPE=Release ..
    make -j$(nproc)
fi

cd "$BUILD_DIR"

# 运行所有可执行文件
echo "运行基准测试..."
echo ""

BENCHMARKS=(
    "src/memory/cache_friendly"
    "src/memory/soa_vs_aos"
    "src/memory/memory_alignment"
    "src/memory/prefetching"
    "src/memory/memory_pool"
    "src/memory/small_buffer_optimization"
    "src/compiler/inlining"
    "src/compiler/loop_unrolling"
    "src/compiler/vectorization"
    "src/compiler/branch_prediction"
    "src/algorithm/time_complexity"
    "src/algorithm/simd_optimization"
    "src/algorithm/parallelization"
    "src/case_studies/vector_operations"
    "src/case_studies/matrix_multiplication"
    "src/case_studies/string_processing"
    "src/case_studies/hash_table"
    "src/case_studies/sorting_optimization"
    "src/concurrency/false_sharing"
    "src/concurrency/thread_pool"
)

for bench in "${BENCHMARKS[@]}"; do
    if [ -x "$bench" ]; then
        echo "----------------------------------------"
        echo "运行: $bench"
        echo "----------------------------------------"
        ./"$bench"
        echo ""
    fi
done

echo "========================================"
echo "  所有基准测试完成"
echo "========================================"
