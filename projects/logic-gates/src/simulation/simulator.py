"""
仿真器模块

实现高级仿真器，支持事件驱动仿真和信号追踪。
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import heapq

from .wire import Wire
from .sim_circuit import Circuit as SimCircuit


class EventType(Enum):
    """事件类型"""
    SIGNAL_CHANGE = "signal_change"
    CLOCK_EDGE = "clock_edge"
    GATE_UPDATE = "gate_update"
    CUSTOM = "custom"


@dataclass
class Event:
    """仿真事件"""
    time: int
    event_type: EventType
    target: str
    value: Any = None
    priority: int = 0

    def __lt__(self, other):
        if self.time != other.time:
            return self.time < other.time
        return self.priority < other.priority


class Simulator:
    """仿真器

    事件驱动的仿真器，支持：
    - 事件调度
    - 时间管理
    - 信号追踪
    - 波形生成

    Examples:
        >>> sim = Simulator()
        >>> sim.add_wire("A")
        >>> sim.add_wire("B")
        >>> sim.add_wire("OUT")
        >>> sim.schedule_event(0, "A", 1)
        >>> sim.schedule_event(0, "B", 1)
        >>> sim.run(10)
        >>> sim.get_waveform("OUT")
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    """

    def __init__(self):
        """初始化仿真器"""
        self._time = 0
        self._wires: Dict[str, Wire] = {}
        self._events: List[Event] = []
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._history: Dict[str, List[tuple]] = {}  # wire_name -> [(time, value)]
        self._is_running = False
        self._max_time = 0

    def add_wire(self, name: str, delay: int = 0) -> Wire:
        """添加连线

        Args:
            name: 连线名称
            delay: 传播延迟

        Returns:
            Wire: 连线实例
        """
        wire = Wire(name, delay)
        self._wires[name] = wire
        self._history[name] = []
        return wire

    def schedule_event(self, time: int, target: str, value: int, 
                      event_type: EventType = EventType.SIGNAL_CHANGE,
                      priority: int = 0):
        """调度事件

        Args:
            time: 事件时间
            target: 目标连线
            value: 信号值
            event_type: 事件类型
            priority: 优先级
        """
        if target not in self._wires:
            raise ValueError(f"Wire '{target}' not found")

        event = Event(time, event_type, target, value, priority)
        heapq.heappush(self._events, event)

    def add_event_handler(self, event_type: str, handler: Callable):
        """添加事件处理器

        Args:
            event_type: 事件类型
            handler: 处理函数
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    def run(self, max_time: int):
        """运行仿真

        Args:
            max_time: 最大仿真时间
        """
        self._max_time = max_time
        self._is_running = True

        while self._events and self._is_running:
            # 获取下一个事件
            event = heapq.heappop(self._events)

            # 检查时间
            if event.time > max_time:
                break

            # 更新时间
            self._time = event.time

            # 处理事件
            self._process_event(event)

        self._is_running = False

    def _process_event(self, event: Event):
        """处理事件

        Args:
            event: 事件
        """
        # 更新连线值（所有事件类型都更新）
        if event.target in self._wires:
            wire = self._wires[event.target]
            wire.set_value(event.value, event.time)

            # 记录历史
            self._history[event.target].append((event.time, event.value))

        # 调用处理器
        if event.event_type == EventType.SIGNAL_CHANGE:
            for handler in self._event_handlers.get("signal_change", []):
                handler(event)

        elif event.event_type == EventType.CLOCK_EDGE:
            for handler in self._event_handlers.get("clock_edge", []):
                handler(event)

        elif event.event_type == EventType.GATE_UPDATE:
            # 调用处理器
            for handler in self._event_handlers.get("gate_update", []):
                handler(event)

        elif event.event_type == EventType.CUSTOM:
            # 调用处理器
            for handler in self._event_handlers.get("custom", []):
                handler(event)

    def get_wire_value(self, name: str) -> int:
        """获取连线值

        Args:
            name: 连线名称

        Returns:
            int: 当前值
        """
        if name not in self._wires:
            raise ValueError(f"Wire '{name}' not found")

        return self._wires[name].get_value()

    def get_waveform(self, name: str) -> List[int]:
        """获取波形

        Args:
            name: 连线名称

        Returns:
            List[int]: 每个时间单位的值
        """
        if name not in self._wires:
            raise ValueError(f"Wire '{name}' not found")

        waveform = []
        current_value = 0

        # 创建时间-值映射
        value_changes = {}
        for time, value in self._history.get(name, []):
            value_changes[time] = value

        # 生成波形
        for t in range(self._max_time):
            if t in value_changes:
                current_value = value_changes[t]
            waveform.append(current_value)

        return waveform

    def get_state(self) -> Dict[str, int]:
        """获取当前状态

        Returns:
            Dict[str, int]: 所有连线的当前值
        """
        return {name: wire.get_value() for name, wire in self._wires.items()}

    def get_time(self) -> int:
        """获取当前时间

        Returns:
            int: 当前仿真时间
        """
        return self._time

    def stop(self):
        """停止仿真"""
        self._is_running = False

    def reset(self):
        """重置仿真器"""
        self._time = 0
        self._events.clear()
        for wire in self._wires.values():
            wire.reset()
        for history in self._history.values():
            history.clear()


class ClockGenerator:
    """时钟生成器

    生成周期性时钟信号。

    Examples:
        >>> clock_gen = ClockGenerator(simulator, "CLK", period=4)
        >>> clock_gen.start(20)  # 生成20个时间单位的时钟
        >>> sim.get_waveform("CLK")
        [0, 0, 1, 1, 0, 0, 1, 1, ...]
    """

    def __init__(self, simulator: Simulator, wire_name: str, 
                 period: int = 2, duty_cycle: float = 0.5):
        """初始化时钟生成器

        Args:
            simulator: 仿真器实例
            wire_name: 时钟连线名称
            period: 时钟周期
            duty_cycle: 占空比
        """
        self._simulator = simulator
        self._wire_name = wire_name
        self._period = period
        self._duty_cycle = duty_cycle
        self._high_time = int(period * duty_cycle)
        self._low_time = period - self._high_time

    def start(self, duration: int):
        """开始生成时钟

        Args:
            duration: 持续时间
        """
        current_time = 0
        while current_time < duration:
            # 高电平
            self._simulator.schedule_event(
                current_time, self._wire_name, 1, EventType.CLOCK_EDGE
            )
            current_time += self._high_time

            if current_time >= duration:
                break

            # 低电平
            self._simulator.schedule_event(
                current_time, self._wire_name, 0, EventType.CLOCK_EDGE
            )
            current_time += self._low_time


class StimulusGenerator:
    """激励生成器

    生成测试激励信号。

    Examples:
        >>> stim = StimulusGenerator(simulator)
        >>> stim.add_signal("A", [(0, 1), (5, 0), (10, 1)])
        >>> stim.apply()
    """

    def __init__(self, simulator: Simulator):
        """初始化激励生成器

        Args:
            simulator: 仿真器实例
        """
        self._simulator = simulator
        self._signals: Dict[str, List[tuple]] = {}  # wire_name -> [(time, value)]

    def add_signal(self, wire_name: str, transitions: List[tuple]):
        """添加信号激励

        Args:
            wire_name: 连线名称
            transitions: 转换列表 [(时间, 值), ...]
        """
        self._signals[wire_name] = transitions

    def add_pulse(self, wire_name: str, start_time: int, duration: int, value: int = 1):
        """添加脉冲信号

        Args:
            wire_name: 连线名称
            start_time: 开始时间
            duration: 脉冲持续时间
            value: 脉冲值
        """
        if wire_name not in self._signals:
            self._signals[wire_name] = []

        self._signals[wire_name].append((start_time, value))
        self._signals[wire_name].append((start_time + duration, 1 - value))

    def add_random_signal(self, wire_name: str, num_transitions: int, 
                         max_time: int, seed: int = None):
        """添加随机信号

        Args:
            wire_name: 连线名称
            num_transitions: 转换次数
            max_time: 最大时间
            seed: 随机种子
        """
        import random
        if seed is not None:
            random.seed(seed)

        transitions = []
        current_value = 0

        for _ in range(num_transitions):
            time = random.randint(0, max_time)
            current_value = 1 - current_value
            transitions.append((time, current_value))

        # 按时间排序
        transitions.sort(key=lambda x: x[0])
        self._signals[wire_name] = transitions

    def apply(self):
        """应用激励信号"""
        for wire_name, transitions in self._signals.items():
            for time, value in transitions:
                self._simulator.schedule_event(time, wire_name, value)
