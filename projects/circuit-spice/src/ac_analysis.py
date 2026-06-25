"""
交流分析模块 - AC Analysis

实现交流电路的频率响应分析：
- 阻抗计算
- 频率扫描
- 增益/相位分析
- 波特图数据
"""

import numpy as np
from typing import Dict, List, Optional, Tuple

from .circuit import Circuit, ACSolution, FrequencyResponse
from .components import Resistor, Capacitor, Inductor, VoltageSource


class ACAnalysis:
    """
    交流分析器

    使用复数阻抗进行频率扫描分析
    """

    def __init__(self, circuit: Circuit):
        self.circuit = circuit
        self.circuit.build_node_map()

    def solve(self, frequency: float) -> ACSolution:
        """
        求解指定频率的交流响应

        Args:
            frequency: 频率 (Hz)

        Returns:
            ACSolution: 交流解
        """
        n = self.circuit.num_nodes
        m = self.circuit.num_v_sources
        size = n + m

        # 初始化复数矩阵
        A = np.zeros((size, size), dtype=complex)
        b = np.zeros(size, dtype=complex)

        # 印记元件
        for comp in self.circuit.components:
            v_idx = -1
            if isinstance(comp, VoltageSource):
                v_idx = n + self.circuit.voltage_sources.index(comp)

            comp.stamp_ac(A, frequency, self.circuit.node_map, v_idx)

        # 设置电压源激励
        for i, v_source in enumerate(self.circuit.voltage_sources):
            idx = n + i
            if v_source.ac_mag > 0:
                b[idx] = v_source.ac_mag * np.exp(1j * np.radians(v_source.phase))

        # 求解线性方程组
        try:
            x = np.linalg.solve(A, b)
        except np.linalg.LinAlgError:
            x, _, _, _ = np.linalg.lstsq(A, b, rcond=None)

        # 提取节点电压
        node_voltages = {self.circuit.ground_node: complex(0, 0)}
        for node, idx in self.circuit.node_map.items():
            node_voltages[node] = x[idx]

        return ACSolution(frequency, node_voltages)

    def frequency_response(self, f_start: float, f_stop: float,
                          points_per_decade: int = 100) -> FrequencyResponse:
        """
        频率响应分析

        Args:
            f_start: 起始频率 (Hz)
            f_stop: 终止频率 (Hz)
            points_per_decade: 每十倍频程的点数

        Returns:
            FrequencyResponse: 频率响应结果
        """
        # 生成对数频率点
        num_decades = np.log10(f_stop / f_start)
        num_points = int(num_decades * points_per_decade)
        frequencies = np.logspace(np.log10(f_start), np.log10(f_stop), num_points)

        responses = []
        for freq in frequencies:
            result = self.solve(freq)
            responses.append(result)

        return FrequencyResponse(frequencies, responses)

    def frequency_response_linear(self, f_start: float, f_stop: float,
                                  num_points: int = 1000) -> FrequencyResponse:
        """
        线性频率扫描

        Args:
            f_start: 起始频率 (Hz)
            f_stop: 终止频率 (Hz)
            num_points: 频率点数

        Returns:
            FrequencyResponse: 频率响应结果
        """
        frequencies = np.linspace(f_start, f_stop, num_points)

        responses = []
        for freq in frequencies:
            result = self.solve(freq)
            responses.append(result)

        return FrequencyResponse(frequencies, responses)


def impedance_resistor(r: float, freq: float) -> complex:
    """电阻阻抗"""
    return complex(r, 0)


def impedance_capacitor(c: float, freq: float) -> complex:
    """电容阻抗"""
    if freq == 0:
        return complex(float('inf'), 0)
    omega = 2 * np.pi * freq
    return 1.0 / (1j * omega * c)


def impedance_inductor(l: float, freq: float) -> complex:
    """电感阻抗"""
    omega = 2 * np.pi * freq
    return 1j * omega * l


def resonance_frequency(l: float, c: float) -> float:
    """
    LC 谐振频率

    Args:
        l: 电感 (H)
        c: 电容 (F)

    Returns:
        float: 谐振频率 (Hz)
    """
    return 1.0 / (2 * np.pi * np.sqrt(l * c))


def rc_cutoff_frequency(r: float, c: float) -> float:
    """
    RC 截止频率

    Args:
        r: 电阻 (Ohm)
        c: 电容 (F)

        Returns:
        float: 截止频率 (Hz)
    """
    return 1.0 / (2 * np.pi * r * c)


def rl_cutoff_frequency(r: float, l: float) -> float:
    """
    RL 截止频率

    Args:
        r: 电阻 (Ohm)
        l: 电感 (H)

    Returns:
        float: 截止频率 (Hz)
    """
    return r / (2 * np.pi * l)


def rc_lowpass_response(frequencies: np.ndarray, r: float, c: float) -> np.ndarray:
    """
    RC 低通滤波器频率响应

    Args:
        frequencies: 频率数组 (Hz)
        r: 电阻 (Ohm)
        c: 电容 (F)

    Returns:
        np.ndarray: 复数传递函数值
    """
    omega = 2 * np.pi * frequencies
    tau = r * c
    return 1.0 / (1 + 1j * omega * tau)


def rc_highpass_response(frequencies: np.ndarray, r: float, c: float) -> np.ndarray:
    """
    RC 高通滤波器频率响应

    Args:
        frequencies: 频率数组 (Hz)
        r: 电阻 (Ohm)
        c: 电容 (F)

    Returns:
        np.ndarray: 复数传递函数值
    """
    omega = 2 * np.pi * frequencies
    tau = r * c
    return (1j * omega * tau) / (1 + 1j * omega * tau)


def rlc_resonance_response(frequencies: np.ndarray, r: float, l: float, c: float) -> np.ndarray:
    """
    RLC 串联谐振电路频率响应

    Args:
        frequencies: 频率数组 (Hz)
        r: 电阻 (Ohm)
        l: 电感 (H)
        c: 电容 (F)

    Returns:
        np.ndarray: 传递函数值 (电容电压/输入电压)
    """
    omega = 2 * np.pi * frequencies
    z_l = 1j * omega * l
    z_c = 1.0 / (1j * omega * c)
    z_total = r + z_l + z_c

    # 电容上的电压比
    return z_c / z_total


def quality_factor(r: float, l: float, c: float) -> float:
    """
    品质因数 Q

    Args:
        r: 电阻 (Ohm)
        l: 电感 (H)
        c: 电容 (F)

    Returns:
        float: 品质因数
    """
    return (1.0 / r) * np.sqrt(l / c)


def bandwidth(f0: float, q: float) -> float:
    """
    带宽

    Args:
        f0: 中心频率 (Hz)
        q: 品质因数

    Returns:
        float: 带宽 (Hz)
    """
    return f0 / q


def voltage_gain_db(v_out: complex, v_in: complex) -> float:
    """
    电压增益 (dB)

    Args:
        v_out: 输出电压
        v_in: 输入电压

    Returns:
        float: 增益 (dB)
    """
    if abs(v_in) == 0:
        return float('-inf')
    gain = abs(v_out) / abs(v_in)
    return 20 * np.log10(gain) if gain > 0 else float('-inf')


def phase_degrees(v_out: complex, v_in: complex) -> float:
    """
    相位差 (度)

    Args:
        v_out: 输出电压
        v_in: 输入电压

    Returns:
        float: 相位差 (度)
    """
    if abs(v_in) == 0 or abs(v_out) == 0:
        return 0
    return np.degrees(np.angle(v_out) - np.angle(v_in))
