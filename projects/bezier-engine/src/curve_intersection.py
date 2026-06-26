"""
曲线相交检测 (Curve Intersection Detection)
============================================

检测两条曲线之间或曲线与直线之间的交点。

方法概述:
    1. 曲线-直线相交：将曲线参数方程代入直线方程
    2. 曲线-曲线相交：使用分离轴定理 + 二分法/牛顿法

数值方法:
    - 边界框快速排除
    - 递归细分缩小搜索范围
    - 牛顿迭代法精化交点
"""

from __future__ import annotations

import numpy as np
from typing import List, Tuple, Optional
from .cubic_bezier import cubic_bezier, cubic_bezier_derivative
from .quadratic_bezier import quadratic_bezier


def bounding_box(control_points: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    计算控制点的轴对齐边界框。

    参数:
        control_points: 控制点数组，形状为 (n+1, 2)

    返回:
        (min_corner, max_corner) 边界框对角
    """
    min_corner = np.min(control_points, axis=0)
    max_corner = np.max(control_points, axis=0)
    return min_corner, max_corner


def boxes_intersect(box1_min: np.ndarray, box1_max: np.ndarray,
                    box2_min: np.ndarray, box2_max: np.ndarray) -> bool:
    """
    检查两个轴对齐边界框是否相交。

    参数:
        box1_min, box1_max: 第一个边界框的最小和最大角
        box2_min, box2_max: 第二个边界框的最小和最大角

    返回:
        是否相交
    """
    return (box1_min[0] <= box2_max[0] and box1_max[0] >= box2_min[0]
            and box1_min[1] <= box2_max[1] and box1_max[1] >= box2_min[1])


def curve_line_intersection(
    control_points: np.ndarray,
    line_p1: np.ndarray,
    line_p2: np.ndarray,
    tol: float = 1e-6
) -> List[float]:
    """
    检测贝塞尔曲线与线段的交点。

    使用递归细分 + 边界框测试的方法。

    参数:
        control_points: 贝塞尔曲线控制点，形状为 (n+1, 2)
        line_p1: 线段起点
        line_p2: 线段终点
        tol: 容差

    返回:
        交点对应的参数 t 值列表
    """
    line_p1 = np.asarray(line_p1, dtype=float)
    line_p2 = np.asarray(line_p2, dtype=float)

    # 直线方程: (x - p1) × (p2 - p1) = 0
    # 即: (x - p1) 与 (p2 - p1) 的叉积为零
    line_dir = line_p2 - line_p1
    line_normal = np.array([-line_dir[1], line_dir[0]])

    def f(t_val: float) -> float:
        """距离函数：曲线点到直线的有符号距离"""
        from .cubic_bezier import cubic_bezier as cb
        from .quadratic_bezier import quadratic_bezier as qb
        # 根据控制点数量选择曲线类型
        if len(control_points) == 4:
            point = cb(control_points[0], control_points[1],
                       control_points[2], control_points[3], t_val)
        elif len(control_points) == 3:
            point = qb(control_points[0], control_points[1],
                       control_points[2], t_val)
        else:
            from .linear_bezier import linear_bezier as lb
            point = lb(control_points[0], control_points[1], t_val)
        # 有符号距离
        return float(np.dot(point - line_p1, line_normal)) / np.linalg.norm(line_dir)

    def find_roots_recursive(ctrl_pts, t_start, t_end, sign_prev):
        """递归寻找根"""
        if t_end - t_start < tol:
            return []

        t_mid = (t_start + t_end) / 2.0
        val_start = f(t_start)
        val_mid = f(t_mid)

        # 检查符号变化
        sign_mid = np.sign(val_mid)

        roots = []

        if sign_prev * sign_mid < 0:
            # 符号变化，二分法精化
            a, b = t_start, t_mid
            for _ in range(50):  # 二分法迭代
                m = (a + b) / 2.0
                if f(a) * f(m) <= 0:
                    b = m
                else:
                    a = m
            roots.append((a + b) / 2.0)
        elif sign_mid != sign_prev:
            # 极值点，可能需要进一步细分
            if abs(val_mid) < 0.01:
                roots.append(t_mid)

        # 继续细分
        roots.extend(find_roots_recursive(ctrl_pts, t_start, t_mid, sign_mid))

        return roots

    # 初始符号
    sign_start = np.sign(f(0.0))
    roots = find_roots_recursive(control_points, 0.0, 1.0, sign_start)

    # 去重
    unique_roots = []
    for r in roots:
        if not unique_roots or abs(r - unique_roots[-1]) > tol:
            unique_roots.append(r)

    return unique_roots


def curve_curve_intersection(
    ctrl1: np.ndarray,
    ctrl2: np.ndarray,
    tol: float = 1e-6,
    max_depth: int = 10
) -> List[Tuple[float, float]]:
    """
    检测两条贝塞尔曲线的交点。

    使用分离轴思想的递归细分方法：
    1. 检查边界框是否相交
    2. 如果不相交，排除
    3. 如果相交且足够小，记录近似交点
    4. 否则，细分两条曲线并递归检查

    参数:
        ctrl1: 第一条曲线的控制点，形状为 (n+1, 2)
        ctrl2: 第二条曲线的控制点，形状为 (m+1, 2)
        tol: 容差
        max_depth: 最大递归深度

    返回:
        交点列表，每个元素为 (t1, t2) 元组
    """
    ctrl1 = np.asarray(ctrl1, dtype=float)
    ctrl2 = np.asarray(ctrl2, dtype=float)

    box1_min, box1_max = bounding_box(ctrl1)
    box2_min, box2_max = bounding_box(ctrl2)

    if not boxes_intersect(box1_min, box1_max, box2_min, box2_max):
        return []

    if max_depth <= 0:
        # 返回近似交点（两条曲线中点的平均值）
        from .de_casteljau import de_casteljau_evaluate
        pt1, _, _ = de_casteljau_evaluate(ctrl1, 0.5)
        pt2, _, _ = de_casteljau_evaluate(ctrl2, 0.5)
        midpoint = (pt1 + pt2) / 2.0
        # 估计 t 值
        t1 = np.linalg.norm(midpoint - ctrl1[0]) / max(np.linalg.norm(ctrl1[-1] - ctrl1[0]), 1e-10)
        t2 = np.linalg.norm(midpoint - ctrl2[0]) / max(np.linalg.norm(ctrl2[-1] - ctrl2[0]), 1e-10)
        return [(max(0.0, min(1.0, t1)), max(0.0, min(1.0, t2)))]

    # 细分两条曲线
    from .subdivision import subdivide_bezier
    left1, right1 = subdivide_bezier(ctrl1, 0.5)
    left2, right2 = subdivide_bezier(ctrl2, 0.5)

    results = []
    results.extend(curve_curve_intersection(left1, left2, tol, max_depth - 1))
    results.extend(curve_curve_intersection(left1, right2, tol, max_depth - 1))
    results.extend(curve_curve_intersection(right1, left2, tol, max_depth - 1))
    results.extend(curve_curve_intersection(right1, right2, tol, max_depth - 1))

    # 去重
    unique_results = []
    for t1, t2 in results:
        is_duplicate = False
        for ut1, ut2 in unique_results:
            if abs(t1 - ut1) < tol and abs(t2 - ut2) < tol:
                is_duplicate = True
                break
        if not is_duplicate:
            unique_results.append((t1, t2))

    return unique_results
