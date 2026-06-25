#!/usr/bin/env python3
"""
电路组合示例

演示如何组合多个逻辑门构建电路。
"""

import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.circuit import Circuit
from src.gates import AndGate, OrGate, NotGate, XorGate
from src.truth_table import TruthTableGenerator
from src.utils import create_half_adder, create_full_adder, create_mux_2to1


def demo_half_adder():
    """演示半加器"""
    print("=" * 60)
    print("半加器演示")
    print("=" * 60)

    print("\n半加器逻辑:")
    print("  Sum = A XOR B")
    print("  Carry = A AND B")

    circuit = create_half_adder()

    print("\n真值表:")
    print(TruthTableGenerator.generate_circuit_table(circuit))

    print("\n计算示例:")
    test_cases = [
        (0, 0),
        (0, 1),
        (1, 0),
        (1, 1),
    ]

    for a, b in test_cases:
        circuit.set_inputs({"A": a, "B": b})
        results = circuit.evaluate()
        print(f"  A={a}, B={b} -> Sum={results['XOR']}, Carry={results['AND']}")


def demo_full_adder():
    """演示全加器"""
    print("\n" + "=" * 60)
    print("全加器演示")
    print("=" * 60)

    print("\n全加器逻辑:")
    print("  Sum = A XOR B XOR Cin")
    print("  Cout = (A AND B) OR ((A XOR B) AND Cin)")

    circuit = create_full_adder()

    print("\n真值表:")
    print(TruthTableGenerator.generate_circuit_table(circuit))

    print("\n计算示例:")
    test_cases = [
        (0, 0, 0),
        (0, 0, 1),
        (0, 1, 0),
        (0, 1, 1),
        (1, 0, 0),
        (1, 0, 1),
        (1, 1, 0),
        (1, 1, 1),
    ]

    for a, b, cin in test_cases:
        circuit.set_inputs({"A": a, "B": b, "CIN": cin})
        results = circuit.evaluate()
        print(f"  A={a}, B={b}, Cin={cin} -> Sum={results['XOR2']}, Cout={results['OR1']}")


def demo_mux():
    """演示多路选择器"""
    print("\n" + "=" * 60)
    print("2:1 多路选择器演示")
    print("=" * 60)

    print("\n多路选择器逻辑:")
    print("  当 S=0 时，输出 = A")
    print("  当 S=1 时，输出 = B")
    print("  Y = (A AND NOT S) OR (B AND S)")

    circuit = create_mux_2to1()

    print("\n真值表:")
    print(TruthTableGenerator.generate_circuit_table(circuit))

    print("\n计算示例:")
    test_cases = [
        (0, 0, 0),
        (0, 0, 1),
        (0, 1, 0),
        (0, 1, 1),
        (1, 0, 0),
        (1, 0, 1),
        (1, 1, 0),
        (1, 1, 1),
    ]

    for a, b, s in test_cases:
        circuit.set_inputs({"A": a, "B": b, "S": s})
        results = circuit.evaluate()
        expected = a if s == 0 else b
        print(f"  A={a}, B={b}, S={s} -> Y={results['OR']} (expected={expected})")


def demo_custom_circuit():
    """演示自定义电路"""
    print("\n" + "=" * 60)
    print("自定义电路演示 - 比较器")
    print("=" * 60)

    print("\n比较器逻辑:")
    print("  A > B: A AND NOT B")
    print("  A = B: NOT (A XOR B)")
    print("  A < B: NOT A AND B")

    circuit = Circuit("Comparator")

    # 添加门
    not_a = circuit.add_gate(NotGate(), "NOT_A")
    not_b = circuit.add_gate(NotGate(), "NOT_B")
    xor = circuit.add_gate(XorGate(), "XOR")
    not_xor = circuit.add_gate(NotGate(), "NOT_XOR")
    and_gt = circuit.add_gate(AndGate(), "AND_GT")
    and_lt = circuit.add_gate(AndGate(), "AND_LT")

    # 连接
    circuit.connect("A", "NOT_A", 0)
    circuit.connect("B", "NOT_B", 0)
    circuit.connect("A", "XOR", 0)
    circuit.connect("B", "XOR", 1)
    circuit.connect("XOR", "NOT_XOR", 0)
    circuit.connect("A", "AND_GT", 0)
    circuit.connect("NOT_B", "AND_GT", 1)
    circuit.connect("NOT_A", "AND_LT", 0)
    circuit.connect("B", "AND_LT", 1)

    # 标记输入输出
    circuit.mark_as_input("A")
    circuit.mark_as_input("B")
    circuit.mark_as_output("AND_GT")
    circuit.mark_as_output("NOT_XOR")
    circuit.mark_as_output("AND_LT")

    print("\n真值表:")
    print(TruthTableGenerator.generate_circuit_table(circuit))

    print("\n计算示例:")
    test_cases = [
        (0, 0),
        (0, 1),
        (1, 0),
        (1, 1),
    ]

    for a, b in test_cases:
        circuit.set_inputs({"A": a, "B": b})
        results = circuit.evaluate()
        gt = results["AND_GT"]
        eq = results["NOT_XOR"]
        lt = results["AND_LT"]

        if gt:
            comparison = "A > B"
        elif eq:
            comparison = "A = B"
        else:
            comparison = "A < B"

        print(f"  A={a}, B={b} -> {comparison} (GT={gt}, EQ={eq}, LT={lt})")


def main():
    """主函数"""
    print("逻辑门模拟器 - 电路组合演示")
    print("=" * 60)

    demo_half_adder()
    demo_full_adder()
    demo_mux()
    demo_custom_circuit()

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
