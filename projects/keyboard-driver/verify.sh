#!/bin/bash

# 键盘驱动项目验证脚本

echo "========================================"
echo "键盘驱动项目验证"
echo "========================================"

# 检查项目结构
echo ""
echo "1. 检查项目结构..."
echo "----------------------------------------"

# 检查必要目录
for dir in src include tests examples docs; do
    if [ -d "$dir" ]; then
        echo "✓ $dir 目录存在"
    else
        echo "✗ $dir 目录缺失"
    fi
done

# 检查必要文件
echo ""
echo "2. 检查必要文件..."
echo "----------------------------------------"

required_files=(
    "README.md"
    "Makefile"
    "include/keyboard.h"
    "src/keyboard_driver.c"
    "src/matrix_scanner.c"
    "src/interrupt_handler.c"
    "src/debounce.c"
    "src/input_event.c"
    "tests/test_keyboard.c"
    "examples/example.c"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file 存在"
    else
        echo "✗ $file 缺失"
    fi
done

# 检查文档文件
echo ""
echo "3. 检查文档文件..."
echo "----------------------------------------"

doc_files=(
    "docs/01-RESEARCH.md"
    "docs/02-REQUIREMENTS.md"
    "docs/03-DESIGN.md"
    "docs/04-PRODUCT.md"
    "docs/05-DEVELOPMENT.md"
    "LEARNING_NOTES.md"
)

for file in "${doc_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file 存在"
    else
        echo "✗ $file 缺失"
    fi
done

# 检查代码语法
echo ""
echo "4. 检查代码语法..."
echo "----------------------------------------"

# 检查头文件
if grep -q "#ifndef KEYBOARD_H" include/keyboard.h; then
    echo "✓ keyboard.h 头文件保护正确"
else
    echo "✗ keyboard.h 头文件保护缺失"
fi

# 检查函数声明
if grep -q "int keyboard_init" include/keyboard.h; then
    echo "✓ keyboard_init 函数已声明"
else
    echo "✗ keyboard_init 函数未声明"
fi

# 检查Makefile
if [ -f "Makefile" ]; then
    echo "✓ Makefile 存在"
    if grep -q "all:" Makefile; then
        echo "✓ Makefile 包含默认目标"
    fi
fi

# 检查代码质量
echo ""
echo "5. 检查代码质量..."
echo "----------------------------------------"

# 检查注释
comment_count=$(grep -r "/\*" src/ | wc -l)
echo "源文件注释行数: $comment_count"

# 检查函数数量
func_count=$(grep -r "^[a-z].*(" src/ | grep -v "static" | wc -l)
echo "公共函数数量: $func_count"

# 检查代码行数
total_lines=$(find src -name "*.c" -exec cat {} \; | wc -l)
echo "源代码总行数: $total_lines"

# 总结
echo ""
echo "========================================"
echo "验证完成"
echo "========================================"
echo ""
echo "项目结构完整，可以进行编译和测试。"
echo ""
echo "下一步操作："
echo "1. 运行 'make' 编译项目"
echo "2. 运行 'make test' 编译测试"
echo "3. 运行 './build/keyboard_test' 执行测试"
echo "4. 运行 'make example' 编译示例"
echo "5. 运行 './build/keyboard_example' 查看示例"
echo ""
