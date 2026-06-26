"""
三态缓冲器模块
Tri-state Buffer Module

三态缓冲器有三个输出状态：
- 0: 逻辑低电平
- 1: 逻辑高电平
- Z: 高阻态（断开连接）

Tri-state buffer has three output states:
- 0: Logic low
- 1: Logic high
- Z: High impedance (disconnected)

用途：
- 总线驱动：多个设备可以共享同一组信号线
- 双向I/O：可以配置为输入或输出

Use cases:
- Bus driving: multiple devices share signal lines
- Bidirectional I/O: configurable as input or output
"""


class TriStateBuffer:
    """
    三态缓冲器
    Tri-state Buffer

    当使能端有效时，输出等于输入。
    当使能端无效时，输出为高阻态（用None表示）。

    When enabled, output equals input.
    When disabled, output is high-impedance (represented as None).
    """

    def __init__(self, active_high: bool = True):
        """
        Args:
            active_high: True=使能高电平有效, False=使能低电平有效
        """
        self.active_high = active_high

    def output(self, data: int, enable: int) -> int:
        """
        Args:
            data: 输入数据 (0或1)
            enable: 使能信号

        Returns:
            输出: 0, 1, 或 None (高阻态Z)
        """
        if data not in (0, 1):
            raise ValueError("Data must be 0 or 1")

        # 判断使能是否有效
        is_enabled = enable == 1 if self.active_high else enable == 0

        if is_enabled:
            return data
        else:
            return None  # 高阻态

    def output_z_str(self, data: int, enable: int) -> str:
        """
        获取带高阻态符号的输出字符串

        Returns:
            "0", "1", 或 "Z"
        """
        result = self.output(data, enable)
        if result is None:
            return "Z"
        return str(result)


class BusDriver:
    """
    总线驱动器 - 多个三态缓冲器共享总线
    Bus Driver - multiple tri-state buffers sharing a bus

    关键规则：同一时刻只能有一个三态缓冲器使能，
    否则会导致总线冲突（两个输出驱动同一总线）。

    Key rule: only one tri-state buffer can be enabled at a time,
    otherwise bus contention occurs.
    """

    def __init__(self, num_buffers: int = 4):
        """
        Args:
            num_buffers: 三态缓冲器数量
        """
        self.num_buffers = num_buffers
        self.buffers = [TriStateBuffer(active_high=True) for _ in range(num_buffers)]
        self.bus_value = None  # 总线当前值

    def drive(self, buffer_index: int, data: int, enable: int) -> int:
        """
        驱动总线

        Args:
            buffer_index: 缓冲器索引
            data: 输入数据
            enable: 使能信号

        Returns:
            总线上的值 (0, 1, 或 None/Z)
        """
        if not (0 <= buffer_index < self.num_buffers):
            raise ValueError(f"Buffer index must be 0-{self.num_buffers - 1}")

        result = self.buffers[buffer_index].output(data, enable)
        self.bus_value = result
        return result

    def get_bus_value(self) -> int:
        """
        获取总线当前值

        Returns:
            总线值 (0, 1, 或 None)
        """
        return self.bus_value

    def check_bus_conflict(self, enables: list) -> bool:
        """
        检查总线冲突

        Args:
            enables: 所有缓冲器的使能信号列表

        Returns:
            True如果检测到冲突
        """
        active_count = sum(1 for e in enables if e == 1)
        return active_count > 1
