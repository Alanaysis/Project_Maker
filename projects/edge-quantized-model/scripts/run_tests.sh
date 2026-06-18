#!/bin/bash

# 运行测试脚本

set -e

echo "=========================================="
echo "运行测试"
echo "=========================================="

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 切换到项目目录
cd "$PROJECT_DIR"

# 运行测试
echo "运行单元测试..."
python -m pytest tests/ -v --tb=short

echo ""
echo "=========================================="
echo "测试完成!"
echo "=========================================="
