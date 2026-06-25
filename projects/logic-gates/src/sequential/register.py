"""
寄存器模块

实现寄存器和移位寄存器。
"""

from typing import List, Dict
from .flipflop import DFlipFlop


class Register:
    """寄存器

    使用D触发器实现的n位寄存器。

    特性：
    - 可配置位数
    - 并行加载
    - 同步写入

    Examples:
        >>> reg = Register(4)  # 4位寄存器
        >>> reg.load([1, 0, 1, 0])  # 加载数据
        >>> reg.read()
        [1, 0, 1, 0]
    """

    def __init__(self, num_bits: int):
        """初始化寄存器

        Args:
            num_bits: 位数
        """
        if num_bits < 1:
            raise ValueError("Number of bits must be positive")

        self.num_bits = num_bits
        self._flipflops = [DFlipFlop() for _ in range(num_bits)]

    def load(self, data: List[int]) -> List[int]:
        """加载数据到寄存器

        Args:
            data: 要加载的数据（二进制列表，高位在前）

        Returns:
            List[int]: 寄存器内容
        """
        if len(data) != self.num_bits:
            raise ValueError(f"Expected {self.num_bits} bits, got {len(data)}")

        # 在时钟上升沿加载数据
        for i in range(self.num_bits):
            self._flipflops[i].evaluate(data[i], 1)  # CLK = 1

        # 时钟下降沿
        for i in range(self.num_bits):
            self._flipflops[i].clock(0)

        return self.read()

    def read(self) -> List[int]:
        """读取寄存器内容

        Returns:
            List[int]: 寄存器内容（二进制列表，高位在前）
        """
        return [ff.get_state()['Q'] for ff in self._flipflops]

    def clear(self):
        """清零寄存器"""
        self.load([0] * self.num_bits)

    def get_value(self) -> int:
        """获取寄存器值（整数）

        Returns:
            int: 寄存器值
        """
        value = 0
        for i, bit in enumerate(self.read()):
            value |= bit << (self.num_bits - 1 - i)
        return value

    def set_value(self, value: int):
        """设置寄存器值（整数）

        Args:
            value: 要设置的值
        """
        if value < 0 or value >= 2 ** self.num_bits:
            raise ValueError(f"Value must be between 0 and {2 ** self.num_bits - 1}")

        data = []
        for i in range(self.num_bits - 1, -1, -1):
            data.append((value >> i) & 1)

        self.load(data)


class ShiftRegister:
    """移位寄存器

    支持左移、右移和并行加载。

    特性：
    - 可配置位数
    - 左移/右移
    - 串行输入/输出
    - 并行加载

    Examples:
        >>> sr = ShiftRegister(4)
        >>> sr.serial_in(1)  # 串行输入1
        [0, 0, 0, 1]
        >>> sr.shift_right()
        [0, 0, 1, 0]
    """

    def __init__(self, num_bits: int):
        """初始化移位寄存器

        Args:
            num_bits: 位数
        """
        if num_bits < 1:
            raise ValueError("Number of bits must be positive")

        self.num_bits = num_bits
        self._flipflops = [DFlipFlop() for _ in range(num_bits)]

    def shift_right(self, serial_input: int = 0) -> List[int]:
        """右移

        Args:
            serial_input: 串行输入（进入最高位）

        Returns:
            List[int]: 移位后的内容
        """
        # 读取当前状态
        current = self.read()

        # 右移：所有位向右移动一位
        new_data = [serial_input] + current[:-1]

        # 加载新数据
        return self.load(new_data)

    def shift_left(self, serial_input: int = 0) -> List[int]:
        """左移

        Args:
            serial_input: 串行输入（进入最低位）

        Returns:
            List[int]: 移位后的内容
        """
        # 读取当前状态
        current = self.read()

        # 左移：所有位向左移动一位
        new_data = current[1:] + [serial_input]

        # 加载新数据
        return self.load(new_data)

    def serial_in(self, bit: int) -> List[int]:
        """串行输入（右移）

        Args:
            bit: 输入位

        Returns:
            List[int]: 移位后的内容
        """
        return self.shift_right(bit)

    def serial_out(self) -> int:
        """串行输出（最低位）

        Returns:
            int: 最低位的值
        """
        return self.read()[-1]

    def parallel_load(self, data: List[int]) -> List[int]:
        """并行加载

        Args:
            data: 要加载的数据

        Returns:
            List[int]: 加载后的内容
        """
        return self.load(data)

    def load(self, data: List[int]) -> List[int]:
        """加载数据

        Args:
            data: 要加载的数据

        Returns:
            List[int]: 加载后的内容
        """
        if len(data) != self.num_bits:
            raise ValueError(f"Expected {self.num_bits} bits, got {len(data)}")

        # 在时钟上升沿加载数据
        for i in range(self.num_bits):
            self._flipflops[i].evaluate(data[i], 1)  # CLK = 1

        # 时钟下降沿
        for i in range(self.num_bits):
            self._flipflops[i].clock(0)

        return self.read()

    def read(self) -> List[int]:
        """读取寄存器内容

        Returns:
            List[int]: 寄存器内容（高位在前）
        """
        return [ff.get_state()['Q'] for ff in self._flipflops]

    def clear(self):
        """清零寄存器"""
        self.load([0] * self.num_bits)

    def get_value(self) -> int:
        """获取寄存器值（整数）

        Returns:
            int: 寄存器值
        """
        value = 0
        for i, bit in enumerate(self.read()):
            value |= bit << (self.num_bits - 1 - i)
        return value


class UniversalShiftRegister:
    """通用移位寄存器

    支持多种操作模式：
    - 保持
    - 右移
    - 左移
    - 并行加载

    Examples:
        >>> usr = UniversalShiftRegister(4)
        >>> usr.set_mode([0, 1])  # 右移模式
        >>> usr.clock(1)
        [0, 0, 0, 0]
    """

    # 模式定义
    MODE_HOLD = [0, 0]
    MODE_SHIFT_RIGHT = [0, 1]
    MODE_SHIFT_LEFT = [1, 0]
    MODE_PARALLEL_LOAD = [1, 1]

    def __init__(self, num_bits: int):
        """初始化通用移位寄存器

        Args:
            num_bits: 位数
        """
        if num_bits < 1:
            raise ValueError("Number of bits must be positive")

        self.num_bits = num_bits
        self._data = [0] * num_bits
        self._mode = self.MODE_HOLD
        self._serial_right_input = 0
        self._serial_left_input = 0

    def set_mode(self, mode: List[int]):
        """设置操作模式

        Args:
            mode: 模式选择（2位）
        """
        if len(mode) != 2:
            raise ValueError("Mode must be 2 bits")
        self._mode = mode

    def set_serial_inputs(self, right: int = 0, left: int = 0):
        """设置串行输入

        Args:
            right: 右移串行输入
            left: 左移串行输入
        """
        self._serial_right_input = right
        self._serial_left_input = left

    def clock(self, parallel_data: List[int] = None) -> List[int]:
        """执行时钟

        Args:
            parallel_data: 并行加载数据（仅在并行加载模式下使用）

        Returns:
            List[int]: 当前数据
        """
        if self._mode == self.MODE_HOLD:
            # 保持
            pass

        elif self._mode == self.MODE_SHIFT_RIGHT:
            # 右移
            self._data = [self._serial_right_input] + self._data[:-1]

        elif self._mode == self.MODE_SHIFT_LEFT:
            # 左移
            self._data = self._data[1:] + [self._serial_left_input]

        elif self._mode == self.MODE_PARALLEL_LOAD:
            # 并行加载
            if parallel_data is not None:
                if len(parallel_data) != self.num_bits:
                    raise ValueError(f"Expected {self.num_bits} bits, got {len(parallel_data)}")
                self._data = parallel_data.copy()

        return self.read()

    def read(self) -> List[int]:
        """读取数据

        Returns:
            List[int]: 当前数据
        """
        return self._data.copy()

    def clear(self):
        """清零"""
        self._data = [0] * self.num_bits
