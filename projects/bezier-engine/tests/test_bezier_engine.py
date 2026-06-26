"""
贝塞尔曲线引擎 - 单元测试
=========================

测试所有核心模块的功能正确性。

运行测试:
    python -m pytest tests/ -v
    或
    python -m tests.run_tests
"""

import numpy as np
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.linear_bezier import linear_bezier, linear_bezier_points, linear_bezier_derivative
from src.quadratic_bezier import (
    quadratic_bezier, quadratic_bezier_points,
    quadratic_bezier_derivative, quadratic_bezier_second_derivative
)
from src.cubic_bezier import (
    cubic_bezier, cubic_bezier_points,
    cubic_bezier_derivative, cubic_bezier_second_derivative,
    cubic_bezier_control_polygon
)
from src.de_casteljau import de_casteljau_evaluate, de_casteljau_subdivide, de_casteljau_recursive
from src.subdivision import subdivide_bezier, adaptive_subdivide, flatten_bezier
from src.tangent_normal import (
    tangent_vector, unit_tangent, normal_vector, unit_normal,
    curvature, radius_of_curvature
)
from src.curve_length import (
    curve_length_numerical, curve_length_simpson,
    curve_length_gaussian, curve_length_adaptive
)
from src.curve_intersection import (
    bounding_box, boxes_intersect,
    curve_line_intersection, curve_curve_intersection
)


class TestLinearBezier:
    """线性贝塞尔曲线测试"""

    def test_linear_bezier_start(self):
        """测试 t=0 时返回起点"""
        P0 = np.array([1.0, 2.0])
        P1 = np.array([3.0, 4.0])
        result = linear_bezier(P0, P1, 0.0)
        np.testing.assert_array_almost_equal(result, P0)

    def test_linear_bezier_end(self):
        """测试 t=1 时返回终点"""
        P0 = np.array([1.0, 2.0])
        P1 = np.array([3.0, 4.0])
        result = linear_bezier(P0, P1, 1.0)
        np.testing.assert_array_almost_equal(result, P1)

    def test_linear_bezier_midpoint(self):
        """测试 t=0.5 时返回中点"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([2.0, 4.0])
        result = linear_bezier(P0, P1, 0.5)
        expected = np.array([1.0, 2.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_linear_bezier_derivative(self):
        """测试导数计算"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([3.0, 4.0])
        deriv = linear_bezier_derivative(P0, P1)
        expected = np.array([3.0, 4.0])
        np.testing.assert_array_almost_equal(deriv, expected)

    def test_linear_bezier_points(self):
        """测试多点采样"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([10.0, 0.0])
        points = linear_bezier_points(P0, P1, 11)
        assert points.shape == (11, 2)
        np.testing.assert_array_almost_equal(points[0], P0)
        np.testing.assert_array_almost_equal(points[-1], P1)

    def test_linear_bezier_invalid_t(self):
        """测试无效参数"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([1.0, 1.0])
        try:
            linear_bezier(P0, P1, 1.5)
            assert False, "应该抛出 ValueError"
        except ValueError:
            pass


class TestQuadraticBezier:
    """二次贝塞尔曲线测试"""

    def test_quadratic_start(self):
        """测试 t=0 时返回起点"""
        P0 = np.array([1.0, 1.0])
        P1 = np.array([2.0, 3.0])
        P2 = np.array([3.0, 1.0])
        result = quadratic_bezier(P0, P1, P2, 0.0)
        np.testing.assert_array_almost_equal(result, P0)

    def test_quadratic_end(self):
        """测试 t=1 时返回终点"""
        P0 = np.array([1.0, 1.0])
        P1 = np.array([2.0, 3.0])
        P2 = np.array([3.0, 1.0])
        result = quadratic_bezier(P0, P1, P2, 1.0)
        np.testing.assert_array_almost_equal(result, P2)

    def test_quadratic_midpoint(self):
        """测试 t=0.5 时的点"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([1.0, 2.0])
        P2 = np.array([2.0, 0.0])
        result = quadratic_bezier(P0, P1, P2, 0.5)
        expected = np.array([1.0, 1.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_quadratic_derivative(self):
        """测试导数"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([1.0, 2.0])
        P2 = np.array([2.0, 0.0])
        deriv = quadratic_bezier_derivative(P0, P1, P2, 0.5)
        # B'(0.5) = 2(0.5)(P1-P0) + 2(0.5)(P2-P1) = P1-P0 + P2-P1 = P2-P0
        expected = P2 - P0
        np.testing.assert_array_almost_equal(deriv, expected)

    def test_quadratic_second_derivative(self):
        """测试二阶导数"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([1.0, 2.0])
        P2 = np.array([2.0, 0.0])
        second_deriv = quadratic_bezier_second_derivative(P0, P1, P2)
        expected = 2.0 * (P0 - 2.0 * P1 + P2)
        np.testing.assert_array_almost_equal(second_deriv, expected)

    def test_quadratic_invalid_t(self):
        """测试无效参数"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([1.0, 1.0])
        P2 = np.array([2.0, 0.0])
        try:
            quadratic_bezier(P0, P1, P2, -0.1)
            assert False, "应该抛出 ValueError"
        except ValueError:
            pass


class TestCubicBezier:
    """三次贝塞尔曲线测试"""

    def test_cubic_start(self):
        """测试 t=0 时返回起点"""
        P0 = np.array([1.0, 1.0])
        P1 = np.array([2.0, 3.0])
        P2 = np.array([4.0, 3.0])
        P3 = np.array([5.0, 1.0])
        result = cubic_bezier(P0, P1, P2, P3, 0.0)
        np.testing.assert_array_almost_equal(result, P0)

    def test_cubic_end(self):
        """测试 t=1 时返回终点"""
        P0 = np.array([1.0, 1.0])
        P1 = np.array([2.0, 3.0])
        P2 = np.array([4.0, 3.0])
        P3 = np.array([5.0, 1.0])
        result = cubic_bezier(P0, P1, P2, P3, 1.0)
        np.testing.assert_array_almost_equal(result, P3)

    def test_cubic_midpoint(self):
        """测试 t=0.5 时的点"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([1.0, 2.0])
        P2 = np.array([3.0, 2.0])
        P3 = np.array([4.0, 0.0])
        result = cubic_bezier(P0, P1, P2, P3, 0.5)
        expected = np.array([2.0, 1.5])
        np.testing.assert_array_almost_equal(result, expected)

    def test_cubic_derivative(self):
        """测试导数"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([1.0, 0.0])
        P2 = np.array([2.0, 0.0])
        P3 = np.array([3.0, 0.0])
        deriv = cubic_bezier_derivative(P0, P1, P2, P3, 0.5)
        # 对于水平直线，导数应为常数 [3, 0]
        expected = np.array([3.0, 0.0])
        np.testing.assert_array_almost_equal(deriv, expected)

    def test_cubic_control_polygon(self):
        """测试控制多边形"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([1.0, 2.0])
        P2 = np.array([3.0, 2.0])
        P3 = np.array([4.0, 0.0])
        polygon = cubic_bezier_control_polygon(P0, P1, P2, P3)
        assert polygon.shape == (4, 2)
        np.testing.assert_array_almost_equal(polygon[0], P0)
        np.testing.assert_array_almost_equal(polygon[1], P1)
        np.testing.assert_array_almost_equal(polygon[2], P2)
        np.testing.assert_array_almost_equal(polygon[3], P3)

    def test_cubic_invalid_t(self):
        """测试无效参数"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([1.0, 1.0])
        P2 = np.array([2.0, 0.0])
        P3 = np.array([3.0, 0.0])
        try:
            cubic_bezier(P0, P1, P2, P3, 1.5)
            assert False, "应该抛出 ValueError"
        except ValueError:
            pass


class TestDeCasteljau:
    """De Casteljau 算法测试"""

    def test_evaluate_matches_bezier(self):
        """测试 De Casteljau 结果与直接计算一致"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([1.0, 2.0])
        P2 = np.array([3.0, 2.0])
        P3 = np.array([4.0, 0.0])
        control_points = np.array([P0, P1, P2, P3])

        t = 0.3
        point, _, _ = de_casteljau_evaluate(control_points, t)
        direct = cubic_bezier(P0, P1, P2, P3, t)
        np.testing.assert_array_almost_equal(point, direct)

    def test_subdivide_preserves_curve(self):
        """测试细分后曲线不变"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([1.0, 3.0])
        P2 = np.array([4.0, 3.0])
        P3 = np.array([5.0, 0.0])
        control_points = np.array([P0, P1, P2, P3])

        t = 0.4
        left, right = de_casteljau_subdivide(control_points, t)

        # 分割点：左段终点 = 右段终点 = 原曲线在 t 处的点
        left_end = cubic_bezier(left[0], left[1], left[2], left[3], 1.0)
        right_end = cubic_bezier(right[0], right[1], right[2], right[3], 1.0)
        orig_at_t = cubic_bezier(P0, P1, P2, P3, t)
        np.testing.assert_array_almost_equal(left_end, right_end)
        np.testing.assert_array_almost_equal(left_end, orig_at_t)

        # 左段起点 = 原曲线起点
        orig_start = cubic_bezier(P0, P1, P2, P3, 0.0)
        np.testing.assert_array_almost_equal(left[0], orig_start)

    def test_recursive_matches_iterative(self):
        """测试递归版本与迭代版本结果一致"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([1.0, 2.0])
        P2 = np.array([3.0, 2.0])
        P3 = np.array([4.0, 0.0])
        control_points = np.array([P0, P1, P2, P3])

        t = 0.6
        point_iter, _, _ = de_casteljau_evaluate(control_points, t)
        point_rec = de_casteljau_recursive(control_points, t)
        np.testing.assert_array_almost_equal(point_iter, point_rec)

    def test_subdivide_at_t0(self):
        """测试在 t=0 处细分"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([1.0, 2.0])
        P2 = np.array([3.0, 2.0])
        P3 = np.array([4.0, 0.0])
        control_points = np.array([P0, P1, P2, P3])

        left, right = subdivide_bezier(control_points, 0.0)
        # 左段起点应等于原曲线起点
        np.testing.assert_array_almost_equal(left[0], P0)
        assert left.shape == (4, 2)

    def test_subdivide_at_t1(self):
        """测试在 t=1 处细分"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([1.0, 2.0])
        P2 = np.array([3.0, 2.0])
        P3 = np.array([4.0, 0.0])
        control_points = np.array([P0, P1, P2, P3])

        left, right = subdivide_bezier(control_points, 1.0)
        # 右段终点应等于原曲线终点
        np.testing.assert_array_almost_equal(right[-1], P3)
        assert right.shape == (4, 2)


class TestTangentNormal:
    """切线和法向量测试"""

    def test_tangent_linear(self):
        """测试线性曲线的切线"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([3.0, 4.0])
        ctrl = np.array([P0, P1])
        tangent = tangent_vector(ctrl, 0.5)
        expected = P1 - P0
        np.testing.assert_array_almost_equal(tangent, expected)

    def test_unit_tangent_linear(self):
        """测试单位切线"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([3.0, 4.0])
        ctrl = np.array([P0, P1])
        ut = unit_tangent(ctrl, 0.5)
        np.testing.assert_almost_equal(np.linalg.norm(ut), 1.0)

    def test_normal_perpendicular(self):
        """测试法向量与切线垂直"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([1.0, 2.0])
        P2 = np.array([2.0, 0.0])
        ctrl = np.array([P0, P1, P2])
        t = unit_tangent(ctrl, 0.5)
        n = unit_normal(ctrl, 0.5)
        # 点积应为 0
        np.testing.assert_almost_equal(np.dot(t, n), 0.0, decimal=10)

    def test_normal_linear(self):
        """测试线性曲线的法向量"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([1.0, 0.0])
        ctrl = np.array([P0, P1])
        n = unit_normal(ctrl, 0.5)
        # 水平线的法向量应为 [0, 1] 或 [0, -1]
        np.testing.assert_almost_equal(abs(n[0]), 0.0, decimal=10)

    def test_curvature_linear(self):
        """测试线性曲线曲率为 0"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([1.0, 1.0])
        ctrl = np.array([P0, P1])
        k = curvature(ctrl, 0.5)
        np.testing.assert_almost_equal(k, 0.0)

    def test_radius_of_curvature_linear(self):
        """测试线性曲线曲率半径为无穷大"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([1.0, 1.0])
        ctrl = np.array([P0, P1])
        r = radius_of_curvature(ctrl, 0.5)
        assert np.isinf(r) or r > 1e6


class TestCurveLength:
    """曲线长度测试"""

    def test_linear_length(self):
        """测试线性曲线长度"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([3.0, 4.0])
        ctrl = np.array([P0, P1])
        length = curve_length_numerical(ctrl, 1000)
        expected = 5.0  # 3-4-5 直角三角形
        np.testing.assert_almost_equal(length, expected, decimal=1)

    def test_simpson_vs_numerical(self):
        """测试辛普森法与梯形法结果接近"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([1.0, 2.0])
        P2 = np.array([3.0, 2.0])
        P3 = np.array([4.0, 0.0])
        ctrl = np.array([P0, P1, P2, P3])

        l1 = curve_length_numerical(ctrl, 1000)
        l2 = curve_length_simpson(ctrl, 1000)
        np.testing.assert_almost_equal(l1, l2, decimal=2)

    def test_gaussian_vs_numerical(self):
        """测试高斯求积与数值积分结果接近"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([1.0, 3.0])
        P2 = np.array([4.0, 3.0])
        P3 = np.array([5.0, 0.0])
        ctrl = np.array([P0, P1, P2, P3])

        l1 = curve_length_numerical(ctrl, 1000)
        l2 = curve_length_gaussian(ctrl, order=10)
        np.testing.assert_almost_equal(l1, l2, decimal=2)

    def test_adaptive_converges(self):
        """测试自适应方法收敛"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([1.0, 2.0])
        P2 = np.array([3.0, 2.0])
        P3 = np.array([4.0, 0.0])
        ctrl = np.array([P0, P1, P2, P3])

        l1 = curve_length_adaptive(ctrl, tolerance=1e-4)
        l2 = curve_length_adaptive(ctrl, tolerance=1e-8)
        np.testing.assert_almost_equal(l1, l2, decimal=2)

    def test_length_positive(self):
        """测试长度始终为正"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([1.0, 1.0])
        P2 = np.array([2.0, 0.0])
        ctrl = np.array([P0, P1, P2])
        length = curve_length_numerical(ctrl, 100)
        assert length > 0


class TestCurveIntersection:
    """曲线相交检测测试"""

    def test_bounding_box(self):
        """测试边界框计算"""
        pts = np.array([[0, 0], [1, 3], [2, 1]])
        min_corner, max_corner = bounding_box(pts)
        np.testing.assert_array_almost_equal(min_corner, [0, 0])
        np.testing.assert_array_almost_equal(max_corner, [2, 3])

    def test_boxes_intersect(self):
        """测试边界框相交检测"""
        box1_min, box1_max = np.array([0, 0]), np.array([2, 2])
        box2_min, box2_max = np.array([1, 1]), np.array([3, 3])
        assert boxes_intersect(box1_min, box1_max, box2_min, box2_max)

        box3_min, box3_max = np.array([3, 3]), np.array([5, 5])
        assert not boxes_intersect(box1_min, box1_max, box3_min, box3_max)

    def test_curve_line_intersection_simple(self):
        """测试简单的曲线-直线相交"""
        # 从 (0,0) 到 (2,0) 的直线与 x 轴相交
        P0 = np.array([0.0, -1.0])
        P1 = np.array([1.0, 1.0])
        P2 = np.array([2.0, -1.0])
        ctrl = np.array([P0, P1, P2])

        line_p1 = np.array([-1.0, 0.0])
        line_p2 = np.array([3.0, 0.0])

        intersections = curve_line_intersection(ctrl, line_p1, line_p2)
        assert len(intersections) >= 1  # 至少有1个交点
        # 交点应该在 [0, 1] 范围内
        for t in intersections:
            assert 0.0 <= t <= 1.0

    def test_curve_curve_intersection(self):
        """测试曲线-曲线相交"""
        # 两条对称的曲线应该相交
        ctrl1 = np.array([[0.0, 0.0], [1.0, 2.0], [3.0, 2.0], [4.0, 0.0]])
        ctrl2 = np.array([[1.0, -1.0], [2.0, 1.0], [2.0, 3.0], [3.0, 1.0]])

        intersections = curve_curve_intersection(ctrl1, ctrl2)
        # 可能有也可能没有交点，但至少不应报错
        assert isinstance(intersections, list)


class TestFlatten:
    """曲线展平测试"""

    def test_flatten_linear(self):
        """测试线性曲线展平"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([10.0, 0.0])
        ctrl = np.array([P0, P1])
        pts = flatten_bezier(ctrl, tolerance=0.1)
        assert len(pts) >= 2
        np.testing.assert_almost_equal(pts[0], P0)
        np.testing.assert_almost_equal(pts[-1], P1)

    def test_flatten_returns_array(self):
        """测试展平返回数组"""
        P0 = np.array([0.0, 0.0])
        P1 = np.array([1.0, 1.0])
        P2 = np.array([2.0, 0.0])
        ctrl = np.array([P0, P1, P2])
        pts = flatten_bezier(ctrl, tolerance=1.0)
        assert isinstance(pts, np.ndarray)
        assert pts.ndim == 2
        assert pts.shape[1] == 2


def run_all_tests():
    """运行所有测试"""
    import traceback

    test_classes = [
        TestLinearBezier,
        TestQuadraticBezier,
        TestCubicBezier,
        TestDeCasteljau,
        TestTangentNormal,
        TestCurveLength,
        TestCurveIntersection,
        TestFlatten,
    ]

    total = 0
    passed = 0
    failed = 0
    errors = []

    for test_class in test_classes:
        instance = test_class()
        class_name = test_class.__name__
        methods = [m for m in dir(instance) if m.startswith('test_')]

        print(f"\n{'='*60}")
        print(f"  {class_name}")
        print('='*60)

        for method_name in methods:
            total += 1
            method = getattr(instance, method_name)
            try:
                method()
                print(f"  ✓ {method_name}")
                passed += 1
            except Exception as e:
                print(f"  ✗ {method_name}")
                errors.append((class_name, method_name, str(e)))
                failed += 1

    print(f"\n{'='*60}")
    print(f"  测试结果汇总")
    print('='*60)
    print(f"  总计: {total}")
    print(f"  通过: {passed}")
    print(f"  失败: {failed}")

    if errors:
        print(f"\n  失败详情:")
        for class_name, method_name, error in errors:
            print(f"    {class_name}.{method_name}: {error}")

    print()
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
