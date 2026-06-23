"""
FFT 模块 - 快速傅里叶变换实现

实现 Cooley-Tukey FFT 算法，用于音频信号的频域分析和处理。
"""

import numpy as np
from typing import Union


class FFT:
    """快速傅里叶变换 (Fast Fourier Transform)

    实现 Cooley-Tukey 基2 FFT 算法，将时域信号转换为频域表示。

    算法原理:
    1. 将 N 点 DFT 分解为两个 N/2 点 DFT（偶数项和奇数项）
    2. 递归分解直到达到基础情况（N=1）
    3. 通过蝶形运算合并结果

    时间复杂度: O(N log N)
    空间复杂度: O(N)
    """

    @staticmethod
    def transform(x: np.ndarray) -> np.ndarray:
        """执行 FFT 变换

        Args:
            x: 输入时域信号（复数数组）

        Returns:
            频域表示（复数数组）

        Raises:
            ValueError: 输入不是 numpy 数组或为空
        """
        if not isinstance(x, np.ndarray):
            raise ValueError("输入必须是 numpy 数组")
        if len(x) == 0:
            raise ValueError("输入数组不能为空")

        N = len(x)

        # 基础情况
        if N == 1:
            return x.copy()

        # 确保长度为2的幂次（零填充）
        if N & (N - 1) != 0:
            next_power = 1
            while next_power < N:
                next_power <<= 1
            x = np.pad(x, (0, next_power - N), mode='constant')
            N = next_power

        # Cooley-Tukey FFT 算法
        return FFT._fft_recursive(x)

    @staticmethod
    def _fft_recursive(x: np.ndarray) -> np.ndarray:
        """递归实现 FFT

        Args:
            x: 输入信号（长度必须为2的幂次）

        Returns:
            FFT 结果
        """
        N = len(x)

        # 基础情况
        if N == 1:
            return x.copy()

        # 分治：分离偶数项和奇数项
        even = FFT._fft_recursive(x[0::2])
        odd = FFT._fft_recursive(x[1::2])

        # 蝶形运算
        # 旋转因子: W_N^k = e^(-2πi*k/N)
        T = np.exp(-2j * np.pi * np.arange(N // 2) / N) * odd

        # 合并结果
        result = np.zeros(N, dtype=complex)
        result[:N // 2] = even + T
        result[N // 2:] = even - T

        return result

    @staticmethod
    def magnitude_spectrum(x: np.ndarray) -> np.ndarray:
        """计算幅度谱

        Args:
            x: 输入时域信号

        Returns:
            幅度谱（仅正频率部分）
        """
        X = FFT.transform(x)
        N = len(X)
        # 取单边谱，并归一化
        magnitude = np.abs(X[:N // 2]) * 2.0 / N
        magnitude[0] /= 2.0  # DC 分量不需要乘以2
        return magnitude

    @staticmethod
    def power_spectrum(x: np.ndarray) -> np.ndarray:
        """计算功率谱

        Args:
            x: 输入时域信号

        Returns:
            功率谱密度
        """
        X = FFT.transform(x)
        N = len(X)
        power = np.abs(X[:N // 2]) ** 2 / (N ** 2)
        return power

    @staticmethod
    def phase_spectrum(x: np.ndarray) -> np.ndarray:
        """计算相位谱

        Args:
            x: 输入时域信号

        Returns:
            相位谱（弧度）
        """
        X = FFT.transform(x)
        return np.angle(X)


class IFFT:
    """逆快速傅里叶变换 (Inverse FFT)

    将频域信号转换回时域。
    """

    @staticmethod
    def transform(X: np.ndarray) -> np.ndarray:
        """执行逆 FFT 变换

        Args:
            X: 输入频域信号（复数数组）

        Returns:
            时域表示（复数数组）

        Raises:
            ValueError: 输入不是 numpy 数组或为空
        """
        if not isinstance(X, np.ndarray):
            raise ValueError("输入必须是 numpy 数组")
        if len(X) == 0:
            raise ValueError("输入数组不能为空")

        N = len(X)

        # 基础情况
        if N == 1:
            return X.copy()

        # 确保长度为2的幂次
        if N & (N - 1) != 0:
            next_power = 1
            while next_power < N:
                next_power <<= 1
            X = np.pad(X, (0, next_power - N), mode='constant')
            N = next_power

        # IFFT = (1/N) * conj(FFT(conj(X)))
        return np.conj(FFT.transform(np.conj(X))) / N

    @staticmethod
    def transform_real(X: np.ndarray) -> np.ndarray:
        """执行逆 FFT 并返回实部

        Args:
            X: 输入频域信号

        Returns:
            时域实数信号
        """
        return np.real(IFFT.transform(X))
