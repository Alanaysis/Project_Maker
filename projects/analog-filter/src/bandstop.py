"""
RLC 带阻滤波器实现
====================

带阻滤波器（陷波滤波器）衰减特定频率范围内的信号，允许该范围外的信号通过。

传递函数: H(s) = (s² + 1/LC) / (s² + s/RC + 1/LC)

中心频率: f0 = 1 / (2π√(LC))
带宽: BW = 1 / (2πRC)  (单位: Hz)
品质因数: Q = f0 / BW = (1/R) * √(L/C)
"""

import numpy as np


class RLCBandStop:
    """RLC 带阻滤波器 (陷波滤波器)

    电路结构: LC 串联谐振电路与负载并联
    传递函数: H(s) = (s² + 1/LC) / (s² + s/RC + 1/LC)

    Parameters
    ----------
    R : float
        电阻值 (欧姆)
    L : float
        电感值 (亨利)
    C : float
        电容值 (法拉)
    """

    def __init__(self, R: float, L: float, C: float):
        if R <= 0:
            raise ValueError("电阻值 R 必须为正数")
        if L <= 0:
            raise ValueError("电感值 L 必须为正数")
        if C <= 0:
            raise ValueError("电容值 C 必须为正数")

        self.R = R
        self.L = L
        self.C = C

        # 中心频率 (Hz)
        self.f0 = 1.0 / (2.0 * np.pi * np.sqrt(L * C))
        self.omega0 = 1.0 / np.sqrt(L * C)

        # 带宽 (Hz)
        self.bw = 1.0 / (2.0 * np.pi * R * C)
        self.bw_rad = 1.0 / (R * C)

        # 品质因数
        self.Q = self.omega0 * R * C

    def transfer_function(self, f: np.ndarray) -> np.ndarray:
        """计算传递函数 H(jω)

        H(s) = (s² + 1/LC) / (s² + s/RC + 1/LC)

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

        numerator = s ** 2 + 1.0 / (self.L * self.C)
        denominator = s ** 2 + s / (self.R * self.C) + 1.0 / (self.L * self.C)

        return numerator / denominator

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

    def lower_cutoff(self) -> float:
        """计算下截止频率 (Hz)"""
        return self.f0 * (np.sqrt(1.0 + 1.0 / (4.0 * self.Q ** 2)) - 1.0 / (2.0 * self.Q))

    def upper_cutoff(self) -> float:
        """计算上截止频率 (Hz)"""
        return self.f0 * (np.sqrt(1.0 + 1.0 / (4.0 * self.Q ** 2)) + 1.0 / (2.0 * self.Q))

    def step_response(self, t: np.ndarray) -> np.ndarray:
        """计算阶跃响应 (数值积分)"""
        dt = t[1] - t[0] if len(t) > 1 else 1e-6
        impulse = self.impulse_response(t)
        return np.cumsum(impulse) * dt

    def impulse_response(self, t: np.ndarray) -> np.ndarray:
        """计算冲激响应

        对于欠阻尼情况 (Q > 0.5):
        h(t) = δ(t) - (ω0/Q) * exp(-ω0t/(2Q)) * sin(ωd*t) * u(t)
        这里只返回连续部分。

        Parameters
        ----------
        t : np.ndarray
            时间数组 (秒)

        Returns
        -------
        np.ndarray
            冲激响应的连续部分
        """
        alpha = self.omega0 / (2.0 * self.Q)

        if self.Q > 0.5:
            omega_d = self.omega0 * np.sqrt(1.0 - 1.0 / (4.0 * self.Q ** 2))
            return -(self.omega0 / self.Q) * np.exp(-alpha * t) * np.sin(omega_d * t) * (t >= 0)
        elif self.Q == 0.5:
            return -(self.omega0 ** 2) * t * np.exp(-alpha * t) * (t >= 0)
        else:
            gamma = alpha * np.sqrt(1.0 - 1.0 / (4.0 * self.Q ** 2))
            return -(self.omega0 / (self.Q * gamma)) * np.exp(-alpha * t) * np.sinh(gamma * t) * (t >= 0)

    def __repr__(self) -> str:
        return (
            f"RLCBandStop(R={self.R}Ω, L={self.L}H, C={self.C}F, "
            f"f0={self.f0:.2f}Hz, BW={self.bw:.2f}Hz, Q={self.Q:.2f})"
        )
