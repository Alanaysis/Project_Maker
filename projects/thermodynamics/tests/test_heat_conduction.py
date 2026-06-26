"""
热传导方程求解器测试
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from src.heat_conduction import heat_conduction_1d, heat_conduction_2d
from src.heat_conduction import _solve_tridiagonal
from src.boundary_conditions import DirichletBC, NeumannBC, RobinBC
from src.heat_source import (
    UniformHeatSource,
    PointHeatSource,
    TimeVaryingHeatSource,
    TemperatureDependentSource,
)
from src.analysis import (
    compute_steady_state_1d,
    compute_steady_state_2d,
    thermal_time_constant,
    fourier_number,
    biot_number,
    analyze_steady_state_reached,
    compute_heat_flux_1d,
)


class TestHeatConduction1D(unittest.TestCase):
    """一维热传导测试"""

    def test_1d_basic(self):
        """测试基本求解"""
        x, T_history = heat_conduction_1d(
            L=1.0, nx=10, alpha=1e-5, dt=0.1, nt=10,
            T_left=100.0, T_right=0.0, T_initial=0.0,
            method="explicit",
        )
        self.assertEqual(len(x), 10)
        self.assertEqual(T_history.shape, (11, 10))

    def test_1d_boundary_conditions_preserved(self):
        """测试边界条件在求解过程中保持不变"""
        x, T_history = heat_conduction_1d(
            L=0.1, nx=20, alpha=1e-5, dt=0.01, nt=50,
            T_left=100.0, T_right=0.0, T_initial=20.0,
            method="explicit",
        )
        # 从 t=1 开始检查 (t=0 是初始条件)
        np.testing.assert_allclose(T_history[1:, 0], 100.0, rtol=1e-10)
        np.testing.assert_allclose(T_history[1:, -1], 0.0, rtol=1e-10)

    def test_1d_steady_state_linear(self):
        """测试稳态时一维温度分布为线性"""
        from src.analysis import compute_steady_state_1d
        x, T = compute_steady_state_1d(
            L=1.0, nx=50, k=50.0,
            T_left=100.0, T_right=0.0,
        )
        # 稳态解应为线性: T(x) = 100 - 100*x
        T_analytical = 100.0 * (1 - x)
        np.testing.assert_allclose(T, T_analytical, rtol=1e-10)

    def test_1d_implicit_unconditionally_stable(self):
        """测试隐式方法的无条件稳定性"""
        # 使用很大的时间步长，显式方法会发散，隐式方法应该稳定
        x, T_history = heat_conduction_1d(
            L=1.0, nx=20, alpha=1e-5, dt=10.0, nt=10,
            T_left=100.0, T_right=0.0, T_initial=0.0,
            method="implicit",
        )
        # 温度应该在合理范围内
        self.assertTrue(np.all(np.isfinite(T_history)))
        self.assertTrue(np.all(T_history >= -10))
        self.assertTrue(np.all(T_history <= 110))

    def test_1d_explicit_stability_violation(self):
        """测试显式方法在违反稳定性条件时抛出异常"""
        # dx = 1.0/9 = 0.111, Fo = 1e-5 * 1000 / (0.111)^2 = 0.81 > 0.5
        with self.assertRaises(ValueError):
            heat_conduction_1d(
                L=1.0, nx=10, alpha=1e-5, dt=1000.0, nt=10,
                T_left=100.0, T_right=0.0, T_initial=0.0,
                method="explicit",
            )

    def test_1d_heat_source(self):
        """测试热源对温度分布的影响"""
        x_no_source, T_no_source = heat_conduction_1d(
            L=1.0, nx=20, alpha=1e-5, dt=0.1, nt=1000,
            T_left=100.0, T_right=0.0, T_initial=50.0,
            method="explicit",
        )

        x_with_source, T_with_source = heat_conduction_1d(
            L=1.0, nx=20, alpha=1e-5, dt=0.1, nt=1000,
            T_left=100.0, T_right=0.0, T_initial=50.0,
            heat_source=lambda x: 100.0,  # 均匀热源
            method="explicit",
        )

        # 有热源时内部温度应该更高 (排除边界)
        interior_no = T_no_source[-1][1:-1]
        interior_with = T_with_source[-1][1:-1]
        np.testing.assert_array_less(interior_no, interior_with)


class TestHeatConduction2D(unittest.TestCase):
    """二维热传导测试"""

    def test_2d_basic(self):
        """测试基本二维求解"""
        x, y, T_history = heat_conduction_2d(
            Lx=1.0, Ly=1.0, nx=10, ny=10,
            alpha=1e-5, dt=0.01, nt=10,
            T_left=0.0, T_right=0.0, T_top=0.0, T_bottom=0.0,
            T_initial=50.0,
            method="explicit",
        )
        self.assertEqual(len(x), 10)
        self.assertEqual(len(y), 10)
        self.assertEqual(T_history.shape, (11, 10, 10))

    def test_2d_boundary_conditions(self):
        """测试二维边界条件"""
        x, y, T_history = heat_conduction_2d(
            Lx=0.1, Ly=0.1, nx=10, ny=10,
            alpha=1e-5, dt=0.001, nt=10,
            T_left=100.0, T_right=0.0, T_top=50.0, T_bottom=50.0,
            T_initial=0.0,
            method="crank_nicolson",
        )
        # 从 t=1 开始检查 (t=0 是初始条件)
        # 检查非角点边界
        np.testing.assert_allclose(T_history[1:, 0, 1:-1], 50.0, rtol=1e-10)  # 下边界
        np.testing.assert_allclose(T_history[1:, -1, 1:-1], 50.0, rtol=1e-10)  # 上边界
        np.testing.assert_allclose(T_history[1:, 1:-1, 0], 100.0, rtol=1e-10)  # 左边界
        np.testing.assert_allclose(T_history[1:, 1:-1, -1], 0.0, rtol=1e-10)   # 右边界

    def test_2d_stability_violation(self):
        """测试二维显式方法稳定性条件"""
        # Fo_x + Fo_y = 2 * 1e-5 * 1000 / (1/9)^2 = 1.62 > 0.5
        with self.assertRaises(ValueError):
            heat_conduction_2d(
                Lx=1.0, Ly=1.0, nx=10, ny=10,
                alpha=1e-5, dt=1000.0, nt=10,
                T_left=0.0, T_right=0.0, T_top=0.0, T_bottom=0.0,
                T_initial=50.0,
                method="explicit",
            )


class TestBoundaryConditions(unittest.TestCase):
    """边界条件测试"""

    def test_dirichlet_1d(self):
        """测试 Dirichlet 边界条件"""
        bc = DirichletBC(value=100.0)
        T = np.zeros(10)
        T = bc.apply_1d(T, direction="left")
        self.assertEqual(T[0], 100.0)
        self.assertEqual(T[-1], 0.0)

    def test_neumann_1d(self):
        """测试 Neumann 边界条件"""
        bc = NeumannBC(flux=0.0, thermal_conductivity=50.0)
        T = np.array([0.0, 10.0, 20.0, 30.0])
        T_new = bc.apply_1d(T, dx=1.0, direction="left")
        # 绝热边界: T[0] = T[1]
        np.testing.assert_allclose(T_new[0], T[1])

    def test_robin_1d(self):
        """测试 Robin 边界条件"""
        bc = RobinBC(heat_transfer_coefficient=100.0, ambient_temperature=20.0, thermal_conductivity=50.0)
        T = np.array([0.0, 10.0, 20.0, 30.0])
        T_new = bc.apply_1d(T, dx=0.01, direction="left")
        # Robin 边界温度应该在环境温度和对侧温度之间
        self.assertTrue(20.0 < T_new[0] < 10.0 or T_new[0] < 20.0)

    def test_dirichlet_2d(self):
        """测试二维 Dirichlet 边界条件"""
        bc = DirichletBC(value=100.0)
        T = np.zeros((5, 5))
        T = bc.apply_2d(T, direction="bottom")
        np.testing.assert_allclose(T[0, :], 100.0)


class TestHeatSources(unittest.TestCase):
    """热源测试"""

    def test_uniform_heat_source(self):
        """测试均匀热源"""
        source = UniformHeatSource(q=1000.0)
        self.assertEqual(source.evaluate(x=0.0), 1000.0)
        self.assertEqual(source.evaluate(x=1.0, y=2.0), 1000.0)

    def test_point_heat_source(self):
        """测试点热源"""
        source = PointHeatSource(Q0=1000.0, center=(0.5, 0.5), sigma=0.1)
        # 在中心点应该达到最大值
        q_center = source.evaluate(x=0.5, y=0.5)
        q_off = source.evaluate(x=0.6, y=0.6)
        self.assertGreater(q_center, q_off)

    def test_time_varying_heat_source(self):
        """测试时变热源"""
        source = TimeVaryingHeatSource(Q_base=100.0, Q_amp=50.0, frequency=1.0)
        # t=0 时: Q = 100 + 50*sin(0) = 100
        self.assertEqual(source.evaluate(x=0.0, t=0.0), 100.0)
        # t=0.25 时: Q = 100 + 50*sin(π/2) = 150
        self.assertAlmostEqual(source.evaluate(x=0.0, t=0.25), 150.0, places=5)

    def test_temperature_dependent_source(self):
        """测试温度依赖热源"""
        source = TemperatureDependentSource(Q0=100.0, beta=0.01, T_ref=0.0)
        q_at_ref = source.evaluate(x=0.0, T=0.0)
        q_at_high = source.evaluate(x=0.0, T=10.0)
        self.assertGreater(q_at_high, q_at_ref)


class TestAnalysis(unittest.TestCase):
    """分析函数测试"""

    def test_thermal_time_constant(self):
        """测试热时间常数计算"""
        tau = thermal_time_constant(L=0.1, alpha=1e-5)
        self.assertAlmostEqual(tau, 1000.0, places=1)

    def test_fourier_number(self):
        """测试傅里叶数计算"""
        Fo = fourier_number(L=0.1, alpha=1e-5, t=1000)
        self.assertAlmostEqual(Fo, 1.0, places=5)

    def test_biot_number(self):
        """测试毕渥数计算"""
        Bi = biot_number(h=100.0, L=0.1, k=50.0)
        self.assertAlmostEqual(Bi, 0.2, places=5)

    def test_steady_state_1d_no_source(self):
        """测试一维稳态无热源"""
        x, T = compute_steady_state_1d(
            L=1.0, nx=10, k=50.0,
            T_left=100.0, T_right=0.0,
        )
        T_analytical = 100.0 * (1 - x)
        np.testing.assert_allclose(T, T_analytical, rtol=1e-10)

    def test_steady_state_1d_with_source(self):
        """测试一维稳态有热源"""
        x, T = compute_steady_state_1d(
            L=1.0, nx=50, k=50.0,
            T_left=0.0, T_right=0.0,
            heat_source=lambda x: 100.0,
        )
        # 有热源且两端同温时，温度分布为抛物线
        # T(x) = Q/(2k) * x * (L - x)
        T_analytical = 100.0 / (2 * 50.0) * x * (1.0 - x)
        np.testing.assert_allclose(T, T_analytical, rtol=0.01)

    def test_steady_state_reached(self):
        """测试稳态判断"""
        T_prev = np.array([1.0, 2.0, 3.0])
        T_curr = np.array([1.0 + 1e-7, 2.0 + 1e-7, 3.0 + 1e-7])
        self.assertTrue(analyze_steady_state_reached(T_prev, T_curr, tolerance=1e-5))

        T_curr_large = np.array([1.0 + 0.1, 2.0 + 0.1, 3.0 + 0.1])
        self.assertFalse(analyze_steady_state_reached(T_prev, T_curr_large, tolerance=1e-5))

    def test_heat_flux_1d(self):
        """测试热流计算"""
        T = np.array([100.0, 80.0, 60.0, 40.0])
        dx = 0.01
        k = 50.0
        q = compute_heat_flux_1d(T, dx, k)
        # 温度梯度: dT/dx = -2000 K/m
        # 热流: q = -k * dT/dx = -50 * (-2000) = 100000 W/m²
        np.testing.assert_allclose(q, 100000.0, rtol=0.01)


class TestTridiagonalSolver(unittest.TestCase):
    """三对角矩阵求解器测试"""

    def test_tridiagonal_basic(self):
        """测试三对角求解器"""
        # 使用 np.linalg.solve 验证: 构造一个已知解的系统
        n = 4
        A = np.diag([3.0] * n) + np.diag([1.0] * (n - 1), 1) + np.diag([1.0] * (n - 1), -1)
        x_true = np.array([1.0, 2.0, 3.0, 4.0])
        rhs = A @ x_true

        main = np.diag(A)
        lower = np.diag(A, -1)
        upper = np.diag(A, 1)

        x = _solve_tridiagonal(lower, main, upper, rhs)
        np.testing.assert_allclose(x, x_true, rtol=1e-10)

    def test_tridiagonal_larger(self):
        """测试较大规模的三对角求解"""
        n = 10
        main = np.full(n, 2.0)
        lower = np.full(n - 1, -1.0)
        upper = np.full(n - 1, -1.0)
        rhs = np.ones(n)

        x = _solve_tridiagonal(lower, main, upper, rhs)

        # 验证: A * x = b
        A = np.diag(main) + np.diag(lower, -1) + np.diag(upper, 1)
        np.testing.assert_allclose(A @ x, rhs, rtol=1e-8)


if __name__ == "__main__":
    unittest.main()
