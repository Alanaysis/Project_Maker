"""
贝塞尔曲线细分 (Bezier Curve Subdivision)
==========================================

细分是将一条贝塞尔曲线在参数 t 处分割为两条独立的贝塞尔曲线。
细分后的两段曲线组合起来与原曲线完全相同。

用途:
    - 渲染优化：只在需要高精度的区域细分
    - 碰撞检测：将曲线分解为更简单的段
    - 曲线编辑：局部修改曲线的一部分

细分公式 (De Casteljau 算法):
    给定控制点 P₀, P₁, ..., Pₙ 和参数 t:

    左段控制点:  Qᵢ = P₀ⁱ (每层的第一个插值点)
    右段控制点:  Rᵢ = Pᵢ₋₁ⁿ⁻ⁱ⁺¹ (每层的最后一个插值点)

性质:
    - 左段曲线在 t=0 处与原曲线在 P₀ 处相接
    - 右段曲线在 t=1 处与原曲线在 Pₙ 处相接
    - 两段曲线在分割点处 C∞ 连续（无限光滑）
    - 细分可以递归进行
"""

from __future__ import annotations

import numpy as np
from typing import List, Tuple
from .de_casteljau import de_casteljau_subdivide


def subdivide_bezier(control_points: np.ndarray, t: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    将贝塞尔曲线在参数 t 处细分。

    参数:
        control_points: 控制点数组，形状为 (n+1, 2)
        t: 细分点参数，范围 [0, 1]

    返回:
        (左段控制点, 右段控制点)，每个形状为 (m+1, 2)
    """
    return de_casteljau_subdivide(control_points, t)


def recursive_subdivide(control_points: np.ndarray, t_values: List[float]) -> List[np.ndarray]:
    """
    递归细分贝塞尔曲线。

    按给定的参数值列表依次细分，每次将一段曲线一分为二。

    参数:
        control_points: 控制点数组，形状为 (n+1, 2)
        t_values: 细分参数列表（相对于原始曲线）

    返回:
        细分后的所有曲线段控制点列表
    """
    if not t_values:
        return [control_points.copy()]

    t_values = sorted(t_values)
    segments = [control_points.copy()]
    result = []

    for t in t_values:
        new_segments = []
        for seg in segments:
            left, right = subdivide_bezier(seg, t)
            new_segments.append(left)
            new_segments.append(right)
        segments = new_segments
        result = segments

    return result


def adaptive_subdivide(control_points: np.ndarray, tolerance: float = 0.5, max_depth: int = 10) -> List[np.ndarray]:
    """
    自适应细分贝塞尔曲线。

    根据曲线的弯曲程度自动决定细分位置。
    如果控制多边形的中间点与曲线中点的距离小于容差，则不需要细分。

    参数:
        control_points: 控制点数组，形状为 (n+1, 2)
        tolerance: 容差，控制细分精度
        max_depth: 最大递归深度

    返回:
        细分后的曲线段控制点列表
    """
    if max_depth <= 0:
        return [control_points.copy()]

    n = len(control_points) - 1

    # 检查是否需要细分：比较曲线中点与控制多边形中点
    midpoint_t = 0.5

    # 计算曲线中点（使用 De Casteljau）
    from .de_casteljau import de_casteljau_evaluate
    curve_midpoint, _, _ = de_casteljau_evaluate(control_points, midpoint_t)

    # 计算控制多边形的中点
    polygon_midpoint = np.mean(control_points, axis=0)

    # 计算距离
    distance = np.linalg.norm(curve_midpoint - polygon_midpoint)

    if distance < tolerance:
        return [control_points.copy()]

    # 需要细分
    left, right = subdivide_bezier(control_points, midpoint_t)
    left_segments = adaptive_subdivide(left, tolerance, max_depth - 1)
    right_segments = adaptive_subdivide(right, tolerance, max_depth - 1)

    return left_segments + right_segments


def flatten_bezier(control_points: np.ndarray, tolerance: float = 1.0) -> np.ndarray:
    """
    将贝塞尔曲线"展平"为折线段。

    自适应地将曲线分解为一系列直线段，使得每段的偏差小于容差。

    参数:
        control_points: 控制点数组，形状为 (n+1, 2)
        tolerance: 最大允许偏差

    返回:
        折线采样点数组，形状为 (m, 2)
    """
    segments = adaptive_subdivide(control_points, tolerance=tolerance)

    # 连接所有段的端点（去重重叠点）
    points = []
    for seg in segments:
        if not points or not np.allclose(points[-1], seg[0]):
            points.append(seg[0])
        points.append(seg[-1])

    return np.array(points)
