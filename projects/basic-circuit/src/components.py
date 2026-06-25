"""
基本电路元件模块

实现电阻、电容、电感、电压源、电流源等基本电路元件。
"""

import numpy as np
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ComponentType(Enum):
    """元件类型枚举"""
    RESISTOR = "R"
    CAPACITOR = "C"
    INDUCTOR = "L"
    VOLTAGE_SOURCE = "V"
    CURRENT_SOURCE = "I"


@dataclass
class Component:
    """电路元件基类"""
    name: str
    node1: int  # 节点1
    node2: int  # 节点2
    component_type: ComponentType = None

    def __repr__(self):
        return f"{self.component_type.value}({self.name}: node{self.node1}-node{self.node2})"


@dataclass
class Resistor(Component):
    """
    电阻元件

    参数:
        name: 元件名称
        node1: 节点1编号
        node2: 节点2编号
        resistance: 电阻值 (欧姆)
    """
    resistance: float = 0.0

    def __post_init__(self):
        self.component_type = ComponentType.RESISTOR
        if self.resistance <= 0:
            raise ValueError("电阻值必须为正数")

    def impedance(self, frequency: float = 0) -> complex:
        """计算阻抗 (纯电阻，与频率无关)"""
        return complex(self.resistance, 0)

    def conductance(self) -> float:
        """计算电导 (1/R)"""
        return 1.0 / self.resistance


@dataclass
class Capacitor(Component):
    """
    电容元件

    参数:
        name: 元件名称
        node1: 节点1编号
        node2: 节点2编号
        capacitance: 电容值 (法拉)
    """
    capacitance: float = 0.0

    def __post_init__(self):
        self.component_type = ComponentType.CAPACITOR
        if self.capacitance <= 0:
            raise ValueError("电容值必须为正数")

    def impedance(self, frequency: float) -> complex:
        """
        计算阻抗

        Z = 1 / (jωC) = -j / (2πfC)
        """
        if frequency == 0:
            return complex(float('inf'), 0)  # 直流开路
        omega = 2 * np.pi * frequency
        return complex(0, -1.0 / (omega * self.capacitance))

    def reactance(self, frequency: float) -> float:
        """计算容抗"""
        if frequency == 0:
            return float('inf')
        omega = 2 * np.pi * frequency
        return -1.0 / (omega * self.capacitance)


@dataclass
class Inductor(Component):
    """
    电感元件

    参数:
        name: 元件名称
        node1: 节点1编号
        node2: 节点2编号
        inductance: 电感值 (亨利)
    """
    inductance: float = 0.0

    def __post_init__(self):
        self.component_type = ComponentType.INDUCTOR
        if self.inductance <= 0:
            raise ValueError("电感值必须为正数")

    def impedance(self, frequency: float) -> complex:
        """
        计算阻抗

        Z = jωL
        """
        omega = 2 * np.pi * frequency
        return complex(0, omega * self.inductance)

    def reactance(self, frequency: float) -> float:
        """计算感抗"""
        omega = 2 * np.pi * frequency
        return omega * self.inductance


@dataclass
class VoltageSource(Component):
    """
    电压源

    参数:
        name: 元件名称
        node1: 正极节点
        node2: 负极节点
        voltage: 电压值 (伏特)
        frequency: 频率 (赫兹)，0表示直流
        phase: 相位 (弧度)
    """
    voltage: float = 0.0
    frequency: float = 0.0
    phase: float = 0.0

    def __post_init__(self):
        self.component_type = ComponentType.VOLTAGE_SOURCE

    def phasor(self) -> complex:
        """计算相量表示"""
        if self.frequency == 0:
            return complex(self.voltage, 0)
        return self.voltage * np.exp(1j * self.phase)

    def time_value(self, t: float) -> float:
        """计算时刻t的电压值"""
        if self.frequency == 0:
            return self.voltage
        omega = 2 * np.pi * self.frequency
        return self.voltage * np.cos(omega * t + self.phase)


@dataclass
class CurrentSource(Component):
    """
    电流源

    参数:
        name: 元件名称
        node1: 电流流入节点
        node2: 电流流出节点
        current: 电流值 (安培)
        frequency: 频率 (赫兹)，0表示直流
        phase: 相位 (弧度)
    """
    current: float = 0.0
    frequency: float = 0.0
    phase: float = 0.0

    def __post_init__(self):
        self.component_type = ComponentType.CURRENT_SOURCE

    def phasor(self) -> complex:
        """计算相量表示"""
        if self.frequency == 0:
            return complex(self.current, 0)
        return self.current * np.exp(1j * self.phase)

    def time_value(self, t: float) -> float:
        """计算时刻t的电流值"""
        if self.frequency == 0:
            return self.current
        omega = 2 * np.pi * self.frequency
        return self.current * np.cos(omega * t + self.phase)


def ohms_law(voltage: float = None, current: float = None, resistance: float = None) -> dict:
    """
    欧姆定律计算器

    V = IR

    根据已知两个量计算第三个量。

    参数:
        voltage: 电压 (V)
        current: 电流 (I)
        resistance: 电阻 (R)

    返回:
        dict: 包含 V, I, R 的计算结果

    示例:
        >>> ohms_law(voltage=10, resistance=5)
        {'voltage': 10, 'current': 2.0, 'resistance': 5}
    """
    values = {'voltage': voltage, 'current': current, 'resistance': resistance}
    known = sum(v is not None for v in values.values())

    if known < 2:
        raise ValueError("至少需要提供两个已知量")

    if voltage is None:
        values['voltage'] = current * resistance
    elif current is None:
        if resistance == 0:
            raise ZeroDivisionError("电阻不能为零")
        values['current'] = voltage / resistance
    elif resistance is None:
        if current == 0:
            raise ZeroDivisionError("电流不能为零")
        values['resistance'] = voltage / current

    return values


def power(voltage: float = None, current: float = None, resistance: float = None) -> float:
    """
    功率计算

    P = VI = I²R = V²/R

    参数:
        voltage: 电压 (V)
        current: 电流 (I)
        resistance: 电阻 (R)

    返回:
        float: 功率 (W)
    """
    if voltage is not None and current is not None:
        return voltage * current
    elif current is not None and resistance is not None:
        return current ** 2 * resistance
    elif voltage is not None and resistance is not None:
        if resistance == 0:
            raise ZeroDivisionError("电阻不能为零")
        return voltage ** 2 / resistance
    else:
        raise ValueError("至少需要提供两个已知量")
