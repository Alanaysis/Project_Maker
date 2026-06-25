"""
加法器模块

实现半加器、全加器和纹波进位加法器。
"""

from typing import List, Dict, Tuple
from ..gates import AndGate, OrGate, XorGate
from ..circuit import Circuit


class HalfAdder:
    """半加器

    计算两个一位二进制数的和与进位。

    Truth Table:
        A | B | Sum | Carry
        0 | 0 |  0  |  0
        0 | 1 |  1  |  0
        1 | 0 |  1  |  0
        1 | 1 |  0  |  1

    Examples:
        >>> ha = HalfAdder()
        >>> sum_val, carry = ha.evaluate(1, 1)
        >>> sum_val, carry
        (0, 1)
    """

    def __init__(self):
        """初始化半加器"""
        self._circuit = self._build_circuit()

    def _build_circuit(self) -> Circuit:
        """构建半加器电路

        Returns:
            Circuit: 电路实例
        """
        circuit = Circuit("Half Adder")

        # 添加门
        xor_gate = circuit.add_gate(XorGate(), "XOR")
        and_gate = circuit.add_gate(AndGate(), "AND")

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

    def evaluate(self, a: int, b: int) -> Tuple[int, int]:
        """计算半加器输出

        Args:
            a: 第一个输入
            b: 第二个输入

        Returns:
            Tuple[int, int]: (和, 进位)
        """
        self._circuit.set_inputs({"A": a, "B": b})
        results = self._circuit.evaluate()

        return results.get("XOR", 0), results.get("AND", 0)


class FullAdder:
    """全加器

    计算两个一位二进制数与进位输入的和。

    Truth Table:
        A | B | Cin | Sum | Cout
        0 | 0 |  0  |  0  |  0
        0 | 0 |  1  |  1  |  0
        0 | 1 |  0  |  1  |  0
        0 | 1 |  1  |  0  |  1
        1 | 0 |  0  |  1  |  0
        1 | 0 |  1  |  0  |  1
        1 | 1 |  0  |  0  |  1
        1 | 1 |  1  |  1  |  1

    Examples:
        >>> fa = FullAdder()
        >>> sum_val, carry = fa.evaluate(1, 1, 1)
        >>> sum_val, carry
        (1, 1)
    """

    def __init__(self):
        """初始化全加器"""
        self._circuit = self._build_circuit()

    def _build_circuit(self) -> Circuit:
        """构建全加器电路

        Returns:
            Circuit: 电路实例
        """
        circuit = Circuit("Full Adder")

        # 添加门
        xor1 = circuit.add_gate(XorGate(), "XOR1")
        xor2 = circuit.add_gate(XorGate(), "XOR2")
        and1 = circuit.add_gate(AndGate(), "AND1")
        and2 = circuit.add_gate(AndGate(), "AND2")
        or_gate = circuit.add_gate(OrGate(), "OR1")

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

    def evaluate(self, a: int, b: int, cin: int) -> Tuple[int, int]:
        """计算全加器输出

        Args:
            a: 第一个输入
            b: 第二个输入
            cin: 进位输入

        Returns:
            Tuple[int, int]: (和, 进位输出)
        """
        self._circuit.set_inputs({"A": a, "B": b, "CIN": cin})
        results = self._circuit.evaluate()

        return results.get("XOR2", 0), results.get("OR1", 0)


class RippleCarryAdder:
    """纹波进位加法器

    使用多个全加器串联实现多位加法。

    Examples:
        >>> adder = RippleCarryAdder(4)  # 4位加法器
        >>> result, carry = adder.evaluate([0, 1, 0, 1], [0, 0, 1, 1])
        >>> result, carry
        ([1, 0, 0, 0], 0)  # 5 + 3 = 8
    """

    def __init__(self, num_bits: int):
        """初始化纹波进位加法器

        Args:
            num_bits: 位数
        """
        if num_bits < 1:
            raise ValueError("Number of bits must be positive")

        self.num_bits = num_bits
        self._full_adders = [FullAdder() for _ in range(num_bits)]

    def evaluate(self, a: List[int], b: List[int], cin: int = 0) -> Tuple[List[int], int]:
        """计算加法结果

        Args:
            a: 第一个操作数（二进制列表，低位在前）
            b: 第二个操作数（二进制列表，低位在前）
            cin: 初始进位输入

        Returns:
            Tuple[List[int], int]: (结果列表, 最终进位)

        Raises:
            ValueError: 输入位数不正确
        """
        if len(a) != self.num_bits:
            raise ValueError(f"Expected {self.num_bits} bits for a, got {len(a)}")
        if len(b) != self.num_bits:
            raise ValueError(f"Expected {self.num_bits} bits for b, got {len(b)}")

        result = []
        carry = cin

        for i in range(self.num_bits):
            sum_val, carry = self._full_adders[i].evaluate(a[i], b[i], carry)
            result.append(sum_val)

        return result, carry

    def add(self, a: int, b: int, cin: int = 0) -> Tuple[int, int]:
        """使用整数进行加法

        Args:
            a: 第一个操作数
            b: 第二个操作数
            cin: 初始进位输入

        Returns:
            Tuple[int, int]: (结果, 进位)
        """
        # 转换为二进制列表
        a_bits = [(a >> i) & 1 for i in range(self.num_bits)]
        b_bits = [(b >> i) & 1 for i in range(self.num_bits)]

        # 执行加法
        result_bits, carry = self.evaluate(a_bits, b_bits, cin)

        # 转换回整数
        result = 0
        for i, bit in enumerate(result_bits):
            result |= bit << i

        return result, carry
