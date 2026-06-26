"""
SR Latch and JK Flip-Flop / SR锁存器和JK触发器

Sequential logic circuits store state information, unlike combinational circuits.
时序逻辑电路存储状态信息，与组合逻辑电路不同。

The SR Latch is the simplest sequential element, built from cross-coupled NOR/NAND gates.
SR锁存器是最简单的时序元件，由交叉耦合的NOR/NAND门构成。

The JK Flip-Flop is an enhanced version of the SR latch that eliminates the invalid state.
JK触发器是SR锁存器的增强版，消除了无效状态。
"""

from enum import Enum
from typing import List, Tuple


class LatchState(Enum):
    """Latch output state / 锁存器输出状态"""
    RESET = 0  # Q=0, Q_bar=1
    SET = 1    # Q=1, Q_bar=0
    INVALID = -1  # Q=1, Q_bar=1 (invalid for NOR-based SR latch)


class SRLatch:
    """
    SR Latch (Set-Reset Latch) / SR锁存器

    An SR latch has two inputs (S=Set, R=Reset) and two outputs (Q, Q_bar).
    SR锁存器有两个输入（S=置位，R=复位）和两个输出（Q，Q_bar）。

    Truth table / 真值表:
        S | R | Q(next) | Description
        --+---+---------+---------------------------
        0 | 0 |   Q     | No change (保持)
        0 | 1 |   0     | Reset (复位)
        1 | 0 |   1     | Set (置位)
        1 | 1 |  invalid | Invalid state (无效状态)

    Key concept: Memory element that retains state without clock / 无需时钟即可保持状态的存储元件
    """

    def __init__(self, initial_state: LatchState = LatchState.RESET):
        self._q = 1 if initial_state == LatchState.SET else 0
        self._q_bar = 0 if initial_state == LatchState.SET else 1
        self._state = initial_state
        self.history: List[Tuple[int, int, int, int]] = []  # (s, r, q, q_bar)

    @property
    def q(self) -> int:
        """Output Q / 输出Q"""
        return self._q

    @property
    def q_bar(self) -> int:
        """Output Q_bar (complement of Q) / 输出Q_bar（Q的反相）"""
        return self._q_bar

    @property
    def state(self) -> LatchState:
        """Current state / 当前状态"""
        return self._state

    def set(self) -> None:
        """Set the latch (S=1, R=0) / 置位"""
        self._q = 1
        self._q_bar = 0
        self._state = LatchState.SET
        self.history.append((1, 0, self._q, self._q_bar))

    def reset(self) -> None:
        """Reset the latch (S=0, R=1) / 复位"""
        self._q = 0
        self._q_bar = 1
        self._state = LatchState.RESET
        self.history.append((0, 1, self._q, self._q_bar))

    def no_change(self) -> None:
        """No change (S=0, R=0) / 保持"""
        self.history.append((0, 0, self._q, self._q_bar))

    def invalid_input(self) -> None:
        """Invalid input (S=1, R=1) / 无效输入"""
        self._state = LatchState.INVALID
        self.history.append((1, 1, self._q, self._q_bar))

    def pulse(self, s: int, r: int) -> str:
        """
        Apply S and R inputs, return description of result.
        施加S和R输入，返回结果描述。
        """
        if s == 0 and r == 0:
            self.no_change()
            return f"保持: Q={self._q}, Q_bar={self._q_bar}"
        elif s == 0 and r == 1:
            self.reset()
            return f"复位: Q={self._q}, Q_bar={self._q_bar}"
        elif s == 1 and r == 0:
            self.set()
            return f"置位: Q={self._q}, Q_bar={self._q_bar}"
        else:
            self.invalid_input()
            return f"无效: S=1, R=1 (禁止状态)"

    def get_history(self) -> List[Tuple[int, int, int, int]]:
        """Get input history / 获取输入历史"""
        return self.history.copy()

    def reset_history(self) -> None:
        """Clear history / 清除历史"""
        self.history.clear()

    def __repr__(self) -> str:
        return f"SRLatch(Q={self._q}, Q_bar={self._q_bar}, state={self._state.name})"


class JKFlipFlop:
    """
    JK Flip-Flop / JK触发器

    The JK flip-flop solves the SR latch's invalid state problem.
    JK触发器解决了SR锁存器的无效状态问题。

    When J=1, K=1: output toggles (flips to opposite state).
    当J=1, K=1时：输出翻转。

    Truth table / 真值表:
        J | K | Q(next) | Description
        --+---+---------+---------------------------
        0 | 0 |   Q     | No change (保持)
        0 | 1 |   0     | Reset (复位)
        1 | 0 |   1     | Set (置位)
        1 | 1 |  ~Q     | Toggle (翻转)

    Edge-triggered: state changes only on clock edge.
    边沿触发：状态仅有时钟边沿时改变。
    """

    def __init__(self, initial_q: int = 0):
        self._q = initial_q
        self._q_bar = 1 - initial_q
        self.clock_edge: str = "none"  # "rising" or "falling"
        self.history: List[Tuple[int, int, int, int, int]] = []  # (j, k, clk, q, q_bar)

    @property
    def q(self) -> int:
        """Output Q / 输出Q"""
        return self._q

    @property
    def q_bar(self) -> int:
        """Output Q_bar / 输出Q_bar"""
        return self._q_bar

    def clock_rising_edge(self, j: int, k: int) -> str:
        """
        Process J, K inputs on rising clock edge.
        在时钟上升沿处理J、K输入。
        """
        self.clock_edge = "rising"
        old_q = self._q

        if j == 0 and k == 0:
            pass  # No change
        elif j == 0 and k == 1:
            self._q = 0
        elif j == 1 and k == 0:
            self._q = 1
        elif j == 1 and k == 1:
            self._q = 1 - self._q  # Toggle

        self._q_bar = 1 - self._q
        self.history.append((j, k, 1, self._q, self._q_bar))

        if self._q != old_q:
            return f"翻转: Q={old_q} -> Q={self._q}"
        return f"保持: Q={self._q}, Q_bar={self._q_bar}"

    def clock_falling_edge(self, j: int, k: int) -> str:
        """
        Process J, K inputs on falling clock edge.
        在时钟下降沿处理J、K输入。
        """
        self.clock_edge = "falling"
        old_q = self._q

        if j == 0 and k == 0:
            pass  # No change
        elif j == 0 and k == 1:
            self._q = 0
        elif j == 1 and k == 0:
            self._q = 1
        elif j == 1 and k == 1:
            self._q = 1 - self._q  # Toggle

        self._q_bar = 1 - self._q
        self.history.append((j, k, 0, self._q, self._q_bar))

        if self._q != old_q:
            return f"翻转: Q={old_q} -> Q={self._q}"
        return f"保持: Q={self._q}, Q_bar={self._q_bar}"

    def get_history(self) -> List[Tuple[int, int, int, int, int]]:
        """Get input history / 获取输入历史"""
        return self.history.copy()

    def reset_history(self) -> None:
        """Clear history / 清除历史"""
        self.history.clear()

    def __repr__(self) -> str:
        return f"JKFlipFlop(Q={self._q}, Q_bar={self._q_bar}, edge={self.clock_edge})"
