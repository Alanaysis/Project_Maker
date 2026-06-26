"""
三次贝塞尔曲线 (Cubic Bezier Curve)
====================================

三次贝塞尔曲线由四个控制点定义，是最常用的贝塞尔曲线类型。
SVG、字体和矢量图形软件广泛使用它。

数学公式:
    B(t) = (1-t)³ * P0 + 3(1-t)²t * P1 + 3(1-t)t² * P2 + t³ * P3,  t ∈ [0, 1]

其中:
    P0: 起点
    P1: 第一个控制点（控制起点处的切线方向）
    P2: 第二个控制点（控制终点处的切线方向）
    P3: 终点

 Bernstein 基函数:
    B₀³(t) = (1-t)³
    B₁³(t) = 3(1-t)²t
    B₂³(t) = 3(1-t)t²
    B₃³(t) = t³

可视化:
          P1         P2
         /   \     /   \
        /     \   /     \
       /       \ /       \
    P0----------           P3
    (起点)                   (终点)

性质:
    - 曲线通过 P0 和 PP3
    - 曲线在 P0 处与 P0-P1 相切
    - 曲线在 P3 处与 P2-P3 相切
    - 曲线整体位于控制多边形的凸包内
"""

from __future__ import annotations

import numpy as np
from typing import List, Tuple


def cubic_bezier(P0: np.ndarray, P1: np.ndarray, P2: np.ndarray, P3: np.ndarray, t: float) -> np.ndarray:
    """
    计算三次贝塞尔曲线在参数 t 处的点。

    使用 Bernstein 多项式公式:
        B(t) = (1-t)³·P0 + 3(1-t)²t·P1 + 3(1-t)t²·P2 + t³·P3

    参数:
        P0: 起点，形状为 (2,) 的 numpy 数组 [x, y]
        P1: 第一控制点，形状为 (2,) 的 numpy 数组 [x, y]
        P2: 第二控制点，形状为 (2,) 的 numpy 数组 [x, y]
        P3: 终点，形状为 (2,) 的 numpy 数组 [x, y]
        t: 参数，范围 [0, 1]

    返回:
        曲线上的点，形状为 (2,) 的 numpy 数组 [x, y]

    示例:
        >>> P0 = np.array([0.0, 0.0])
        >>> P1 = np.array([1.0, 2.0])
        >>> P2 = np.array([3.0, 2.0])
        >>> P3 = np.array([4.0, 0.0])
        >>> cubic_bezier(P0, P1, P2, P3, 0.5)
        array([2. , 1.5])
    """
    if not (0.0 <= t <= 1.0):
        raise ValueError(f"参数 t 必须在 [0, 1] 范围内，收到 t={t}")

    P0 = np.asarray(P0, dtype=float)
    P1 = np.asarray(P1, dtype=float)
    P2 = np.asarray(P2, dtype=float)
    P3 = np.asarray(P3, dtype=float)

    # Bernstein 基函数计算
    u = 1.0 - t
    u3 = u * u * u
    u2t = u * u * t
    ut2 = u * t * t
    t3 = t * t * t

    # B(t) = u³·P0 + 3u²t·P1 + 3ut²·P2 + t³·P3
    return u3 * P0 + 3.0 * u2t * P1 + 3.0 * ut2 * P2 + t3 * P3


def cubic_bezier_points(P0: np.ndarray, P1: np.ndarray, P2: np.ndarray, P3: np.ndarray, num_samples: int = 100) -> np.ndarray:
    """
    计算三次贝塞尔曲线上的多个采样点。

    参数:
        P0: 起点
        P1: 第一控制点
        P2: 第二控制点
        P3: 终点
        num_samples: 采样点数量

    返回:
        采样点数组，形状为 (num_samples, 2)
    """
    P0 = np.asarray(P0, dtype=float)
    P1 = np.asarray(P1, dtype=float)
    P2 = np.asarray(P2, dtype=float)
    P3 = np.asarray(P3, dtype=float)

    t_values = np.linspace(0.0, 1.0, num_samples)
    return np.array([cubic_bezier(P0, P1, P2, P3, t) for t in t_values])


def cubic_bezier_derivative(P0: np.ndarray, P1: np.ndarray, P2: np.ndarray, P3: np.ndarray, t: float) -> np.ndarray:
    """
    计算三次贝塞尔曲线在参数 t 处的导数。

    导数公式:
        B'(t) = 3(1-t)²(P1-P0) + 6(1-t)t(P2-P1) + 3t²(P3-P2)

    导数曲线的控制点:
        P0' = 3(P1 - P0)
        P1' = 3(P2 - P1)
        P2' = 3(P3 - P2)

    参数:
        P0: 起点
        P1: 第一控制点
        P2: 第二控制点
        P3: 终点
        t: 参数

    返回:
        导数向量（切线方向），形状为 (2,)
    """
    P0 = np.asarray(P0, dtype=float)
    P1 = np.asarray(P1, dtype=float)
    P2 = np.asarray(P2, dtype=float)
    P3 = np.asarray(P3, dtype=float)

    u = 1.0 - t
    return (
        3.0 * u * u * (P1 - P0)
        + 6.0 * u * t * (P2 - P1)
        + 3.0 * t * t * (P3 - P2)
    )


def cubic_bezier_second_derivative(P0: np.ndarray, P1: np.ndarray, P2: np.ndarray, P3: np.ndarray, t: float) -> np.ndarray:
    """
    计算三次贝塞尔曲线在参数 t 处的二阶导数。

    二阶导数公式:
        B''(t) = 6(1-t)(P2-2P1+P0) + 6t(P3-2P2+P1)

    参数:
        P0: 起点
        P1: 第一控制点
        P2: 第二控制点
        P3: 终点
        t: 参数

    返回:
        二阶导数向量，形状为 (2,)
    """
    P0 = np.asarray(P0, dtype=float)
    P1 = np.asarray(P1, dtype=float)
    P2 = np.asarray(P2, dtype=float)
    P3 = np.asarray(P3, dtype=float)

    u = 1.0 - t
    return (
        6.0 * u * (P2 - 2.0 * P1 + P0)
        + 6.0 * t * (P3 - 2.0 * P2 + P1)
    )


def cubic_bezier_control_polygon(P0: np.ndarray, P1: np.ndarray, P2: np.ndarray, P3: np.ndarray) -> np.ndarray:
    """
    返回控制多边形（连接所有控制点的折线）。

    参数:
        P0: 起点
        P1: 第一控制点
        P2: 第二控制点
        P3: 终点

    返回:
        控制多边形顶点数组，形状为 (4, 2)
    """
    P0 = np.asarray(P0, dtype=float)
    P1 = np.asarray(P1, dtype=float)
    P2 = np.asarray(P2, dtype=float)
    P3 = np.asarray(P3, dtype=float)

    return np.array([P0, P1, P2, P3])


def cubic_bezier_from_polynomial(coeffs: List[Tuple[float, float]]) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    从多项式系数反推三次贝塞尔曲线的控制点。

    三次多项式: P(t) = a·t³ + b·t² + c·t + d
    三次贝塞尔: B(t) = (1-t)³·P0 + 3(1-t)²t·P1 + 3(1-t)t²·P2 + t³·P3

    通过比较系数:
        P0 = d
        P1 = d + c/3
        P2 = d + c/3 + b/3
        P3 = d + c/3 + b/3 + a/3

    参数:
        coeffs: 多项式系数 [(a_x, a_y), (b_x, b_y), (c_x, c_y), (d_x, d_y)]

    返回:
        (P0, P1, P2, P3) 元组
    """
    a, b, c, d = coeffs
    P0 = np.asarray(d, dtype=float)
    P1 = P0 + np.asarray(c) / 3.0
    P2 = P1 + np.asarray(b) / 3.0
    P3 = P2 + np.asarray(a) / 3.0
    return P0, P1, P2, P3
