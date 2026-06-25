"""
实际应用模块

实现分压器、滤波器、放大器等实际电路应用。
"""

import numpy as np
from typing import Tuple, Optional, Dict, List
from dataclasses import dataclass, field
from .circuit import Circuit
from .ac_analysis import ACAnalyzer, FrequencyResponse, resonance_frequency
from .components import Resistor, Capacitor, Inductor, VoltageSource


class VoltageDivider:
    """
    分压器

    V_out = V_in * R2 / (R1 + R2)

    示例:
        >>> divider = VoltageDivider(v_in=12, r1=1000, r2=2000)
        >>> divider.output_voltage()
        8.0
        >>> divider.transfer_ratio()
        0.6667
    """

    def __init__(self, v_in: float, r1: float, r2: float,
                 r_load: Optional[float] = None):
        """
        初始化分压器

        参数:
            v_in: 输入电压 (V)
            r1: 上臂电阻 (Ω)
            r2: 下臂电阻 (Ω)
            r_load: 负载电阻 (Ω)，None表示无负载
        """
        self.v_in = v_in
        self.r1 = r1
        self.r2 = r2
        self.r_load = r_load

    def output_voltage(self) -> float:
        """计算输出电压"""
        if self.r_load is not None:
            # 有负载时，R2与R_load并联
            r2_parallel = (self.r2 * self.r_load) / (self.r2 + self.r_load)
            return self.v_in * r2_parallel / (self.r1 + r2_parallel)
        return self.v_in * self.r2 / (self.r1 + self.r2)

    def transfer_ratio(self) -> float:
        """计算传输比 (V_out / V_in)"""
        return self.output_voltage() / self.v_in

    def output_impedance(self) -> float:
        """计算输出阻抗"""
        # R1与R2并联
        return (self.r1 * self.r2) / (self.r1 + self.r2)

    def current(self) -> float:
        """计算总电流"""
        return self.v_in / (self.r1 + self.r2)

    def power_dissipation(self) -> Tuple[float, float]:
        """
        计算功率消耗

        返回:
            Tuple[float, float]: (P_R1, P_R2)
        """
        i = self.current()
        p_r1 = i ** 2 * self.r1
        p_r2 = i ** 2 * self.r2
        return p_r1, p_r2

    def to_circuit(self) -> Circuit:
        """转换为电路对象"""
        circuit = Circuit("Voltage Divider")
        n0 = circuit.add_node("GND")
        n1 = circuit.add_node("IN")
        n2 = circuit.add_node("OUT")
        circuit.set_ground(n0)

        circuit.add_voltage_source("V_in", n0, n1, self.v_in)
        circuit.add_resistor("R1", n1, n2, self.r1)
        circuit.add_resistor("R2", n2, n0, self.r2)

        if self.r_load is not None:
            circuit.add_resistor("R_load", n2, n0, self.r_load)

        return circuit

    def __repr__(self):
        return f"VoltageDivider(V_in={self.v_in}V, R1={self.r1}Ω, R2={self.r2}Ω)"


class RCFilter:
    """
    RC滤波器

    支持低通和高通配置。

    示例:
        >>> # 低通滤波器
        >>> lpf = RCFilter(r=1000, c=1e-6, filter_type='low')
        >>> lpf.cutoff_frequency()
        159.15 Hz

        >>> # 高通滤波器
        >>> hpf = RCFilter(r=1000, c=1e-6, filter_type='high')
        >>> hpf.cutoff_frequency()
        159.15 Hz
    """

    def __init__(self, r: float, c: float, filter_type: str = 'low'):
        """
        初始化RC滤波器

        参数:
            r: 电阻值 (Ω)
            c: 电容值 (F)
            filter_type: 滤波器类型 ('low' 或 'high')
        """
        self.r = r
        self.c = c
        self.filter_type = filter_type

        if filter_type not in ('low', 'high'):
            raise ValueError("filter_type 必须是 'low' 或 'high'")

    def cutoff_frequency(self) -> float:
        """
        计算截止频率

        f_c = 1 / (2πRC)
        """
        return 1.0 / (2 * np.pi * self.r * self.c)

    def time_constant(self) -> float:
        """计算时间常数"""
        return self.r * self.c

    def transfer_function(self, frequency: float) -> complex:
        """
        计算传输函数 H(f)

        低通: H(f) = 1 / (1 + j2πfRC)
        高通: H(f) = j2πfRC / (1 + j2πfRC)
        """
        jwrc = 1j * 2 * np.pi * frequency * self.r * self.c

        if self.filter_type == 'low':
            return 1.0 / (1 + jwrc)
        else:  # high
            return jwrc / (1 + jwrc)

    def gain_dB(self, frequency: float) -> float:
        """计算增益 (dB)"""
        h = self.transfer_function(frequency)
        return 20 * np.log10(abs(h))

    def phase(self, frequency: float) -> float:
        """计算相位 (度)"""
        h = self.transfer_function(frequency)
        return np.degrees(np.angle(h))

    def frequency_response(self, f_start: float = 1, f_stop: float = 1e6,
                          f_points: int = 1000) -> FrequencyResponse:
        """计算频率响应"""
        frequencies = np.logspace(np.log10(f_start), np.log10(f_stop), f_points)
        magnitude = np.zeros(f_points)
        phase = np.zeros(f_points)

        for i, freq in enumerate(frequencies):
            h = self.transfer_function(freq)
            magnitude[i] = abs(h)
            phase[i] = np.degrees(np.angle(h))

        return FrequencyResponse(frequencies=frequencies, magnitude=magnitude, phase=phase)

    def to_circuit(self) -> Circuit:
        """转换为电路对象"""
        circuit = Circuit(f"RC {self.filter_type.capitalize()} Pass Filter")
        n0 = circuit.add_node("GND")
        n1 = circuit.add_node("IN")
        n2 = circuit.add_node("OUT")
        circuit.set_ground(n0)

        circuit.add_voltage_source("V_in", n0, n1, 1.0)

        if self.filter_type == 'low':
            circuit.add_resistor("R", n1, n2, self.r)
            circuit.add_capacitor("C", n2, n0, self.c)
        else:  # high
            circuit.add_capacitor("C", n1, n2, self.c)
            circuit.add_resistor("R", n2, n0, self.r)

        return circuit

    def __repr__(self):
        return f"RCFilter(R={self.r}Ω, C={self.c}F, type={self.filter_type})"


class RLCFilter:
    """
    RLC滤波器

    支持带通和带阻配置。

    示例:
        >>> # 带通滤波器
        >>> bpf = RLCFilter(r=100, l=1e-3, c=1e-6, filter_type='bandpass')
        >>> bpf.resonance_freq()
        5032.92 Hz
    """

    def __init__(self, r: float, l: float, c: float, filter_type: str = 'bandpass'):
        """
        初始化RLC滤波器

        参数:
            r: 电阻值 (Ω)
            l: 电感值 (H)
            c: 电容值 (F)
            filter_type: 滤波器类型 ('bandpass' 或 'bandstop')
        """
        self.r = r
        self.l = l
        self.c = c
        self.filter_type = filter_type

        if filter_type not in ('bandpass', 'bandstop'):
            raise ValueError("filter_type 必须是 'bandpass' 或 'bandstop'")

    def resonance_freq(self) -> float:
        """计算谐振频率"""
        return resonance_frequency(self.l, self.c)

    def quality_factor(self) -> float:
        """计算品质因数"""
        omega_0 = 2 * np.pi * self.resonance_freq()
        return omega_0 * self.l / self.r

    def bandwidth(self) -> float:
        """计算带宽"""
        return self.r / (2 * np.pi * self.l)

    def transfer_function(self, frequency: float) -> complex:
        """
        计算传输函数 H(f)

        带通: H(f) = (jωL) / (R + jωL + 1/(jωC))
        带阻: H(f) = (R) / (R + jωL + 1/(jωC))
        """
        omega = 2 * np.pi * frequency
        z_l = 1j * omega * self.l
        z_c = 1.0 / (1j * omega * self.c) if omega > 0 else float('inf')

        z_total = self.r + z_l + z_c

        if self.filter_type == 'bandpass':
            return z_l / z_total
        else:  # bandstop
            return self.r / z_total

    def gain_dB(self, frequency: float) -> float:
        """计算增益 (dB)"""
        h = self.transfer_function(frequency)
        return 20 * np.log10(max(abs(h), 1e-10))

    def phase(self, frequency: float) -> float:
        """计算相位 (度)"""
        h = self.transfer_function(frequency)
        return np.degrees(np.angle(h))

    def frequency_response(self, f_start: float = 100, f_stop: float = 1e6,
                          f_points: int = 1000) -> FrequencyResponse:
        """计算频率响应"""
        frequencies = np.logspace(np.log10(f_start), np.log10(f_stop), f_points)
        magnitude = np.zeros(f_points)
        phase = np.zeros(f_points)

        for i, freq in enumerate(frequencies):
            h = self.transfer_function(freq)
            magnitude[i] = abs(h)
            phase[i] = np.degrees(np.angle(h))

        return FrequencyResponse(frequencies=frequencies, magnitude=magnitude, phase=phase)

    def to_circuit(self) -> Circuit:
        """转换为电路对象"""
        circuit = Circuit(f"RLC {self.filter_type.capitalize()} Filter")
        n0 = circuit.add_node("GND")
        n1 = circuit.add_node("IN")
        n2 = circuit.add_node("MID")
        n3 = circuit.add_node("OUT")
        circuit.set_ground(n0)

        circuit.add_voltage_source("V_in", n0, n1, 1.0)
        circuit.add_resistor("R", n1, n2, self.r)
        circuit.add_inductor("L", n2, n3, self.l)
        circuit.add_capacitor("C", n3, n0, self.c)

        return circuit

    def __repr__(self):
        return f"RLCFilter(R={self.r}Ω, L={self.l}H, C={self.c}F, type={self.filter_type})"


class Amplifier:
    """
    放大器模型

    支持反相、同相、差分放大器配置。

    示例:
        >>> # 反相放大器
        >>> inv_amp = Amplifier(r_in=10000, r_f=100000, config='inverting')
        >>> inv_amp.gain()
        -10.0

        >>> # 同相放大器
        >>> non_inv_amp = Amplifier(r_in=10000, r_f=100000, config='non_inverting')
        >>> non_inv_amp.gain()
        11.0
    """

    def __init__(self, r_in: float, r_f: float, config: str = 'inverting',
                 r_g: Optional[float] = None):
        """
        初始化放大器

        参数:
            r_in: 输入电阻 (Ω)
            r_f: 反馈电阻 (Ω)
            config: 配置类型 ('inverting', 'non_inverting', 'differential')
            r_g: 差分放大器的接地电阻 (Ω)
        """
        self.r_in = r_in
        self.r_f = r_f
        self.config = config
        self.r_g = r_g

        if config not in ('inverting', 'non_inverting', 'differential'):
            raise ValueError("config 必须是 'inverting', 'non_inverting' 或 'differential'")

    def gain(self) -> float:
        """
        计算增益

        反相: A = -R_f / R_in
        同相: A = 1 + R_f / R_in
        差分: A = R_f / R_in (当 R_g = R_in 时)
        """
        if self.config == 'inverting':
            return -self.r_f / self.r_in
        elif self.config == 'non_inverting':
            return 1 + self.r_f / self.r_in
        else:  # differential
            return self.r_f / self.r_in

    def gain_dB(self) -> float:
        """计算增益 (dB)"""
        return 20 * np.log10(abs(self.gain()))

    def output_voltage(self, v_in: float) -> float:
        """计算输出电压"""
        return self.gain() * v_in

    def input_impedance(self) -> float:
        """计算输入阻抗"""
        if self.config == 'inverting':
            return self.r_in
        elif self.config == 'non_inverting':
            # 理想运放输入阻抗无穷大
            return float('inf')
        else:  # differential
            return self.r_in

    def bandwidth(self, gain_bandwidth_product: float) -> float:
        """
        计算带宽

        BW = GBW / |A|
        """
        return gain_bandwidth_product / abs(self.gain())

    def to_circuit(self) -> Circuit:
        """转换为电路对象 (简化模型)"""
        circuit = Circuit(f"Amplifier ({self.config})")
        n0 = circuit.add_node("GND")
        n1 = circuit.add_node("IN")
        n2 = circuit.add_node("OUT")
        circuit.set_ground(n0)

        circuit.add_voltage_source("V_in", n0, n1, 1.0)
        circuit.add_resistor("R_in", n1, n2, self.r_in)
        circuit.add_resistor("R_f", n2, n0, self.r_f)

        return circuit

    def __repr__(self):
        return f"Amplifier(config={self.config}, gain={self.gain():.2f})"


class Integrator:
    """
    积分器

    V_out = -1/(RC) * ∫V_in dt

    示例:
        >>> integrator = Integrator(r=10000, c=1e-6)
        >>> integrator.gain_at_freq(100)
        -1.59
    """

    def __init__(self, r: float, c: float):
        self.r = r
        self.c = c

    def gain_at_freq(self, frequency: float) -> float:
        """计算指定频率的增益"""
        if frequency == 0:
            return float('inf')
        return -1.0 / (2 * np.pi * frequency * self.r * self.c)

    def transfer_function(self, frequency: float) -> complex:
        """计算传输函数"""
        if frequency == 0:
            return complex(float('-inf'), 0)
        omega = 2 * np.pi * frequency
        return -1.0 / (1j * omega * self.r * self.c)


class Differentiator:
    """
    微分器

    V_out = -RC * dV_in/dt

    示例:
        >>> differentiator = Differentiator(r=10000, c=1e-6)
        >>> differentiator.gain_at_freq(100)
        -6.28
    """

    def __init__(self, r: float, c: float):
        self.r = r
        self.c = c

    def gain_at_freq(self, frequency: float) -> float:
        """计算指定频率的增益"""
        omega = 2 * np.pi * frequency
        return -omega * self.r * self.c

    def transfer_function(self, frequency: float) -> complex:
        """计算传输函数"""
        omega = 2 * np.pi * frequency
        return -1j * omega * self.r * self.c
