"""
存储单元模块

实现各种存储单元，展示数字电路在存储系统中的应用。
"""

from typing import List, Dict, Optional
from ..sequential.register import Register
from ..sequential.flipflop import DFlipFlop
from ..combinational.decoder import Decoder


class MemoryCell:
    """存储单元

    使用D触发器实现的基本存储单元。

    Examples:
        >>> cell = MemoryCell()
        >>> cell.write(1)
        >>> cell.read()
        1
    """

    def __init__(self):
        """初始化存储单元"""
        self._flipflop = DFlipFlop()
        self._value = 0

    def write(self, value: int, write_enable: int = 1):
        """写入数据

        Args:
            value: 数据值
            write_enable: 写使能
        """
        if write_enable == 1:
            self._flipflop.evaluate(value, 1)  # CLK = 1
            self._flipflop.clock(0)  # CLK = 0
            self._value = value

    def read(self) -> int:
        """读取数据

        Returns:
            int: 数据值
        """
        return self._flipflop.get_state()['Q']

    def clear(self):
        """清零"""
        self.write(0)


class MemoryRow:
    """存储行

    由多个存储单元组成的一行存储器。

    Examples:
        >>> row = MemoryRow(4)  # 4位宽
        >>> row.write([1, 0, 1, 0])
        >>> row.read()
        [1, 0, 1, 0]
    """

    def __init__(self, width: int):
        """初始化存储行

        Args:
            width: 位宽
        """
        self.width = width
        self._cells = [MemoryCell() for _ in range(width)]

    def write(self, data: List[int], write_enable: int = 1):
        """写入数据

        Args:
            data: 数据列表
            write_enable: 写使能
        """
        if len(data) != self.width:
            raise ValueError(f"Expected {self.width} bits, got {len(data)}")

        for i, value in enumerate(data):
            self._cells[i].write(value, write_enable)

    def read(self) -> List[int]:
        """读取数据

        Returns:
            List[int]: 数据列表
        """
        return [cell.read() for cell in self._cells]

    def clear(self):
        """清零"""
        for cell in self._cells:
            cell.clear()


class MemoryUnit:
    """存储单元

    使用地址解码器和存储行实现的随机存取存储器(RAM)。

    特性：
    - 可配置地址宽度和数据宽度
    - 地址解码
    - 读写控制

    Examples:
        >>> memory = MemoryUnit(4, 8)  # 16个地址，每个8位
        >>> memory.write(0, [1, 0, 1, 0, 1, 0, 1, 0])
        >>> memory.read(0)
        [1, 0, 1, 0, 1, 0, 1, 0]
    """

    def __init__(self, address_width: int, data_width: int):
        """初始化存储单元

        Args:
            address_width: 地址宽度（位）
            data_width: 数据宽度（位）
        """
        if address_width < 1:
            raise ValueError("Address width must be positive")
        if data_width < 1:
            raise ValueError("Data width must be positive")

        self.address_width = address_width
        self.data_width = data_width
        self.num_locations = 2 ** address_width

        # 创建存储行
        self._rows = [MemoryRow(data_width) for _ in range(self.num_locations)]

        # 创建地址解码器
        self._decoder = Decoder(address_width)

    def write(self, address: int, data: List[int], write_enable: int = 1):
        """写入数据

        Args:
            address: 地址
            data: 数据列表
            write_enable: 写使能
        """
        if address < 0 or address >= self.num_locations:
            raise ValueError(f"Address out of range: {address}")
        if len(data) != self.data_width:
            raise ValueError(f"Expected {self.data_width} bits, got {len(data)}")

        # 解码地址
        address_bits = self._int_to_bits(address)
        select_lines = self._decoder.evaluate(address_bits)

        # 写入到选中的行
        for i, select in enumerate(select_lines):
            if select == 1:
                self._rows[i].write(data, write_enable)
                break

    def read(self, address: int) -> List[int]:
        """读取数据

        Args:
            address: 地址

        Returns:
            List[int]: 数据列表
        """
        if address < 0 or address >= self.num_locations:
            raise ValueError(f"Address out of range: {address}")

        # 解码地址
        address_bits = self._int_to_bits(address)
        select_lines = self._decoder.evaluate(address_bits)

        # 读取选中的行
        for i, select in enumerate(select_lines):
            if select == 1:
                return self._rows[i].read()

        return [0] * self.data_width

    def clear(self):
        """清零所有存储"""
        for row in self._rows:
            row.clear()

    def _int_to_bits(self, value: int) -> List[int]:
        """将整数转换为二进制列表

        Args:
            value: 整数值

        Returns:
            List[int]: 二进制列表（高位在前）
        """
        bits = []
        for i in range(self.address_width - 1, -1, -1):
            bits.append((value >> i) & 1)
        return bits

    def dump(self) -> Dict[int, List[int]]:
        """转储内存内容

        Returns:
            Dict[int, List[int]]: 内存内容
        """
        result = {}
        for i in range(self.num_locations):
            data = self.read(i)
            if any(bit == 1 for bit in data):  # 只显示非零内容
                result[i] = data
        return result

    def get_size(self) -> int:
        """获取存储大小（位）

        Returns:
            int: 存储大小
        """
        return self.num_locations * self.data_width


class ROM:
    """只读存储器

    预先编程的存储器。

    Examples:
        >>> rom = ROM(4, 8)  # 16个地址，每个8位
        >>> rom.program(0, [1, 0, 1, 0, 1, 0, 1, 0])
        >>> rom.read(0)
        [1, 0, 1, 0, 1, 0, 1, 0]
    """

    def __init__(self, address_width: int, data_width: int):
        """初始化ROM

        Args:
            address_width: 地址宽度
            data_width: 数据宽度
        """
        self.address_width = address_width
        self.data_width = data_width
        self.num_locations = 2 ** address_width

        # 创建存储
        self._data = [[0] * data_width for _ in range(self.num_locations)]

        # 创建地址解码器
        self._decoder = Decoder(address_width)

    def program(self, address: int, data: List[int]):
        """编程ROM

        Args:
            address: 地址
            data: 数据列表
        """
        if address < 0 or address >= self.num_locations:
            raise ValueError(f"Address out of range: {address}")
        if len(data) != self.data_width:
            raise ValueError(f"Expected {self.data_width} bits, got {len(data)}")

        self._data[address] = data.copy()

    def read(self, address: int) -> List[int]:
        """读取数据

        Args:
            address: 地址

        Returns:
            List[int]: 数据列表
        """
        if address < 0 or address >= self.num_locations:
            raise ValueError(f"Address out of range: {address}")

        return self._data[address].copy()

    def load_program(self, program: List[List[int]]):
        """加载程序

        Args:
            program: 程序（数据列表）
        """
        for i, data in enumerate(program):
            if i < self.num_locations:
                self.program(i, data)

    def dump(self) -> Dict[int, List[int]]:
        """转储ROM内容

        Returns:
            Dict[int, List[int]]: ROM内容
        """
        result = {}
        for i in range(self.num_locations):
            data = self._data[i]
            if any(bit == 1 for bit in data):
                result[i] = data
        return result


class CacheLine:
    """缓存行

    实现简单的缓存行结构。

    Examples:
        >>> line = CacheLine(4, 8)  # 4路组相联，8位数据
        >>> line.write(0, [1, 0, 1, 0, 1, 0, 1, 0])
        >>> line.read(0)
        [1, 0, 1, 0, 1, 0, 1, 0]
    """

    def __init__(self, associativity: int, data_width: int):
        """初始化缓存行

        Args:
            associativity: 关联度
            data_width: 数据宽度
        """
        self.associativity = associativity
        self.data_width = data_width

        # 创建存储
        self._data = [[0] * data_width for _ in range(associativity)]
        self._valid = [0] * associativity
        self._dirty = [0] * associativity
        self._tags = [0] * associativity

    def write(self, way: int, data: List[int], tag: int = 0):
        """写入数据

        Args:
            way: 路索引
            data: 数据列表
            tag: 标签
        """
        if way < 0 or way >= self.associativity:
            raise ValueError(f"Way out of range: {way}")

        self._data[way] = data.copy()
        self._valid[way] = 1
        self._dirty[way] = 1
        self._tags[way] = tag

    def read(self, way: int) -> List[int]:
        """读取数据

        Args:
            way: 路索引

        Returns:
            List[int]: 数据列表
        """
        if way < 0 or way >= self.associativity:
            raise ValueError(f"Way out of range: {way}")

        if self._valid[way]:
            return self._data[way].copy()
        return [0] * self.data_width

    def is_valid(self, way: int) -> bool:
        """检查是否有效

        Args:
            way: 路索引

        Returns:
            bool: 是否有效
        """
        return self._valid[way] == 1

    def is_dirty(self, way: int) -> bool:
        """检查是否脏

        Args:
            way: 路索引

        Returns:
            bool: 是否脏
        """
        return self._dirty[way] == 1

    def invalidate(self, way: int):
        """使无效

        Args:
            way: 路索引
        """
        self._valid[way] = 0
        self._dirty[way] = 0

    def clear(self):
        """清零"""
        for i in range(self.associativity):
            self._data[i] = [0] * self.data_width
            self._valid[i] = 0
            self._dirty[i] = 0
            self._tags[i] = 0
