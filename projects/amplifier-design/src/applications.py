"""
放大器实际应用

实现放大器在以下领域的应用：
- 信号调理 (Signal Conditioning)
- 传感器放大 (Sensor Amplification)
- 音频放大 (Audio Amplification)
"""

import numpy as np
from .opamp import NonInvertingAmp, InvertingAmp, InstrumentationAmp, OpAmpParams


class SignalConditioner:
    """
    信号调理器

    功能:
    - 直流偏移消除
    - 增益调整
    - 电平移位
    - 单端到差分转换
    """

    def __init__(self, gain: float = 1.0, offset: float = 0.0,
                 v_ref: float = 0.0, v_supply: float = 15.0):
        """
        Args:
            gain: 信号增益
            offset: 输出偏移电压, V
            v_ref: 参考电压, V
            v_supply: 电源电压, V
        """
        self.gain = gain
        self.offset = offset
        self.v_ref = v_ref
        self.v_supply = v_supply

    def process(self, signal: np.ndarray) -> np.ndarray:
        """
        处理信号: 放大 + 偏移

        Args:
            signal: 输入信号数组

        Returns:
            np.ndarray: 处理后的信号
        """
        output = self.gain * (signal - self.v_ref) + self.offset
        return np.clip(output, -self.v_supply, self.v_supply)

    def level_shift(self, signal: np.ndarray, shift: float) -> np.ndarray:
        """
        电平移位

        Args:
            signal: 输入信号
            shift: 移位电压, V

        Returns:
            np.ndarray: 移位后的信号
        """
        return np.clip(signal + shift, -self.v_supply, self.v_supply)

    def ac_coupled_amplify(self, signal: np.ndarray, f_cutoff: float,
                           fs: float, gain: float = None) -> np.ndarray:
        """
        交流耦合放大 (去除直流分量后放大)

        Args:
            signal: 输入信号
            f_cutoff: 高通截止频率, Hz
            fs: 采样率, Hz
            gain: 放大增益 (默认使用self.gain)

        Returns:
            np.ndarray: 放大后的信号
        """
        gain = gain or self.gain

        # 简单的一阶高通滤波 (去除直流)
        alpha = 1.0 / (1.0 + 2 * np.pi * f_cutoff / fs)
        filtered = np.zeros_like(signal)
        filtered[0] = signal[0]
        for i in range(1, len(signal)):
            filtered[i] = alpha * (filtered[i - 1] + signal[i] - signal[i - 1])

        return gain * filtered

    def differential_to_single(self, v_pos: np.ndarray, v_neg: np.ndarray) -> np.ndarray:
        """
        差分转单端

        Args:
            v_pos: 正输入信号
            v_neg: 负输入信号

        Returns:
            np.ndarray: 单端输出
        """
        return self.gain * (v_pos - v_neg) + self.offset


class SensorAmplifier:
    """
    传感器信号放大器

    支持常见传感器类型:
    - 热电偶 (Thermocouple)
    - 应变片 (Strain Gauge)
    - 光电二极管 (Photodiode)
    - 压电传感器 (Piezoelectric)
    """

    def __init__(self, opamp: OpAmpParams = None):
        self.opamp = opamp or OpAmpParams()

    def thermocouple_amp(self, R_g: float, R1: float = 49.4e3) -> dict:
        """
        热电偶放大器 (仪表放大器)

        热电偶输出很小 (约 40uV/degC)，需要高增益差分放大。

        Args:
            R_g: 增益设置电阻, Ohm
            R1: 仪表放大器前级电阻, Ohm

        Returns:
            dict: 放大器参数
        """
        inamp = InstrumentationAmp(R1=R1, R_g=R_g, opamp=self.opamp)
        gain = inamp.gain()

        return {
            'type': '热电偶放大器',
            'topology': '仪表放大器',
            'gain': gain,
            'gain_dB': 20 * np.log10(gain),
            'sensitivity': 40e-6 * gain,  # V/degC (K型热电偶)
            'R_g': R_g,
            'R1': R1,
            'bandwidth': inamp.bandwidth(),
        }

    def strain_gauge_amp(self, R_gauge: float, R_g: float,
                          V_excitation: float = 5.0,
                          gauge_factor: float = 2.0,
                          R1: float = 49.4e3) -> dict:
        """
        应变片放大器

        使用惠斯通电桥 + 仪表放大器。

        Args:
            R_gauge: 应变片标称电阻, Ohm
            R_g: 增益设置电阻, Ohm
            V_excitation: 电桥激励电压, V
            gauge_factor: 应变系数
            R1: 仪表放大器前级电阻, Ohm

        Returns:
            dict: 放大器参数
        """
        inamp = InstrumentationAmp(R1=R1, R_g=R_g, opamp=self.opamp)
        gain = inamp.gain()

        # 满量程应变输出
        # dV = V_exc * GF * strain / 4 (惠斯通电桥)
        max_strain = 0.001  # 1000 微应变
        bridge_output = V_excitation * gauge_factor * max_strain / 4

        return {
            'type': '应变片放大器',
            'topology': '惠斯通电桥 + 仪表放大器',
            'gain': gain,
            'bridge_output': bridge_output,
            'amplified_output': bridge_output * gain,
            'V_excitation': V_excitation,
            'gauge_factor': gauge_factor,
            'sensitivity': V_excitation * gauge_factor * gain / 4,
        }

    def photodiode_amp(self, R_f: float, C_f: float = 0.0,
                        responsivity: float = 0.5) -> dict:
        """
        光电二极管放大器 (跨阻放大器 TIA)

        使用反相放大器配置，光电二极管接在虚地端。

        Args:
            R_f: 反馈电阻, Ohm (决定跨阻增益)
            C_f: 反馈电容, F (限制带宽，减少噪声)
            responsivity: 光电二极管响应度, A/W

        Returns:
            dict: 放大器参数
        """
        transimpedance = R_f  # V/A

        # 带宽由 R_f * C_f 决定
        if C_f > 0:
            bandwidth = 1 / (2 * np.pi * R_f * C_f)
        else:
            bandwidth = self.opamp.GBW / (1 + R_f / 1e3)  # 简化

        return {
            'type': '光电二极管跨阻放大器',
            'topology': '反相放大器 (TIA)',
            'transimpedance': transimpedance,
            'responsivity': responsivity,
            'sensitivity': responsivity * transimpedance,  # V/W
            'bandwidth': bandwidth,
            'R_f': R_f,
            'C_f': C_f,
        }

    def piezo_amp(self, R_f: float, C_in: float = 1e-9) -> dict:
        """
        压电传感器放大器

        压电传感器输出高阻抗，需要高输入阻抗放大器。
        使用电荷放大器或高阻抗同相放大器。

        Args:
            R_f: 反馈电阻, Ohm
            C_in: 传感器电容, F

        Returns:
            dict: 放大器参数
        """
        # 电荷放大器: 增益由 C_f / C_sensor 决定
        # 简化为高阻抗同相放大器
        gain = 1 + R_f / 1e3  # 简化

        # 高通截止频率 (由传感器电容和输入阻抗决定)
        f_low = 1 / (2 * np.pi * R_f * C_in)

        return {
            'type': '压电传感器放大器',
            'topology': '高阻抗同相放大器',
            'gain': gain,
            'input_impedance': 1e12,  # 运放输入阻抗
            'low_cutoff': f_low,
            'sensor_capacitance': C_in,
        }


class AudioAmplifier:
    """
    音频放大器

    功能:
    - 前置放大 (Pre-amplification)
    - 音调控制 (Tone Control)
    - 功率放大驱动
    """

    def __init__(self, v_supply: float = 15.0, opamp: OpAmpParams = None):
        """
        Args:
            v_supply: 电源电压, V
            opamp: 运放参数
        """
        self.v_supply = v_supply
        self.opamp = opamp or OpAmpParams()

    def preamp(self, R_in: float = 10e3, R_f: float = 100e3) -> dict:
        """
        前置放大器

        低噪声同相放大器，用于麦克风等信号源。

        Args:
            R_in: 输入电阻, Ohm
            R_f: 反馈电阻, Ohm

        Returns:
            dict: 前置放大器参数
        """
        amp = NonInvertingAmp(R_in=R_in, R_f=R_f, opamp=self.opamp)
        gain = amp.gain()

        # 噪声增益
        noise_gain = 1 + R_f / R_in

        return {
            'type': '音频前置放大器',
            'gain': gain,
            'gain_dB': 20 * np.log10(gain),
            'noise_gain': noise_gain,
            'bandwidth': amp.bandwidth(),
            'input_impedance': amp.input_impedance(),
            'max_output': self.v_supply - 2,  # 留2V余量
        }

    def tone_control(self, bass_gain: float = 1.0, treble_gain: float = 1.0,
                      f_bass: float = 300, f_treble: float = 3000) -> dict:
        """
        音调控制 (Baxandall 型)

        Args:
            bass_gain: 低音增益 (线性, 如2.0表示+6dB)
            treble_gain: 高音增益
            f_bass: 低音转折频率, Hz
            f_treble: 高音转折频率, Hz

        Returns:
            dict: 音调控制参数
        """
        return {
            'type': 'Baxandall 音调控制',
            'bass_gain': bass_gain,
            'bass_gain_dB': 20 * np.log10(bass_gain),
            'treble_gain': treble_gain,
            'treble_gain_dB': 20 * np.log10(treble_gain),
            'bass_frequency': f_bass,
            'treble_frequency': f_treble,
        }

    def baxandall_response(self, f: np.ndarray, bass_gain: float,
                             treble_gain: float, f_bass: float = 300,
                             f_treble: float = 3000) -> np.ndarray:
        """
        计算 Baxandall 音调控制的频率响应

        Args:
            f: 频率数组, Hz
            bass_gain: 低频增益 (线性)
            treble_gain: 高频增益 (线性)
            f_bass: 低音转折频率, Hz
            f_treble: 高音转折频率, Hz

        Returns:
            np.ndarray: 频率响应 (dB)
        """
        # 简化的一阶 Baxandall 模型
        s = 1j * 2 * np.pi * f

        # 低音部分: 一阶全通 + 增益调节
        H_bass = (1 + s / (2 * np.pi * f_bass)) / (1 + s / (2 * np.pi * f_bass) / bass_gain)

        # 高音部分
        H_treble = (1 + s / (2 * np.pi * f_treble) * treble_gain) / (1 + s / (2 * np.pi * f_treble))

        H = H_bass * H_treble
        return 20 * np.log10(np.abs(H) + 1e-30)

    def power_amp_driver(self, gain: float = 10.0,
                          f_low: float = 20.0,
                          f_high: float = 20000.0) -> dict:
        """
        功率放大器驱动级

        带通滤波 + 增益缓冲，驱动功率晶体管。

        Args:
            gain: 驱动增益
            f_low: 低频截止, Hz
            f_high: 高频截止, Hz

        Returns:
            dict: 驱动级参数
        """
        bw = f_high - f_low

        return {
            'type': '功率放大器驱动级',
            'gain': gain,
            'gain_dB': 20 * np.log10(gain),
            'low_cutoff': f_low,
            'high_cutoff': f_high,
            'bandwidth': bw,
            'max_output_voltage': self.v_supply - 3,
            'max_output_power_8ohm': (self.v_supply - 3) ** 2 / (2 * 8),
        }

    def crossover_network(self, f_crossover: float = 3000,
                           order: int = 2) -> dict:
        """
        分频器设计参数

        Args:
            f_crossover: 分频频率, Hz
            order: 滤波器阶数

        Returns:
            dict: 分频器参数
        """
        # Linkwitz-Riley 分频器
        # 2阶: -12dB/oct
        # 4阶: -24dB/oct
        slope_db_oct = order * 6

        return {
            'type': 'Linkwitz-Riley 分频器',
            'crossover_frequency': f_crossover,
            'order': order,
            'slope': f'{slope_db_oct} dB/octave',
            'low_pass_type': f'LR{order} LPF',
            'high_pass_type': f'LR{order} HPF',
        }
