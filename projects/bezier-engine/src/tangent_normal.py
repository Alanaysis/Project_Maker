"""
切线和法向量计算 (Tangent and Normal Computation)
==================================================

计算贝塞尔曲线在任意参数处的切线向量和法向量。

数学基础:
    切向量 T(t) = B'(t) = dB/dt
    单位切向量 T̂(t) = B'(t) / ||B'(t)||

    法向量 N(t) = (-T̂_y, T̂_x)  (逆时针旋转90度)
    单位法向量 N̂(t) = N(t) / ||N(t)||

用途:
    - 曲线着色（沿切线方向渐变）
    - 碰撞响应（沿法线方向反弹）
    - 构造管状/带状区域
    - 计算曲率
"""

from __future__ import annotations

import numpy as np
from typing import Tuple
from .cubic_bezier import cubic_bezier, cubic_bezier_derivative
from .quadratic_bezier import quadratic_bezier, quadratic_bezier_derivative
from .linear_bezier import linear_bezier, linear_bezier_derivative


def tangent_vector(control_points: np.ndarray, t: float) -> np.ndarray:
    """
    计算贝塞尔曲线在参数 t 处的切线向量（未归一化）。

    参数:
        control_points: 控制点数组，形状为 (n+1, 2)
        t: 参数，范围 [0, 1]

    返回:
        切线向量，形状为 (2,)
    """
    control_points = np.asarray(control_points, dtype=float)
    n = len(control_points) - 1

    if n == 1:
        return linear_bezier_derivative(control_points[0], control_points[1])
    elif n == 2:
        return quadratic_bezier_derivative(control_points[0], control_points[1],
                                           control_points[2], t)
    elif n == 3:
        return cubic_bezier_derivative(control_points[0], control_points[1],
                                       control_points[2], control_points[3], t)
    else:
        raise ValueError(f"不支持 {n} 次贝塞尔曲线的切线计算")


def unit_tangent(control_points: np.ndarray, t: float) -> np.ndarray:
    """
    计算贝塞尔曲线在参数 t 处的单位切向量。

    参数:
        control_points: 控制点数组
        t: 参数

    返回:
        单位切向量，形状为 (2,)
    """
    tangent = tangent_vector(control_points, t)
    norm = np.linalg.norm(tangent)
    if norm < 1e-10:
        return np.array([1.0, 0.0])  # 退化情况
    return tangent / norm


def normal_vector(control_points: np.ndarray, t: float) -> np.ndarray:
    """
    计算贝塞尔曲线在参数 t 处的法向量（未归一化）。

    法向量由切向量逆时针旋转 90° 得到:
        N = (-T_y, T_x)

    参数:
        control_points: 控制点数组
        t: 参数

    返回:
        法向量，形状为 (2,)
    """
    tangent = tangent_vector(control_points, t)
    return np.array([-tangent[1], tangent[0]])


def unit_normal(control_points: np.ndarray, t: float) -> np.ndarray:
    """
    计算贝塞尔曲线在参数 t 处的单位法向量。

    参数:
        control_points: 控制点数组
        t: 参数

    返回:
        单位法向量，形状为 (2,)
    """
    tangent = tangent_vector(control_points, t)
    norm = np.linalg.norm(tangent)
    if norm < 1e-10:
        return np.array([0.0, 1.0])  # 退化情况
    # 逆时针旋转90度并归一化
    normal = np.array([-tangent[1], tangent[0]])
    return normal / norm


def curvature(control_points: np.ndarray, t: float) -> float:
    """
    计算贝塞尔曲线在参数 t 处的曲率。

    曲率公式（二维曲线）:
        κ = |x'y'' - y'x''| / (x'² + y'²)^(3/2)

    其中 ' 表示对 t 的导数。

    参数:
        control_points: 控制点数组
        t: 参数

    返回:
        曲率值（标量）
    """
    control_points = np.asarray(control_points, dtype=float)
    n = len(control_points) - 1

    if n == 1:
        return 0.0  # 直线曲率为0

    if n == 2:
        p0, p1, p2 = control_points
        first = quadratic_bezier_derivative(p0, p1, p2, t)
        second = quadratic_bezier.second_derivative(p0, p1, p2)
    elif n == 3:
        p0, p1, p2, p3 = control_points
        first = cubic_bezier_derivative(p0, p1, p2, p3, t)
        second = cubic_bezier.second_derivative(p0, p1, p2, p3, t)
    else:
        raise ValueError(f"不支持 {n} 次贝塞尔曲线的曲率计算")

    # 叉积的绝对值（二维）
    cross = abs(first[0] * second[1] - first[1] * second[0])
    # 模长的三次方
    norm_cubed = np.linalg.norm(first) ** 3

    if norm_cubed < 1e-10:
        return 0.0

    return float(cross / norm_cubed)


def radius_of_curvature(control_points: np.ndarray, t: float) -> float:
    """
    计算曲率半径。

    曲率半径 = 1 / 曲率

    参数:
        control_points: 控制点数组
        t: 参数

    返回:
        曲率半径
    """
    k = curvature(control_points, t)
    if abs(k) < 1e-10:
        return float('inf')
    return 1.0 / abs(k)
