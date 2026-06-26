"""
Register implementations / 寄存器实现

Registers store multiple bits of data.
寄存器存储多位数据。

Types:
- SIPO (Serial-In Parallel-Out): serial data in, parallel data out
  串行输入并行输出
- PISO (Parallel-In Serial-Out): parallel data in, serial data out
  并行输入串行输出
- PIPO (Parallel-In Parallel-Out): parallel data in and out
  并行输入并行输出
- SIPO with bidirectional shift / 双向移位寄存器
"""

from typing import List, Optional, Tuple


class Register:
    """
    Base Register class / 基础寄存器类

    A register is a group of flip-flops that stores binary data.
    寄存器是一组存储二进制数据的触发器。

    Key concept: Sequential circuits that store N bits of information.
    关键概念：存储N位信息的时序电路。
    """

    def __init__(self, width: int = 8, initial_value: int = 0):
        self.width = width
        self.value = initial_value & ((1 << width) - 1)
        self.history: List[int] = []
        self.history.append(self.value)

    def get_bits(self) -> List[int]:
        """Get individual bit values (MSB first) / 获取各个位的值（MSB优先）"""
        return [(self.value >> i) & 1 for i in range(self.width - 1, -1, -1)]

    def set_value(self, value: int) -> None:
        """Set the register value / 设置寄存器值"""
        self.value = value & ((1 << self.width) - 1)
        self.history.append(self.value)

    def get_value(self) -> int:
        """Get the register value / 获取寄存器值"""
        return self.value

    def get_binary_string(self) -> str:
        """Get binary string representation / 获取二进制字符串表示"""
        return format(self.value, f'0{self.width}b')

    def get_history(self) -> List[int]:
        """Get value history / 获取值历史"""
        return self.history.copy()


class SIPORegister:
    """
    Serial-In Parallel-Out (SIPO) Register / 串行输入并行输出寄存器

    Data enters one bit at a time serially, but all bits are available
    in parallel at the output.
    数据一次一位串行输入，但所有位并行输出。

    Used in: serial-to-parallel conversion, LED displays.
    用途：串行到并行转换、LED显示。

    Classic example: 74HC164 shift register.
    经典示例：74HC164移位寄存器。
    """

    def __init__(self, width: int = 8):
        self.width = width
        self.value = 0
        self.shift_count = 0
        self.history: List[Tuple[int, int, int]] = []  # (cycle, data_in, value)

    def shift_in(self, data_bit: int) -> int:
        """
        Shift in one bit (MSB first).
        移入一位数据（MSB优先）。

        Args:
            data_bit: The bit to shift in (0 or 1)

        Returns:
            The new register value.
            新的寄存器值。
        """
        # Shift left and insert new bit at LSB
        self.value = ((self.value << 1) | data_bit) & ((1 << self.width) - 1)
        self.shift_count += 1
        self.history.append((self.shift_count, data_bit, self.value))
        return self.value

    def get_parallel_output(self) -> List[int]:
        """Get parallel output bits (MSB first) / 获取并行输出位"""
        return self.get_bits()

    def get_bits(self) -> List[int]:
        """Get individual bits (MSB first) / 获取各个位"""
        return [(self.value >> i) & 1 for i in range(self.width - 1, -1, -1)]

    def reset(self) -> None:
        """Clear the register / 清除寄存器"""
        self.value = 0
        self.shift_count = 0
        self.history.append((self.shift_count, -1, self.value))

    def get_history(self) -> List[Tuple[int, int, int]]:
        """Get shift history / 获取移位历史"""
        return self.history.copy()

    def __repr__(self) -> str:
        return f"SIPO(width={self.width}, value={self.get_binary_string()}, shifted={self.shift_count})"

    def get_binary_string(self) -> str:
        return format(self.value, f'0{self.width}b')


class PISOResister:
    """
    Parallel-In Serial-Out (PISO) Register / 并行输入串行输出寄存器

    Data is loaded in parallel, then shifted out one bit at a time.
    数据并行加载，然后一位一位移位输出。

    Used in: parallel-to-serial conversion, data transmission.
    用途：并行到串行转换、数据传输。

    Classic example: 74HC166 shift register.
    经典示例：74HC166移位寄存器。
    """

    def __init__(self, width: int = 8):
        self.width = width
        self.value = 0
        self.load_count = 0
        self.shift_count = 0
        self.output_history: List[int] = []  # Output bits
        self.history: List[Tuple[str, int]] = []  # (operation, value)

    def parallel_load(self, data: int) -> int:
        """
        Load data in parallel.
        并行加载数据。

        Args:
            data: The data value to load

        Returns:
            The loaded value.
            加载的值。
        """
        self.value = data & ((1 << self.width) - 1)
        self.load_count += 1
        self.history.append(("load", self.value))
        return self.value

    def shift_out(self) -> int:
        """
        Shift out the MSB (Most Significant Bit).
        移出MSB（最高有效位）。

        Returns:
            The bit that was shifted out.
            移出的位。
        """
        # Get MSB
        msb = (self.value >> (self.width - 1)) & 1
        self.output_history.append(msb)

        # Shift right
        self.value = (self.value >> 1) & ((1 << self.width) - 1)
        self.shift_count += 1
        self.history.append(("shift", self.value))

        return msb

    def get_serial_output(self) -> List[int]:
        """Get all shifted out bits / 获取所有移出的位"""
        return self.output_history.copy()

    def reset(self) -> None:
        """Clear the register / 清除寄存器"""
        self.value = 0
        self.shift_count = 0
        self.output_history.clear()

    def get_history(self) -> List[Tuple[str, int]]:
        """Get operation history / 获取操作历史"""
        return self.history.copy()

    def __repr__(self) -> str:
        return f"PISO(width={self.width}, value={self.get_binary_string()}, shifted={self.shift_count})"

    def get_binary_string(self) -> str:
        return format(self.value, f'0{self.width}b')


class PIPORegister:
    """
    Parallel-In Parallel-Out (PIPO) Register / 并行输入并行输出寄存器

    Data is loaded and read out in parallel. This is the standard register.
    数据并行加载和读取。这是标准寄存器。

    Used in: data storage, temporary holding, bus interfaces.
    用途：数据存储、临时保持、总线接口。

    Classic example: 74HC374 octal D flip-flop register.
    经典示例：74HC374八D触发器寄存器。
    """

    def __init__(self, width: int = 8):
        self.width = width
        self.value = 0
        self.history: List[Tuple[str, int]] = []

    def parallel_load(self, data: int) -> int:
        """
        Load data in parallel.
        并行加载数据。

        Returns:
            The loaded value.
            加载的值。
        """
        self.value = data & ((1 << self.width) - 1)
        self.history.append(("load", self.value))
        return self.value

    def parallel_read(self) -> int:
        """
        Read data in parallel.
        并行读取数据。

        Returns:
            The current register value.
            当前寄存器值。
        """
        return self.value

    def get_bits(self) -> List[int]:
        """Get individual bits (MSB first) / 获取各个位"""
        return [(self.value >> i) & 1 for i in range(self.width - 1, -1, -1)]

    def reset(self) -> None:
        """Clear the register / 清除寄存器"""
        self.value = 0
        self.history.append(("reset", 0))

    def get_history(self) -> List[Tuple[str, int]]:
        """Get operation history / 获取操作历史"""
        return self.history.copy()

    def get_binary_string(self) -> str:
        return format(self.value, f'0{self.width}b')

    def __repr__(self) -> str:
        return f"PIPO(width={self.width}, value={self.get_binary_string()})"


class BidirectionalShiftRegister:
    """
    Bidirectional Shift Register / 双向移位寄存器

    Can shift data left or right based on a control signal.
    可以根据控制信号向左或向右移位数据。

    More complex but more versatile than unidirectional shift registers.
    比单向移位寄存器更复杂但更通用。

    Classic example: 74HC194 universal shift register.
    经典示例：74HC194通用移位寄存器。
    """

    def __init__(self, width: int = 8):
        self.width = width
        self.value = 0
        self.shift_count = 0
        self.direction: str = "right"  # "left" or "right"
        self.history: List[Tuple[str, int, int]] = []  # (dir, serial_in, value)

    def set_direction(self, direction: str) -> None:
        """Set shift direction / 设置移位方向"""
        self.direction = direction

    def shift(self, serial_in: int) -> int:
        """
        Shift one bit in the current direction.
        以当前方向移入一位数据。

        Args:
            serial_in: The serial input bit (0 or 1)

        Returns:
            The new register value.
            新的寄存器值。
        """
        if self.direction == "right":
            # Shift right: LSB is shifted out, serial_in enters at MSB
            self.value = (serial_in << (self.width - 1)) | (self.value >> 1)
        else:
            # Shift left: MSB is shifted out, serial_in enters at LSB
            self.value = ((self.value << 1) | serial_in) & ((1 << self.width) - 1)

        self.shift_count += 1
        self.history.append((self.direction, serial_in, self.value))
        return self.value

    def parallel_load(self, data: int) -> int:
        """Load data in parallel / 并行加载数据"""
        self.value = data & ((1 << self.width) - 1)
        self.history.append(("load", -1, self.value))
        return self.value

    def get_bits(self) -> List[int]:
        """Get individual bits (MSB first) / 获取各个位"""
        return [(self.value >> i) & 1 for i in range(self.width - 1, -1, -1)]

    def get_serial_out(self) -> int:
        """Get the bit that would be shifted out / 获取将要移出的位"""
        if self.direction == "right":
            return self.value & 1  # LSB
        else:
            return (self.value >> (self.width - 1)) & 1  # MSB

    def reset(self) -> None:
        """Clear the register / 清除寄存器"""
        self.value = 0
        self.shift_count = 0

    def get_history(self) -> List[Tuple[str, int, int]]:
        """Get shift history / 获取移位历史"""
        return self.history.copy()

    def get_binary_string(self) -> str:
        return format(self.value, f'0{self.width}b')

    def __repr__(self) -> str:
        return f"BidirectionalShiftReg(width={self.width}, value={self.get_binary_string()}, dir={self.direction})"
