"""
数值比较器模块
Magnitude Comparator Module

数值比较器用于比较两个二进制数的大小关系。
- 1位比较器：比较两个1位二进制数
- 多位比较器：比较两个n位二进制数

Magnitude comparators compare the relationship between two binary numbers.
- 1-bit comparator: compares two 1-bit numbers
- Multi-bit comparator: compares two n-bit numbers
"""

from src.gates import XOR, AND, OR, NOT


class Comparator1Bit:
    """
    1位数值比较器
    1-bit Magnitude Comparator

    比较两个1位输入A和B，输出三个信号：
    - A_gt_B: A > B
    - A_eq_B: A = B
    - A_lt_B: A < B

    Truth Table:
    A | B | A>B | A=B | A<B
    0 | 0 |  0  |  1  |  0
    0 | 1 |  0  |  0  |  1
    1 | 0 |  1  |  0  |  0
    1 | 1 |  0  |  1  |  0

    A_gt_B = A AND (NOT B)
    A_eq_B = A XNOR B
    A_lt_B = (NOT A) AND B
    """

    def __init__(self):
        self.xnor = XOR()
        self.and_gt = AND()
        self.and_lt = AND()
        self.not_b = NOT()
        self.not_a = NOT()

    def compare(self, a: int, b: int) -> tuple:
        """
        比较两个1位二进制数

        Args:
            a: 第一个数
            b: 第二个数

        Returns:
            (a_gt_b, a_eq_b, a_lt_b) 元组
        """
        if a not in (0, 1) or b not in (0, 1):
            raise ValueError("Inputs must be 0 or 1")

        not_a = self.not_a.evaluate(a)
        not_b = self.not_b.evaluate(b)

        a_gt_b = self.and_gt.evaluate(a, not_b)
        # XNOR: 输入相同时输出1
        a_eq_b = 1 if self.xnor.evaluate(a, b) == 0 else 0
        a_lt_b = self.and_lt.evaluate(not_a, b)

        return a_gt_b, a_eq_b, a_lt_b


class Comparator4Bit:
    """
    4位数值比较器
    4-bit Magnitude Comparator

    比较两个4位二进制数A和B。
    通过级联实现：从最高位开始比较，如果相等则比较下一位。

    Compares two 4-bit binary numbers A and B.
    Implemented by cascading: compare from MSB, if equal compare next bit.
    """

    def __init__(self):
        self.bit_comparators = [Comparator1Bit() for _ in range(4)]

    def compare(self, a: int, b: int) -> tuple:
        """
        比较两个4位二进制数

        Args:
            a: 第一个4位数
            b: 第二个4位数

        Returns:
            (a_gt_b, a_eq_b, a_lt_b) 元组
        """
        if not (0 <= a <= 15) or not (0 <= b <= 15):
            raise ValueError("Inputs must be 0-15 for 4-bit comparison")

        # 从最高位到最低位逐位比较
        for i in range(3, -1, -1):
            bit_a = (a >> i) & 1
            bit_b = (b >> i) & 1

            gt, eq, lt = self.bit_comparators[i].compare(bit_a, bit_b)

            if gt:
                return (1, 0, 0)  # A > B
            if lt:
                return (0, 0, 1)  # A < B

        return (0, 1, 0)  # A == B

    def to_string(self, a: int, b: int) -> str:
        """
        获取可读的比较结果字符串

        Returns:
            比较结果字符串
        """
        gt, eq, lt = self.compare(a, b)
        if gt:
            return f"{a} > {b}"
        elif lt:
            return f"{a} < {b}"
        else:
            return f"{a} == {b}"

    def get_comparison_details(self, a: int, b: int) -> list:
        """
        获取逐位比较详情（用于教学）

        Returns:
            逐位比较结果列表
        """
        details = []
        for i in range(3, -1, -1):
            bit_a = (a >> i) & 1
            bit_b = (b >> i) & 1
            gt, eq, lt = self.bit_comparators[i].compare(bit_a, bit_b)
            details.append({
                "bit_position": i,
                "a_bit": bit_a,
                "b_bit": bit_b,
                "gt": gt,
                "eq": eq,
                "lt": lt
            })
        return details


class ComparatorNBit:
    """
    n位数值比较器（可扩展）
    n-bit Magnitude Comparator (scalable)

    通过级联1位比较器实现任意位数的比较。
    支持链式扩展：可以级联多个比较器实现更大位数的比较。

    Implemented by cascading 1-bit comparators.
    Supports chain extension: can cascade multiple comparators.
    """

    def __init__(self, num_bits: int = 8):
        """
        Args:
            num_bits: 比较器位数
        """
        if num_bits < 1:
            raise ValueError("Number of bits must be at least 1")
        self.num_bits = num_bits
        self.bit_comparators = [Comparator1Bit() for _ in range(num_bits)]

    def compare(self, a: int, b: int) -> tuple:
        """
        比较两个n位二进制数

        Args:
            a: 第一个数
            b: 第二个数

        Returns:
            (a_gt_b, a_eq_b, a_lt_b) 元组
        """
        max_val = (1 << self.num_bits) - 1
        if not (0 <= a <= max_val) or not (0 <= b <= max_val):
            raise ValueError(f"Inputs must be 0-{max_val}")

        # 从最高位到最低位逐位比较
        for i in range(self.num_bits - 1, -1, -1):
            bit_a = (a >> i) & 1
            bit_b = (b >> i) & 1

            gt, eq, lt = self.bit_comparators[i].compare(bit_a, bit_b)

            if gt:
                return (1, 0, 0)
            if lt:
                return (0, 0, 1)

        return (0, 1, 0)

    def to_string(self, a: int, b: int) -> str:
        """
        获取可读的比较结果字符串

        Returns:
            比较结果字符串
        """
        gt, eq, lt = self.compare(a, b)
        if gt:
            return f"{a} > {b}"
        elif lt:
            return f"{a} < {b}"
        else:
            return f"{a} == {b}"
