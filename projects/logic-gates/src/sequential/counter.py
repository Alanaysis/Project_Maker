"""
计数器模块

实现二进制计数器。
"""

from typing import List, Dict
from .flipflop import TFlipFlop


class Counter:
    """二进制计数器

    使用T触发器实现的同步计数器。

    特性：
    - 可配置位数
    - 同步计数
    - 支持递增和递减
    - 支持重置

    Examples:
        >>> counter = Counter(4)  # 4位计数器
        >>> counter.increment()  # 递增
        [0, 0, 0, 1]
        >>> counter.increment()
        [0, 0, 1, 0]
        >>> counter.get_count()
        2
    """

    def __init__(self, num_bits: int):
        """初始化计数器

        Args:
            num_bits: 位数
        """
        if num_bits < 1:
            raise ValueError("Number of bits must be positive")

        self.num_bits = num_bits
        self._flipflops = [TFlipFlop() for _ in range(num_bits)]
        self._count = 0

    def increment(self) -> List[int]:
        """递增计数器

        Returns:
            List[int]: 当前计数值（二进制列表，高位在前）
        """
        # 异步计数器：每个触发器的时钟由前一个触发器的输出驱动
        carry = 1  # 初始进位为1（递增）

        for i in range(self.num_bits - 1, -1, -1):
            # 如果有进位，触发翻转
            if carry == 1:
                result = self._flipflops[i].evaluate(1, 1)
                carry = result['Q']  # Q作为下一个触发器的时钟
            else:
                # 保持状态
                result = self._flipflops[i].get_state()

        # 更新计数值
        self._count = (self._count + 1) % (2 ** self.num_bits)

        return self.get_value()

    def decrement(self) -> List[int]:
        """递减计数器

        Returns:
            List[int]: 当前计数值（二进制列表，高位在前）
        """
        # 异步递减计数器
        borrow = 1  # 初始借位为1（递减）

        for i in range(self.num_bits - 1, -1, -1):
            # 如果有借位，触发翻转
            if borrow == 1:
                result = self._flipflops[i].evaluate(1, 1)
                borrow = 1 - result['Q']  # NOT Q作为下一个触发器的时钟
            else:
                # 保持状态
                result = self._flipflops[i].get_state()

        # 更新计数值
        self._count = (self._count - 1) % (2 ** self.num_bits)

        return self.get_value()

    def reset(self):
        """重置计数器"""
        for ff in self._flipflops:
            ff.reset_state()
        self._count = 0

    def get_value(self) -> List[int]:
        """获取当前计数值

        Returns:
            List[int]: 当前计数值（二进制列表，高位在前）
        """
        return [ff.get_state()['Q'] for ff in self._flipflops]

    def get_count(self) -> int:
        """获取当前计数值（整数）

        Returns:
            int: 当前计数值
        """
        return self._count

    def set_count(self, value: int):
        """设置计数值

        Args:
            value: 要设置的值
        """
        if value < 0 or value >= 2 ** self.num_bits:
            raise ValueError(f"Value must be between 0 and {2 ** self.num_bits - 1}")

        self._count = value

        # 更新触发器状态
        for i in range(self.num_bits):
            bit = (value >> (self.num_bits - 1 - i)) & 1
            if bit == 1:
                self._flipflops[i].evaluate(1, 1)  # 置位
            else:
                self._flipflops[i].reset_state()

    def clock(self, clk: int) -> List[int]:
        """时钟信号

        Args:
            clk: 时钟信号

        Returns:
            List[int]: 当前计数值
        """
        if clk not in (0, 1):
            raise ValueError("Clock must be 0 or 1")

        if clk == 1:
            return self.increment()
        return self.get_value()


class DecadeCounter:
    """十进制计数器

    0-9 循环计数。

    Examples:
        >>> counter = DecadeCounter()
        >>> for _ in range(10):
        ...     counter.increment()
        >>> counter.get_count()
        0  # 回到0
    """

    def __init__(self):
        """初始化十进制计数器"""
        self._counter = Counter(4)  # 4位计数器
        self._max_count = 10

    def increment(self) -> int:
        """递增计数器

        Returns:
            int: 当前计数值
        """
        self._counter.increment()
        if self._counter.get_count() >= self._max_count:
            self._counter.reset()
        return self._counter.get_count()

    def get_count(self) -> int:
        """获取当前计数值

        Returns:
            int: 当前计数值
        """
        return self._counter.get_count()

    def reset(self):
        """重置计数器"""
        self._counter.reset()


class RingCounter:
    """环形计数器

    在固定模式中循环。

    Examples:
        >>> counter = RingCounter(4)
        >>> counter.get_pattern()
        [1, 0, 0, 0]
        >>> counter.clock()
        [0, 1, 0, 0]
    """

    def __init__(self, num_bits: int, initial_pattern: List[int] = None):
        """初始化环形计数器

        Args:
            num_bits: 位数
            initial_pattern: 初始模式，默认为 [1, 0, 0, ...]
        """
        if num_bits < 2:
            raise ValueError("Number of bits must be at least 2")

        self.num_bits = num_bits

        if initial_pattern is None:
            self._pattern = [1] + [0] * (num_bits - 1)
        else:
            if len(initial_pattern) != num_bits:
                raise ValueError("Pattern length must match num_bits")
            self._pattern = initial_pattern.copy()

    def clock(self) -> List[int]:
        """执行一次时钟

        Returns:
            List[int]: 新的模式
        """
        # 右移，最低位移到最高位
        last_bit = self._pattern[-1]
        self._pattern = [last_bit] + self._pattern[:-1]
        return self._pattern.copy()

    def get_pattern(self) -> List[int]:
        """获取当前模式

        Returns:
            List[int]: 当前模式
        """
        return self._pattern.copy()

    def reset(self):
        """重置计数器"""
        self._pattern = [1] + [0] * (self.num_bits - 1)
