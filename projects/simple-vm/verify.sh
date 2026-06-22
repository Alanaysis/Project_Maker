#!/bin/bash

# Simple VM - 项目验证脚本

echo "=== Simple VM 项目验证 ==="
echo ""

# 检查目录结构
echo "1. 检查目录结构..."
dirs=("src" "include" "tests" "examples" "docs")
for dir in "${dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "   ✓ $dir 目录存在"
    else
        echo "   ✗ $dir 目录不存在"
    fi
done
echo ""

# 检查源文件
echo "2. 检查源文件..."
src_files=("src/main.cpp" "src/vm.cpp" "src/vcpu.cpp" "src/io.cpp")
for file in "${src_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file 存在"
    else
        echo "   ✗ $file 不存在"
    fi
done
echo ""

# 检查头文件
echo "3. 检查头文件..."
header_files=("include/vm.h" "include/vcpu.h" "include/memory.h" "include/io.h")
for file in "${header_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file 存在"
    else
        echo "   ✗ $file 不存在"
    fi
done
echo ""

# 检查测试文件
echo "4. 检查测试文件..."
test_files=("tests/test_vm.cpp" "tests/test_io.cpp")
for file in "${test_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file 存在"
    else
        echo "   ✗ $file 不存在"
    fi
done
echo ""

# 检查示例文件
echo "5. 检查示例文件..."
example_files=("examples/hello.asm" "examples/calc.asm" "examples/README.md")
for file in "${example_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file 存在"
    else
        echo "   ✗ $file 不存在"
    fi
done
echo ""

# 检查文档文件
echo "6. 检查文档文件..."
doc_files=("README.md" "LEARNING_NOTES.md" "docs/01-RESEARCH.md" "docs/02-REQUIREMENTS.md" "docs/03-DESIGN.md" "docs/04-PRODUCT.md" "docs/05-DEVELOPMENT.md")
for file in "${doc_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file 存在"
    else
        echo "   ✗ $file 不存在"
    fi
done
echo ""

# 检查构建文件
echo "7. 检查构建文件..."
build_files=("CMakeLists.txt" "Makefile" ".gitignore")
for file in "${build_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file 存在"
    else
        echo "   ✗ $file 不存在"
    fi
done
echo ""

# 检查编译工具
echo "8. 检查编译工具..."
if command -v g++ &> /dev/null; then
    echo "   ✓ g++ 已安装"
else
    echo "   ✗ g++ 未安装"
fi

if command -v cmake &> /dev/null; then
    echo "   ✓ cmake 已安装"
else
    echo "   ✗ cmake 未安装"
fi

if command -v nasm &> /dev/null; then
    echo "   ✓ nasm 已安装"
else
    echo "   ✗ nasm 未安装 (需要安装以编译示例程序)"
fi
echo ""

# 检查 KVM 支持
echo "9. 检查 KVM 支持..."
if [ -e /dev/kvm ]; then
    echo "   ✓ /dev/kvm 存在"
else
    echo "   ✗ /dev/kvm 不存在 (需要启用 KVM)"
fi

if lsmod | grep -q kvm; then
    echo "   ✓ KVM 模块已加载"
else
    echo "   ✗ KVM 模块未加载"
fi
echo ""

echo "=== 验证完成 ==="
echo ""
echo "如果所有检查都通过，可以使用以下命令构建项目："
echo ""
echo "  mkdir build && cd build"
echo "  cmake .."
echo "  make"
echo ""
echo "或者使用 Makefile："
echo ""
echo "  make"
echo ""
echo "运行测试："
echo ""
echo "  make test"
echo ""
echo "运行示例："
echo ""
echo "  make run-hello"
