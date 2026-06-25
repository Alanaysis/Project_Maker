#!/bin/bash
# 编译脚本

set -e

echo "=== Building MapReduce ==="

# 创建输出目录
mkdir -p bin/

# 编译 Coordinator
echo "Building Coordinator..."
go build -o bin/coordinator ./cmd/coordinator

# 编译 Worker
echo "Building Worker..."
go build -o bin/worker ./cmd/worker

echo ""
echo "=== Build Complete ==="
echo "Binaries:"
ls -la bin/
