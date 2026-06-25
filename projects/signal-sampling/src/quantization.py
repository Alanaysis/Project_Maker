"""
信号量化实现
=============

实现均匀量化和非均匀量化。

核心原理:
- 均匀量化: 等间隔划分量化区间
- 非均匀量化: 非等间隔划分，对小信号更精确
- mu律/A律: 常用的非均匀量化方法

量化误差:
- 量化误差 e[n] = x[n] - Q(x[n])
- 量化步长: Δ = (max - min) / (2^b - 1)
- SQNR (信号量化噪声比): SQNR = 6.02*b + 1.76 dB (正弦信号)
"""

import numpy as np
from typing import Tuple, Optional


class UniformQuantizer:
    """均匀量化器

    将连续幅度信号量化为离散电平。

    Parameters
    ----------
    bits : int
        量化位数
    vmin : float
        最小量化值
    vmax : float
        最大量化值
    """

    def __init__(self, bits: int, vmin: float = -1.0, vmax: float = 1.0):
        if bits <= 0:
            raise ValueError("量化位数必须为正整数")
        if vmin >= vmax:
            raise ValueError("vmin 必须小于 vmax")

        self.bits = bits
        self.vmin = vmin
        self.vmax = vmax
        self.levels = 2 ** bits
        self.step = (vmax - vmin) / (self.levels - 1)

    def quantize(self, signal: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """量化信号

        Parameters
        ----------
        signal : np.ndarray
            输入信号

        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            (量化值, 量化索引)
        """
        # 限幅
        clipped = np.clip(signal, self.vmin, self.vmax)

        # 计算量化索引
        indices = np.round((clipped - self.vmin) / self.step).astype(int)
        indices = np.clip(indices, 0, self.levels - 1)

        # 重建量化值
        quantized = self.vmin + indices * self.step

        return quantized, indices

    def dequantize(self, indices: np.ndarray) -> np.ndarray:
        """反量化

        Parameters
        ----------
        indices : np.ndarray
            量化索引

        Returns
        -------
        np.ndarray
            重建值
        """
        return self.vmin + indices * self.step

    def quantization_error(self, signal: np.ndarray) -> np.ndarray:
        """计算量化误差

        Parameters
        ----------
        signal : np.ndarray
            原始信号

        Returns
        -------
        np.ndarray
            量化误差
        """
        quantized, _ = self.quantize(signal)
        return signal - quantized

    def sqnr(self, signal: np.ndarray) -> float:
        """计算信号量化噪声比 (SQNR)

        Parameters
        ----------
        signal : np.ndarray
            输入信号

        Returns
        -------
        float
            SQNR (dB)
        """
        quantized, _ = self.quantize(signal)
        noise = signal - quantized

        signal_power = np.mean(signal ** 2)
        noise_power = np.mean(noise ** 2)

        if noise_power == 0:
            return float('inf')

        return 10.0 * np.log10(signal_power / noise_power)

    @property
    def theoretical_sqnr(self) -> float:
        """理论 SQNR (正弦信号)

        SQNR = 6.02 * b + 1.76 dB
        """
        return 6.02 * self.bits + 1.76


class NonUniformQuantizer:
    """非均匀量化器

    使用 mu律或 A律压缩进行非均匀量化。

    Parameters
    ----------
    bits : int
        量化位数
    mu : float
        mu律压缩参数 (默认 255)
    vmin : float
        最小量化值
    vmax : float
        最大量化值
    """

    def __init__(
        self,
        bits: int,
        mu: float = 255.0,
        vmin: float = -1.0,
        vmax: float = 1.0,
    ):
        if bits <= 0:
            raise ValueError("量化位数必须为正整数")
        if mu <= 0:
            raise ValueError("mu 参数必须为正数")

        self.bits = bits
        self.mu = mu
        self.vmin = vmin
        self.vmax = vmax
        self.levels = 2 ** bits
        self.uniform = UniformQuantizer(bits, vmin, vmax)

    def compress(self, signal: np.ndarray) -> np.ndarray:
        """mu律压缩

        y = sign(x) * ln(1 + mu*|x|) / ln(1 + mu)

        Parameters
        ----------
        signal : np.ndarray
            输入信号 (归一化到 [-1, 1])

        Returns
        -------
        np.ndarray
            压缩后的信号
        """
        normalized = (signal - self.vmin) / (self.vmax - self.vmin) * 2 - 1
        compressed = np.sign(normalized) * np.log(1 + self.mu * np.abs(normalized)) / np.log(1 + self.mu)
        return (compressed + 1) / 2 * (self.vmax - self.vmin) + self.vmin

    def expand(self, signal: np.ndarray) -> np.ndarray:
        """mu律扩展 (解压缩)

        x = sign(y) * (1/mu) * ((1+mu)^|y| - 1)

        Parameters
        ----------
        signal : np.ndarray
            压缩后的信号

        Returns
        -------
        np.ndarray
            扩展后的信号
        """
        normalized = (signal - self.vmin) / (self.vmax - self.vmin) * 2 - 1
        expanded = np.sign(normalized) * (1.0 / self.mu) * (
            (1 + self.mu) ** np.abs(normalized) - 1
        )
        return (expanded + 1) / 2 * (self.vmax - self.vmin) + self.vmin

    def quantize(self, signal: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """非均匀量化

        Parameters
        ----------
        signal : np.ndarray
            输入信号

        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            (量化值, 量化索引)
        """
        compressed = self.compress(signal)
        quantized, indices = self.uniform.quantize(compressed)
        result = self.expand(quantized)
        return result, indices

    def sqnr(self, signal: np.ndarray) -> float:
        """计算 SQNR

        Parameters
        ----------
        signal : np.ndarray
            输入信号

        Returns
        -------
        float
            SQNR (dB)
        """
        quantized, _ = self.quantize(signal)
        noise = signal - quantized

        signal_power = np.mean(signal ** 2)
        noise_power = np.mean(noise ** 2)

        if noise_power == 0:
            return float('inf')

        return 10.0 * np.log10(signal_power / noise_power)


def mu_law_quantizer(
    signal: np.ndarray,
    bits: int,
    mu: float = 255.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """mu律量化 (便捷函数)

    Parameters
    ----------
    signal : np.ndarray
        输入信号
    bits : int
        量化位数
    mu : float
        mu律压缩参数

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        (量化值, 量化索引)
    """
    vmin, vmax = signal.min(), signal.max()
    if vmin == vmax:
        vmax = vmin + 1.0
    quantizer = NonUniformQuantizer(bits, mu, vmin, vmax)
    return quantizer.quantize(signal)


def a_law_quantizer(
    signal: np.ndarray,
    bits: int,
    a: float = 87.6,
) -> Tuple[np.ndarray, np.ndarray]:
    """A律量化

    Parameters
    ----------
    signal : np.ndarray
        输入信号
    bits : int
        量化位数
    a : float
        A律压缩参数

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        (量化值, 量化索引)
    """
    vmin, vmax = signal.min(), signal.max()
    if vmin == vmax:
        vmax = vmin + 1.0

    # A律压缩
    normalized = (signal - vmin) / (vmax - vmin)
    compressed = np.where(
        normalized < 1.0 / a,
        a * normalized / (1 + np.log(a)),
        (1 + np.log(a * normalized)) / (1 + np.log(a)),
    )

    # 均匀量化
    quantizer = UniformQuantizer(bits, 0, 1)
    quantized, indices = quantizer.quantize(compressed)

    # A律扩展
    expanded = np.where(
        quantized < 1.0 / (1 + np.log(a)),
        quantized * (1 + np.log(a)) / a,
        np.exp(quantized * (1 + np.log(a)) - 1) / a,
    )

    result = expanded * (vmax - vmin) + vmin
    return result, indices


def snr_quantization(
    signal: np.ndarray,
    bits_range: range,
    quantizer_type: str = 'uniform',
) -> Tuple[np.ndarray, np.ndarray]:
    """分析不同量化位数的 SQNR

    Parameters
    ----------
    signal : np.ndarray
        输入信号
    bits_range : range
        量化位数范围
    quantizer_type : str
        量化类型: 'uniform' 或 'mu_law'

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        (量化位数数组, SQNR 数组)
    """
    bits_arr = np.array(list(bits_range))
    sqnr_arr = np.zeros(len(bits_arr))

    for i, b in enumerate(bits_arr):
        if quantizer_type == 'uniform':
            vmin, vmax = signal.min(), signal.max()
            if vmin == vmax:
                vmax = vmin + 1.0
            quantizer = UniformQuantizer(b, vmin, vmax)
            sqnr_arr[i] = quantizer.sqnr(signal)
        elif quantizer_type == 'mu_law':
            vmin, vmax = signal.min(), signal.max()
            if vmin == vmax:
                vmax = vmin + 1.0
            quantizer = NonUniformQuantizer(b, mu=255.0, vmin=vmin, vmax=vmax)
            sqnr_arr[i] = quantizer.sqnr(signal)

    return bits_arr, sqnr_arr
