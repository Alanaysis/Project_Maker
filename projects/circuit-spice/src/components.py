"""
电路元件模块 - Circuit Components

实现基本电路元件：
- 电阻 (Resistor)
- 电容 (Capacitor)
- 电感 (Inductor)
- 电压源 (VoltageSource)
- 电流源 (CurrentSource)
"""

import numpy as np
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class Component(ABC):
    """电路元件基类"""
    name: str
    node1: int
    node2: int
    value: float

    @abstractmethod
    def stamp_dc(self, G: np.ndarray, I: np.ndarray, node_map: dict, v_idx: int = -1):
        """直流分析时的矩阵印记"""
        pass

    @abstractmethod
    def stamp_ac(self, G: np.ndarray, freq: float, node_map: dict, v_idx: int = -1):
        """交流分析时的矩阵印记"""
        pass

    @abstractmethod
    def stamp_transient(self, G: np.ndarray, C: np.ndarray, I: np.ndarray,
                       node_map: dict, v_idx: int = -1, h: float = 0):
        """瞬态分析时的矩阵印记"""
        pass

    def _get_indices(self, node_map: dict) -> Tuple[int, int]:
        """获取节点在矩阵中的索引"""
        i = node_map.get(self.node1, -1)
        j = node_map.get(self.node2, -1)
        return i, j


class Resistor(Component):
    """
    电阻元件

    V = IR
    导纳: Y = 1/R
    """

    def __init__(self, name: str, node1: int, node2: int, resistance: float):
        super().__init__(name, node1, node2, resistance)
        if resistance <= 0:
            raise ValueError(f"电阻值必须为正: {resistance}")
        self.resistance = resistance
        self.conductance = 1.0 / resistance

    def stamp_dc(self, G: np.ndarray, I: np.ndarray, node_map: dict, v_idx: int = -1):
        i, j = self._get_indices(node_map)
        g = self.conductance

        if i >= 0:
            G[i, i] += g
        if j >= 0:
            G[j, j] += g
        if i >= 0 and j >= 0:
            G[i, j] -= g
            G[j, i] -= g

    def stamp_ac(self, G: np.ndarray, freq: float, node_map: dict, v_idx: int = -1):
        self.stamp_dc(G, np.zeros(G.shape[0]), node_map)

    def stamp_transient(self, G: np.ndarray, C: np.ndarray, I: np.ndarray,
                       node_map: dict, v_idx: int = -1, h: float = 0):
        self.stamp_dc(G, I, node_map)

    def impedance(self, freq: float) -> complex:
        return complex(self.resistance, 0)


class Capacitor(Component):
    """
    电容元件

    I = C * dV/dt
    导纳: Y = jωC
    """

    def __init__(self, name: str, node1: int, node2: int, capacitance: float):
        super().__init__(name, node1, node2, capacitance)
        if capacitance <= 0:
            raise ValueError(f"电容值必须为正: {capacitance}")
        self.capacitance = capacitance

    def stamp_dc(self, G: np.ndarray, I: np.ndarray, node_map: dict, v_idx: int = -1):
        # 直流分析中电容视为开路
        pass

    def stamp_ac(self, G: np.ndarray, freq: float, node_map: dict, v_idx: int = -1):
        i, j = self._get_indices(node_map)
        omega = 2 * np.pi * freq
        y = 1j * omega * self.capacitance

        if i >= 0:
            G[i, i] += y
        if j >= 0:
            G[j, j] += y
        if i >= 0 and j >= 0:
            G[i, j] -= y
            G[j, i] -= y

    def stamp_transient(self, G: np.ndarray, C: np.ndarray, I: np.ndarray,
                       node_map: dict, v_idx: int = -1, h: float = 0):
        i, j = self._get_indices(node_map)

        # 使用梯形法: C/h 矩阵
        c = self.capacitance

        if i >= 0:
            C[i, i] += c
        if j >= 0:
            C[j, j] += c
        if i >= 0 and j >= 0:
            C[i, j] -= c
            C[j, i] -= c

    def impedance(self, freq: float) -> complex:
        omega = 2 * np.pi * freq
        return 1.0 / (1j * omega * self.capacitance) if freq > 0 else complex(float('inf'), 0)


class Inductor(Component):
    """
    电感元件

    V = L * dI/dt
    导纳: Y = 1/(jωL)
    """

    def __init__(self, name: str, node1: int, node2: int, inductance: float):
        super().__init__(name, node1, node2, inductance)
        if inductance <= 0:
            raise ValueError(f"电感值必须为正: {inductance}")
        self.inductance = inductance

    def stamp_dc(self, G: np.ndarray, I: np.ndarray, node_map: dict, v_idx: int = -1):
        # 直流分析中电感视为短路 (用大电导近似)
        i, j = self._get_indices(node_map)
        g = 1e9  # 近似短路

        if i >= 0:
            G[i, i] += g
        if j >= 0:
            G[j, j] += g
        if i >= 0 and j >= 0:
            G[i, j] -= g
            G[j, i] -= g

    def stamp_ac(self, G: np.ndarray, freq: float, node_map: dict, v_idx: int = -1):
        i, j = self._get_indices(node_map)
        omega = 2 * np.pi * freq
        y = 1.0 / (1j * omega * self.inductance) if freq > 0 else 1e9

        if i >= 0:
            G[i, i] += y
        if j >= 0:
            G[j, j] += y
        if i >= 0 and j >= 0:
            G[i, j] -= y
            G[j, i] -= y

    def stamp_transient(self, G: np.ndarray, C: np.ndarray, I: np.ndarray,
                       node_map: dict, v_idx: int = -1, h: float = 0):
        # 电感需要额外的电流变量
        # 使用伴随模型: G_eq = L/h, I_eq = i_L(t)
        pass

    def impedance(self, freq: float) -> complex:
        omega = 2 * np.pi * freq
        return 1j * omega * self.inductance


class VoltageSource(Component):
    """
    电压源元件

    V(node1) - V(node2) = voltage
    需要额外的电流变量
    """

    def __init__(self, name: str, node1: int, node2: int, voltage: float,
                 frequency: float = 0, phase: float = 0, ac_mag: float = 0):
        super().__init__(name, node1, node2, voltage)
        self.voltage = voltage
        self.frequency = frequency
        self.phase = phase
        self.ac_mag = ac_mag if ac_mag > 0 else voltage

    def stamp_dc(self, G: np.ndarray, I: np.ndarray, node_map: dict, v_idx: int = -1):
        if v_idx < 0:
            return

        i, j = self._get_indices(node_map)

        # 电压源方程: V(i) - V(j) = V_s
        if i >= 0:
            G[i, v_idx] += 1
            G[v_idx, i] += 1
        if j >= 0:
            G[j, v_idx] -= 1
            G[v_idx, j] -= 1

        I[v_idx] += self.voltage

    def stamp_ac(self, G: np.ndarray, freq: float, node_map: dict, v_idx: int = -1):
        if v_idx < 0:
            return

        i, j = self._get_indices(node_map)

        if i >= 0:
            G[i, v_idx] += 1
            G[v_idx, i] += 1
        if j >= 0:
            G[j, v_idx] -= 1
            G[v_idx, j] -= 1

    def stamp_transient(self, G: np.ndarray, C: np.ndarray, I: np.ndarray,
                       node_map: dict, v_idx: int = -1, h: float = 0):
        if v_idx < 0:
            return

        i, j = self._get_indices(node_map)

        if i >= 0:
            G[i, v_idx] += 1
            G[v_idx, i] += 1
        if j >= 0:
            G[j, v_idx] -= 1
            G[v_idx, j] -= 1

    def voltage_at(self, t: float) -> float:
        """计算时间 t 时的电压值"""
        if self.frequency > 0:
            omega = 2 * np.pi * self.frequency
            return self.ac_mag * np.sin(omega * t + self.phase)
        return self.voltage


class CurrentSource(Component):
    """
    电流源元件

    从 node1 流向 node2 的电流 = current
    """

    def __init__(self, name: str, node1: int, node2: int, current: float,
                 frequency: float = 0, phase: float = 0):
        super().__init__(name, node1, node2, current)
        self.current = current
        self.frequency = frequency
        self.phase = phase

    def stamp_dc(self, G: np.ndarray, I: np.ndarray, node_map: dict, v_idx: int = -1):
        i, j = self._get_indices(node_map)

        # 电流源: 从 node1 流向 node2
        if i >= 0:
            I[i] -= self.current
        if j >= 0:
            I[j] += self.current

    def stamp_ac(self, G: np.ndarray, freq: float, node_map: dict, v_idx: int = -1):
        # AC 电流源处理
        pass

    def stamp_transient(self, G: np.ndarray, C: np.ndarray, I: np.ndarray,
                       node_map: dict, v_idx: int = -1, h: float = 0):
        i, j = self._get_indices(node_map)

        if i >= 0:
            I[i] -= self.current
        if j >= 0:
            I[j] += self.current

    def current_at(self, t: float) -> float:
        """计算时间 t 时的电流值"""
        if self.frequency > 0:
            omega = 2 * np.pi * self.frequency
            return self.current * np.sin(omega * t + self.phase)
        return self.current
