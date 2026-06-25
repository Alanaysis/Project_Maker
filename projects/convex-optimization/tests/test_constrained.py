"""
约束优化测试
"""

import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.constrained.lagrangian import Lagrangian, AugmentedLagrangian
from src.constrained.kkt import KKTChecker, verify_kkt_for_qp
from src.constrained.interior_point import BarrierMethod


class TestLagrangian:
    """拉格朗日函数测试"""

    def test_unconstrained(self):
        """测试无约束情况"""
        objective = lambda x: x[0] ** 2 + x[1] ** 2
        L = Lagrangian(objective)

        x = np.array([1.0, 2.0])
        assert abs(L(x) - 5.0) < 1e-10

    def test_with_eq_constraint(self):
        """测试等式约束"""
        objective = lambda x: x[0] ** 2 + x[1] ** 2
        eq_constraint = lambda x: x[0] + x[1] - 1  # x + y = 1
        L = Lagrangian(objective, eq_constraints=[eq_constraint])

        x = np.array([0.5, 0.5])
        nu = np.array([2.0])
        # L = 0.5 + (0.5)^2 + 2*(0.5+0.5-1) = 0.5
        assert abs(L(x, nu_eq=nu) - 0.5) < 1e-10

    def test_with_ineq_constraint(self):
        """测试不等式约束"""
        objective = lambda x: x[0] ** 2 + x[1] ** 2
        ineq_constraint = lambda x: x[0] + x[1] - 1  # x + y ≤ 1
        L = Lagrangian(objective, ineq_constraints=[ineq_constraint])

        x = np.array([0.5, 0.5])
        lam = np.array([1.0])
        # L = 0.5 + 1*(0.5+0.5-1) = 0.5
        assert abs(L(x, lambda_ineq=lam) - 0.5) < 1e-10


class TestAugmentedLagrangian:
    """增广拉格朗日测试"""

    def test_eq_constraint(self):
        """测试等式约束"""
        objective = lambda x: x[0] ** 2 + x[1] ** 2
        eq_constraint = lambda x: x[0] + x[1] - 1
        AL = AugmentedLagrangian(
            objective,
            eq_constraints=[eq_constraint],
            rho=1.0,
        )

        x = np.array([0.5, 0.5])
        nu = np.array([0.0])
        # L_A = 0.5 + 0 + 0.5*(0)^2 = 0.5
        assert abs(AL(x, nu_eq=nu) - 0.5) < 1e-10

    def test_multiplier_update(self):
        """测试乘子更新"""
        objective = lambda x: x[0] ** 2
        eq_constraint = lambda x: x[0] - 1
        AL = AugmentedLagrangian(
            objective,
            eq_constraints=[eq_constraint],
            rho=1.0,
        )

        x = np.array([0.5])
        nu = np.array([0.0])

        new_lam, new_nu = AL.update_multipliers(x, np.array([]), nu)
        # new_nu = 0 + 1*(0.5-1) = -0.5
        assert abs(new_nu[0] - (-0.5)) < 1e-10


class TestKKT:
    """KKT 条件测试"""

    def test_simple_qp(self):
        """测试简单二次规划"""
        # min 0.5*x^2 + 0.5*y^2
        # s.t. x + y = 1
        # 最优解: x = y = 0.5, nu = -0.5

        grad_obj = lambda x: x
        eq_constraints = [lambda x: x[0] + x[1] - 1]
        grad_eq = [lambda x: np.array([1.0, 1.0])]

        checker = KKTChecker(
            grad_obj=grad_obj,
            grad_eq=grad_eq,
            eq_constraints=eq_constraints,
        )

        x = np.array([0.5, 0.5])
        nu = np.array([-0.5])  # 正确的乘子

        result = checker.check(x, np.array([]), nu)
        assert result.stationarity
        assert result.primal_feasibility

    def test_inequality_constraint(self):
        """测试不等式约束"""
        # min x^2 + y^2
        # s.t. x + y ≤ 1
        # 最优解: x = y = 0, lambda = 0

        grad_obj = lambda x: 2 * x
        ineq_constraints = [lambda x: x[0] + x[1] - 1]
        grad_ineq = [lambda x: np.array([1.0, 1.0])]

        checker = KKTChecker(
            grad_obj=grad_obj,
            grad_ineq=grad_ineq,
            ineq_constraints=ineq_constraints,
        )

        x = np.array([0.0, 0.0])
        lam = np.array([0.0])

        result = checker.check(x, lam, np.array([]))
        assert result.stationarity
        assert result.primal_feasibility
        assert result.dual_feasibility
        assert result.complementary_slackness


class TestBarrierMethod:
    """障碍函数法测试"""

    def test_simple_problem(self):
        """测试简单约束问题"""
        # min x^2
        # s.t. x ≥ 1 (即 -x + 1 ≤ 0)
        # 最优解: x = 1

        objective = lambda x: x[0] ** 2
        grad_obj = lambda x: np.array([2 * x[0]])
        ineq_constraints = [lambda x: -x[0] + 1]
        grad_ineq = [lambda x: np.array([-1.0])]

        barrier = BarrierMethod(
            objective=objective,
            grad_obj=grad_obj,
            ineq_constraints=ineq_constraints,
            grad_ineq=grad_ineq,
            t0=1.0,
            mu=10.0,
            max_iter=20,
        )

        x0 = np.array([2.0])
        result = barrier.solve(x0)

        # 应该接近 1.0
        assert abs(result.x[0] - 1.0) < 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
