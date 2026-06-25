#!/bin/bash
# 测试脚本

set -e

echo "=== Running Unit Tests ==="
go test -race -v ./...

echo ""
echo "=== Running Benchmarks ==="
go test -bench=. ./...

echo ""
echo "=== All Tests Passed ==="
