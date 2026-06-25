#!/usr/bin/env python3
"""
真值表示例

演示真值表的生成和使用。
"""

import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.gates import AndGate, OrGate, NotGate, XorGate, NandGate, NorGate
from src.circuit import Circuit
from src.truth_table import TruthTableGenerator


def demo_single_gate_table():
    """演示单个门的真值表"""
    print("=" * 60)
    print("单个逻辑门真值表")
    print("=" * 60)

    gates = [
        AndGate(),
        OrGate(),
        NotGate(),
        XorGate(),
        NandGate(),
        NorGate(),
    ]

    for gate in gates:
        print(f"\n{gate.name}门真值表:")
        print(TruthTableGenerator.generate(gate))


def demo_circuit_table():
    """演示电路真值表"""
    print("\n" + "=" * 60)
    print("电路真值表")
    print("=" * 60)

    # 创建半加器电路
    circuit = Circuit("Half Adder")
    circuit.add_gate(XorGate(), "XOR")
    circuit.add_gate(AndGate(), "AND")

    circuit.connect("A", "XOR", 0)
    circuit.connect("B", "XOR", 1)
    circuit.connect("A", "AND", 0)
    circuit.connect("B", "AND", 1)

    circuit.mark_as_input("A")
    circuit.mark_as_input("B")
    circuit.mark_as_output("XOR")
    circuit.mark_as_output("AND")

    print("\n半加器真值表:")
    print(TruthTableGenerator.generate_circuit_table(circuit))


def demo_table_formats():
    """演示不同格式的真值表"""
    print("\n" + "=" * 60)
    print("真值表格式")
    print("=" * 60)

    gate = AndGate()
    table = gate.truth_table()

    print("\n1. 表格格式:")
    print(TruthTableGenerator.format_table(table, "AND"))

    print("\n2. 字典格式:")
    dict_table = TruthTableGenerator.to_dict(table)
    for row in dict_table:
        print(f"  {row}")

    print("\n3. CSV格式:")
    csv_table = TruthTableGenerator.to_csv(table, "AND")
    print(csv_table)

    print("\n4. JSON格式:")
    json_table = TruthTableGenerator.to_json(table)
    for row in json_table:
        print(f"  {row}")


def demo_truth_table_analysis():
    """演示真值表分析"""
    print("\n" + "=" * 60)
    print("真值表分析")
    print("=" * 60)

    gate = AndGate()
    table = gate.truth_table()

    # 统计输出为1的数量
    ones_count = sum(1 for _, output in table if output == 1)
    zeros_count = sum(1 for _, output in table if output == 0)

    print(f"\n{gate.name}门统计:")
    print(f"  总行数: {len(table)}")
    print(f"  输出为1的数量: {ones_count}")
    print(f"  输出为0的数量: {zeros_count}")
    print(f"  为1的比例: {ones_count / len(table) * 100:.1f}%")

    # 分析输入组合
    print("\n输入组合分析:")
    for inputs, output in table:
        input_str = ", ".join([f"IN{i}={v}" for i, v in enumerate(inputs)])
        print(f"  {input_str} -> OUT={output}")


def demo_complex_circuit_table():
    """演示复杂电路真值表"""
    print("\n" + "=" * 60)
    print("复杂电路真值表 - 2位加法器")
    print("=" * 60)

    # 创建2位加法器
    circuit = Circuit("2-bit Adder")

    # 低位加法器
    xor1 = circuit.add_gate(XorGate(), "XOR1")
    and1 = circuit.add_gate(AndGate(), "AND1")

    # 高位加法器
    xor2 = circuit.add_gate(XorGate(), "XOR2")
    and2 = circuit.add_gate(AndGate(), "AND2")

    # 进位传播
    or_carry = circuit.add_gate(OrGate(), "OR_CARRY")

    # 连接低位
    circuit.connect("A0", "XOR1", 0)
    circuit.connect("B0", "XOR1", 1)
    circuit.connect("A0", "AND1", 0)
    circuit.connect("B0", "AND1", 1)

    # 连接高位
    circuit.connect("A1", "XOR2", 0)
    circuit.connect("B1", "XOR2", 1)
    circuit.connect("A1", "AND2", 0)
    circuit.connect("B1", "AND2", 1)

    # 连接进位
    circuit.connect("AND1", "OR_CARRY", 0)
    circuit.connect("AND2", "OR_CARRY", 1)

    # 标记输入输出
    circuit.mark_as_input("A0")
    circuit.mark_as_input("B0")
    circuit.mark_as_input("A1")
    circuit.mark_as_input("B1")
    circuit.mark_as_output("XOR1")
    circuit.mark_as_output("XOR2")
    circuit.mark_as_output("OR_CARRY")

    print("\n2位加法器真值表:")
    print(TruthTableGenerator.generate_circuit_table(circuit))


def main():
    """主函数"""
    print("逻辑门模拟器 - 真值表演示")
    print("=" * 60)

    demo_single_gate_table()
    demo_circuit_table()
    demo_table_formats()
    demo_truth_table_analysis()
    demo_complex_circuit_table()

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
