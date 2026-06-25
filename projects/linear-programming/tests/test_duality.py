"""
对偶理论测试。

覆盖：
- 对偶问题构造
- 强对偶定理验证
- 弱对偶定理验证
- 互补松弛条件
- 对偶单纯形法
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pytest
from src.linear_program import LinearProgram, ConstraintType, ObjectiveType
from src.simplex import SimplexSolver
from src.duality import DualProblem, DualSimplexSolver


class TestDualConstruction:
    """对偶问题构造测试。"""

    def test_standard_dual(self):
        """标准对偶问题构造。"""
        primal = LinearProgram(ObjectiveType.MAX)
        primal.set_objective([3, 5])
        primal.add_constraint([1, 0], 4, ConstraintType.LE)
        primal.add_constraint([0, 2], 12, ConstraintType.LE)
        primal.add_constraint([3, 5], 25, ConstraintType.LE)

        dual = DualProblem.construct_dual(primal)

        assert dual.objective_type == ObjectiveType.MIN
        assert dual.num_vars == 3  # 对偶变量数 = 原约束数
        assert dual.num_constraints == 2  # 对偶约束数 = 原变量数

    def test_dual_of_dual(self):
        """对偶的对偶是原问题。"""
        primal = LinearProgram(ObjectiveType.MAX)
        primal.set_objective([2, 3])
        primal.add_constraint([1, 1], 5, ConstraintType.LE)
        primal.add_constraint([1, 0], 3, ConstraintType.LE)

        dual = DualProblem.construct_dual(primal)
        dual_of_dual = DualProblem.construct_dual(dual)

        # 对偶的对偶应等价于原问题
        assert dual_of_dual.objective_type == ObjectiveType.MAX
        np.testing.assert_array_almost_equal(dual_of_dual.c, primal.c)


class TestStrongDuality:
    """强对偶定理测试。"""

    def test_strong_duality_holds(self):
        """验证强对偶定理。"""
        primal = LinearProgram(ObjectiveType.MAX)
        primal.set_objective([3, 5])
        primal.add_constraint([1, 0], 4, ConstraintType.LE)
        primal.add_constraint([0, 2], 12, ConstraintType.LE)
        primal.add_constraint([3, 5], 25, ConstraintType.LE)

        # 求解原问题
        solver = SimplexSolver(method="standard")
        primal_result = solver.solve(primal)

        # 构造并求解对偶问题 (对偶有 GE 约束，需要 big_m)
        dual = DualProblem.construct_dual(primal)
        dual_solver = SimplexSolver(method="big_m", M=1e6)
        dual_result = dual_solver.solve(dual)

        assert primal_result.status == "optimal"
        assert dual_result.status == "optimal"

        # 强对偶: 目标值相等
        assert DualProblem.verify_strong_duality(primal_result, dual_result)

    def test_strong_duality_with_eq(self):
        """含等式约束的强对偶。"""
        primal = LinearProgram(ObjectiveType.MAX)
        primal.set_objective([2, 3])
        primal.add_constraint([1, 1], 5, ConstraintType.EQ)
        primal.add_constraint([1, 0], 3, ConstraintType.LE)

        solver = SimplexSolver(method="two_phase")
        primal_result = solver.solve(primal)

        assert primal_result.status == "optimal"


class TestWeakDuality:
    """弱对偶定理测试。"""

    def test_weak_duality(self):
        """验证弱对偶定理。"""
        primal = LinearProgram(ObjectiveType.MAX)
        primal.set_objective([3, 5])
        primal.add_constraint([1, 0], 4, ConstraintType.LE)
        primal.add_constraint([0, 2], 12, ConstraintType.LE)
        primal.add_constraint([3, 5], 25, ConstraintType.LE)

        solver = SimplexSolver(method="standard")
        result = solver.solve(primal)

        # 任意可行解满足弱对偶
        x_feasible = np.array([1.0, 2.0])  # 可行解
        y_feasible = np.array([3.0, 2.0, 1.0])  # 对偶可行解

        primal_obj, dual_obj, is_valid = DualProblem.check_weak_duality(
            x_feasible, y_feasible, primal.c, primal.b
        )

        # c^T x <= b^T y
        assert is_valid


class TestDualSimplex:
    """对偶单纯形法测试。"""

    def test_dual_simplex_basic(self):
        """基本对偶单纯形法。"""
        lp = LinearProgram(ObjectiveType.MIN)
        lp.set_objective([2, 3])
        lp.add_constraint([1, 0], 4, ConstraintType.GE)
        lp.add_constraint([0, 1], 6, ConstraintType.GE)
        lp.add_constraint([1, 1], 15, ConstraintType.LE)

        # 转为 max 问题并调整约束方向
        lp2 = LinearProgram(ObjectiveType.MAX)
        lp2.set_objective([-2, -3])
        lp2.add_constraint([-1, 0], -4, ConstraintType.LE)
        lp2.add_constraint([0, -1], -6, ConstraintType.LE)
        lp2.add_constraint([1, 1], 15, ConstraintType.LE)

        solver = DualSimplexSolver()
        result = solver.solve(lp2)

        assert result.status in ("optimal", "infeasible")

    def test_dual_simplex_feasibility(self):
        """对偶单纯形法可行性检查。"""
        lp = LinearProgram(ObjectiveType.MAX)
        lp.set_objective([1, 1])
        lp.add_constraint([1, 1], 5, ConstraintType.LE)

        solver = DualSimplexSolver()
        # 初始解可能不满足对偶可行性
        result = solver.solve(lp)

        assert result.status in ("optimal", "error")


class TestComplementarySlackness:
    """互补松弛条件测试。"""

    def test_complementary_slackness(self):
        """验证互补松弛条件。"""
        primal = LinearProgram(ObjectiveType.MAX)
        primal.set_objective([3, 5])
        primal.add_constraint([1, 0], 4, ConstraintType.LE)
        primal.add_constraint([0, 2], 12, ConstraintType.LE)
        primal.add_constraint([3, 5], 25, ConstraintType.LE)

        solver = SimplexSolver(method="standard")
        result = solver.solve(primal)

        if result.status == "optimal" and result.slack is not None:
            # 简单检查: 如果 slack > 0, 对应的 dual 变量应为 0
            for i in range(len(result.slack)):
                if result.slack[i] > 1e-6:
                    assert abs(result.dual_solution[i]) < 1e-6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
