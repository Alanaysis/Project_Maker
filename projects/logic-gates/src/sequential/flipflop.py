"""
触发器模块

实现D触发器、JK触发器和T触发器。
"""

from typing import Dict, List
from .latch import DLatch


class DFlipFlop:
    """D触发器

    边沿触发的D触发器，在时钟上升沿时采样输入。

    特性：
    - 上升沿触发
    - Q = D 在时钟上升沿

    Examples:
        >>> ff = DFlipFlop()
        >>> ff.clock(1)  # 上升沿，D=1
        >>> ff.get_state()
        {'Q': 1, 'Q_bar': 0}
        >>> ff.clock(0)  # 下降沿，保持
        >>> ff.get_state()
        {'Q': 1, 'Q_bar': 0}
    """

    def __init__(self):
        """初始化D触发器"""
        self._q = 0
        self._q_bar = 1
        self._last_clk = 0
        self._d = 0

    def set_data(self, d: int):
        """设置数据输入

        Args:
            d: 数据输入
        """
        if d not in (0, 1):
            raise ValueError("Data must be 0 or 1")
        self._d = d

    def clock(self, clk: int) -> Dict[str, int]:
        """时钟信号

        Args:
            clk: 时钟信号

        Returns:
            Dict[str, int]: {'Q': Q输出, 'Q_bar': Q非输出}
        """
        if clk not in (0, 1):
            raise ValueError("Clock must be 0 or 1")

        # 检测上升沿
        if self._last_clk == 0 and clk == 1:
            self._q = self._d
            self._q_bar = 1 - self._d

        self._last_clk = clk
        return self.get_state()

    def evaluate(self, d: int, clk: int) -> Dict[str, int]:
        """计算触发器输出

        Args:
            d: 数据输入
            clk: 时钟输入

        Returns:
            Dict[str, int]: {'Q': Q输出, 'Q_bar': Q非输出}
        """
        self.set_data(d)
        return self.clock(clk)

    def get_state(self) -> Dict[str, int]:
        """获取当前状态

        Returns:
            Dict[str, int]: {'Q': Q输出, 'Q_bar': Q非输出}
        """
        return {'Q': self._q, 'Q_bar': self._q_bar}

    def reset_state(self):
        """重置触发器状态"""
        self._q = 0
        self._q_bar = 1
        self._last_clk = 0
        self._d = 0


class JKFlipFlop:
    """JK触发器

    全功能触发器，消除了SR触发器的禁止状态。

    特性：
    - J=0, K=0: 保持
    - J=0, K=1: 复位 (Q=0)
    - J=1, K=0: 置位 (Q=1)
    - J=1, K=1: 翻转 (Q=Q')

    Examples:
        >>> ff = JKFlipFlop()
        >>> ff.evaluate(1, 0, 1)  # J=1, K=0, CLK上升沿
        {'Q': 1, 'Q_bar': 0}
        >>> ff.evaluate(1, 1, 1)  # J=1, K=1, CLK上升沿 (翻转)
        {'Q': 0, 'Q_bar': 1}
    """

    def __init__(self):
        """初始化JK触发器"""
        self._q = 0
        self._q_bar = 1
        self._last_clk = 0

    def evaluate(self, j: int, k: int, clk: int) -> Dict[str, int]:
        """计算触发器输出

        Args:
            j: J输入
            k: K输入
            clk: 时钟输入

        Returns:
            Dict[str, int]: {'Q': Q输出, 'Q_bar': Q非输出}
        """
        if j not in (0, 1) or k not in (0, 1) or clk not in (0, 1):
            raise ValueError("Inputs must be 0 or 1")

        # 检测上升沿
        if self._last_clk == 0 and clk == 1:
            if j == 0 and k == 1:
                # 复位
                self._q = 0
                self._q_bar = 1
            elif j == 1 and k == 0:
                # 置位
                self._q = 1
                self._q_bar = 0
            elif j == 1 and k == 1:
                # 翻转
                self._q, self._q_bar = self._q_bar, self._q

        self._last_clk = clk
        return self.get_state()

    def get_state(self) -> Dict[str, int]:
        """获取当前状态

        Returns:
            Dict[str, int]: {'Q': Q输出, 'Q_bar': Q非输出}
        """
        return {'Q': self._q, 'Q_bar': self._q_bar}

    def reset_state(self):
        """重置触发器状态"""
        self._q = 0
        self._q_bar = 1
        self._last_clk = 0


class TFlipFlop:
    """T触发器

    翻转触发器，当T=1时在时钟边沿翻转。

    特性：
    - T=0: 保持
    - T=1: 翻转

    Examples:
        >>> ff = TFlipFlop()
        >>> ff.evaluate(1, 1)  # T=1, CLK上升沿
        {'Q': 1, 'Q_bar': 0}
        >>> ff.evaluate(1, 1)  # T=1, CLK上升沿 (翻转)
        {'Q': 0, 'Q_bar': 1}
    """

    def __init__(self):
        """初始化T触发器"""
        self._q = 0
        self._q_bar = 1
        self._last_clk = 0

    def evaluate(self, t: int, clk: int) -> Dict[str, int]:
        """计算触发器输出

        Args:
            t: T输入
            clk: 时钟输入

        Returns:
            Dict[str, int]: {'Q': Q输出, 'Q_bar': Q非输出}
        """
        if t not in (0, 1) or clk not in (0, 1):
            raise ValueError("Inputs must be 0 or 1")

        # 检测上升沿
        if self._last_clk == 0 and clk == 1:
            if t == 1:
                # 翻转
                self._q, self._q_bar = self._q_bar, self._q

        self._last_clk = clk
        return self.get_state()

    def get_state(self) -> Dict[str, int]:
        """获取当前状态

        Returns:
            Dict[str, int]: {'Q': Q输出, 'Q_bar': Q非输出}
        """
        return {'Q': self._q, 'Q_bar': self._q_bar}

    def reset_state(self):
        """重置触发器状态"""
        self._q = 0
        self._q_bar = 1
        self._last_clk = 0
