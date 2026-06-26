"""
Basic logic gate implementations.

Logic gates are the building blocks of digital circuits.
Each gate performs a specific boolean operation on one or more binary inputs.

基本逻辑门实现。
逻辑门是数字电路的基本构建块。
每个门对输入的二进制信号执行特定的布尔运算。
"""

from typing import List, Tuple


def AND(a: int, b: int) -> int:
    """
    AND gate: Output is 1 only when both inputs are 1.
    与门：仅当两个输入都为1时，输出为1。

    Truth table:
    A | B | Out
    0 | 0 |  0
    0 | 1 |  0
    1 | 0 |  0
    1 | 1 |  1

    Mathematical form: Out = A AND B = A * B (in boolean algebra)
    """
    return 1 if (a == 1 and b == 1) else 0


def OR(a: int, b: int) -> int:
    """
    OR gate: Output is 1 when at least one input is 1.
    或门：当至少一个输入为1时，输出为1。

    Truth table:
    A | B | Out
    0 | 0 |  0
    0 | 1 |  1
    1 | 0 |  1
    1 | 1 |  1

    Mathematical form: Out = A OR B = A + B (in boolean algebra)
    """
    return 1 if (a == 1 or b == 1) else 0


def NOT(a: int) -> int:
    """
    NOT gate (Inverter): Output is the inverse of the input.
    非门（反相器）：输出是输入的反相。

    Truth table:
    A | Out
    0 |  1
    1 |  0

    Mathematical form: Out = NOT A = A' = ~A
    """
    return 1 if a == 0 else 0


def NAND(a: int, b: int) -> int:
    """
    NAND gate: NOT of AND. Output is 0 only when both inputs are 1.
    与非门：与门的反相。仅当两个输入都为1时，输出为0。

    Truth table:
    A | B | Out
    0 | 0 |  1
    0 | 1 |  1
    1 | 0 |  1
    1 | 1 |  0

    NAND is a universal gate - any boolean function can be built from NAND gates alone.
    与非门是通用门 - 仅用与非门就可以构建任何布尔函数。
    """
    return NOT(AND(a, b))


def NOR(a: int, b: int) -> int:
    """
    NOR gate: NOT of OR. Output is 1 only when both inputs are 0.
    或非门：或门的反相。仅当两个输入都为0时，输出为1。

    Truth table:
    A | B | Out
    0 | 0 |  1
    0 | 1 |  0
    1 | 0 |  0
    1 | 1 |  0

    NOR is also a universal gate.
    或非门也是通用门。
    """
    return NOT(OR(a, b))


def XOR(a: int, b: int) -> int:
    """
    XOR gate (Exclusive OR): Output is 1 when inputs differ.
    异或门：当两个输入不同时，输出为1。

    Truth table:
    A | B | Out
    0 | 0 |  0
    0 | 1 |  1
    1 | 0 |  1
    1 | 1 |  0

    Mathematical form: Out = A XOR B = A'B + AB'
    XOR is fundamental for arithmetic operations (addition without carry).
    异或运算是算术操作的基础（无进位加法）。
    """
    return 1 if (a != b) else 0


def XNOR(a: int, b: int) -> int:
    """
    XNOR gate (Exclusive NOR): NOT of XOR. Output is 1 when inputs are equal.
    同或门：异或门的反相。当两个输入相同时，输出为1。

    Truth table:
    A | B | Out
    0 | 0 |  1
    0 | 1 |  0
    1 | 0 |  0
    1 | 1 |  1

    Mathematical form: Out = A XNOR B = (A XOR B)' = AB + A'B'
    """
    return NOT(XOR(a, b))
