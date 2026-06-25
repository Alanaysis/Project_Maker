# 逻辑门模拟器

"""
Logic Gates Simulator - 一个用于学习数字电路的逻辑门模拟器

本包提供以下功能：
- 基本逻辑门（AND、OR、NOT、XOR、NAND、NOR、XNOR）
- 组合电路（多路选择器、解码器、加法器、比较器）
- 时序电路（锁存器、触发器、计数器、寄存器）
- 电路仿真引擎（信号传播、延迟模拟）
- CPU设计基础

使用示例：
    >>> from src import AndGate, OrGate
    >>> and_gate = AndGate()
    >>> and_gate.evaluate(1, 1)
    1
"""

__version__ = "2.0.0"
__author__ = "Logic Gates Simulator"

from .signal import Signal
from .exceptions import LogicGateError, InvalidInputError, ConnectionError, CircuitError
from .gates import (
    Gate,
    AndGate,
    OrGate,
    NotGate,
    XorGate,
    NandGate,
    NorGate,
    XnorGate,
    Buffer,
    CustomGate,
)
from .circuit import Circuit
from .truth_table import TruthTableGenerator
from .registry import GateRegistry
from .utils import (
    print_truth_table,
    print_circuit_table,
    create_circuit_from_description,
)
from .combinational import (
    Multiplexer,
    Demultiplexer,
    Decoder,
    Encoder,
    HalfAdder,
    FullAdder,
    RippleCarryAdder,
    Comparator,
    ALU,
)
from .sequential import (
    SRLatch,
    DLatch,
    DFlipFlop,
    JKFlipFlop,
    TFlipFlop,
    Counter,
    Register,
    ShiftRegister,
)
from .simulation import (
    Wire,
    Circuit as SimCircuit,
    Simulator,
    SignalTrace,
)
from .simulation.sim_circuit import Circuit as SimCircuit
from .applications import (
    SimpleCPU,
    MemoryUnit,
)

__all__ = [
    # 信号
    "Signal",

    # 异常
    "LogicGateError",
    "InvalidInputError",
    "ConnectionError",
    "CircuitError",

    # 逻辑门
    "Gate",
    "AndGate",
    "OrGate",
    "NotGate",
    "XorGate",
    "NandGate",
    "NorGate",
    "XnorGate",
    "Buffer",
    "CustomGate",

    # 电路
    "Circuit",

    # 真值表
    "TruthTableGenerator",

    # 注册表
    "GateRegistry",

    # 工具函数
    "print_truth_table",
    "print_circuit_table",
    "create_circuit_from_description",

    # 组合电路
    "Multiplexer",
    "Demultiplexer",
    "Decoder",
    "Encoder",
    "HalfAdder",
    "FullAdder",
    "RippleCarryAdder",
    "Comparator",
    "ALU",

    # 时序电路
    "SRLatch",
    "DLatch",
    "DFlipFlop",
    "JKFlipFlop",
    "TFlipFlop",
    "Counter",
    "Register",
    "ShiftRegister",

    # 仿真
    "Wire",
    "SimCircuit",
    "Simulator",
    "SignalTrace",

    # 应用
    "SimpleCPU",
    "MemoryUnit",
]
