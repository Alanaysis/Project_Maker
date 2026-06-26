"""
DAC 模块 (Digital-to-Analog Converter)
=======================================

DAC (数模转换器) 将离散时间、离散幅度的数字信号
转换为连续时间、连续幅度的模拟信号。

DAC 工作过程:
1. 解码 (Decoding): 将二进制码转换为模拟电平
2. 保持 (Hold): 使用零阶保持 (ZOH) 保持每个采样值

DAC 类型:
- 权电阻型 DAC: 简单但精度低
- R-2R 型 DAC: 常用，精度较高
- 电流型 DAC: 高速应用

本模块实现理想 DAC 模型 (零阶保持)。
"""

import numpy as np

from .reconstruction import ideal_reconstruction, zero_order_hold


class IdealDAC:
    """
    理想 DAC 类

    模拟一个理想 DAC 的行为，包括解码和重建。
    """

    def __init__(self, num_bits: int, v_range: tuple = (-1.0, 1.0), fs: float = 1000.0):
        """
        初始化 DAC

        参数:
            num_bits: DAC 位数 (决定分辨率)
            v_range: 输出电压范围 (min, max)
            fs: 采样频率 (Hz)
        """
        self.num_bits = num_bits
        self.num_levels = 2 ** num_bits
        self.v_min, self.v_max = v_range
        self.v_range = self.v_max - self.v_min
        self.step_size = self.v_range / self.num_levels
        self.fs = fs
        self.ts = 1.0 / fs

    def convert(self, digital_codes: np.ndarray, sample_times: np.ndarray,
                t_start: float = 0.0, t_end: float = 1.0,
                reconstruction_method: str = "zoh") -> dict:
        """
        将数字信号转换为模拟信号

        参数:
            digital_codes: 数字编码 (整数数组)
            sample_times: 采样时刻数组
            t_start: 输出信号起始时间
            t_end: 输出信号结束时间
            reconstruction_method: 重建方法 ('zoh' 或 'ideal')

        返回:
            dict 包含:
                - analog_signal: 重建的模拟信号
                - reconstruction_times: 重建信号的时间点
                - step_size: 量化步长
                - num_levels: 量化级数
        """
        # 解码: 将数字编码转换为模拟电平
        decoded_values = self._decode(digital_codes)

        # 重建
        if reconstruction_method == "zoh":
            reconstructed = zero_order_hold(decoded_values, sample_times, t_start, t_end, self.fs)
        elif reconstruction_method == "ideal":
            reconstructed = ideal_reconstruction(decoded_values, sample_times, t_start, t_end, self.fs)
        else:
            raise ValueError(f"未知重建方法: {reconstruction_method}")

        return {
            "analog_signal": reconstructed["signal"],
            "reconstruction_times": reconstructed["times"],
            "step_size": self.step_size,
            "num_levels": self.num_levels,
            "decoded_values": decoded_values,
        }

    def _decode(self, codes: np.ndarray) -> np.ndarray:
        """
        将数字编码解码为模拟电平

        参数:
            codes: 数字编码 (整数数组)

        返回:
            解码后的模拟电平
        """
        # 将二进制码映射到对应的电压电平
        values = np.clip(codes, 0, self.num_levels - 1)
        analog = self.v_min + (values + 0.5) * self.step_size
        return analog

    def get_resolution(self) -> float:
        """获取 DAC 的电压分辨率"""
        return self.step_size

    def __repr__(self):
        return (
            f"IdealDAC(bits={self.num_bits}, v_range=({self.v_min}, {self.v_max}), "
            f"fs={self.fs}Hz, resolution={self.get_resolution():.6f}V)"
        )


def simulate_dac_chain(digital_codes: np.ndarray, sample_times: np.ndarray,
                       num_bits: int = 8, v_range: tuple = (-1.0, 1.0),
                       fs: float = 1000.0, t_start: float = 0.0,
                       t_end: float = 1.0, reconstruction_method: str = "zoh") -> dict:
    """
    模拟完整的 DAC 转换链

    参数:
        digital_codes: 数字编码
        sample_times: 采样时刻
        num_bits: DAC 位数
        v_range: 电压范围
        fs: 采样频率
        t_start: 起始时间
        t_end: 结束时间
        reconstruction_method: 重建方法

    返回:
        dict 包含完整的 DAC 转换结果
    """
    dac = IdealDAC(num_bits, v_range, fs)
    result = dac.convert(digital_codes, sample_times, t_start, t_end, reconstruction_method)
    return result
