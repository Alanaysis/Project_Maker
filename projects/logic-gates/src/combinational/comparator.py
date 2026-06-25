"""
比较器模块

实现二进制比较器。
"""

from typing import List, Dict, Tuple
from ..gates import AndGate, OrGate, NotGate, XorGate
from ..circuit import Circuit


class Comparator:
    """二进制比较器

    比较两个 n 位二进制数的大小。

    输出：
    - A > B: 1 当 A 大于 B
    - A = B: 1 当 A 等于 B
    - A < B: 1 当 A 小于 B

    Examples:
        >>> comp = Comparator(4)  # 4位比较器
        >>> result = comp.evaluate([1, 0, 1, 0], [0, 1, 0, 1])
        >>> result
        {'gt': 1, 'eq': 0, 'lt': 0}  # 10 > 5
    """

    def __init__(self, num_bits: int):
        """初始化比较器

        Args:
            num_bits: 位数
        """
        if num_bits < 1:
            raise ValueError("Number of bits must be positive")

        self.num_bits = num_bits

    def evaluate(self, a: List[int], b: List[int]) -> Dict[str, int]:
        """比较两个数

        Args:
            a: 第一个操作数（二进制列表，高位在前）
            b: 第二个操作数（二进制列表，高位在前）

        Returns:
            Dict[str, int]: {'gt': A>B, 'eq': A==B, 'lt': A<B}

        Raises:
            ValueError: 输入位数不正确
        """
        if len(a) != self.num_bits:
            raise ValueError(f"Expected {self.num_bits} bits for a, got {len(a)}")
        if len(b) != self.num_bits:
            raise ValueError(f"Expected {self.num_bits} bits for b, got {len(b)}")

        # 从高位到低位比较
        gt = 0
        lt = 0

        for i in range(self.num_bits):
            # A > B 的条件：A[i] = 1 且 B[i] = 0，且高位相等
            gt = gt or (a[i] and not b[i] and not lt and not gt)
            # A < B 的条件：A[i] = 0 且 B[i] = 1，且高位相等
            lt = lt or (not a[i] and b[i] and not lt and not gt)

        # A == B
        eq = int(not gt and not lt)

        return {
            'gt': int(gt),
            'eq': eq,
            'lt': int(lt)
        }

    def compare(self, a: int, b: int) -> Dict[str, int]:
        """使用整数进行比较

        Args:
            a: 第一个操作数
            b: 第二个操作数

        Returns:
            Dict[str, int]: {'gt': A>B, 'eq': A==B, 'lt': A<B}
        """
        # 转换为二进制列表（高位在前）
        a_bits = [(a >> (self.num_bits - 1 - i)) & 1 for i in range(self.num_bits)]
        b_bits = [(b >> (self.num_bits - 1 - i)) & 1 for i in range(self.num_bits)]

        return self.evaluate(a_bits, b_bits)

    def is_greater(self, a: int, b: int) -> bool:
        """检查 A 是否大于 B"""
        return self.compare(a, b)['gt'] == 1

    def is_equal(self, a: int, b: int) -> bool:
        """检查 A 是否等于 B"""
        return self.compare(a, b)['eq'] == 1

    def is_less(self, a: int, b: int) -> bool:
        """检查 A 是否小于 B"""
        return self.compare(a, b)['lt'] == 1
