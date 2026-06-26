"""
Multi-bit operations for logic gates.

Extends single-bit gates to operate on multi-bit values (bit vectors).
逻辑门的多位操作扩展。
将单比特门扩展到多比特值（位向量）操作。
"""

from typing import List

from .gates import AND, OR, NOT, XOR


def bit_to_list(n: int, width: int) -> List[int]:
    """
    Convert an integer to a list of bits (MSB first).
    将整数转换为位列表（高位在前）。

    Args:
        n: Non-negative integer
        width: Number of bits

    Returns:
        List of bits (0 or 1)
    """
    return [(n >> i) & 1 for i in range(width - 1, -1, -1)]


def list_to_bit(bits: List[int]) -> int:
    """
    Convert a list of bits to an integer (MSB first).
    将位列表转换为整数（高位在前）。

    Args:
        bits: List of bits (0 or 1)

    Returns:
        Integer value
    """
    result = 0
    for bit in bits:
        result = (result << 1) | bit
    return result


def bitwise_and(a: int, b: int, width: int) -> int:
    """
    Perform bitwise AND on two multi-bit values.
    对两个多位值执行按位与运算。

    Args:
        a: First value
        b: Second value
        width: Bit width

    Returns:
        Result as integer
    """
    a_bits = bit_to_list(a, width)
    b_bits = bit_to_list(b, width)
    result_bits = [AND(a_bits[i], b_bits[i]) for i in range(width)]
    return list_to_bit(result_bits)


def bitwise_or(a: int, b: int, width: int) -> int:
    """
    Perform bitwise OR on two multi-bit values.
    对两个多位值执行按位或运算。

    Args:
        a: First value
        b: Second value
        width: Bit width

    Returns:
        Result as integer
    """
    a_bits = bit_to_list(a, width)
    b_bits = bit_to_list(b, width)
    result_bits = [OR(a_bits[i], b_bits[i]) for i in range(width)]
    return list_to_bit(result_bits)


def bitwise_xor(a: int, b: int, width: int) -> int:
    """
    Perform bitwise XOR on two multi-bit values.
    对两个多位值执行按位异或运算。

    Args:
        a: First value
        b: Second value
        width: Bit width

    Returns:
        Result as integer
    """
    a_bits = bit_to_list(a, width)
    b_bits = bit_to_list(b, width)
    result_bits = [XOR(a_bits[i], b_bits[i]) for i in range(width)]
    return list_to_bit(result_bits)


def bitwise_not(a: int, width: int) -> int:
    """
    Perform bitwise NOT on a multi-bit value.
    对多位值执行按位非运算。

    Args:
        a: Input value
        width: Bit width

    Returns:
        Result as integer
    """
    bits = bit_to_list(a, width)
    result_bits = [NOT(bits[i]) for i in range(width)]
    return list_to_bit(result_bits)


def shift_left(value: int, width: int, amount: int) -> int:
    """
    Logical left shift.
    逻辑左移。

    Args:
        value: Input value
        width: Bit width
        amount: Number of positions to shift

    Returns:
        Result as integer
    """
    return (value << amount) & ((1 << width) - 1)


def shift_right(value: int, width: int, amount: int) -> int:
    """
    Logical right shift (fills with zeros).
    逻辑右移（用零填充）。

    Args:
        value: Input value
        width: Bit width
        amount: Number of positions to shift

    Returns:
        Result as integer
    """
    return value >> amount
