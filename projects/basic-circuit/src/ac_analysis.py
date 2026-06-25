"""
交流电路分析模块

实现阻抗计算、频率响应分析、滤波器设计等。
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, field
from .circuit import Circuit
from .components import Resistor, Capacitor, Inductor, VoltageSource, CurrentSource


@dataclass
class Phasor:
    """
    相量表示

    参数:
        magnitude: 幅值
        phase: 相位 (弧度)
    """
    magnitude: float
    phase: float

    @property
    def real(self) -> float:
        return self.magnitude * np.cos(self.phase)

    @property
    def imag(self) -> float:
        return self.magnitude * np.sin(self.phase)

    def to_complex(self) -> complex:
        return complex(self.real, self.imag)

    @classmethod
    def from_complex(cls, z: complex) -> 'Phasor':
        return cls(magnitude=abs(z), phase=np.angle(z))

    def __repr__(self):
        return f"Phasor({self.magnitude:.4f} ∠ {np.degrees(self.phase):.2f}°)"


@dataclass
class ACResult:
    """交流分析结果"""
    frequency: float  # 频率
    node_voltages: Dict[int, complex]  # 节点电压 (相量)
    branch_currents: Dict[str, complex]  # 支路电流 (相量)
    impedances: Dict[str, complex]  # 元件阻抗
    total_impedance: complex  # 总阻抗

    def summary(self) -> str:
        """输出分析结果摘要"""
        lines = [f"=== 交流分析结果 (f = {self.frequency} Hz) ==="]
        lines.append("\n元件阻抗:")
        for name, z in self.impedances.items():
            phasor = Phasor.from_complex(z)
            lines.append(f"  Z_{name} = {z:.4f} = {phasor}")
        lines.append(f"\n总阻抗: Z_total = {self.total_impedance:.4f}")
        lines.append("\n节点电压:")
        for nid, v in self.node_voltages.items():
            phasor = Phasor.from_complex(v)
            lines.append(f"  V_{nid} = {v:.4f} = {phasor}")
        lines.append("\n支路电流:")
        for name, i in self.branch_currents.items():
            phasor = Phasor.from_complex(i)
            lines.append(f"  I_{name} = {i:.4f} = {phasor}")
        return "\n".join(lines)


@dataclass
class FrequencyResponse:
    """
    频率响应

    参数:
        frequencies: 频率数组
        magnitude: 幅频响应 (dB)
        phase: 相频响应 (度)
    """
    frequencies: np.ndarray
    magnitude: np.ndarray
    phase: np.ndarray

    def to_dB(self) -> np.ndarray:
        """转换为分贝"""
        return 20 * np.log10(np.maximum(self.magnitude, 1e-10))

    def cutoff_frequency(self, threshold_dB: float = -3.0) -> Optional[float]:
        """计算截止频率 (-3dB点)"""
        mag_dB = self.to_dB()
        for i in range(len(mag_dB) - 1):
            if mag_dB[i] >= threshold_dB and mag_dB[i + 1] < threshold_dB:
                # 线性插值
                ratio = (threshold_dB - mag_dB[i]) / (mag_dB[i + 1] - mag_dB[i])
                return self.frequencies[i] + ratio * (self.frequencies[i + 1] - self.frequencies[i])
        return None


class ACAnalyzer:
    """
    交流电路分析器

    支持:
    - 阻抗计算
    - 频率响应分析
    - 相量分析

    示例:
        >>> circuit = Circuit()
        >>> n0 = circuit.add_node("GND")
        >>> n1 = circuit.add_node("IN")
        >>> circuit.set_ground(n0)
        >>> circuit.add_resistor("R1", n1, n0, 1000)
        >>> circuit.add_capacitor("C1", n1, n0, 1e-6)
        >>> analyzer = ACAnalyzer(circuit)
        >>> result = analyzer.solve(frequency=1000)
    """

    def __init__(self, circuit: Circuit):
        self.circuit = circuit
        self._ground = circuit.get_ground()

    def solve(self, frequency: float) -> ACResult:
        """
        求解交流电路

        参数:
            frequency: 频率 (赫兹)

        返回:
            ACResult: 分析结果
        """
        if self._ground is None:
            raise ValueError("必须设置接地点")

        # 计算各元件阻抗
        impedances = {}
        for comp in self.circuit.components:
            if isinstance(comp, Resistor):
                impedances[comp.name] = comp.impedance(frequency)
            elif isinstance(comp, Capacitor):
                impedances[comp.name] = comp.impedance(frequency)
            elif isinstance(comp, Inductor):
                impedances[comp.name] = comp.impedance(frequency)

        # 使用节点分析法
        node_voltages = self._ac_nodal_analysis(frequency, impedances)

        # 计算支路电流
        branch_currents = {}
        for comp in self.circuit.components:
            v1 = node_voltages.get(comp.node1, 0)
            v2 = node_voltages.get(comp.node2, 0)
            v_branch = v1 - v2

            if comp.name in impedances:
                z = impedances[comp.name]
                if abs(z) > 1e-10:
                    branch_currents[comp.name] = v_branch / z
                else:
                    branch_currents[comp.name] = 0
            elif isinstance(comp, VoltageSource):
                branch_currents[comp.name] = self._calculate_ac_vs_current(
                    comp, node_voltages, impedances, frequency
                )
            elif isinstance(comp, CurrentSource):
                branch_currents[comp.name] = comp.phasor()

        # 计算总阻抗
        total_impedance = self._calculate_total_impedance(frequency)

        return ACResult(
            frequency=frequency,
            node_voltages=node_voltages,
            branch_currents=branch_currents,
            impedances=impedances,
            total_impedance=total_impedance,
        )

    def _ac_nodal_analysis(self, frequency: float,
                           impedances: Dict[str, complex]) -> Dict[int, complex]:
        """交流节点分析 (MNA方法)"""
        nodes = list(self.circuit.nodes.keys())
        n = len(nodes)
        node_index = {nid: i for i, nid in enumerate(nodes)}

        # 电压源列表
        vs_list = self.circuit.get_voltage_sources()
        m = len(vs_list)

        # MNA矩阵: (n+m) x (n+m)
        size = n + m
        A = np.zeros((size, size), dtype=complex)
        b = np.zeros(size, dtype=complex)

        # 填充导纳矩阵
        for comp in self.circuit.components:
            i1 = node_index.get(comp.node1)
            i2 = node_index.get(comp.node2)

            if comp.name in impedances:
                z = impedances[comp.name]
                if abs(z) > 1e-10:
                    y = 1.0 / z
                    if i1 is not None and i1 != node_index[self._ground]:
                        A[i1, i1] += y
                        if i2 is not None and i2 != node_index[self._ground]:
                            A[i1, i2] -= y
                    if i2 is not None and i2 != node_index[self._ground]:
                        A[i2, i2] += y
                        if i1 is not None and i1 != node_index[self._ground]:
                            A[i2, i1] -= y

            elif isinstance(comp, CurrentSource):
                i_phasor = comp.phasor()
                if i1 is not None and i1 != node_index[self._ground]:
                    b[i1] -= i_phasor
                if i2 is not None and i2 != node_index[self._ground]:
                    b[i2] += i_phasor

        # 填充电压源约束 (MNA扩展)
        for idx, vs in enumerate(vs_list):
            k = n + idx
            i1 = node_index.get(vs.node1)
            i2 = node_index.get(vs.node2)

            if i1 is not None and i1 != node_index[self._ground]:
                A[i1, k] += 1
                A[k, i1] += 1
            if i2 is not None and i2 != node_index[self._ground]:
                A[i2, k] -= 1
                A[k, i2] -= 1

            b[k] = vs.phasor()

        # 移除接地点行列
        ground_idx = node_index[self._ground]
        reduced_indices = [i for i in range(size) if i != ground_idx]
        A_reduced = A[np.ix_(reduced_indices, reduced_indices)]
        b_reduced = b[reduced_indices]

        # 求解
        try:
            x = np.linalg.solve(A_reduced, b_reduced)
        except np.linalg.LinAlgError:
            raise ValueError("电路无法求解")

        # 提取结果
        node_voltages = {self._ground: complex(0, 0)}
        for i, nid in enumerate(nodes):
            if nid == self._ground:
                continue
            idx = reduced_indices.index(i) if i in reduced_indices else -1
            if idx >= 0:
                node_voltages[nid] = x[idx]

        return node_voltages

    def _calculate_ac_vs_current(self, vs: VoltageSource,
                                  node_voltages: Dict[int, complex],
                                  impedances: Dict[str, complex],
                                  frequency: float) -> complex:
        """计算交流电压源电流"""
        node = vs.node1
        total_current = 0 + 0j

        for comp in self.circuit.get_node_components(node):
            if comp is vs:
                continue

            v1 = node_voltages.get(comp.node1, 0)
            v2 = node_voltages.get(comp.node2, 0)
            v_branch = v1 - v2

            if comp.name in impedances:
                z = impedances[comp.name]
                if abs(z) > 1e-10:
                    i = v_branch / z
                    if comp.node1 == node:
                        total_current += i
                    else:
                        total_current -= i
            elif isinstance(comp, CurrentSource):
                i_phasor = comp.phasor()
                if comp.node1 == node:
                    total_current -= i_phasor
                else:
                    total_current += i_phasor

        return -total_current

    def _calculate_total_impedance(self, frequency: float) -> complex:
        """计算总阻抗"""
        # 简化: 计算所有串联阻抗之和
        total = 0 + 0j
        for comp in self.circuit.components:
            if isinstance(comp, (Resistor, Capacitor, Inductor)):
                total += comp.impedance(frequency)
        return total

    def frequency_response(self, f_start: float, f_stop: float,
                          f_points: int = 1000,
                          node_id: Optional[int] = None) -> FrequencyResponse:
        """
        计算频率响应

        参数:
            f_start: 起始频率
            f_stop: 终止频率
            f_points: 频率点数
            node_id: 输出节点 (默认为第一个非接地点)

        返回:
            FrequencyResponse: 频率响应数据
        """
        frequencies = np.logspace(np.log10(f_start), np.log10(f_stop), f_points)
        magnitude = np.zeros(f_points)
        phase = np.zeros(f_points)

        # 找到输入源
        vs_list = self.circuit.get_voltage_sources()
        if not vs_list:
            raise ValueError("需要至少一个电压源")

        # 默认输出节点
        if node_id is None:
            for nid in self.circuit.nodes:
                if nid != self._ground:
                    node_id = nid
                    break

        for i, freq in enumerate(frequencies):
            result = self.solve(freq)
            v_out = result.node_voltages.get(node_id, 0)
            v_in = vs_list[0].voltage

            if v_in != 0:
                transfer = v_out / v_in
                magnitude[i] = abs(transfer)
                phase[i] = np.degrees(np.angle(transfer))
            else:
                magnitude[i] = 0
                phase[i] = 0

        return FrequencyResponse(frequencies=frequencies, magnitude=magnitude, phase=phase)


def impedance_series(*impedances: complex) -> complex:
    """
    串联阻抗计算

    Z_total = Z1 + Z2 + ... + Zn

    参数:
        *impedances: 阻抗值列表

    返回:
        complex: 总阻抗
    """
    return sum(impedances)


def impedance_parallel(*impedances: complex) -> complex:
    """
    并联阻抗计算

    1/Z_total = 1/Z1 + 1/Z2 + ... + 1/Zn

    参数:
        *impedances: 阻抗值列表

    返回:
        complex: 总阻抗
    """
    if any(abs(z) < 1e-10 for z in impedances):
        return 0 + 0j
    return 1.0 / sum(1.0 / z for z in impedances)


def resonance_frequency(inductance: float, capacitance: float) -> float:
    """
    谐振频率计算

    f = 1 / (2π√(LC))

    参数:
        inductance: 电感值 (H)
        capacitance: 电容值 (F)

    返回:
        float: 谐振频率 (Hz)
    """
    if inductance <= 0 or capacitance <= 0:
        raise ValueError("电感和电容值必须为正数")
    return 1.0 / (2 * np.pi * np.sqrt(inductance * capacitance))


def quality_factor(inductance: float, resistance: float, frequency: float) -> float:
    """
    品质因数计算

    Q = ωL / R

    参数:
        inductance: 电感值 (H)
        resistance: 电阻值 (Ω)
        frequency: 频率 (Hz)

    返回:
        float: 品质因数
    """
    if resistance <= 0:
        raise ValueError("电阻值必须为正数")
    omega = 2 * np.pi * frequency
    return omega * inductance / resistance
