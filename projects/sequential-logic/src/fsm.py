"""
Finite State Machine (FSM) simulation / 有限状态机模拟

FSMs are the foundation of sequential logic design.
状态机是时序逻辑设计的基础。

Types:
- Mealy: output depends on current state AND inputs
  米利型：输出取决于当前状态和输入
- Moore: output depends only on current state
  摩尔型：输出仅取决于当前状态
"""

from enum import Enum, auto
from typing import Dict, List, Tuple, Callable, Optional, Any
from dataclasses import dataclass, field


class FSMType(Enum):
    """Type of finite state machine / 状态机类型"""
    MOORE = "moore"
    MEALY = "mealy"


@dataclass
class State:
    """Represents a state in the FSM / 表示状态机中的一个状态"""
    name: str
    state_id: int
    is_start: bool = False
    is_final: bool = False

    def __repr__(self):
        flags = []
        if self.is_start:
            flags.append("START")
        if self.is_final:
            flags.append("FINAL")
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        return f"State({self.name}{flag_str})"


@dataclass
class Transition:
    """Represents a state transition / 表示状态转换"""
    from_state: str
    to_state: str
    input_symbol: str
    output: str = ""  # For Moore machines, output is on the state
    description: str = ""

    def __repr__(self):
        return f"Transition({self.from_state} --[{self.input_symbol}]--> {self.to_state})"


class FiniteStateMachine:
    """
    Finite State Machine implementation / 有限状态机实现

    An FSM is a computational model consisting of:
    - A finite set of states
    - A set of input symbols
    - A transition function
    - A start state
    - A set of final/accepting states

    状态机由以下组成：
    - 有限个状态集合
    - 输入符号集合
    - 转换函数
    - 起始状态
    - 接受状态集合

    Moore Machine: output is associated with states
    摩尔型：输出与状态关联

    Mealy Machine: output is associated with transitions
    米利型：输出与转换关联
    """

    def __init__(self, fsm_type: FSMType = FSMType.MOORE):
        self.fsm_type = fsm_type
        self.states: Dict[str, State] = {}
        self.transitions: List[Transition] = []
        self.current_state: Optional[str] = None
        self.start_state: Optional[str] = None
        self.history: List[Tuple[str, str, str, str]] = []  # (step, input, output, state)
        self._step_count = 0

    def add_state(self, name: str, is_start: bool = False, is_final: bool = False) -> State:
        """Add a state to the FSM / 添加状态"""
        state = State(name=name, state_id=len(self.states), is_start=is_start, is_final=is_final)
        self.states[name] = state
        if is_start:
            self.start_state = name
            self.current_state = name
        return state

    def add_transition(self, from_state: str, to_state: str, input_symbol: str,
                       output: str = "", description: str = "") -> Transition:
        """
        Add a transition to the FSM.
        添加状态转换。

        For Moore machines, the output is typically on the state, not the transition.
        对于摩尔型，输出通常在状态上而非转换上。
        """
        transition = Transition(
            from_state=from_state,
            to_state=to_state,
            input_symbol=input_symbol,
            output=output,
            description=description
        )
        self.transitions.append(transition)
        return transition

    def reset(self) -> None:
        """Reset to initial state / 重置到初始状态"""
        self.current_state = self.start_state
        self.history.clear()
        self._step_count = 0

    def step(self, input_symbol: str) -> Tuple[str, str]:
        """
        Process one input symbol and transition to the next state.
        处理一个输入符号并转换到下一个状态。

        Returns:
            Tuple of (output, new_state_name)
            (输出, 新状态名)的元组
        """
        if self.current_state is None:
            raise ValueError("FSM not initialized. Call reset() first.")

        self._step_count += 1
        output = ""

        # Find matching transition
        for trans in self.transitions:
            if trans.from_state == self.current_state and trans.input_symbol == input_symbol:
                self.current_state = trans.to_state
                # Get output based on FSM type
                if self.fsm_type == FSMType.MEALY:
                    output = trans.output
                else:  # Moore
                    output = self.states.get(self.current_state, State("unknown", -1)).name
                break
        else:
            # No transition found - error
            output = "ERROR"
            self.history.append((self._step_count, input_symbol, output, self.current_state or "NONE"))
            raise ValueError(f"No transition from state '{self.current_state}' on input '{input_symbol}'")

        self.history.append((self._step_count, input_symbol, output, self.current_state))
        return output, self.current_state

    def run(self, input_sequence: List[str]) -> List[Tuple[str, str]]:
        """
        Run the FSM on a sequence of inputs.
        在输入序列上运行状态机。

        Args:
            input_sequence: List of input symbols

        Returns:
            List of (output, state) tuples for each step
            每步的(output, state)元组列表
        """
        results = []
        for inp in input_sequence:
            output, state = self.step(inp)
            results.append((output, state))
        return results

    def is_accepted(self, input_sequence: List[str]) -> bool:
        """
        Check if the FSM accepts the given input sequence.
        检查状态机是否接受给定的输入序列。

        A sequence is accepted if the FSM ends in a final state.
        如果状态机最终处于接受状态，则序列被接受。
        """
        self.reset()
        try:
            self.run(input_sequence)
            if self.current_state and self.states.get(self.current_state, State("unknown", -1)).is_final:
                return True
            return False
        except ValueError:
            return False

    def get_history(self) -> List[Tuple[str, str, str, str]]:
        """Get execution history / 获取执行历史"""
        return self.history.copy()

    def get_state_diagram(self) -> str:
        """
        Get a text-based state diagram representation.
        获取基于文本的状态图表示。
        """
        lines = [f"Finite State Machine ({self.fsm_type.value}):"]
        lines.append(f"States: {', '.join(self.states.keys())}")
        if self.start_state:
            lines.append(f"Start state: {self.start_state}")
        final_states = [s for s, st in self.states.items() if st.is_final]
        if final_states:
            lines.append(f"Final states: {', '.join(final_states)}")
        lines.append("Transitions:")
        for t in self.transitions:
            lines.append(f"  {t.from_state} --[{t.input_symbol}]{'->' + t.output if t.output else ''}--> {t.to_state}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"FSM(states={len(self.states)}, current={self.current_state or 'none'}, type={self.fsm_type.value})"


class SequenceDetector(FiniteStateMachine):
    """
    Sequence detector FSM / 序列检测器状态机

    Detects a specific bit sequence in a stream of bits.
    在位流中检测特定的位序列。

    Example: Detect the sequence "101" in a bit stream.
    示例：在位流中检测序列"101"。
    """

    def __init__(self, sequence: str = "101"):
        super().__init__(FSMType.MOORE)
        self.sequence = sequence
        self._build_fsm()

    def _build_fsm(self) -> None:
        """Build the FSM for sequence detection / 构建序列检测的状态机"""
        n = len(self.sequence)

        # States: S0 (reset/nothing matched), S1 (matched first bit), ..., Sn (sequence found)
        self.add_state("S0", is_start=True)
        for i in range(1, n):
            self.add_state(f"S{i}")
        self.add_state(f"S{n}", is_final=True)

        # Build transitions for each state
        for state_idx in range(n + 1):
            if state_idx == n:
                # Already detected - restart
                self.add_transition(f"S{n}", "S0", "0", output="DETECTED")
                self.add_transition(f"S{n}", "S0", "1", output="DETECTED")
            else:
                for bit in ["0", "1"]:
                    if bit == self.sequence[state_idx]:
                        # Match: advance to next state
                        self.add_transition(
                            f"S{state_idx}", f"S{state_idx + 1}", bit,
                            output="NO" if state_idx < n - 1 else "YES"
                        )
                    else:
                        # Mismatch: find longest prefix that matches the suffix
                        # Check if any prefix of the sequence matches a suffix of current matched bits + new bit
                        matched_so_far = self.sequence[:state_idx] + bit
                        next_state = 0
                        for k in range(min(state_idx + 1, n), 0, -1):
                            if matched_so_far.endswith(self.sequence[:k]):
                                next_state = k
                                break
                        self.add_transition(
                            f"S{state_idx}", f"S{next_state}", bit,
                            output="NO" if state_idx < n - 1 else "YES"
                        )


class TrafficLightFSM(FiniteStateMachine):
    """
    Traffic light finite state machine / 交通灯状态机

    Simulates a simple traffic light cycle:
    Green -> Yellow -> Red -> Red+Yellow -> Green
    模拟简单的交通灯循环：
    绿 -> 黄 -> 红 -> 红+黄 -> 绿
    """

    def __init__(self):
        super().__init__(FSMType.MOORE)
        self._build_fsm()

    def _build_fsm(self) -> None:
        """Build traffic light state machine / 构建交通灯状态机"""
        self.add_state("GREEN", is_start=True)
        self.add_state("YELLOW")
        self.add_state("RED")
        self.add_state("RED_YELLOW")

        # Timer-based transitions (triggered by 'tick' input)
        self.add_transition("GREEN", "YELLOW", "tick", output="GREEN")
        self.add_transition("YELLOW", "RED", "tick", output="YELLOW")
        self.add_transition("RED", "RED_YELLOW", "tick", output="RED")
        self.add_transition("RED_YELLOW", "GREEN", "tick", output="RED_YELLOW")


class VendingMachineFSM(FiniteStateMachine):
    """
    Vending machine finite state machine / 售货机状态机

    Simulates a simple vending machine:
    - Accepts coins (0.25, 0.50, 0.75, 1.00)
    - Dispenses product at $1.00
    - Returns change if overpaid
    模拟简单售货机：
    - 接受硬币（0.25, 0.50, 0.75, 1.00）
    - 达到$1.00时出货
    - 超额时找零
    """

    def __init__(self):
        super().__init__(FSMType.MEALY)
        self._build_fsm()

    def _build_fsm(self) -> None:
        """Build vending machine state machine / 构建售货机状态机"""
        states = ["$0.00", "$0.25", "$0.50", "$0.75"]
        for s in states:
            self.add_state(s, is_start=(s == "$0.00"), is_final=(s == "$1.00"))

        for state in states:
            for coin in ["0.25", "0.50", "0.75", "1.00"]:
                current = float(state.replace("$", ""))
                new_amount = current + float(coin)

                if new_amount >= 1.00:
                    next_state = "$0.00"
                    change = new_amount - 1.00
                    output = f"DISPENSE(change=${change:.2f})"
                else:
                    next_state = f"${new_amount:.2f}"
                    output = "IDLE"

                self.add_transition(state, next_state, coin, output=output)

    def __init__(self):
        super().__init__(FSMType.MEALY)
        self._build_fsm()
