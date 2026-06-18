#!/bin/bash

# 运行所有测试的脚本

set -e

echo "=== 运行单元测试 ==="
go test ./... -v

echo ""
echo "=== 运行测试并显示覆盖率 ==="
go test ./... -coverprofile=coverage.out

echo ""
echo "=== 生成覆盖率报告 ==="
go tool cover -func=coverage.out

echo ""
echo "=== 测试完成 ==="
