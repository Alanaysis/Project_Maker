"""
曲线长度近似 (Curve Length Approximation)
==========================================

计算贝塞尔曲线的弧长。由于贝塞尔曲线的弧长一般没有解析解，
我们使用数值方法来近似。

方法:
    1. 梯形法则 (Trapezoidal Rule)
    2. 辛普森法则 (Simpson's Rule)
    3. 高斯求积 (Gaussian Quadrature)
    4. 自适应细分 (Adaptive Subdivision)

弧长公式:
    L = ∫₀¹ ||B'(t)|| dt

其中 B'(t) 是曲线的导数，||·|| 表示欧几里得范数。
"""

from __future__ import annotations

import numpy as np
from typing import List, Tuple
from .cubic_bezier import cubic_bezier_derivative
from .quadratic_bezier import quadratic_bezier_derivative
from .linear_bezier import linear_bezier_derivative


def curve_length_numerical(control_points: np.ndarray, num_samples: int = 1000) -> float:
    """
    使用梯形法则数值积分计算曲线长度。

    L ≈ Σ (||B'(tᵢ)|| + ||B'(tᵢ₊₁)||) · Δt / 2

    参数:
        control_points: 控制点数组，形状为 (n+1, 2)
        num_samples: 采样点数量

    返回:
        近似弧长
    """
    control_points = np.asarray(control_points, dtype=float)
    n = len(control_points) - 1

    t_values = np.linspace(0.0, 1.0, num_samples)
    dt = 1.0 / (num_samples - 1)

    # 计算所有采样点的导数模长
    derivatives = []
    for t in t_values:
        if n == 1:
            deriv = linear_bezier_derivative(control_points[0], control_points[1])
        elif n == 2:
            deriv = quadratic_bezier_derivative(control_points[0], control_points[1],
                                                control_points[2], t)
        elif n == 3:
            deriv = cubic_bezier_derivative(control_points[0], control_points[1],
                                            control_points[2], control_points[3], t)
        else:
            raise ValueError(f"不支持 {n} 次贝塞尔曲线的长度计算")
        derivatives.append(np.linalg.norm(deriv))

    derivatives = np.array(derivatives)

    # 梯形法则
    length = np.sum(derivatives) * dt
    # 减去首尾的半个权重
    length -= (derivatives[0] + derivatives[-1]) * dt / 2.0

    return float(length)


def curve_length_simpson(control_points: np.ndarray, num_samples: int = 1000) -> float:
    """
    使用辛普森法则数值积分计算曲线长度（更高精度）。

    辛普森法则要求采样点数为奇数。

    L ≈ Δt/3 · [f(t₀) + 4f(t₁) + 2f(t₂) + 4f(t₃) + ... + f(tₙ)]

    参数:
        control_points: 控制点数组
        num_samples: 采样点数量（应为奇数）

    返回:
        近似弧长
    """
    control_points = np.asarray(control_points, dtype=float)
    n = len(control_points) - 1

    # 确保采样点数为奇数
    if num_samples % 2 == 0:
        num_samples += 1

    t_values = np.linspace(0.0, 1.0, num_samples)
    dt = 1.0 / (num_samples - 1)

    # 计算导数模长
    f_values = []
    for t in t_values:
        if n == 1:
            deriv = linear_bezier_derivative(control_points[0], control_points[1])
        elif n == 2:
            deriv = quadratic_bezier_derivative(control_points[0], control_points[1],
                                                control_points[2], t)
        elif n == 3:
            deriv = cubic_bezier_derivative(control_points[0], control_points[1],
                                            control_points[2], control_points[3], t)
        else:
            raise ValueError(f"不支持 {n} 次贝塞尔曲线的长度计算")
        f_values.append(np.linalg.norm(deriv))

    f_values = np.array(f_values)

    # 辛普森法则
    length = f_values[0] + f_values[-1]
    for i in range(1, num_samples - 1):
        if i % 2 == 1:
            length += 4.0 * f_values[i]
        else:
            length += 2.0 * f_values[i]
    length *= dt / 3.0

    return float(length)


def curve_length_gaussian(control_points: np.ndarray, order: int = 5) -> float:
    """
    使用高斯求积计算曲线长度。

    高斯求积在较少的采样点下提供高精度结果。

    参数:
        control_points: 控制点数组
        order: 高斯求积阶数

    返回:
        近似弧长
    """
    control_points = np.asarray(control_points, dtype=float)
    n = len(control_points) - 1

    # 高斯求积节点和权重（在 [-1, 1] 区间）
    nodes, weights = np.polynomial.legendre.leggauss(order)

    # 映射到 [0, 1] 区间
    t_values = (nodes + 1.0) / 2.0
    dt = 0.5  # 映射的雅可比行列式

    length = 0.0
    for t, w in zip(t_values, weights):
        if n == 1:
            deriv = linear_bezier_derivative(control_points[0], control_points[1])
        elif n == 2:
            deriv = quadratic_bezier_derivative(control_points[0], control_points[1],
                                                control_points[2], t)
        elif n == 3:
            deriv = cubic_bezier_derivative(control_points[0], control_points[1],
                                            control_points[2], control_points[3], t)
        else:
            raise ValueError(f"不支持 {n} 次贝塞尔曲线的长度计算")
        length += w * np.linalg.norm(deriv) * dt

    return float(length)


def curve_length_adaptive(control_points: np.ndarray, tolerance: float = 1e-8,
                          max_depth: int = 20) -> float:
    """
    使用自适应细分计算曲线长度。

    递归细分曲线，直到相邻细分估计的长度差小于容差。

    参数:
        control_points: 控制点数组
        tolerance: 容差
        max_depth: 最大递归深度

    返回:
        近似弧长
    """
    control_points = np.asarray(control_points, dtype=float)

    def _estimate_length(pts):
        """使用两端点距离近似曲线长度"""
        return float(np.linalg.norm(pts[-1] - pts[0]))

    def _adaptive_length(pts, current_length, depth):
        if depth <= 0:
            return current_length

        # 细分
        from .subdivision import subdivide_bezier
        left, right = subdivide_bezier(pts, 0.5)

        # 估计细分后的长度
        left_len = _estimate_length(left)
        right_len = _estimate_length(right)
        new_length = left_len + right_len

        # 检查收敛
        if abs(new_length - current_length) < tolerance:
            return new_length

        # 继续细分
        return (_adaptive_length(left, left_len, depth - 1)
                + _adaptive_length(right, right_len, depth - 1))

    initial_length = _estimate_length(control_points)
    return _adaptive_length(control_points, initial_length, max_depth)


def approximate_curve_as_polyline(control_points: np.ndarray, tolerance: float = 1.0) -> np.ndarray:
    """
    将曲线近似为折线（用于渲染）。

    使用自适应细分，使得每段直线与曲线的偏差小于容差。

    参数:
        control_points: 控制点数组
        tolerance: 最大偏差容差

    返回:
        折线顶点数组，形状为 (m, 2)
    """
    from .subdivision import flatten_bezier
    return flatten_bezier(control_points, tolerance=tolerance)
