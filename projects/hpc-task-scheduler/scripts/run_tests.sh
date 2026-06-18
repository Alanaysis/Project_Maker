#!/bin/bash

# HPC Task Scheduler - 测试脚本

set -e

echo "=== HPC Task Scheduler - Running Tests ==="
echo ""

# 运行单元测试
echo "Running unit tests..."
go test ./internal/... -v -race

echo ""
echo "=== Unit tests completed ==="

# 运行集成测试
echo ""
echo "Running integration tests..."
go test ./tests/... -v -race -timeout 60s

echo ""
echo "=== Integration tests completed ==="

# 运行基准测试
echo ""
echo "Running benchmarks..."
go test ./internal/... -bench=. -benchmem

echo ""
echo "=== All tests completed ==="
