"""
Counter implementations / 计数器实现

Counters are sequential circuits that count clock pulses.
计数器是计数时钟脉冲的时序电路。

Types:
- Asynchronous (Ripple): clock cascades through flip-flops
  异步（纹波）：时钟在触发器间级联
- Synchronous: all flip-flops share the same clock
  同步：所有触发器共享同一时钟
- Up/Down: count up or down
  加/减：可向上或向下计数
"""

from typing import List, Tuple
from enum import Enum

from .d_and_t_ff import TFlipFlop, DFlipFlop


class CounterMode(Enum):
    """Counter counting mode / 计数器计数模式"""
    UP = "up"
    DOWN = "down"
    UP_DOWN = "up_down"


class RippleCounter:
    """
    Asynchronous (Ripple) Counter / 异步（纹波）计数器

    In a ripple counter, each flip-flop's clock is driven by the output
    of the previous flip-flop. This creates a "ripple" effect.
    在纹波计数器中，每个触发器的时钟由前一个触发器的输出驱动。
    这产生了"纹波"效应。

    Characteristics:
    - Simple to build from T flip-flops
    - Propagation delay accumulates (slow at high frequencies)
    - Modulo-2^n counter with n flip-flops

    特点：
    - 由T触发器构建简单
    - 传播延迟累积（高频时慢）
    - n个触发器构成模2^n计数器
    """

    def __init__(self, num_bits: int = 4, initial_value: int = 0, mode: CounterMode = CounterMode.UP):
        self.num_bits = num_bits
        self.value = initial_value & ((1 << num_bits) - 1)
        self.mode = mode
        self.ff_list: List[TFlipFlop] = [TFlipFlop((self.value >> i) & 1) for i in range(num_bits)]
        self.history: List[Tuple[int, int]] = []  # (clock_cycle, value)
        self.history.append((0, self.value))

    def _get_bits(self) -> List[int]:
        """Get individual bit values / 获取各个位的值"""
        return [(self.value >> i) & 1 for i in range(self.num_bits)]

    def step(self) -> int:
        """
        Advance the counter by one clock cycle.
        推进一个时钟周期。

        Returns the new count value.
        返回新的计数值。
        """
        old_value = self.value

        if self.mode == CounterMode.UP:
            self.value = (self.value + 1) & ((1 << self.num_bits) - 1)
        elif self.mode == CounterMode.DOWN:
            self.value = (self.value - 1) & ((1 << self.num_bits) - 1)

        # Update flip-flop states to reflect new value
        for i in range(self.num_bits):
            new_bit = (self.value >> i) & 1
            if new_bit != (old_value >> i) & 1:
                self.ff_list[i].clock_rising_edge(1)  # Toggle

        cycle = len(self.history)
        self.history.append((cycle, self.value))
        return self.value

    def get_binary_output(self) -> str:
        """Get binary string representation / 获取二进制字符串表示"""
        return format(self.value, f'0{self.num_bits}b')

    def get_history(self) -> List[Tuple[int, int]]:
        """Get count history / 获取计数历史"""
        return self.history.copy()

    def reset(self, value: int = 0) -> None:
        """Reset counter to initial value / 重置计数器"""
        self.value = value & ((1 << self.num_bits) - 1)
        self.ff_list = [TFlipFlop((self.value >> i) & 1) for i in range(self.num_bits)]
        self.history.append((len(self.history), self.value))

    def __repr__(self) -> str:
        return f"RippleCounter(bits={self.num_bits}, value={self.value} ({self.get_binary_output()}), mode={self.mode.value})"


class SynchronousCounter:
    """
    Synchronous Counter / 同步计数器

    All flip-flops receive the same clock signal simultaneously.
    所有触发器同时接收相同的时钟信号。

    Uses combinational logic to determine each flip-flop's next state.
    使用组合逻辑确定每个触发器的下一状态。

    Characteristics:
    - Faster than ripple counters (no ripple delay)
    - More complex wiring
    - Can be designed for any modulus

    特点：
    - 比纹波计数器快（无纹波延迟）
    - 布线更复杂
    - 可设计为任意模数
    """

    def __init__(self, num_bits: int = 4, initial_value: int = 0, modulus: int = 0, mode: CounterMode = CounterMode.UP):
        """
        Args:
            num_bits: Number of bits / 位数
            initial_value: Initial count value / 初始计数值
            modulus: Counter modulus (0 = 2^num_bits) / 模数（0表示2^num_bits）
            mode: Counting direction / 计数方向
        """
        self.num_bits = num_bits
        self.modulus = modulus if modulus > 0 else (1 << num_bits)
        self.max_count = self.modulus - 1
        self.value = initial_value % self.modulus
        self.mode = mode
        self.history: List[Tuple[int, int]] = []
        self.history.append((0, self.value))

    def step(self) -> int:
        """
        Advance the counter by one clock cycle.
        推进一个时钟周期。

        Returns the new count value.
        返回新的计数值。
        """
        old_value = self.value

        if self.mode == CounterMode.UP:
            if self.value < self.max_count:
                self.value += 1
            else:
                self.value = 0  # Roll over
        elif self.mode == CounterMode.DOWN:
            if self.value > 0:
                self.value -= 1
            else:
                self.value = self.max_count  # Roll under

        cycle = len(self.history)
        self.history.append((cycle, self.value))
        return self.value

    def load(self, value: int) -> None:
        """
        Load a specific value (parallel load).
        加载特定值（并行加载）。
        """
        self.value = value % self.modulus
        self.history.append((len(self.history), self.value))

    def get_binary_output(self) -> str:
        """Get binary string representation / 获取二进制字符串表示"""
        return format(self.value, f'0{self.num_bits}b')

    def get_history(self) -> List[Tuple[int, int]]:
        """Get count history / 获取计数历史"""
        return self.history.copy()

    def reset(self) -> None:
        """Reset to zero / 归零"""
        self.value = 0
        self.history.append((len(self.history), self.value))

    def __repr__(self) -> str:
        return f"SyncCounter(bits={self.num_bits}, mod={self.modulus}, value={self.value} ({self.get_binary_output()}))"


class UpDownCounter:
    """
    Up/Down Counter / 加/减计数器

    Can count up or down based on a control input.
    可以根据控制输入向上或向下计数。

    This is one of the most useful counter types in digital systems.
    这是数字系统中最有用的计数器类型之一。
    """

    def __init__(self, num_bits: int = 4, initial_value: int = 0):
        self.num_bits = num_bits
        self.value = initial_value & ((1 << num_bits) - 1)
        self.up_down: int = 1  # 1 = up, 0 = down
        self.max_count = (1 << num_bits) - 1
        self.history: List[Tuple[int, int, str]] = []  # (cycle, value, direction)
        self.history.append((0, self.value, "init"))

    def set_direction(self, up: bool) -> None:
        """Set counting direction / 设置计数方向"""
        self.up_down = 1 if up else 0

    def step(self) -> int:
        """
        Advance the counter by one clock cycle in current direction.
        以当前方向推进一个时钟周期。

        Returns the new count value.
        返回新的计数值。
        """
        old_value = self.value

        if self.up_down == 1:
            self.value = (self.value + 1) & self.max_count
        else:
            self.value = (self.value - 1) & self.max_count

        direction = "up" if self.up_down == 1 else "down"
        cycle = len(self.history)
        self.history.append((cycle, self.value, direction))
        return self.value

    def load(self, value: int) -> None:
        """Load a specific value / 加载特定值"""
        self.value = value & self.max_count
        self.history.append((len(self.history), self.value, "load"))

    def get_binary_output(self) -> str:
        """Get binary string representation / 获取二进制字符串表示"""
        return format(self.value, f'0{self.num_bits}b')

    def get_history(self) -> List[Tuple[int, int, str]]:
        """Get count history / 获取计数历史"""
        return self.history.copy()

    def __repr__(self) -> str:
        direction = "UP" if self.up_down == 1 else "DOWN"
        return f"UpDownCounter(bits={self.num_bits}, value={self.value} ({self.get_binary_output()}), dir={direction})"
