"""
De Casteljau 算法 (De Casteljau's Algorithm)
============================================

De Casteljau 算法是一种数值稳定的方法，用于计算贝塞尔曲线上的点
并将曲线细分（分割）为两段。它通过递归线性插值实现。

算法原理:
    给定 n 次贝塞尔曲线的控制点 P₀, P₁, ..., Pₙ，
    在参数 t 处计算曲线点，通过反复线性插值。

递归公式:
    Pᵢ⁰ = Pᵢ (初始控制点)
    Pᵢʳ(t) = (1-t) · Pᵢʳ⁻¹ + t · Pᵢ₊₁ʳ⁻¹

其中:
    r: 递归层数 (1, 2, ..., n)
    i: 索引 (0, 1, ..., n-r)

最终结果:
    B(t) = P₀ⁿ(t)

可视化 (二次贝塞尔曲线, n=2):
    第0层:  P₀ --------- P₁ --------- P₂     (原始控制点)
              \         /   \         /
               \       /     \       /
                \     /       \     /
            第1层:  Q₀ --------- Q₁     (中间插值点)
                      \         /
                       \       /
                        \     /
                    第2层:  R₀       (最终曲线点)

性质:
    - 数值稳定性好
    - 可同时得到曲线点和细分后的两段控制点
    - 计算复杂度: O(n²) 对于 n 次曲线
"""

from __future__ import annotations

import numpy as np
from typing import List, Tuple


def de_casteljau_evaluate(control_points: np.ndarray, t: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    使用 De Casteljau 算法计算贝塞尔曲线上的点并返回细分控制点。

    参数:
        control_points: 控制点数组，形状为 (n+1, 2)
        t: 参数，范围 [0, 1]

    返回:
        (curve_point, left_subdivision, right_subdivision)
        - curve_point: 曲线上的点，形状为 (2,)
        - left_subdivision: 左半段控制点，形状为 (n+1, 2)
        - right_subdivision: 右半段控制点，形状为 (n+1, 2)

    示例:
        >>> pts = np.array([[0, 0], [1, 2], [3, 2], [4, 0]])
        >>> point, left, right = de_casteljau_evaluate(pts, 0.5)
        >>> print(point)
        [2. 1.5]
    """
    if not (0.0 <= t <= 1.0):
        raise ValueError(f"参数 t 必须在 [0, 1] 范围内，收到 t={t}")

    n = len(control_points) - 1  # 曲线次数
    control_points = np.asarray(control_points, dtype=float)

    # 复制控制点用于递归计算
    # work[r][i] 表示第 r 层第 i 个插值点
    work = [control_points.copy()]

    for r in range(1, n + 1):
        prev = work[r - 1]
        current = np.zeros((len(prev) - 1, 2))
        for i in range(len(prev) - 1):
            # 线性插值: Pᵢʳ = (1-t)·Pᵢʳ⁻¹ + t·Pᵢ₊₁ʳ⁻¹
            current[i] = (1.0 - t) * prev[i] + t * prev[i + 1]
        work.append(current)

    # 最终结果
    curve_point = work[n][0]

    # 左半段控制点: 取每层的第一个点
    left_subdivision = np.array([work[i][0] for i in range(n + 1)])

    # 右半段控制点: 取每层的最后一个点
    right_subdivision = np.array([work[i][-1] for i in range(n + 1)])

    return curve_point, left_subdivision, right_subdivision


def de_casteljau_subdivide(control_points: np.ndarray, t: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    使用 De Casteljau 算法细分贝塞尔曲线为两段。

    参数:
        control_points: 控制点数组，形状为 (n+1, 2)
        t: 细分参数，范围 [0, 1]

    返回:
        (left_control_points, right_control_points) 元组
    """
    _, left, right = de_casteljau_evaluate(control_points, t)
    return left, right


def de_casteljau_recursive(control_points: np.ndarray, t: float, level: int = 0, max_level: int = None) -> np.ndarray:
    """
    递归版本的 De Casteljau 算法（教学用途）。

    这个版本清晰地展示了算法的递归本质，但效率不如迭代版本。

    参数:
        control_points: 控制点数组
        t: 参数
        level: 当前递归层数（内部使用）
        max_level: 最大递归深度（内部使用）

    返回:
        曲线上的点
    """
    if max_level is None:
        max_level = len(control_points) - 1

    if max_level == 0:
        return control_points[0]

    # 递归步骤: 对相邻点对做线性插值
    new_points = np.zeros((len(control_points) - 1, 2))
    for i in range(len(control_points) - 1):
        new_points[i] = (1.0 - t) * control_points[i] + t * control_points[i + 1]

    return de_casteljau_recursive(new_points, t, level + 1, max_level - 1)
