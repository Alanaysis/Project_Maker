"""
线性贝塞尔曲线 (Linear Bezier Curve)
=====================================

线性贝塞尔曲线是最简单的贝塞尔曲线，由两个控制点定义。
它在两个控制点之间进行线性插值。

数学公式:
    B(t) = (1 - t) * P0 + t * P1,  t ∈ [0, 1]

其中:
    P0, P1: 控制点
    t: 参数，范围 [0, 1]

可视化:
    P0 --------- P1
    (起点)       (终点)

线性贝塞尔曲线退化为一条直线段。
"""

from __future__ import annotations

import numpy as np
from typing import List, Tuple


def linear_bezier(P0: np.ndarray, P1: np.ndarray, t: float) -> np.ndarray:
    """
    计算线性贝塞尔曲线在参数 t 处的点。

    参数:
        P0: 起点，形状为 (2,) 的 numpy 数组 [x, y]
        P1: 终点，形状为 (2,) 的 numpy 数组 [x, y]
        t: 参数，范围 [0, 1]

    返回:
        曲线上的点，形状为 (2,) 的 numpy 数组 [x, y]

    示例:
        >>> P0 = np.array([0.0, 0.0])
        >>> P1 = np.array([1.0, 1.0])
        >>> linear_bezier(P0, P1, 0.5)
        array([0.5, 0.5])
    """
    if not (0.0 <= t <= 1.0):
        raise ValueError(f"参数 t 必须在 [0, 1] 范围内，收到 t={t}")

    P0 = np.asarray(P0, dtype=float)
    P1 = np.asarray(P1, dtype=float)

    # 线性插值公式: B(t) = (1-t)*P0 + t*P1
    return (1.0 - t) * P0 + t * P1


def linear_bezier_points(P0: np.ndarray, P1: np.ndarray, num_samples: int = 100) -> np.ndarray:
    """
    计算线性贝塞尔曲线上的多个采样点。

    参数:
        P0: 起点，形状为 (2,) 的 numpy 数组 [x, y]
        P1: 终点，形状为 (2,) 的 numpy 数组 [x, y]
        num_samples: 采样点数量

    返回:
        采样点数组，形状为 (num_samples, 2)
    """
    P0 = np.asarray(P0, dtype=float)
    P1 = np.asarray(P1, dtype=float)

    t_values = np.linspace(0.0, 1.0, num_samples)

    # 批量计算: (num_samples, 2) = (num_samples, 1) * P0 + (num_samples, 1) * P1
    t_col = t_values.reshape(-1, 1)
    return (1.0 - t_col) * P0 + t_col * P1


def linear_bezier_derivative(P0: np.ndarray, P1: np.ndarray) -> np.ndarray:
    """
    计算线性贝塞尔曲线的导数（恒为常数向量）。

    导数公式:
        B'(t) = P1 - P0

    参数:
        P0: 起点
        P1: 终点

    返回:
        导数向量，形状为 (2,)
    """
    P0 = np.asarray(P0, dtype=float)
    P1 = np.asarray(P1, dtype=float)
    return P1 - P0


def linear_bezier_from_angle(angle_degrees: float, length: float, origin: np.ndarray = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    从角度和长度生成线性贝塞尔曲线的两个控制点。

    参数:
        angle_degrees: 角度（度）
        length: 线段长度
        origin: 起点，默认为原点

    返回:
        (P0, P1) 元组
    """
    if origin is None:
        origin = np.array([0.0, 0.0])
    else:
        origin = np.asarray(origin, dtype=float)

    angle_rad = np.radians(angle_degrees)
    P1 = origin + np.array([length * np.cos(angle_rad), length * np.sin(angle_rad)])
    return origin, P1
