"""
ADC 模块 (Analog-to-Digital Converter)
=======================================

ADC (模数转换器) 将连续时间、连续幅度的模拟信号
转换为离散时间、离散幅度的数字信号。

ADC 工作过程:
1. 采样 (Sampling): 将连续时间信号离散化
2. 保持 (Hold): 保持采样值稳定
3. 量化 (Quantization): 将幅度映射到离散电平
4. 编码 (Encoding): 将量化值转换为二进制码

ADC 类型:
- 逐次逼近型 (SAR ADC): 中等速度，中等精度
- Sigma-Delta ADC: 高精度，低速度
- 并行/闪速 ADC (Flash ADC): 高速，低精度
- 分级 ADC (Pipeline ADC): 高速，中等精度

本模块实现理想 ADC 模型。
"""

import numpy as np

from .sampling import ideal_sampling, check_aliasing, calculate_nyquist
from .quantization import uniform_quantize


class IdealADC:
    """
    理想 ADC 类

    模拟一个理想 ADC 的行为，包括采样、量化和编码。
    """

    def __init__(self, num_bits: int, v_range: tuple = (-1.0, 1.0), fs: float = 1000.0):
        """
        初始化 ADC

        参数:
            num_bits: 量化位数 (决定分辨率)
            v_range: 输入电压范围 (min, max)
            fs: 采样频率 (Hz)
        """
        self.num_bits = num_bits
        self.num_levels = 2 ** num_bits
        self.v_min, self.v_max = v_range
        self._v_range_tuple = v_range
        self.v_range = self.v_max - self.v_min
        self.step_size = self.v_range / self.num_levels
        self.fs = fs
        self.ts = 1.0 / fs

    def convert(self, signal: np.ndarray, t_start: float = 0.0, t_end: float = 1.0) -> dict:
        """
        将模拟信号转换为数字信号

        参数:
            signal: 模拟信号 (numpy array)
            t_start: 起始时间 (秒)
            t_end: 结束时间 (秒)

        返回:
            dict 包含:
                - digital_signal: 数字信号值 (量化后的幅度)
                - digital_codes: 二进制编码 (整数)
                - sample_times: 采样时刻
                - fs: 采样频率
                - step_size: 量化步长
                - snr: 信噪比 (dB)
        """
        # 步骤1: 采样
        sampled = ideal_sampling(signal, self.fs, t_start, t_end)
        sample_times = sampled["sample_times"]
        sampled_values = sampled["samples"]

        # 步骤2: 量化
        quantized = uniform_quantize(sampled_values, self.num_bits, self._v_range_tuple)

        # 步骤3: 编码 (将量化电平映射为二进制整数)
        digital_codes = self._encode(quantized["quantized"])

        # 计算实际 SNR
        actual_snr = self._calculate_snr(sampled_values, quantized["quantized"])

        return {
            "digital_signal": quantized["quantized"],
            "digital_codes": digital_codes,
            "sample_times": sample_times,
            "fs": self.fs,
            "step_size": self.step_size,
            "num_levels": self.num_levels,
            "num_samples": len(digital_codes),
            "quantization_error": quantized["quantization_error"],
            "snr": actual_snr,
            "snr_theoretical": quantized["snr_theoretical"],
        }

    def _encode(self, quantized_values: np.ndarray) -> np.ndarray:
        """
        将量化值编码为二进制整数

        参数:
            quantized_values: 量化后的信号值

        返回:
            二进制编码 (整数数组)
        """
        # 将量化值映射到 [0, num_levels-1]
        codes = ((quantized_values - self.v_min) / self.step_size + 0.5).astype(int)
        codes = np.clip(codes, 0, self.num_levels - 1)
        return codes

    def _calculate_snr(self, original: np.ndarray, quantized: np.ndarray) -> float:
        """计算实际 SNR"""
        signal_power = np.mean(original ** 2)
        noise_power = np.mean((original - quantized) ** 2)

        if noise_power == 0 or signal_power == 0:
            return float("inf")

        return 10.0 * np.log10(signal_power / noise_power)

    def get_resolution(self) -> float:
        """获取 ADC 的电压分辨率"""
        return self.step_size

    def get_theoretical_snr(self) -> float:
        """获取理论 SNR"""
        return 6.02 * self.num_bits + 1.76

    def __repr__(self):
        return (
            f"IdealADC(bits={self.num_bits}, v_range=({self.v_min}, {self.v_max}), "
            f"fs={self.fs}Hz, resolution={self.get_resolution():.6f}V)"
        )


def simulate_adc_chain(signal: np.ndarray, signal_freq: float,
                       num_bits: int = 8, fs: float = 1000.0,
                       t_start: float = 0.0, t_end: float = 1.0) -> dict:
    """
    模拟完整的 ADC 转换链

    参数:
        signal: 输入模拟信号
        signal_freq: 信号频率
        num_bits: ADC 位数
        fs: 采样频率
        t_start: 起始时间
        t_end: 结束时间

    返回:
        dict 包含完整的 ADC 转换结果和分析
    """
    adc = IdealADC(num_bits, (-1.0, 1.0), fs)
    result = adc.convert(signal, t_start, t_end)

    # 添加混叠检测
    alias_check = check_aliasing(signal_freq, fs)
    result["aliasing"] = alias_check

    # 添加理论 SNR
    result["theoretical_snr"] = adc.get_theoretical_snr()

    return result


def simulate_adc_chain(signal: np.ndarray, signal_freq: float,
                       num_bits: int = 8, fs: float = 1000.0,
                       t_start: float = 0.0, t_end: float = 1.0,
                       v_range: tuple = (-1.0, 1.0)) -> dict:
    """
    模拟完整的 ADC 转换链

    参数:
        signal: 输入模拟信号
        signal_freq: 信号频率
        num_bits: ADC 位数
        fs: 采样频率
        t_start: 起始时间
        t_end: 结束时间
        v_range: 电压范围

    返回:
        dict 包含完整的 ADC 转换结果和分析
    """
    adc = IdealADC(num_bits, v_range, fs)
    result = adc.convert(signal, t_start, t_end)

    # 添加混叠检测
    alias_check = check_aliasing(signal_freq, fs)
    result["aliasing"] = alias_check

    # 添加理论 SNR
    result["theoretical_snr"] = adc.get_theoretical_snr()

    return result

    return result
