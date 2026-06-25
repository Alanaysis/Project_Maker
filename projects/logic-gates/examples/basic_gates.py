#!/usr/bin/env python3
"""
基本逻辑门示例

演示所有基本逻辑门的使用方法。
"""

import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.gates import AndGate, OrGate, NotGate, XorGate, NandGate, NorGate
from src.truth_table import TruthTableGenerator


def demo_and_gate():
    """演示AND门"""
    print("=" * 50)
    print("AND门演示")
    print("=" * 50)

    gate = AndGate()

    print(f"\n门名称: {gate.name}")
    print(f"输入数量: {gate.num_inputs}")

    print("\n真值表:")
    print(TruthTableGenerator.generate(gate))

    print("\n计算示例:")
    print(f"  AND(0, 0) = {gate.evaluate(0, 0)}")
    print(f"  AND(0, 1) = {gate.evaluate(0, 1)}")
    print(f"  AND(1, 0) = {gate.evaluate(1, 0)}")
    print(f"  AND(1, 1) = {gate.evaluate(1, 1)}")


def demo_or_gate():
    """演示OR门"""
    print("\n" + "=" * 50)
    print("OR门演示")
    print("=" * 50)

    gate = OrGate()

    print(f"\n门名称: {gate.name}")
    print(f"输入数量: {gate.num_inputs}")

    print("\n真值表:")
    print(TruthTableGenerator.generate(gate))

    print("\n计算示例:")
    print(f"  OR(0, 0) = {gate.evaluate(0, 0)}")
    print(f"  OR(0, 1) = {gate.evaluate(0, 1)}")
    print(f"  OR(1, 0) = {gate.evaluate(1, 0)}")
    print(f"  OR(1, 1) = {gate.evaluate(1, 1)}")


def demo_not_gate():
    """演示NOT门"""
    print("\n" + "=" * 50)
    print("NOT门演示")
    print("=" * 50)

    gate = NotGate()

    print(f"\n门名称: {gate.name}")
    print(f"输入数量: {gate.num_inputs}")

    print("\n真值表:")
    print(TruthTableGenerator.generate(gate))

    print("\n计算示例:")
    print(f"  NOT(0) = {gate.evaluate(0)}")
    print(f"  NOT(1) = {gate.evaluate(1)}")


def demo_xor_gate():
    """演示XOR门"""
    print("\n" + "=" * 50)
    print("XOR门演示")
    print("=" * 50)

    gate = XorGate()

    print(f"\n门名称: {gate.name}")
    print(f"输入数量: {gate.num_inputs}")

    print("\n真值表:")
    print(TruthTableGenerator.generate(gate))

    print("\n计算示例:")
    print(f"  XOR(0, 0) = {gate.evaluate(0, 0)}")
    print(f"  XOR(0, 1) = {gate.evaluate(0, 1)}")
    print(f"  XOR(1, 0) = {gate.evaluate(1, 0)}")
    print(f"  XOR(1, 1) = {gate.evaluate(1, 1)}")


def demo_nand_gate():
    """演示NAND门"""
    print("\n" + "=" * 50)
    print("NAND门演示")
    print("=" * 50)

    gate = NandGate()

    print(f"\n门名称: {gate.name}")
    print(f"输入数量: {gate.num_inputs}")

    print("\n真值表:")
    print(TruthTableGenerator.generate(gate))

    print("\n计算示例:")
    print(f"  NAND(0, 0) = {gate.evaluate(0, 0)}")
    print(f"  NAND(0, 1) = {gate.evaluate(0, 1)}")
    print(f"  NAND(1, 0) = {gate.evaluate(1, 0)}")
    print(f"  NAND(1, 1) = {gate.evaluate(1, 1)}")


def demo_nor_gate():
    """演示NOR门"""
    print("\n" + "=" * 50)
    print("NOR门演示")
    print("=" * 50)

    gate = NorGate()

    print(f"\n门名称: {gate.name}")
    print(f"输入数量: {gate.num_inputs}")

    print("\n真值表:")
    print(TruthTableGenerator.generate(gate))

    print("\n计算示例:")
    print(f"  NOR(0, 0) = {gate.evaluate(0, 0)}")
    print(f"  NOR(0, 1) = {gate.evaluate(0, 1)}")
    print(f"  NOR(1, 0) = {gate.evaluate(1, 0)}")
    print(f"  NOR(1, 1) = {gate.evaluate(1, 1)}")


def demo_custom_gate():
    """演示自定义门"""
    print("\n" + "=" * 50)
    print("自定义门演示 - 多数表决器")
    print("=" * 50)

    from src.gates import CustomGate

    def majority(*inputs):
        """多数表决：超过半数输入为1时输出1"""
        return int(sum(inputs) > len(inputs) / 2)

    gate = CustomGate("MAJ", 3, majority)

    print(f"\n门名称: {gate.name}")
    print(f"输入数量: {gate.num_inputs}")

    print("\n真值表:")
    print(TruthTableGenerator.generate(gate))

    print("\n计算示例:")
    print(f"  MAJ(0, 0, 0) = {gate.evaluate(0, 0, 0)}")
    print(f"  MAJ(0, 0, 1) = {gate.evaluate(0, 0, 1)}")
    print(f"  MAJ(0, 1, 1) = {gate.evaluate(0, 1, 1)}")
    print(f"  MAJ(1, 1, 1) = {gate.evaluate(1, 1, 1)}")


def main():
    """主函数"""
    print("逻辑门模拟器 - 基本逻辑门演示")
    print("=" * 50)

    demo_and_gate()
    demo_or_gate()
    demo_not_gate()
    demo_xor_gate()
    demo_nand_gate()
    demo_nor_gate()
    demo_custom_gate()

    print("\n" + "=" * 50)
    print("演示完成！")
    print("=" * 50)


if __name__ == "__main__":
    main()
