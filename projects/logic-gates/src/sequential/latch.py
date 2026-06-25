"""
锁存器模块

实现SR锁存器和D锁存器。
"""

from typing import Dict, Tuple
from ..gates import AndGate, OrGate, NotGate, NandGate, NorGate
from ..circuit import Circuit


class SRLatch:
    """SR锁存器

    基本的存储单元，使用两个交叉耦合的门实现。

    使用 NOR 门实现：
    - S=1, R=0: 置位 (Q=1)
    - S=0, R=1: 复位 (Q=0)
    - S=0, R=0: 保持
    - S=1, R=1: 禁止状态

    Examples:
        >>> latch = SRLatch()
        >>> latch.set()  # 置位
        >>> latch.get_state()
        {'Q': 1, 'Q_bar': 0}
        >>> latch.reset()  # 复位
        >>> latch.get_state()
        {'Q': 0, 'Q_bar': 1}
    """

    def __init__(self):
        """初始化SR锁存器"""
        self._q = 0
        self._q_bar = 1

    def evaluate(self, s: int, r: int) -> Dict[str, int]:
        """计算锁存器输出

        Args:
            s: 置位输入
            r: 复位输入

        Returns:
            Dict[str, int]: {'Q': Q输出, 'Q_bar': Q非输出}

        Raises:
            ValueError: 输入无效或禁止状态
        """
        if s not in (0, 1) or r not in (0, 1):
            raise ValueError("Inputs must be 0 or 1")

        if s == 1 and r == 1:
            raise ValueError("Invalid state: S=1, R=1 is forbidden")

        if s == 1:
            self._q = 1
            self._q_bar = 0
        elif r == 1:
            self._q = 0
            self._q_bar = 1
        # else: 保持当前状态

        return self.get_state()

    def set(self):
        """置位锁存器"""
        self.evaluate(1, 0)

    def reset(self):
        """复位锁存器"""
        self.evaluate(0, 1)

    def get_state(self) -> Dict[str, int]:
        """获取当前状态

        Returns:
            Dict[str, int]: {'Q': Q输出, 'Q_bar': Q非输出}
        """
        return {'Q': self._q, 'Q_bar': self._q_bar}

    def reset_state(self):
        """重置锁存器状态"""
        self._q = 0
        self._q_bar = 1


class DLatch:
    """D锁存器

    数据锁存器，当时钟为高电平时，输出跟随输入。

    使用 NAND 门实现：
    - CLK=1: Q = D
    - CLK=0: Q 保持

    Examples:
        >>> latch = DLatch()
        >>> latch.evaluate(1, 1)  # D=1, CLK=1
        {'Q': 1, 'Q_bar': 0}
        >>> latch.evaluate(0, 0)  # D=0, CLK=0 (保持)
        {'Q': 1, 'Q_bar': 0}
    """

    def __init__(self):
        """初始化D锁存器"""
        self._q = 0
        self._q_bar = 1

    def evaluate(self, d: int, clk: int) -> Dict[str, int]:
        """计算锁存器输出

        Args:
            d: 数据输入
            clk: 时钟输入

        Returns:
            Dict[str, int]: {'Q': Q输出, 'Q_bar': Q非输出}
        """
        if d not in (0, 1) or clk not in (0, 1):
            raise ValueError("Inputs must be 0 or 1")

        if clk == 1:
            self._q = d
            self._q_bar = 1 - d

        return self.get_state()

    def get_state(self) -> Dict[str, int]:
        """获取当前状态

        Returns:
            Dict[str, int]: {'Q': Q输出, 'Q_bar': Q非输出}
        """
        return {'Q': self._q, 'Q_bar': self._q_bar}

    def reset_state(self):
        """重置锁存器状态"""
        self._q = 0
        self._q_bar = 1
