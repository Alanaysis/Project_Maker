"""
D Flip-Flop and T Flip-Flop / D触发器和T触发器

D (Data/Delay) Flip-Flop: stores one bit of data.
D（数据/延迟）触发器：存储一位数据。

T (Toggle) Flip-Flop: toggles output on each clock pulse when T=1.
T（翻转）触发器：当T=1时在每个时钟脉冲时翻转输出。
"""

from typing import List, Tuple


class DFlipFlop:
    """
    D Flip-Flop (Data/Delay Flip-Flop) / D触发器

    The D flip-flop has one data input (D) and captures it on the clock edge.
    D触发器有一个数据输入（D），在时钟边沿捕获它。

    Truth table / 真值表:
        D | Q(next) | Description
        --+---------+---------------------------
        0 |   0     | Reset (复位)
        1 |   1     | Set (置位)

    Key property: Q follows D after clock edge.
    关键特性：时钟边沿后Q跟随D。

    Used in: shift registers, counters, memory elements.
    用途：移位寄存器、计数器、存储元件。
    """

    def __init__(self, initial_q: int = 0):
        self._q = initial_q
        self._q_bar = 1 - initial_q
        self.clock_edge: str = "none"
        self.d_input_history: List[Tuple[int, int, int]] = []  # (clk, d, q)

    @property
    def q(self) -> int:
        """Output Q / 输出Q"""
        return self._q

    @property
    def q_bar(self) -> int:
        """Output Q_bar / 输出Q_bar"""
        return self._q_bar

    def clock_rising_edge(self, d: int) -> str:
        """
        Capture D on rising clock edge.
        在时钟上升沿捕获D。
        """
        self.clock_edge = "rising"
        old_q = self._q
        self._q = d
        self._q_bar = 1 - d
        self.d_input_history.append((1, d, self._q))

        if self._q != old_q:
            return f"更新: D={d}, Q={old_q} -> Q={self._q}"
        return f"保持: Q={self._q}"

    def clock_falling_edge(self, d: int) -> str:
        """
        Capture D on falling clock edge.
        在时钟下降沿捕获D。
        """
        self.clock_edge = "falling"
        old_q = self._q
        self._q = d
        self._q_bar = 1 - d
        self.d_input_history.append((0, d, self._q))

        if self._q != old_q:
            return f"更新: D={d}, Q={old_q} -> Q={self._q}"
        return f"保持: Q={self._q}"

    def get_history(self) -> List[Tuple[int, int, int]]:
        """Get history / 获取历史"""
        return self.d_input_history.copy()

    def reset_history(self) -> None:
        """Clear history / 清除历史"""
        self.d_input_history.clear()

    def __repr__(self) -> str:
        return f"DFlipFlop(Q={self._q}, D_history={len(self.d_input_history)})"


class TFlipFlop:
    """
    T Flip-Flop (Toggle Flip-Flop) / T触发器

    The T flip-flop toggles its output when T=1 on each clock edge.
    T触发器在每个时钟边沿当T=1时翻转输出。

    Truth table / 真值表:
        T | Q(next) | Description
        --+---------+---------------------------
        0 |   Q     | No change (保持)
        1 |  ~Q     | Toggle (翻转)

    Key property: When T=1, output frequency is divided by 2.
    关键特性：当T=1时，输出频率除以2（分频）。

    Used in: binary counters, frequency dividers.
    用途：二进制计数器、分频器。

    Can be built from JK flip-flop by tying J=K=T.
    可以从JK触发器构建，连接J=K=T。
    """

    def __init__(self, initial_q: int = 0):
        self._q = initial_q
        self._q_bar = 1 - initial_q
        self.clock_edge: str = "none"
        self.t_input_history: List[Tuple[int, int, int]] = []  # (clk, t, q)

    @property
    def q(self) -> int:
        """Output Q / 输出Q"""
        return self._q

    @property
    def q_bar(self) -> int:
        """Output Q_bar / 输出Q_bar"""
        return self._q_bar

    def clock_rising_edge(self, t: int) -> str:
        """
        Toggle on rising clock edge if T=1.
        如果T=1，在时钟上升沿翻转。
        """
        self.clock_edge = "rising"
        old_q = self._q

        if t == 1:
            self._q = 1 - self._q  # Toggle

        self._q_bar = 1 - self._q
        self.t_input_history.append((1, t, self._q))

        if self._q != old_q:
            return f"翻转: Q={old_q} -> Q={self._q}"
        return f"保持: Q={self._q}"

    def clock_falling_edge(self, t: int) -> str:
        """
        Toggle on falling clock edge if T=1.
        如果T=1，在时钟下降沿翻转。
        """
        self.clock_edge = "falling"
        old_q = self._q

        if t == 1:
            self._q = 1 - self._q  # Toggle

        self._q_bar = 1 - self._q
        self.t_input_history.append((0, t, self._q))

        if self._q != old_q:
            return f"翻转: Q={old_q} -> Q={self._q}"
        return f"保持: Q={self._q}"

    def get_history(self) -> List[Tuple[int, int, int]]:
        """Get history / 获取历史"""
        return self.t_input_history.copy()

    def reset_history(self) -> None:
        """Clear history / 清除历史"""
        self.t_input_history.clear()

    def __repr__(self) -> str:
        return f"TFlipFlop(Q={self._q}, T_history={len(self.t_input_history)})"
