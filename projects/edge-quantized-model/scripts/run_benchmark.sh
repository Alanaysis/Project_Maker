#!/bin/bash

# 运行基准测试脚本

set -e

echo "=========================================="
echo "运行基准测试"
echo "=========================================="

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 切换到项目目录
cd "$PROJECT_DIR"

# 运行基准测试
echo "运行目标检测 Demo..."
python examples/automotive/object_detection_demo.py

echo ""
echo "运行简单量化示例..."
python examples/basic/simple_quantize.py

echo ""
echo "=========================================="
echo "基准测试完成!"
echo "=========================================="
