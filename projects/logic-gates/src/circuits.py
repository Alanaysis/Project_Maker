"""
Gate composition - building complex circuits from basic gates.

This module demonstrates how to construct arithmetic circuits
from fundamental logic gates.
门组合 - 从基本门构建复杂电路。
本模块演示如何从基本逻辑门构建算术电路。
"""

from typing import List, Tuple

from .gates import XOR, AND, OR, NOT
from .multi_bit import bit_to_list, list_to_bit


class Wire:
    """Represents a signal wire carrying a single bit value."""

    def __init__(self, name: str = "", value: int = 0):
        self.name = name
        self.value = value

    def __repr__(self):
        return f"Wire({self.name}={self.value})"


class Gate:
    """Base class for logic gate components."""

    def __init__(self, name: str, num_inputs: int):
        self.name = name
        self.num_inputs = num_inputs
        self.inputs: List[Wire] = []
        self.output: Wire = Wire()

    def set_inputs(self, wires: List[Wire]):
        """Set the input wires for this gate."""
        self.inputs = wires

    def evaluate(self) -> int:
        """Evaluate the gate and return the output value."""
        raise NotImplementedError

    def update(self):
        """Evaluate and update the output wire."""
        self.output.value = self.evaluate()


class HalfAdder(Gate):
    """
    Half Adder (半加器): Adds two single bits.

    Produces a Sum and a Carry output.
    产生和（Sum）与进位（Carry）输出。

    Truth table:
    A | B | Sum | Carry
    0 | 0 |  0  |   0
    0 | 1 |  1  |   0
    1 | 0 |  1  |   0
    1 | 1 |  0  |   1

    Sum = A XOR B
    Carry = A AND B
    """

    def __init__(self):
        super().__init__("HalfAdder", 2)
        self.sum_wire = Wire("Sum")
        self.carry_wire = Wire("Carry")
        self.sum_gate = Gate("XOR", 2)
        self.carry_gate = Gate("AND", 2)

    def set_inputs(self, a: Wire, b: Wire):
        """Set inputs and connect internal gates."""
        self.inputs = [a, b]
        self.sum_gate.set_inputs([a, b])
        self.carry_gate.set_inputs([a, b])

    def evaluate(self) -> int:
        """Evaluate and return sum (for interface compatibility)."""
        self.sum_gate.update()
        self.carry_gate.update()
        self.sum_wire.value = self.sum_gate.output.value
        self.carry_wire.value = self.carry_gate.output.value
        self.output.value = self.sum_gate.output.value
        return self.output.value

    def get_result(self) -> Tuple[int, int]:
        """Get (sum, carry) result."""
        return self.sum_wire.value, self.carry_wire.value


class FullAdder(Gate):
    """
    Full Adder (全加器): Adds three single bits (A, B, Carry-in).

    Produces a Sum and a Carry-out output.
    产生和（Sum）与进位输出（Carry-out）。

    Truth table:
    A | B | Cin | Sum | Cout
    0 | 0 |  0  |  0  |  0
    0 | 1 |  0  |  1  |  0
    1 | 0 |  0  |  1  |  0
    1 | 1 |  0  |  0  |  1
    0 | 0 |  1  |  1  |  0
    0 | 1 |  1  |  0  |  1
    1 | 0 |  1  |  0  |  1
    1 | 1 |  1  |  1  |  1

    Sum = A XOR B XOR Cin
    Cout = (A AND B) OR (Cin AND (A XOR B))
    """

    def __init__(self):
        super().__init__("FullAdder", 3)
        self.sum_wire = Wire("Sum")
        self.carry_wire = Wire("Cout")
        # Internal gates
        self.xor1 = Gate("XOR1", 2)
        self.xor2 = Gate("XOR2", 2)
        self.and1 = Gate("AND1", 2)
        self.and2 = Gate("AND2", 2)
        self.or_gate = Gate("OR", 2)

    def set_inputs(self, a: Wire, b: Wire, cin: Wire):
        """Set inputs and connect internal gates."""
        self.inputs = [a, b, cin]
        self.xor1.set_inputs([a, b])
        self.and1.set_inputs([a, b])
        self.and2.set_inputs([self.xor1.output, cin])
        self.xor2.set_inputs([self.xor1.output, cin])
        self.or_gate.set_inputs([self.and1.output, self.and2.output])

    def evaluate(self) -> int:
        """Evaluate and return sum."""
        self.xor1.update()
        self.and1.update()
        self.and2.update()
        self.xor2.update()
        self.or_gate.update()
        self.sum_wire.value = self.xor2.output.value
        self.carry_wire.value = self.or_gate.output.value
        self.output.value = self.xor2.output.value
        return self.output.value

    def get_result(self) -> Tuple[int, int]:
        """Get (sum, carry_out) result."""
        return self.sum_wire.value, self.carry_wire.value


def build_n_bit_adder(n: int) -> List[FullAdder]:
    """
    Build an n-bit ripple carry adder from full adders.
    从全加器构建 n 位行波进位加法器。

    Args:
        n: Number of bits

    Returns:
        List of FullAdder instances
    """
    adders = []
    for i in range(n):
        adder = FullAdder()
        adders.append(adder)
    return adders


def add_n_bit(a: int, b: int, n: int) -> Tuple[int, int]:
    """
    Add two n-bit numbers using ripple carry addition.
    使用行波进位加法器对两个 n 位数相加。

    Args:
        a: First n-bit number
        b: Second n-bit number
        n: Bit width

    Returns:
        (sum, final_carry) as integers
    """
    a_bits = bit_to_list(a, n)
    b_bits = bit_to_list(b, n)

    # Create wires for each bit
    a_wires = [Wire(f"A{i}") for i in range(n)]
    b_wires = [Wire(f"B{i}") for i in range(n)]

    for i in range(n):
        a_wires[i].value = a_bits[i]
        b_wires[i].value = b_bits[i]

    # Build adder chain
    adders = build_n_bit_adder(n)
    carry_in = Wire("Cin", 0)

    for i in range(n):
        adders[i].set_inputs(a_wires[i], b_wires[i], carry_in)
        adders[i].evaluate()
        carry_in = Wire("Cin", adders[i].get_result()[1])

    # Collect sum bits (LSB first)
    sum_bits = [adders[i].get_result()[0] for i in range(n)]
    sum_value = list_to_bit(sum_bits[::-1])
    final_carry = carry_in.value

    return sum_value, final_carry


def build_half_adder_circuit() -> Tuple[HalfAdder, str]:
    """
    Build and demonstrate a half adder circuit.

    Returns:
        Tuple of (HalfAdder instance, description string)
    """
    ha = HalfAdder()
    a = Wire("A", 1)
    b = Wire("B", 1)
    ha.set_inputs(a, b)
    ha.evaluate()
    s, c = ha.get_result()
    desc = (
        f"Half Adder (半加器):\n"
        f"  Input: A={a.value}, B={b.value}\n"
        f"  Sum = {s}, Carry = {c}\n"
        f"  (Sum = A XOR B, Carry = A AND B)"
    )
    return ha, desc
