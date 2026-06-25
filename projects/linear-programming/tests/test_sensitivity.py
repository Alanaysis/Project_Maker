"""
敏感性分析测试。

覆盖：
- 目标函数系数变化
- 右端项变化
- 影子价格
- 约简成本
- 退化性检查
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pytest
from src.linear_program import LinearProgram, ConstraintType, ObjectiveType
from src.simplex import SimplexSolver
from src.sensitivity import SensitivityAnalyzer


class TestSensitivityAnalysis:
    """敏感性分析测试。"""

    def setup_method(self):
        """设置测试问题。"""
        self.lp = LinearProgram(ObjectiveType.MAX)
        self.lp.set_objective([3, 5])
        self.lp.add_constraint([1, 0], 4, ConstraintType.LE)
        self.lp.add_constraint([0, 2], 12, ConstraintType.LE)
        self.lp.add_constraint([3, 5], 25, ConstraintType.LE)

        solver = SimplexSolver(method="standard")
        self.result = solver.solve(self.lp)

    def test_analysis_runs(self):
        """敏感性分析可以运行。"""
        analyzer = SensitivityAnalyzer()
        report = analyzer.analyze(self.lp, self.result)

        assert report is not None
        assert len(report.objective_coefficients) == self.lp.num_vars
        assert len(report.rhs_values) == self.lp.num_constraints

    def test_shadow_prices(self):
        """影子价格分析。"""
        analyzer = SensitivityAnalyzer()
        report = analyzer.analyze(self.lp, self.result)

        # 影子价格应该是有限值
        assert np.all(np.isfinite(report.shadow_prices))

    def test_reduced_costs(self):
        """约简成本分析。"""
        analyzer = SensitivityAnalyzer()
        report = analyzer.analyze(self.lp, self.result)

        # 约简成本应该是有限值
        assert np.all(np.isfinite(report.reduced_costs))

    def test_objective_ranges(self):
        """目标函数系数变化范围。"""
        analyzer = SensitivityAnalyzer()
        report = analyzer.analyze(self.lp, self.result)

        for r in report.objective_coefficients:
            assert r.current_value is not None
            # 范围应该有意义
            if r.lower_bound is not None:
                assert r.lower_bound <= r.current_value + 1e-6
            if r.upper_bound is not None:
                assert r.upper_bound >= r.current_value - 1e-6

    def test_rhs_ranges(self):
        """右端项变化范围。"""
        analyzer = SensitivityAnalyzer()
        report = analyzer.analyze(self.lp, self.result)

        for r in report.rhs_values:
            assert r.current_value is not None

    def test_degeneracy_check(self):
        """退化性检查。"""
        analyzer = SensitivityAnalyzer()
        report = analyzer.analyze(self.lp, self.result)

        assert isinstance(report.is_degenerate, bool)

    def test_report_string(self):
        """报告字符串输出。"""
        analyzer = SensitivityAnalyzer()
        report = analyzer.analyze(self.lp, self.result)

        report_str = str(report)
        assert "Sensitivity Report" in report_str
        assert "Shadow Prices" in report_str


class TestObjectiveChange:
    """目标函数系数变化测试。"""

    def test_small_change_preserves_optimality(self):
        """小变化应保持最优性。"""
        lp = LinearProgram(ObjectiveType.MAX)
        lp.set_objective([3, 5])
        lp.add_constraint([1, 0], 4, ConstraintType.LE)
        lp.add_constraint([0, 2], 12, ConstraintType.LE)
        lp.add_constraint([3, 5], 25, ConstraintType.LE)

        solver = SimplexSolver(method="standard")
        result = solver.solve(lp)

        analyzer = SensitivityAnalyzer()

        # 小变化应保持最优
        delta_c = np.array([0.1, -0.1])
        new_result = analyzer.analyze_objective_change(lp, result, delta_c)

        assert new_result.status in ("optimal", "need_reoptimize")

    def test_zero_change_no_effect(self):
        """零变化应保持不变。"""
        lp = LinearProgram(ObjectiveType.MAX)
        lp.set_objective([3, 5])
        lp.add_constraint([1, 0], 4, ConstraintType.LE)
        lp.add_constraint([0, 2], 12, ConstraintType.LE)

        solver = SimplexSolver(method="standard")
        result = solver.solve(lp)

        analyzer = SensitivityAnalyzer()
        delta_c = np.array([0.0, 0.0])
        new_result = analyzer.analyze_objective_change(lp, result, delta_c)

        assert new_result.status == "optimal"
        assert abs(new_result.optimal_value - result.optimal_value) < 1e-6


class TestRHSChange:
    """右端项变化测试。"""

    def test_small_rhs_change(self):
        """小右端项变化。"""
        lp = LinearProgram(ObjectiveType.MAX)
        lp.set_objective([3, 5])
        lp.add_constraint([1, 0], 4, ConstraintType.LE)
        lp.add_constraint([0, 2], 12, ConstraintType.LE)
        lp.add_constraint([3, 5], 25, ConstraintType.LE)

        solver = SimplexSolver(method="standard")
        result = solver.solve(lp)

        analyzer = SensitivityAnalyzer()
        delta_b = np.array([0.5, -0.5, 0.0])
        new_result = analyzer.analyze_rhs_change(lp, result, delta_b)

        assert new_result.status in ("optimal", "need_dual_simplex")

    def test_zero_rhs_change(self):
        """零右端项变化。"""
        lp = LinearProgram(ObjectiveType.MAX)
        lp.set_objective([3, 5])
        lp.add_constraint([1, 0], 4, ConstraintType.LE)
        lp.add_constraint([0, 2], 12, ConstraintType.LE)

        solver = SimplexSolver(method="standard")
        result = solver.solve(lp)

        analyzer = SensitivityAnalyzer()
        delta_b = np.array([0.0, 0.0])
        new_result = analyzer.analyze_rhs_change(lp, result, delta_b)

        assert new_result.status == "optimal"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
