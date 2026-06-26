"""
边界条件模块

热传导问题中，边界条件决定了问题的适定性。三类基本边界条件：

1. Dirichlet 边界 (第一类): 指定边界上的温度值
   T|_boundary = T_specified

2. Neumann 边界 (第二类): 指定边界上的热流密度
   -k ∂T/∂n|_boundary = q_specified

3. Robin 边界 (第三类/混合): 指定对流换热条件
   -k ∂T/∂n|_boundary = h(T - T_inf)

其中:
    k  - 热导率 (W/(m·K))
    h  - 对流换热系数 (W/(m²·K))
    T_inf - 环境温度 (°C)
    n  - 边界法向
"""

import numpy as np
from typing import Callable, Optional


class BoundaryCondition:
    """边界条件基类"""

    def apply(self, T: np.ndarray, boundary: str, **kwargs) -> np.ndarray:
        raise NotImplementedError


class DirichletBC(BoundaryCondition):
    """
    Dirichlet 边界条件 (第一类边界条件)

    直接指定边界上的温度值。

    示例
    ----
    >>> bc = DirichletBC(value=100.0)
    >>> T = bc.apply_1d(T, direction='left')
    """

    def __init__(self, value: float):
        self.value = value

    def apply_1d(self, T: np.ndarray, direction: str) -> np.ndarray:
        """在一维网格上应用 Dirichlet 边界条件"""
        T = T.copy()
        if direction == "left":
            T[0] = self.value
        elif direction == "right":
            T[-1] = self.value
        else:
            raise ValueError(f"未知方向: {direction}")
        return T

    def apply_2d(self, T: np.ndarray, direction: str) -> np.ndarray:
        """在二维网格上应用 Dirichlet 边界条件"""
        T = T.copy()
        if direction == "bottom":
            T[0, :] = self.value
        elif direction == "top":
            T[-1, :] = self.value
        elif direction == "left":
            T[:, 0] = self.value
        elif direction == "right":
            T[:, -1] = self.value
        else:
            raise ValueError(f"未知方向: {direction}")
        return T


class NeumannBC(BoundaryCondition):
    """
    Neumann 边界条件 (第二类边界条件)

    指定边界上的热流密度 q (W/m²):
        -k ∂T/∂n = q

    当 q = 0 时，表示绝热边界 (无热流通过)。

    参数
    ----
    flux : float
        热流密度 (W/m²). 正值表示热量流出。
    thermal_conductivity : float
        热导率 (W/(m·K))
    """

    def __init__(self, flux: float, thermal_conductivity: float):
        self.flux = flux
        self.k = thermal_conductivity

    def apply_1d(self, T: np.ndarray, dx: float, direction: str) -> np.ndarray:
        """
        在一维网格上使用单侧差分近似 Neumann 边界条件

        使用一阶后向/前向差分:
            ∂T/∂x ≈ (T_1 - T_0) / dx   (左边界)
            ∂T/∂x ≈ (T_{-1} - T_{-2}) / dx  (右边界)
        """
        T = T.copy()
        if direction == "left":
            # -k * (T[1] - T[0]) / dx = q
            # T[0] = T[1] + q * dx / k
            T[0] = T[1] + self.flux * dx / self.k
        elif direction == "right":
            # -k * (T[-1] - T[-2]) / dx = q
            # T[-1] = T[-2] - q * dx / k
            T[-1] = T[-2] - self.flux * dx / self.k
        else:
            raise ValueError(f"未知方向: {direction}")
        return T

    def apply_2d(self, T: np.ndarray, dx: float, dy: float, direction: str) -> np.ndarray:
        """在二维网格上应用 Neumann 边界条件"""
        T = T.copy()
        if direction == "bottom":
            T[0, :] = T[1, :] + self.flux * dy / self.k
        elif direction == "top":
            T[-1, :] = T[-2, :] - self.flux * dy / self.k
        elif direction == "left":
            T[:, 0] = T[:, 1] + self.flux * dx / self.k
        elif direction == "right":
            T[:, -1] = T[:, -2] - self.flux * dx / self.k
        else:
            raise ValueError(f"未知方向: {direction}")
        return T


class RobinBC(BoundaryCondition):
    """
    Robin 边界条件 (第三类/对流边界条件)

    描述对流换热:
        -k ∂T/∂n = h(T - T_inf)

    其中 h 是对流换热系数，T_inf 是环境温度。

    结合 Dirichlet 和 Neumann 边界条件:
        - 当 h → 0: 退化为 Neumann 边界 (绝热)
        - 当 h → ∞: 退化为 Dirichlet 边界 (T = T_inf)

    参数
    ----
    heat_transfer_coefficient : float
        对流换热系数 h (W/(m²·K))
    ambient_temperature : float
        环境温度 T_inf (°C)
    thermal_conductivity : float
        热导率 k (W/(m·K))
    """

    def __init__(
        self,
        heat_transfer_coefficient: float,
        ambient_temperature: float,
        thermal_conductivity: float,
    ):
        self.h = heat_transfer_coefficient
        self.T_inf = ambient_temperature
        self.k = thermal_conductivity

    def apply_1d(self, T: np.ndarray, dx: float, direction: str) -> np.ndarray:
        """
        在一维网格上应用 Robin 边界条件

        推导:
            -k * (T_boundary - T_internal) / dx = h * (T_boundary - T_inf)
            解出 T_boundary:
            T_boundary = (k * T_internal + h * dx * T_inf) / (k + h * dx)
        """
        T = T.copy()
        if direction == "left":
            T[0] = (self.k * T[1] + self.h * dx * self.T_inf) / (self.k + self.h * dx)
        elif direction == "right":
            T[-1] = (self.k * T[-2] + self.h * dx * self.T_inf) / (self.k + self.h * dx)
        else:
            raise ValueError(f"未知方向: {direction}")
        return T

    def apply_2d(self, T: np.ndarray, dx: float, dy: float, direction: str) -> np.ndarray:
        """在二维网格上应用 Robin 边界条件"""
        T = T.copy()
        if direction == "bottom":
            T[0, :] = (self.k * T[1, :] + self.h * dy * self.T_inf) / (self.k + self.h * dy)
        elif direction == "top":
            T[-1, :] = (self.k * T[-2, :] + self.h * dy * self.T_inf) / (self.k + self.h * dy)
        elif direction == "left":
            T[:, 0] = (self.k * T[:, 1] + self.h * dx * self.T_inf) / (self.k + self.h * dx)
        elif direction == "right":
            T[:, -1] = (self.k * T[:, -2] + self.h * dx * self.T_inf) / (self.k + self.h * dx)
        else:
            raise ValueError(f"未知方向: {direction}")
        return T


def apply_boundary_conditions_1d(
    T: np.ndarray,
    left_bc: Optional[BoundaryCondition] = None,
    right_bc: Optional[BoundaryCondition] = None,
    dx: float = 1.0,
) -> np.ndarray:
    """
    便捷函数: 在一维网格上应用边界条件

    参数
    ----------
    T : np.ndarray
        温度数组
    left_bc, right_bc : BoundaryCondition, optional
        左右边界条件
    dx : float
        空间步长

    返回
    -------
    T : np.ndarray
        更新后的温度数组
    """
    if left_bc:
        T = left_bc.apply_1d(T, dx=dx, direction="left")
    if right_bc:
        T = right_bc.apply_1d(T, dx=dx, direction="right")
    return T


def apply_boundary_conditions_2d(
    T: np.ndarray,
    bottom_bc: Optional[BoundaryCondition] = None,
    top_bc: Optional[BoundaryCondition] = None,
    left_bc: Optional[BoundaryCondition] = None,
    right_bc: Optional[BoundaryCondition] = None,
    dx: float = 1.0,
    dy: float = 1.0,
) -> np.ndarray:
    """
    便捷函数: 在二维网格上应用边界条件
    """
    if bottom_bc:
        T = bottom_bc.apply_2d(T, dx=dx, dy=dy, direction="bottom")
    if top_bc:
        T = top_bc.apply_2d(T, dx=dx, dy=dy, direction="top")
    if left_bc:
        T = left_bc.apply_2d(T, dx=dx, dy=dy, direction="left")
    if right_bc:
        T = right_bc.apply_2d(T, dx=dx, dy=dy, direction="right")
    return T
