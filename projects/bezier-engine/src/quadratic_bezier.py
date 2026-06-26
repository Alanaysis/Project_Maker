"""
二次贝塞尔曲线 (Quadratic Bezier Curve)
========================================

二次贝塞尔曲线由三个控制点定义：起点、控制点（中间点）、终点。
控制点像磁铁一样"拉"曲线靠近自己。

数学公式:
    B(t) = (1-t)² * P0 + 2(1-t)t * P1 + t² * P2,  t ∈ [0, 1]

其中:
    P0: 起点
    P1: 控制点（控制曲线形状）
    P2: 终点

 Bernstein 基函数:
    B₀²(t) = (1-t)²
    B₁²(t) = 2(1-t)t
    B₂²(t) = t²

可视化:
         P1 (控制点)
        / \
       /   \
      /     \
    P0-------P2
    (起点)   (终点)
"""

from __future__ import annotations

import numpy as np
from typing import List, Tuple


def quadratic_bezier(P0: np.ndarray, P1: np.ndarray, P2: np.ndarray, t: float) -> np.ndarray:
    """
    计算二次贝塞尔曲线在参数 t 处的点。

    使用 Bernstein 多项式公式:
        B(t) = (1-t)² * P0 + 2(1-t)t * P1 + t² * P2

    参数:
        P0: 起点，形状为 (2,) 的 numpy 数组 [x, y]
        P1: 控制点，形状为 (2,) 的 numpy 数组 [x, y]
        P2: 终点，形状为 (2,) 的 numpy 数组 [x, y]
        t: 参数，范围 [0, 1]

    返回:
        曲线上的点，形状为 (2,) 的 numpy 数组 [x, y]

    示例:
        >>> P0 = np.array([0.0, 0.0])
        >>> P1 = np.array([1.0, 2.0])
        >>> P2 = np.array([2.0, 0.0])
        >>> quadratic_bezier(P0, P1, P2, 0.5)
        array([1., 1.])
    """
    if not (0.0 <= t <= 1.0):
        raise ValueError(f"参数 t 必须在 [0, 1] 范围内，收到 t={t}")

    P0 = np.asarray(P0, dtype=float)
    P1 = np.asarray(P1, dtype=float)
    P2 = np.asarray(P2, dtype=float)

    # Bernstein 基函数计算
    u = 1.0 - t
    t2 = t * t
    u2 = u * u

    # B(t) = u² * P0 + 2*u*t * P1 + t² * P2
    return u2 * P0 + 2.0 * u * t * P1 + t2 * P2


def quadratic_bezier_points(P0: np.ndarray, P1: np.ndarray, P2: np.ndarray, num_samples: int = 100) -> np.ndarray:
    """
    计算二次贝塞尔曲线上的多个采样点。

    参数:
        P0: 起点
        P1: 控制点
        P2: 终点
        num_samples: 采样点数量

    返回:
        采样点数组，形状为 (num_samples, 2)
    """
    P0 = np.asarray(P0, dtype=float)
    P1 = np.asarray(P1, dtype=float)
    P2 = np.asarray(P2, dtype=float)

    t_values = np.linspace(0.0, 1.0, num_samples)
    return np.array([quadratic_bezier(P0, P1, P2, t) for t in t_values])


def quadratic_bezier_derivative(P0: np.ndarray, P1: np.ndarray, P2: np.ndarray, t: float) -> np.ndarray:
    """
    计算二次贝塞尔曲线在参数 t 处的导数。

    导数公式:
        B'(t) = 2(1-t)(P1 - P0) + 2t(P2 - P1)

    参数:
        P0: 起点
        P1: 控制点
        P2: 终点
        t: 参数

    返回:
        导数向量（切线方向），形状为 (2,)
    """
    P0 = np.asarray(P0, dtype=float)
    P1 = np.asarray(P1, dtype=float)
    P2 = np.asarray(P2, dtype=float)

    u = 1.0 - t
    return 2.0 * u * (P1 - P0) + 2.0 * t * (P2 - P1)


def quadratic_bezier_second_derivative(P0: np.ndarray, P1: np.ndarray, P2: np.ndarray) -> np.ndarray:
    """
    计算二次贝塞尔曲线的二阶导数（恒为常数向量）。

    二阶导数公式:
        B''(t) = 2(P0 - 2P1 + P2)

    参数:
        P0: 起点
        P1: 控制点
        P2: 终点

    返回:
        二阶导数向量，形状为 (2,)
    """
    P0 = np.asarray(P0, dtype=float)
    P1 = np.asarray(P1, dtype=float)
    P2 = np.asarray(P2, dtype=float)

    return 2.0 * (P0 - 2.0 * P1 + P2)


def quadratic_bezier_control_polygon(P0: np.ndarray, P1: np.ndarray, P2: np.ndarray) -> np.ndarray:
    """
    返回控制多边形（连接所有控制点的折线）。

    参数:
        P0: 起点
        P1: 控制点
        P2: 终点

    返回:
        控制多边形顶点数组，形状为 (3, 2)
    """
    P0 = np.asarray(P0, dtype=float)
    P1 = np.asarray(P1, dtype=float)
    P2 = np.asarray(P2, dtype=float)

    return np.array([P0, P1, P2])
