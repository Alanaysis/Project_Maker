"""
RLC 带通滤波器实现
====================

带通滤波器允许特定频率范围内的信号通过，衰减该范围外的信号。

传递函数: H(s) = (s/RC) / (s² + s/RC + 1/LC)

中心频率: f0 = 1 / (2π√(LC))
带宽: BW = 1 / (RC)  (单位: rad/s)
品质因数: Q = f0 / BW = (1/R) * √(L/C)
"""

import numpy as np


class RLCBandPass:
    """RLC 带通滤波器 (串联 RLC 电路)

    电路结构: 串联 RLC，输出取自 R 两端
    传递函数: H(s) = (s/RC) / (s² + s/RC + 1/LC)

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
        self.omega0 = 1.0 / np.sqrt(L * C)  # 中心角频率 (rad/s)

        # 带宽 (Hz)
        self.bw = 1.0 / (2.0 * np.pi * R * C)
        self.bw_rad = 1.0 / (R * C)  # 带宽 (rad/s)

        # 品质因数
        self.Q = self.omega0 * R * C  # Q = (1/R) * sqrt(L/C)

    def transfer_function(self, f: np.ndarray) -> np.ndarray:
        """计算传递函数 H(jω)

        H(s) = (s/RC) / (s² + s/RC + 1/LC)

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

        numerator = s / (self.R * self.C)
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
        """计算下截止频率 (Hz)

        Returns
        -------
        float
            下截止频率
        """
        return self.f0 * (np.sqrt(1.0 + 1.0 / (4.0 * self.Q ** 2)) - 1.0 / (2.0 * self.Q))

    def upper_cutoff(self) -> float:
        """计算上截止频率 (Hz)

        Returns
        -------
        float
            上截止频率
        """
        return self.f0 * (np.sqrt(1.0 + 1.0 / (4.0 * self.Q ** 2)) + 1.0 / (2.0 * self.Q))

    def step_response(self, t: np.ndarray) -> np.ndarray:
        """计算阶跃响应 (数值积分)

        Parameters
        ----------
        t : np.ndarray
            时间数组 (秒)

        Returns
        -------
        np.ndarray
            阶跃响应值
        """
        # 使用数值方法计算阶跃响应 (卷积冲激响应)
        dt = t[1] - t[0] if len(t) > 1 else 1e-6
        impulse = self.impulse_response(t)
        step = np.cumsum(impulse) * dt
        return step

    def impulse_response(self, t: np.ndarray) -> np.ndarray:
        """计算冲激响应

        对于欠阻尼情况 (Q > 0.5):
        h(t) = (ω0/Q) * exp(-ω0t/(2Q)) * sin(ωd*t) * u(t)
        其中 ωd = ω0 * sqrt(1 - 1/(4Q²))

        Parameters
        ----------
        t : np.ndarray
            时间数组 (秒)

        Returns
        -------
        np.ndarray
            冲激响应值
        """
        alpha = self.omega0 / (2.0 * self.Q)

        if self.Q > 0.5:
            # 欠阻尼
            omega_d = self.omega0 * np.sqrt(1.0 - 1.0 / (4.0 * self.Q ** 2))
            return (self.omega0 / self.Q) * np.exp(-alpha * t) * np.sin(omega_d * t) * (t >= 0)
        elif self.Q == 0.5:
            # 临界阻尼
            return (self.omega0 ** 2) * t * np.exp(-alpha * t) * (t >= 0)
        else:
            # 过阻尼
            gamma = alpha * np.sqrt(1.0 - 1.0 / (4.0 * self.Q ** 2))
            return (self.omega0 / (self.Q * gamma)) * np.exp(-alpha * t) * np.sinh(gamma * t) * (t >= 0)

    def __repr__(self) -> str:
        return (
            f"RLCBandPass(R={self.R}Ω, L={self.L}H, C={self.C}F, "
            f"f0={self.f0:.2f}Hz, BW={self.bw:.2f}Hz, Q={self.Q:.2f})"
        )
