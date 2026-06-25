"""
QP 求解器测试
"""

import pytest
import numpy as np
from src.qp_solver import QPSolver, QPSolverType, QPResult


class TestQPSolver:
    """QP 求解器测试"""

    def test_unconstrained_hildreth(self):
        """测试无约束 Hildreth 求解"""
        solver = QPSolver(QPSolverType.HILDRETH)

        # min 0.5*x^2 + 0.5*y^2 - x - y
        H = np.array([[1.0, 0.0], [0.0, 1.0]])
        f = np.array([-1.0, -1.0])

        result = solver.solve(H, f)

        assert result.success
        np.testing.assert_array_almost_equal(result.x_optimal, [1.0, 1.0])
        np.testing.assert_almost_equal(result.cost, -1.0)

    def test_constrained_hildreth(self):
        """测试有约束 Hildreth 求解"""
        solver = QPSolver(QPSolverType.HILDRETH)

        # min 0.5*x^2 + 0.5*y^2 - x - y
        # s.t. x <= 0.5
        H = np.array([[1.0, 0.0], [0.0, 1.0]])
        f = np.array([-1.0, -1.0])
        ub = np.array([0.5, np.inf])

        result = solver.solve(H, f, ub=ub)

        assert result.success
        assert result.x_optimal[0] <= 0.5 + 1e-6
        np.testing.assert_almost_equal(result.x_optimal[1], 1.0, decimal=5)

    def test_box_constraints_hildreth(self):
        """测试边界约束 Hildreth 求解"""
        solver = QPSolver(QPSolverType.HILDRETH)

        H = np.array([[2.0, 0.0], [0.0, 2.0]])
        f = np.array([-2.0, -2.0])
        lb = np.array([0.0, 0.0])
        ub = np.array([0.5, 0.5])

        result = solver.solve(H, f, lb=lb, ub=ub)

        assert result.success
        assert np.all(result.x_optimal >= -1e-6)
        assert np.all(result.x_optimal <= 0.5 + 1e-6)

    def test_active_set_solver(self):
        """测试活动集求解器"""
        solver = QPSolver(QPSolverType.ACTIVE_SET)

        H = np.array([[2.0, 0.0], [0.0, 2.0]])
        f = np.array([-2.0, -2.0])
        lb = np.array([0.0, 0.0])

        result = solver.solve(H, f, lb=lb)

        assert result.success
        np.testing.assert_array_almost_equal(result.x_optimal, [1.0, 1.0], decimal=5)

    def test_scipy_solver(self):
        """测试 scipy 求解器"""
        solver = QPSolver(QPSolverType.SCIPY)

        H = np.array([[2.0, 0.0], [0.0, 2.0]])
        f = np.array([-2.0, -2.0])
        lb = np.array([0.0, 0.0])

        result = solver.solve(H, f, lb=lb)

        assert result.success
        np.testing.assert_array_almost_equal(result.x_optimal, [1.0, 1.0], decimal=5)

    def test_inequality_constraints(self):
        """测试不等式约束"""
        solver = QPSolver(QPSolverType.HILDRETH)

        # min 0.5*x^2 + 0.5*y^2
        # s.t. x + y <= 1
        H = np.array([[1.0, 0.0], [0.0, 1.0]])
        f = np.array([0.0, 0.0])
        A_ineq = np.array([[1.0, 1.0]])
        b_ineq = np.array([1.0])

        result = solver.solve(H, f, A_ineq=A_ineq, b_ineq=b_ineq)

        assert result.success
        assert result.x_optimal[0] + result.x_optimal[1] <= 1.0 + 1e-6

    def test_qp_result_attributes(self):
        """测试 QP 结果属性"""
        solver = QPSolver(QPSolverType.HILDRETH)

        H = np.array([[1.0]])
        f = np.array([-1.0])

        result = solver.solve(H, f)

        assert hasattr(result, 'x_optimal')
        assert hasattr(result, 'cost')
        assert hasattr(result, 'iterations')
        assert hasattr(result, 'success')
        assert hasattr(result, 'message')

    def test_regularization(self):
        """测试正则化"""
        solver = QPSolver(
            QPSolverType.HILDRETH,
            regularization=1e-6
        )

        # 几乎奇异的 Hessian
        H = np.array([[1.0, 1.0], [1.0, 1.0]])
        f = np.array([-1.0, -1.0])

        result = solver.solve(H, f)

        # 应该能够求解
        assert result.success

    def test_convergence(self):
        """测试收敛性"""
        solver = QPSolver(
            QPSolverType.HILDRETH,
            max_iterations=100,
            tolerance=1e-10
        )

        # 大规模问题
        n = 10
        H = np.eye(n)
        f = -np.ones(n)

        result = solver.solve(H, f)

        assert result.success
        np.testing.assert_array_almost_equal(result.x_optimal, np.ones(n), decimal=5)

    def test_multiple_constraints(self):
        """测试多重约束"""
        solver = QPSolver(QPSolverType.HILDRETH)

        H = np.eye(2)
        f = np.array([-2.0, -3.0])

        # 多个不等式约束
        A_ineq = np.array([
            [1.0, 0.0],   # x <= 1
            [0.0, 1.0],   # y <= 2
            [-1.0, 0.0],  # -x <= 0 => x >= 0
            [0.0, -1.0]   # -y <= 0 => y >= 0
        ])
        b_ineq = np.array([1.0, 2.0, 0.0, 0.0])

        result = solver.solve(H, f, A_ineq=A_ineq, b_ineq=b_ineq)

        assert result.success
        assert 0 <= result.x_optimal[0] <= 1.0 + 1e-6
        assert 0 <= result.x_optimal[1] <= 2.0 + 1e-6


class TestQPSolverComparison:
    """比较不同 QP 求解器"""

    def test_solvers_give_same_result(self):
        """测试不同求解器给出相同结果"""
        H = np.array([[2.0, 0.5], [0.5, 1.0]])
        f = np.array([-1.0, -2.0])
        lb = np.array([0.0, 0.0])
        ub = np.array([2.0, 2.0])

        # Hildreth
        solver_h = QPSolver(QPSolverType.HILDRETH)
        result_h = solver_h.solve(H, f, lb=lb, ub=ub)

        # scipy
        solver_s = QPSolver(QPSolverType.SCIPY)
        result_s = solver_s.solve(H, f, lb=lb, ub=ub)

        # 结果应该接近
        np.testing.assert_array_almost_equal(
            result_h.x_optimal, result_s.x_optimal, decimal=4
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
