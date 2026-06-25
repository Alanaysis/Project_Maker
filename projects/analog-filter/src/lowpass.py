"""
模拟低通滤波器实现
====================

实现 RC 低通和 RL 低通滤波器，支持频率响应计算。

低通滤波器允许低频信号通过，衰减高频信号。

传递函数:
- RC 低通: H(s) = 1 / (1 + sRC)
- RL 低通: H(s) = (R/L) / (s + R/L)

截止频率:
- RC 低通: fc = 1 / (2π * R * C)
- RL 低通: fc = R / (2π * L)
"""

import numpy as np
from typing import Tuple


class RCLowPass:
    """RC 低通滤波器

    电路结构: 输入 → R → 输出 → C → 地
    传递函数: H(s) = 1 / (1 + sRC)

    Parameters
    ----------
    R : float
        电阻值 (欧姆)
    C : float
        电容值 (法拉)
    """

    def __init__(self, R: float, C: float):
        if R <= 0:
            raise ValueError("电阻值 R 必须为正数")
        if C <= 0:
            raise ValueError("电容值 C 必须为正数")

        self.R = R
        self.C = C
        self.tau = R * C  # 时间常数
        self.fc = 1.0 / (2.0 * np.pi * self.tau)  # 截止频率

    def transfer_function(self, f: np.ndarray) -> np.ndarray:
        """计算传递函数 H(jω)

        Parameters
        ----------
        f : np.ndarray
            频率数组 (Hz)

        Returns
        -------
        np.ndarray
            复数传递函数值
        """
        omega = 2.0 * np.pi * f
        s = 1j * omega
        return 1.0 / (1.0 + s * self.tau)

    def magnitude(self, f: np.ndarray) -> np.ndarray:
        """计算幅频响应 (线性值)

        Parameters
        ----------
        f : np.ndarray
            频率数组 (Hz)

        Returns
        -------
        np.ndarray
            幅度响应 (线性)
        """
        return np.abs(self.transfer_function(f))

    def magnitude_db(self, f: np.ndarray) -> np.ndarray:
        """计算幅频响应 (dB)

        Parameters
        ----------
        f : np.ndarray
            频率数组 (Hz)

        Returns
        -------
        np.ndarray
            幅度响应 (dB)
        """
        mag = self.magnitude(f)
        return 20.0 * np.log10(np.maximum(mag, 1e-30))

    def phase(self, f: np.ndarray) -> np.ndarray:
        """计算相频响应 (度)

        Parameters
        ----------
        f : np.ndarray
            频率数组 (Hz)

        Returns
        -------
        np.ndarray
            相位响应 (度)
        """
        H = self.transfer_function(f)
        return np.degrees(np.angle(H))

    def group_delay(self, f: np.ndarray) -> np.ndarray:
        """计算群延迟

        Parameters
        ----------
        f : np.ndarray
            频率数组 (Hz)

        Returns
        -------
        np.ndarray
            群延迟 (秒)
        """
        # 群延迟 = -dφ/dω
        omega = 2.0 * np.pi * f
        return self.tau / (1.0 + (omega * self.tau) ** 2)

    def step_response(self, t: np.ndarray) -> np.ndarray:
        """计算阶跃响应

        Parameters
        ----------
        t : np.ndarray
            时间数组 (秒)

        Returns
        -------
        np.ndarray
            阶跃响应值
        """
        return 1.0 - np.exp(-t / self.tau)

    def impulse_response(self, t: np.ndarray) -> np.ndarray:
        """计算冲激响应

        Parameters
        ----------
        t : np.ndarray
            时间数组 (秒)

        Returns
        -------
        np.ndarray
            冲激响应值
        """
        return (1.0 / self.tau) * np.exp(-t / self.tau) * (t >= 0)

    def __repr__(self) -> str:
        return (
            f"RCLowPass(R={self.R}Ω, C={self.C}F, "
            f"τ={self.tau:.6e}s, fc={self.fc:.2f}Hz)"
        )


class RLLowPass:
    """RL 低通滤波器

    电路结构: 输入 → R → 输出, L → 地
    传递函数: H(s) = (R/L) / (s + R/L)

    Parameters
    ----------
    R : float
        电阻值 (欧姆)
    L : float
        电感值 (亨利)
    """

    def __init__(self, R: float, L: float):
        if R <= 0:
            raise ValueError("电阻值 R 必须为正数")
        if L <= 0:
            raise ValueError("电感值 L 必须为正数")

        self.R = R
        self.L = L
        self.tau = L / R  # 时间常数
        self.fc = R / (2.0 * np.pi * L)  # 截止频率

    def transfer_function(self, f: np.ndarray) -> np.ndarray:
        """计算传递函数 H(jω)

        Parameters
        ----------
        f : np.ndarray
            频率数组 (Hz)

        Returns
        -------
        np.ndarray
            复数传递函数值
        """
        omega = 2.0 * np.pi * f
        s = 1j * omega
        return (self.R / self.L) / (s + self.R / self.L)

    def magnitude(self, f: np.ndarray) -> np.ndarray:
        """计算幅频响应 (线性值)"""
        return np.abs(self.transfer_function(f))

    def magnitude_db(self, f: np.ndarray) -> np.ndarray:
        """计算幅频响应 (dB)"""
        mag = self.magnitude(f)
        return 20.0 * np.log10(np.maximum(mag, 1e-30))

    def phase(self, f: np.ndarray) -> np.ndarray:
        """计算相频响应 (度)"""
        H = self.transfer_function(f)
        return np.degrees(np.angle(H))

    def step_response(self, t: np.ndarray) -> np.ndarray:
        """计算阶跃响应"""
        return 1.0 - np.exp(-t / self.tau)

    def impulse_response(self, t: np.ndarray) -> np.ndarray:
        """计算冲激响应"""
        return (1.0 / self.tau) * np.exp(-t / self.tau) * (t >= 0)

    def __repr__(self) -> str:
        return (
            f"RLLowPass(R={self.R}Ω, L={self.L}H, "
            f"τ={self.tau:.6e}s, fc={self.fc:.2f}Hz)"
        )
