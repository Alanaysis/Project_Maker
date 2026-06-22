#!/bin/bash

# 键盘驱动构建脚本

set -e

echo "========================================"
echo "键盘驱动项目构建"
echo "========================================"

# 检查编译器
if ! command -v gcc &> /dev/null; then
    echo "错误: 未找到gcc编译器"
    exit 1
fi

# 创建构建目录
mkdir -p build

# 编译选项
CFLAGS="-Wall -Wextra -std=c99 -g -I./include"

# 源文件
SRC_FILES=(
    "src/keyboard_driver.c"
    "src/matrix_scanner.c"
    "src/interrupt_handler.c"
    "src/debounce.c"
    "src/input_event.c"
)

# 编译源文件
echo ""
echo "1. 编译源文件..."
echo "----------------------------------------"

OBJ_FILES=()
for src in "${SRC_FILES[@]}"; do
    obj="build/$(basename "$src" .c).o"
    echo "编译 $src -> $obj"
    gcc $CFLAGS -c "$src" -o "$obj"
    OBJ_FILES+=("$obj")
done

# 编译测试
echo ""
echo "2. 编译测试..."
echo "----------------------------------------"
gcc $CFLAGS "${OBJ_FILES[@]}" "tests/test_keyboard.c" -o "build/keyboard_test"
echo "测试程序已生成: build/keyboard_test"

# 编译示例
echo ""
echo "3. 编译示例..."
echo "----------------------------------------"
gcc $CFLAGS "${OBJ_FILES[@]}" "examples/example.c" -o "build/keyboard_example"
echo "示例程序已生成: build/keyboard_example"

echo ""
echo "========================================"
echo "构建完成"
echo "========================================"
echo ""
echo "运行测试: ./build/keyboard_test"
echo "运行示例: ./build/keyboard_example"
echo ""
