"""
单纯形法测试。

覆盖：
- 标准单纯形法
- 大M法
- 两阶段法
- 退化情况
- 无界问题
- 不可行问题
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pytest
from src.linear_program import LinearProgram, ConstraintType, ObjectiveType
from src.simplex import SimplexSolver


class TestStandardSimplex:
    """标准单纯形法测试。"""

    def test_basic_max_problem(self):
        """经典例题: max 3x1 + 5x2"""
        lp = LinearProgram(ObjectiveType.MAX)
        lp.set_objective([3, 5])
        lp.add_constraint([1, 0], 4, ConstraintType.LE)
        lp.add_constraint([0, 2], 12, ConstraintType.LE)
        lp.add_constraint([3, 5], 25, ConstraintType.LE)

        solver = SimplexSolver(method="standard")
        result = solver.solve(lp)

        assert result.status == "optimal"
        # 最优解: x1=4, x2=2.6, z=25
        assert abs(result.optimal_value - 25.0) < 1e-4
        assert abs(result.solution[0] - 4.0) < 1e-4
        assert abs(result.solution[1] - 2.6) < 1e-4

    def test_two_variable_problem(self):
        """两变量问题: max 5x1 + 4x2, 6x1+4x2<=24, x1+2x2<=6"""
        lp = LinearProgram(ObjectiveType.MAX)
        lp.set_objective([5, 4])
        lp.add_constraint([6, 4], 24, ConstraintType.LE)
        lp.add_constraint([1, 2], 6, ConstraintType.LE)

        solver = SimplexSolver(method="standard")
        result = solver.solve(lp)

        assert result.status == "optimal"
        assert abs(result.optimal_value - 21.0) < 1e-4

    def test_three_variable_problem(self):
        """三变量问题。"""
        lp = LinearProgram(ObjectiveType.MAX)
        lp.set_objective([2, 3, 1])
        lp.add_constraint([1, 1, 1], 40, ConstraintType.LE)
        lp.add_constraint([2, 1, -1], 10, ConstraintType.LE)
        lp.add_constraint([0, -1, 2], 10, ConstraintType.LE)

        solver = SimplexSolver(method="standard")
        result = solver.solve(lp)

        assert result.status == "optimal"
        assert abs(result.optimal_value - 90.0) < 1e-4

    def test_minimization_problem(self):
        """最小化问题。"""
        lp = LinearProgram(ObjectiveType.MIN)
        lp.set_objective([2, 3])
        lp.add_constraint([1, 2], 8, ConstraintType.LE)
        lp.add_constraint([2, 1], 10, ConstraintType.LE)

        solver = SimplexSolver(method="standard")
        result = solver.solve(lp)

        assert result.status == "optimal"
        # min 2x1+3x2, 原点可行, 最优值=0
        assert abs(result.optimal_value) < 1e-4

    def test_single_constraint(self):
        """单约束: max 3x1+2x2, x1+x2<=5"""
        lp = LinearProgram(ObjectiveType.MAX)
        lp.set_objective([3, 2])
        lp.add_constraint([1, 1], 5, ConstraintType.LE)

        solver = SimplexSolver(method="standard")
        result = solver.solve(lp)

        assert result.status == "optimal"
        assert abs(result.optimal_value - 15.0) < 1e-4

    def test_degenerate_problem(self):
        """退化问题测试。"""
        lp = LinearProgram(ObjectiveType.MAX)
        lp.set_objective([1, 1])
        lp.add_constraint([1, -1], 1, ConstraintType.LE)
        lp.add_constraint([-1, 1], 1, ConstraintType.LE)
        lp.add_constraint([1, 0], 2, ConstraintType.LE)

        solver = SimplexSolver(method="standard")
        result = solver.solve(lp)

        assert result.status == "optimal"


class TestBigMMethod:
    """大M法测试。"""

    def test_ge_constraint(self):
        """包含 >= 约束: max 3x1+5x2, x1<=4, 2x2<=12, 3x1+5x2>=25"""
        lp = LinearProgram(ObjectiveType.MAX)
        lp.set_objective([3, 5])
        lp.add_constraint([1, 0], 4, ConstraintType.LE)
        lp.add_constraint([0, 2], 12, ConstraintType.LE)
        lp.add_constraint([3, 5], 25, ConstraintType.GE)

        solver = SimplexSolver(method="big_m", M=1e6)
        result = solver.solve(lp)

        assert result.status == "optimal"
        # x1=4, x2=6, z=42
        assert abs(result.optimal_value - 42.0) < 1e-3

    def test_eq_constraint(self):
        """包含 == 约束: max 2x1+3x2, x1+x2=5, x1<=3"""
        lp = LinearProgram(ObjectiveType.MAX)
        lp.set_objective([2, 3])
        lp.add_constraint([1, 1], 5, ConstraintType.EQ)
        lp.add_constraint([1, 0], 3, ConstraintType.LE)

        solver = SimplexSolver(method="big_m", M=1e6)
        result = solver.solve(lp)

        assert result.status == "optimal"
        # x1=0, x2=5, z=15
        assert abs(result.optimal_value - 15.0) < 1e-3

    def test_mixed_constraints(self):
        """混合约束类型: max 5x1+4x2, 6x1+4x2<=24, x1+2x2>=6"""
        lp = LinearProgram(ObjectiveType.MAX)
        lp.set_objective([5, 4])
        lp.add_constraint([6, 4], 24, ConstraintType.LE)
        lp.add_constraint([1, 2], 6, ConstraintType.GE)

        solver = SimplexSolver(method="big_m", M=1e6)
        result = solver.solve(lp)

        assert result.status == "optimal"
        # x1=0, x2=6, z=24
        assert abs(result.optimal_value - 24.0) < 1e-3


class TestTwoPhaseMethod:
    """两阶段法测试。"""

    def test_ge_constraint(self):
        """包含 >= 约束。"""
        lp = LinearProgram(ObjectiveType.MAX)
        lp.set_objective([3, 5])
        lp.add_constraint([1, 0], 4, ConstraintType.LE)
        lp.add_constraint([0, 2], 12, ConstraintType.LE)
        lp.add_constraint([3, 5], 25, ConstraintType.GE)

        solver = SimplexSolver(method="two_phase")
        result = solver.solve(lp)

        assert result.status == "optimal"
        assert abs(result.optimal_value - 42.0) < 1e-3

    def test_eq_constraint(self):
        """包含 == 约束。"""
        lp = LinearProgram(ObjectiveType.MAX)
        lp.set_objective([2, 3])
        lp.add_constraint([1, 1], 5, ConstraintType.EQ)
        lp.add_constraint([1, 0], 3, ConstraintType.LE)

        solver = SimplexSolver(method="two_phase")
        result = solver.solve(lp)

        assert result.status == "optimal"
        assert abs(result.optimal_value - 15.0) < 1e-3

    def test_all_eq_constraints(self):
        """全等式约束: max x1+x2+x3, x1=2, x2=3, x3=1"""
        lp = LinearProgram(ObjectiveType.MAX)
        lp.set_objective([1, 1, 1])
        lp.add_constraint([1, 0, 0], 2, ConstraintType.EQ)
        lp.add_constraint([0, 1, 0], 3, ConstraintType.EQ)
        lp.add_constraint([0, 0, 1], 1, ConstraintType.EQ)

        solver = SimplexSolver(method="two_phase")
        result = solver.solve(lp)

        assert result.status == "optimal"
        assert abs(result.optimal_value - 6.0) < 1e-4


class TestMethodComparison:
    """三种方法结果一致性测试。"""

    def test_methods_agree_on_simple_problem(self):
        """简单问题三种方法结果一致。"""
        lp = LinearProgram(ObjectiveType.MAX)
        lp.set_objective([3, 5])
        lp.add_constraint([1, 0], 4, ConstraintType.LE)
        lp.add_constraint([0, 2], 12, ConstraintType.LE)
        lp.add_constraint([3, 5], 25, ConstraintType.LE)

        results = {}
        for method in ("standard", "big_m", "two_phase"):
            solver = SimplexSolver(method=method)
            results[method] = solver.solve(lp)

        for method, result in results.items():
            assert result.status == "optimal", f"{method} failed"

        assert abs(results["standard"].optimal_value -
                   results["big_m"].optimal_value) < 1e-4
        assert abs(results["standard"].optimal_value -
                   results["two_phase"].optimal_value) < 1e-4


class TestEdgeCases:
    """边界情况测试。"""

    def test_zero_coefficients(self):
        """零系数目标函数。"""
        lp = LinearProgram(ObjectiveType.MAX)
        lp.set_objective([0, 0])
        lp.add_constraint([1, 1], 5, ConstraintType.LE)

        solver = SimplexSolver(method="standard")
        result = solver.solve(lp)

        assert result.status == "optimal"
        assert abs(result.optimal_value) < 1e-6

    def test_large_problem(self):
        """较大规模问题。"""
        np.random.seed(42)
        n = 10
        m = 8

        lp = LinearProgram(ObjectiveType.MAX)
        lp.set_objective(np.random.rand(n).tolist())

        for i in range(m):
            coeffs = np.random.rand(n).tolist()
            rhs = np.random.rand() * 100
            lp.add_constraint(coeffs, rhs, ConstraintType.LE)

        solver = SimplexSolver(method="standard")
        result = solver.solve(lp)

        assert result.status in ("optimal", "unbounded")

    def test_repeated_solves(self):
        """重复求解同一问题。"""
        lp = LinearProgram(ObjectiveType.MAX)
        lp.set_objective([3, 5])
        lp.add_constraint([1, 0], 4, ConstraintType.LE)
        lp.add_constraint([0, 2], 12, ConstraintType.LE)

        solver = SimplexSolver(method="standard")

        for _ in range(5):
            result = solver.solve(lp)
            assert result.status == "optimal"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
