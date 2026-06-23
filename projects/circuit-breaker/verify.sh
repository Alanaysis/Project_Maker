#!/bin/bash

echo "=== 验证熔断器项目结构 ==="
echo ""

# 检查目录结构
echo "1. 检查目录结构..."
directories=(
    "src"
    "tests"
    "examples"
    "docs"
)

for dir in "${directories[@]}"; do
    if [ -d "$dir" ]; then
        echo "   ✓ $dir 目录存在"
    else
        echo "   ✗ $dir 目录缺失"
    fi
done

echo ""

# 检查源代码文件
echo "2. 检查源代码文件..."
source_files=(
    "src/circuit_breaker.go"
    "src/states.go"
    "src/metrics.go"
    "src/fallback.go"
)

for file in "${source_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file 存在"
    else
        echo "   ✗ $file 缺失"
    fi
done

echo ""

# 检查测试文件
echo "3. 检查测试文件..."
test_files=(
    "tests/circuit_breaker_test.go"
    "tests/states_test.go"
    "tests/metrics_test.go"
)

for file in "${test_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file 存在"
    else
        echo "   ✗ $file 缺失"
    fi
done

echo ""

# 检查文档文件
echo "4. 检查文档文件..."
doc_files=(
    "README.md"
    "LEARNING_NOTES.md"
    "docs/01-RESEARCH.md"
    "docs/02-DESIGN.md"
    "docs/03-IMPLEMENTATION.md"
    "docs/04-TESTING.md"
    "docs/05-DEVELOPMENT.md"
)

for file in "${doc_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file 存在"
    else
        echo "   ✗ $file 缺失"
    fi
done

echo ""

# 检查示例文件
echo "5. 检查示例文件..."
if [ -f "examples/main.go" ]; then
    echo "   ✓ examples/main.go 存在"
else
    echo "   ✗ examples/main.go 缺失"
fi

echo ""

# 检查go.mod
echo "6. 检查Go模块文件..."
if [ -f "go.mod" ]; then
    echo "   ✓ go.mod 存在"
else
    echo "   ✗ go.mod 缺失"
fi

echo ""
echo "=== 验证完成 ==="
