"""
连线模块

实现电路中的连线，支持信号传播和延迟。
"""

from typing import List, Optional, Callable


class Wire:
    """连线

    连接电路中的各个节点，支持信号传播和延迟模拟。

    特性：
    - 可命名
    - 可设置延迟
    - 支持多驱动源
    - 支持信号追踪

    Examples:
        >>> wire = Wire("data_bus", delay=2)
        >>> wire.set_value(1)
        >>> wire.get_value()
        1
        >>> wire.get_delayed_value(1)
        0  # 延迟2个时间单位
    """

    def __init__(self, name: str = "", delay: int = 0):
        """初始化连线

        Args:
            name: 连线名称
            delay: 传播延迟（时间单位）
        """
        self.name = name
        self.delay = delay
        self._value = 0
        self._prev_value = 0
        self._history: List[tuple] = []  # (时间, 值)
        self._drivers: List[str] = []  # 驱动源
        self._observers: List[Callable] = []  # 观察者

    def set_value(self, value: int, time: int = 0):
        """设置连线值

        Args:
            value: 信号值（0或1）
            time: 时间戳
        """
        if value not in (0, 1):
            raise ValueError("Value must be 0 or 1")

        self._prev_value = self._value
        self._value = value

        # 记录历史
        self._history.append((time, value))

        # 通知观察者
        for observer in self._observers:
            observer(self, value, time)

    def get_value(self) -> int:
        """获取当前值

        Returns:
            int: 当前信号值
        """
        return self._value

    def get_delayed_value(self, time: int) -> int:
        """获取延迟后的值

        Args:
            time: 当前时间

        Returns:
            int: 延迟后的值
        """
        # 查找延迟前的值
        delayed_time = time - self.delay
        if delayed_time < 0:
            return 0

        # 查找最接近的值
        for t, v in reversed(self._history):
            if t <= delayed_time:
                return v

        return 0

    def get_previous_value(self) -> int:
        """获取前一个值

        Returns:
            int: 前一个信号值
        """
        return self._prev_value

    def has_changed(self) -> bool:
        """检查值是否改变

        Returns:
            bool: 是否改变
        """
        return self._value != self._prev_value

    def add_driver(self, driver_name: str):
        """添加驱动源

        Args:
            driver_name: 驱动源名称
        """
        if driver_name not in self._drivers:
            self._drivers.append(driver_name)

    def remove_driver(self, driver_name: str):
        """移除驱动源

        Args:
            driver_name: 驱动源名称
        """
        if driver_name in self._drivers:
            self._drivers.remove(driver_name)

    def add_observer(self, observer: Callable):
        """添加观察者

        Args:
            observer: 观察者回调函数
        """
        self._observers.append(observer)

    def get_history(self) -> List[tuple]:
        """获取信号历史

        Returns:
            List[tuple]: [(时间, 值), ...]
        """
        return self._history.copy()

    def clear_history(self):
        """清除历史记录"""
        self._history.clear()

    def reset(self):
        """重置连线"""
        self._value = 0
        self._prev_value = 0
        self._history.clear()

    def __repr__(self) -> str:
        return f"Wire(name='{self.name}', value={self._value}, delay={self.delay})"

    def __str__(self) -> str:
        return f"Wire '{self.name}': {self._value}"


class Bus:
    """总线

    多位连线的集合。

    Examples:
        >>> bus = Bus("data_bus", width=8)
        >>> bus.set_value([1, 0, 1, 0, 1, 0, 1, 0])
        >>> bus.get_value()
        [1, 0, 1, 0, 1, 0, 1, 0]
    """

    def __init__(self, name: str = "", width: int = 8, delay: int = 0):
        """初始化总线

        Args:
            name: 总线名称
            width: 位宽
            delay: 传播延迟
        """
        self.name = name
        self.width = width
        self._wires = [Wire(f"{name}[{i}]", delay) for i in range(width)]

    def set_value(self, value: List[int]):
        """设置总线值

        Args:
            value: 信号值列表
        """
        if len(value) != self.width:
            raise ValueError(f"Expected {self.width} bits, got {len(value)}")

        for i, v in enumerate(value):
            self._wires[i].set_value(v)

    def get_value(self) -> List[int]:
        """获取总线值

        Returns:
            List[int]: 信号值列表
        """
        return [wire.get_value() for wire in self._wires]

    def get_decimal_value(self) -> int:
        """获取十进制值

        Returns:
            int: 十进制值
        """
        value = 0
        for i, wire in enumerate(self._wires):
            value |= wire.get_value() << (self.width - 1 - i)
        return value

    def set_decimal_value(self, value: int):
        """设置十进制值

        Args:
            value: 十进制值
        """
        if value < 0 or value >= 2 ** self.width:
            raise ValueError(f"Value must be between 0 and {2 ** self.width - 1}")

        bits = []
        for i in range(self.width - 1, -1, -1):
            bits.append((value >> i) & 1)
        self.set_value(bits)

    def __repr__(self) -> str:
        return f"Bus(name='{self.name}', width={self.width}, value={self.get_value()})"
