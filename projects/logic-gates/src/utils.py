# 工具函数

"""
工具函数模块

本模块提供各种辅助函数。
"""

from typing import Dict, List, Optional

from .gates import Gate
from .circuit import Circuit
from .truth_table import TruthTableGenerator
from .registry import GateRegistry
from .exceptions import CircuitError


def print_truth_table(gate: Gate):
    """打印真值表

    Args:
        gate: 逻辑门实例

    Examples:
        >>> from logic_gates import AndGate, print_truth_table
        >>> print_truth_table(AndGate())
        AND Gate Truth Table
        --------------------
        | IN0 | IN1 | OUT |
        --------------------
        |  0  |  0  |  0  |
        |  0  |  1  |  0  |
        |  1  |  0  |  0  |
        |  1  |  1  |  1  |
        --------------------
    """
    print(TruthTableGenerator.generate(gate))


def print_circuit_table(circuit: Circuit):
    """打印电路真值表

    Args:
        circuit: 电路实例

    Examples:
        >>> from logic_gates import Circuit, AndGate, print_circuit_table
        >>> circuit = Circuit("Test")
        >>> circuit.add_gate(AndGate(), "AND1")
        >>> print_circuit_table(circuit)
    """
    print(TruthTableGenerator.generate_circuit_table(circuit))


def create_circuit_from_description(description: Dict) -> Circuit:
    """从描述创建电路

    Args:
        description: 电路描述字典，格式如下：
            {
                "name": "电路名称",
                "gates": [
                    {"type": "AND", "name": "AND1"},
                    {"type": "OR", "name": "OR1"}
                ],
                "connections": [
                    {"from": "A", "to": "AND1", "input_idx": 0},
                    {"from": "B", "to": "AND1", "input_idx": 1}
                ],
                "inputs": ["A", "B"],
                "outputs": ["AND1"]
            }

    Returns:
        Circuit: 电路实例

    Raises:
        CircuitError: 描述格式错误

    Examples:
        >>> desc = {
        ...     "name": "AND Circuit",
        ...     "gates": [{"type": "AND", "name": "AND1"}],
        ...     "connections": [
        ...         {"from": "A", "to": "AND1", "input_idx": 0},
        ...         {"from": "B", "to": "AND1", "input_idx": 1}
        ...     ],
        ...     "inputs": ["A", "B"],
        ...     "outputs": ["AND1"]
        ... }
        >>> circuit = create_circuit_from_description(desc)
        >>> circuit.name
        'AND Circuit'
    """
    circuit = Circuit(description.get("name", "Circuit"))

    # 添加门
    for gate_desc in description.get("gates", []):
        gate_type = gate_desc.get("type")
        gate_name = gate_desc.get("name")

        if not gate_type:
            raise CircuitError("Gate type is required")

        gate = GateRegistry.create(gate_type)
        circuit.add_gate(gate, gate_name)

    # 添加连接
    for conn in description.get("connections", []):
        from_name = conn.get("from")
        to_name = conn.get("to")
        input_idx = conn.get("input_idx", 0)

        if not from_name or not to_name:
            raise CircuitError("Connection 'from' and 'to' are required")

        circuit.connect(from_name, to_name, input_idx)

    # 标记输入
    for input_name in description.get("inputs", []):
        circuit.mark_as_input(input_name)

    # 标记输出
    for output_name in description.get("outputs", []):
        circuit.mark_as_output(output_name)

    return circuit


def format_binary(value: int, width: int = 8) -> str:
    """格式化二进制输出

    Args:
        value: 整数值
        width: 位宽

    Returns:
        str: 二进制字符串

    Examples:
        >>> format_binary(5, 8)
        '00000101'
        >>> format_binary(255, 8)
        '11111111'
    """
    return format(value, f'0{width}b')


def binary_to_decimal(binary_str: str) -> int:
    """二进制转十进制

    Args:
        binary_str: 二进制字符串

    Returns:
        int: 十进制值

    Examples:
        >>> binary_to_decimal('101')
        5
        >>> binary_to_decimal('11111111')
        255
    """
    return int(binary_str, 2)


def decimal_to_binary(decimal: int, width: int = 8) -> str:
    """十进制转二进制

    Args:
        decimal: 十进制值
        width: 位宽

    Returns:
        str: 二进制字符串

    Examples:
        >>> decimal_to_binary(5, 8)
        '00000101'
        >>> decimal_to_binary(255, 8)
        '11111111'
    """
    return format(decimal, f'0{width}b')


def create_half_adder() -> Circuit:
    """创建半加器电路

    Returns:
        Circuit: 半加器电路

    Examples:
        >>> circuit = create_half_adder()
        >>> circuit.name
        'Half Adder'
    """
    circuit = Circuit("Half Adder")

    # 添加门
    xor_gate = circuit.add_gate(GateRegistry.create("XOR"), "XOR")
    and_gate = circuit.add_gate(GateRegistry.create("AND"), "AND")

    # 连接
    circuit.connect("A", "XOR", 0)
    circuit.connect("B", "XOR", 1)
    circuit.connect("A", "AND", 0)
    circuit.connect("B", "AND", 1)

    # 标记输入输出
    circuit.mark_as_input("A")
    circuit.mark_as_input("B")
    circuit.mark_as_output("XOR")
    circuit.mark_as_output("AND")

    return circuit


def create_full_adder() -> Circuit:
    """创建全加器电路

    Returns:
        Circuit: 全加器电路

    Examples:
        >>> circuit = create_full_adder()
        >>> circuit.name
        'Full Adder'
    """
    circuit = Circuit("Full Adder")

    # 添加门
    xor1 = circuit.add_gate(GateRegistry.create("XOR"), "XOR1")
    xor2 = circuit.add_gate(GateRegistry.create("XOR"), "XOR2")
    and1 = circuit.add_gate(GateRegistry.create("AND"), "AND1")
    and2 = circuit.add_gate(GateRegistry.create("AND"), "AND2")
    or_gate = circuit.add_gate(GateRegistry.create("OR"), "OR1")

    # 连接第一级
    circuit.connect("A", "XOR1", 0)
    circuit.connect("B", "XOR1", 1)
    circuit.connect("A", "AND1", 0)
    circuit.connect("B", "AND1", 1)

    # 连接第二级
    circuit.connect("XOR1", "XOR2", 0)
    circuit.connect("CIN", "XOR2", 1)
    circuit.connect("XOR1", "AND2", 0)
    circuit.connect("CIN", "AND2", 1)

    # 连接第三级
    circuit.connect("AND1", "OR1", 0)
    circuit.connect("AND2", "OR1", 1)

    # 标记输入输出
    circuit.mark_as_input("A")
    circuit.mark_as_input("B")
    circuit.mark_as_input("CIN")
    circuit.mark_as_output("XOR2")
    circuit.mark_as_output("OR1")

    return circuit


def create_mux_2to1() -> Circuit:
    """创建2选1多路选择器

    Returns:
        Circuit: 多路选择器电路

    Examples:
        >>> circuit = create_mux_2to1()
        >>> circuit.name
        '2:1 MUX'
    """
    circuit = Circuit("2:1 MUX")

    # 添加门
    not_gate = circuit.add_gate(GateRegistry.create("NOT"), "NOT")
    and1 = circuit.add_gate(GateRegistry.create("AND"), "AND1")
    and2 = circuit.add_gate(GateRegistry.create("AND"), "AND2")
    or_gate = circuit.add_gate(GateRegistry.create("OR"), "OR")

    # 连接
    circuit.connect("S", "NOT", 0)
    circuit.connect("NOT", "AND1", 0)
    circuit.connect("A", "AND1", 1)
    circuit.connect("S", "AND2", 0)
    circuit.connect("B", "AND2", 1)
    circuit.connect("AND1", "OR", 0)
    circuit.connect("AND2", "OR", 1)

    # 标记输入输出
    circuit.mark_as_input("A")
    circuit.mark_as_input("B")
    circuit.mark_as_input("S")
    circuit.mark_as_output("OR")

    return circuit
