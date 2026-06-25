"""
仿真引擎模块

本模块实现了电路仿真引擎：
- Wire: 连线
- Circuit: 仿真电路
- Simulator: 仿真器
- SignalTrace: 信号追踪
"""

from .wire import Wire
from .sim_circuit import Circuit
from .simulator import Simulator
from .trace import SignalTrace

__all__ = [
    "Wire",
    "Circuit",
    "Simulator",
    "SignalTrace",
]
