"""
热源建模模块

热源是热传导问题中的重要组成部分，描述了系统内部的热量产生。

热源类型：
1. 均匀热源: Q(x,y,z,t) = constant
2. 空间分布热源: Q(x,y,z,t) = f(x,y,z)
3. 时间变化热源: Q(x,y,z,t) = f(t)
4. 非线性热源: Q 依赖于温度 T
"""

import numpy as np
from typing import Callable, Optional


class HeatSource:
    """热源基类"""

    def evaluate(self, x: float, y: float = 0.0, t: float = 0.0, T: float = 0.0) -> float:
        raise NotImplementedError


class UniformHeatSource(HeatSource):
    """
    均匀热源

    在整个计算域内产生恒定的热功率密度。

    示例
    ----
    >>> source = UniformHeatSource(q=1000.0)  # 1000 W/m³
    """

    def __init__(self, q: float):
        """
        参数
        ----
        q : float
            热功率密度 (W/m³)
        """
        self.q = q

    def evaluate(self, x: float, y: float = 0.0, t: float = 0.0, T: float = 0.0) -> float:
        return self.q


class PointHeatSource(HeatSource):
    """
    点热源 (近似)

    在特定位置附近产生高热量，用高斯函数近似。

    Q(x) = Q0 * exp(-|x - x0|² / (2σ²))

    参数
    ----
    Q0 : float
        峰值热功率密度 (W/m³)
    center : tuple
        热源中心位置 (x0, y0)
    sigma : float
        热源分布宽度 (m)
    """

    def __init__(self, Q0: float, center: tuple = (0.0, 0.0), sigma: float = 0.01):
        self.Q0 = Q0
        self.x0, self.y0 = center
        self.sigma = sigma

    def evaluate(self, x: float, y: float = 0.0, t: float = 0.0, T: float = 0.0) -> float:
        r2 = (x - self.x0) ** 2 + (y - self.y0) ** 2
        return self.Q0 * np.exp(-r2 / (2 * self.sigma ** 2))


class TimeVaryingHeatSource(HeatSource):
    """
    时变热源

    热源强度随时间变化，可用于模拟周期性加热或脉冲加热。

    Q(t) = Q_base + Q_amp * f(t)

    参数
    ----
    Q_base : float
        基础热功率密度 (W/m³)
    Q_amp : float
        振幅 (W/m³)
    frequency : float
        频率 (Hz), 用于正弦变化
    func : callable, optional
        自定义时间函数 f(t) -> 系数
    """

    def __init__(
        self,
        Q_base: float,
        Q_amp: float,
        frequency: float = 0.0,
        func: Optional[Callable[[float], float]] = None,
    ):
        self.Q_base = Q_base
        self.Q_amp = Q_amp
        self.frequency = frequency
        self.func = func

    def evaluate(self, x: float, y: float = 0.0, t: float = 0.0, T: float = 0.0) -> float:
        if self.func:
            coeff = self.func(t)
        elif self.frequency > 0:
            coeff = np.sin(2 * np.pi * self.frequency * t)
        else:
            coeff = 0.0
        return self.Q_base + self.Q_amp * coeff


class TemperatureDependentSource(HeatSource):
    """
    温度依赖热源

    热源强度依赖于局部温度，用于模拟非线性热效应。

    Q(T) = Q0 * (1 + β * (T - T_ref))

    其中 β 是温度系数。

    参数
    ----
    Q0 : float
        参考温度下的热功率密度 (W/m³)
    beta : float
        温度系数 (1/K)
    T_ref : float
        参考温度 (°C)
    """

    def __init__(self, Q0: float, beta: float = 0.0, T_ref: float = 0.0):
        self.Q0 = Q0
        self.beta = beta
        self.T_ref = T_ref

    def evaluate(self, x: float, y: float = 0.0, t: float = 0.0, T: float = 0.0) -> float:
        return self.Q0 * (1 + self.beta * (T - self.T_ref))


def get_heat_source_function(source: Optional[HeatSource]) -> Optional[Callable]:
    """
    将 HeatSource 对象转换为可调用函数

    用于与 heat_conduction 模块集成。
    """
    if source is None:
        return None

    def wrapper_1d(x: float) -> float:
        return source.evaluate(x=x)

    def wrapper_2d(x: float, y: float) -> float:
        return source.evaluate(x=x, y=y)

    return wrapper_1d if hasattr(source, "evaluate") else None
