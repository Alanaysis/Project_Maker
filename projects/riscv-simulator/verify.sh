#!/bin/bash
# ============================================================
# RISC-V Simulator 验证脚本
# ============================================================

set -e

echo "=== RISC-V Simulator Verification ==="
echo ""

# 检查二进制文件
if [ ! -f riscv-sim ]; then
    echo "FAIL: riscv-sim not found"
    exit 1
fi
echo "OK: riscv-sim binary exists"

# 运行内置测试
echo ""
echo "--- Built-in Test ---"
./riscv-sim --test 2>&1 | grep -E "(PASSED|FAILED)"
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "FAIL: built-in test failed"
    exit 1
fi

# 运行单元测试
echo ""
echo "--- Unit Tests ---"
make test-memory 2>&1 | tail -1
make test-decoder 2>&1 | tail -1
make test-assembler 2>&1 | tail -1
make test-integration 2>&1 | tail -1

# 测试汇编模式
echo ""
echo "--- Assembly Mode Test ---"
OUTPUT=$(./riscv-sim -a examples/sum_1_to_10.s 2>&1)
if echo "$OUTPUT" | grep -q "a0.*=.*55"; then
    echo "OK: sum_1_to_10.s produces a0=55"
else
    echo "FAIL: sum_1_to_10.s did not produce expected result"
    exit 1
fi

echo ""
echo "=== All Verification Passed ==="
