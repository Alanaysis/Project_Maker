#!/usr/bin/env python3
"""
命令行接口

提供命令行界面来使用逻辑门模拟器。
"""

import argparse
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.gates import AndGate, OrGate, NotGate, XorGate, NandGate, NorGate
from src.circuit import Circuit
from src.truth_table import TruthTableGenerator
from src.registry import GateRegistry
from src.utils import (
    create_half_adder,
    create_full_adder,
    create_mux_2to1,
)


def print_truth_table(gate_name):
    """打印真值表"""
    gate = GateRegistry.create(gate_name)
    print(TruthTableGenerator.generate(gate))


def run_example(example_name):
    """运行示例"""
    if example_name == "and":
        print("AND门示例:")
        gate = AndGate()
        print(TruthTableGenerator.generate(gate))

    elif example_name == "or":
        print("OR门示例:")
        gate = OrGate()
        print(TruthTableGenerator.generate(gate))

    elif example_name == "not":
        print("NOT门示例:")
        gate = NotGate()
        print(TruthTableGenerator.generate(gate))

    elif example_name == "xor":
        print("XOR门示例:")
        gate = XorGate()
        print(TruthTableGenerator.generate(gate))

    elif example_name == "nand":
        print("NAND门示例:")
        gate = NandGate()
        print(TruthTableGenerator.generate(gate))

    elif example_name == "nor":
        print("NOR门示例:")
        gate = NorGate()
        print(TruthTableGenerator.generate(gate))

    elif example_name == "half_adder":
        print("半加器示例:")
        circuit = create_half_adder()
        print(TruthTableGenerator.generate_circuit_table(circuit))

    elif example_name == "full_adder":
        print("全加器示例:")
        circuit = create_full_adder()
        print(TruthTableGenerator.generate_circuit_table(circuit))

    elif example_name == "mux":
        print("多路选择器示例:")
        circuit = create_mux_2to1()
        print(TruthTableGenerator.generate_circuit_table(circuit))

    else:
        print(f"未知示例: {example_name}")
        print("可用示例: and, or, not, xor, nand, nor, half_adder, full_adder, mux")


def simulate_circuit(circuit_name, inputs_str):
    """模拟电路"""
    # 解析输入
    inputs = {}
    if inputs_str:
        for pair in inputs_str.split(","):
            name, value = pair.split("=")
            inputs[name.strip()] = int(value.strip())

    # 创建电路
    if circuit_name == "half_adder":
        circuit = create_half_adder()
    elif circuit_name == "full_adder":
        circuit = create_full_adder()
    elif circuit_name == "mux":
        circuit = create_mux_2to1()
    else:
        print(f"未知电路: {circuit_name}")
        print("可用电路: half_adder, full_adder, mux")
        return

    # 设置输入
    circuit.set_inputs(inputs)

    # 计算输出
    results = circuit.evaluate()

    # 显示结果
    print(f"\n电路: {circuit.name}")
    print(f"输入: {inputs}")
    print("输出:")
    for name, value in results.items():
        if name in circuit._output_gates:
            print(f"  {name} = {value}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="逻辑门模拟器 - 用于学习数字电路的工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  logic-gates --example and           # 运行AND门示例
  logic-gates --truth-table AND       # 生成AND门真值表
  logic-gates --circuit half_adder --inputs A=1,B=0  # 模拟半加器
        """
    )

    parser.add_argument(
        "--example",
        type=str,
        help="运行示例 (and, or, not, xor, nand, nor, half_adder, full_adder, mux)"
    )

    parser.add_argument(
        "--truth-table",
        type=str,
        help="生成真值表 (AND, OR, NOT, XOR, NAND, NOR)"
    )

    parser.add_argument(
        "--circuit",
        type=str,
        help="模拟电路 (half_adder, full_adder, mux)"
    )

    parser.add_argument(
        "--inputs",
        type=str,
        help="输入信号 (A=1,B=0,...)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="详细输出"
    )

    args = parser.parse_args()

    # 如果没有参数，显示帮助
    if len(sys.argv) == 1:
        parser.print_help()
        return

    # 运行示例
    if args.example:
        run_example(args.example)
        return

    # 生成真值表
    if args.truth_table:
        print_truth_table(args.truth_table)
        return

    # 模拟电路
    if args.circuit:
        simulate_circuit(args.circuit, args.inputs)
        return

    # 如果没有有效参数，显示帮助
    parser.print_help()


if __name__ == "__main__":
    main()
