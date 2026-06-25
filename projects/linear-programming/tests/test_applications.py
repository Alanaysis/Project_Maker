"""
实际应用测试。

覆盖：
- 生产计划问题
- 运输问题
- 指派问题
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pytest
from src.linear_program import LinearProgram, ConstraintType, ObjectiveType
from src.applications import (
    ProductionPlanner, TransportationSolver, AssignmentSolver
)


class TestProductionPlanner:
    """生产计划测试。"""

    def test_basic_production(self):
        """基本生产计划问题。"""
        planner = ProductionPlanner()
        planner.add_resource("工时", 100)
        planner.add_resource("原料", 80)
        planner.add_product("产品A", profit=10, cost=3, usage=[2, 1], max_demand=30)
        planner.add_product("产品B", profit=15, cost=5, usage=[3, 2], max_demand=20)

        result = planner.optimize(method="big_m")

        assert result.status == "optimal"
        assert result.optimal_value > 0

    def test_single_product(self):
        """单一产品。"""
        planner = ProductionPlanner()
        planner.add_resource("工时", 50)
        planner.add_product("产品A", profit=10, cost=2, usage=[5])

        result = planner.optimize(method="standard")

        assert result.status == "optimal"
        # 最大产量 = 50/5 = 10, 利润 = 10 * (10-2) = 80
        assert abs(result.optimal_value - 80.0) < 1e-4

    def test_three_products(self):
        """三产品问题。"""
        planner = ProductionPlanner()
        planner.add_resource("机器", 120)
        planner.add_resource("人工", 100)
        planner.add_resource("原料", 80)
        planner.add_product("A", profit=20, cost=5, usage=[4, 2, 1], max_demand=20)
        planner.add_product("B", profit=30, cost=8, usage=[2, 4, 3], max_demand=15)
        planner.add_product("C", profit=25, cost=6, usage=[3, 3, 2], max_demand=10)

        result = planner.optimize(method="big_m")

        assert result.status == "optimal"

    def test_report_generation(self):
        """报告生成。"""
        planner = ProductionPlanner()
        planner.add_resource("工时", 100)
        planner.add_product("产品A", profit=10, cost=3, usage=[5])

        result = planner.optimize(method="standard")
        report = planner.report(result)

        assert "生产计划报告" in report
        assert "最大利润" in report


class TestTransportationSolver:
    """运输问题测试。"""

    def test_balanced_transport(self):
        """供需平衡的运输问题。"""
        solver = TransportationSolver()
        cost = [[2, 3, 1], [4, 1, 5], [3, 2, 4]]
        supply = [30, 40, 20]
        demand = [25, 35, 30]

        result = solver.solve(cost, supply, demand, method="two_phase")

        assert result.status == "optimal"
        assert result.optimal_value > 0

    def test_unbalanced_supply_exceeds(self):
        """供大于求。"""
        solver = TransportationSolver()
        cost = [[2, 3], [4, 1]]
        supply = [30, 40]
        demand = [25, 30]

        result = solver.solve(cost, supply, demand, method="two_phase")

        assert result.status == "optimal"

    def test_unbalanced_demand_exceeds(self):
        """供不应求。"""
        solver = TransportationSolver()
        cost = [[2, 3], [4, 1]]
        supply = [20, 30]
        demand = [25, 40]

        result = solver.solve(cost, supply, demand, method="two_phase")

        assert result.status == "optimal"

    def test_two_by_two(self):
        """2x2 运输问题。"""
        solver = TransportationSolver()
        cost = [[10, 20], [30, 15]]
        supply = [50, 50]
        demand = [40, 60]

        result = solver.solve(cost, supply, demand, method="two_phase")

        assert result.status == "optimal"
        # 最优: S1->D1=40, S1->D2=10, S2->D2=50
        # 成本 = 40*10 + 10*20 + 50*15 = 400+200+750 = 1350

    def test_northwest_corner(self):
        """西北角法。"""
        supply = np.array([30, 40, 20])
        demand = np.array([25, 35, 30])

        alloc = TransportationSolver.northwest_corner(supply, demand)

        # 检查供需约束
        np.testing.assert_array_almost_equal(alloc.sum(axis=1), supply)
        np.testing.assert_array_almost_equal(alloc.sum(axis=0), demand)

    def test_least_cost_method(self):
        """最小元素法。"""
        cost = np.array([[2, 3, 1], [4, 1, 5], [3, 2, 4]])
        supply = np.array([30, 40, 20])
        demand = np.array([25, 35, 30])

        alloc = TransportationSolver.least_cost_method(cost, supply, demand)

        # 检查供需约束
        np.testing.assert_array_almost_equal(alloc.sum(axis=1), supply)
        np.testing.assert_array_almost_equal(alloc.sum(axis=0), demand)


class TestAssignmentSolver:
    """指派问题测试。"""

    def test_basic_assignment(self):
        """基本指派问题。"""
        solver = AssignmentSolver()
        cost = [[9, 2, 7], [6, 4, 3], [5, 8, 1]]

        result = solver.solve(cost, method="two_phase")

        assert result.status == "optimal"
        # 最优指派: W1->T2(2), W2->T3(3), W3->T1(5) = 10

    def test_identity_cost(self):
        """单位成本矩阵。"""
        solver = AssignmentSolver()
        cost = [[1, 2, 3], [2, 4, 6], [3, 6, 9]]

        result = solver.solve(cost, method="two_phase")

        assert result.status == "optimal"

    def test_two_by_two(self):
        """2x2 指派问题: W1->T1(5), W2->T2(1) = 6"""
        solver = AssignmentSolver()
        cost = [[5, 8], [4, 1]]

        result = solver.solve(cost, method="two_phase")

        assert result.status == "optimal"
        assert abs(result.optimal_value - 6.0) < 1e-4

    def test_hungarian_algorithm(self):
        """匈牙利算法测试。"""
        cost = np.array([[9, 2, 7], [6, 4, 3], [5, 8, 1]])
        assignment, total_cost = AssignmentSolver.hungarian_algorithm(cost)

        assert len(assignment) == 3
        assert total_cost > 0

    def test_report_generation(self):
        """报告生成。"""
        solver = AssignmentSolver()
        cost = [[9, 2, 7], [6, 4, 3], [5, 8, 1]]
        result = solver.solve(cost, method="two_phase")
        report = solver.report(result, np.array(cost))

        assert "指派方案报告" in report


class TestApplicationIntegration:
    """应用集成测试。"""

    def test_production_then_sensitivity(self):
        """生产计划 + 敏感性分析。"""
        from src.sensitivity import SensitivityAnalyzer

        planner = ProductionPlanner()
        planner.add_resource("工时", 100)
        planner.add_product("产品A", profit=10, cost=3, usage=[5])

        result = planner.optimize(method="standard")

        if result.status == "optimal":
            analyzer = SensitivityAnalyzer()
            lp = planner.build_lp()
            report = analyzer.analyze(lp, result)

            assert report is not None

    def test_transport_solution_shape(self):
        """运输问题解的形状。"""
        solver = TransportationSolver()
        cost = [[2, 3, 1], [4, 1, 5], [3, 2, 4]]
        supply = [30, 40, 20]
        demand = [25, 35, 30]

        result = solver.solve(cost, supply, demand, method="two_phase")

        if result.status == "optimal":
            assert result.solution.shape == (3, 3)

    def test_assignment_solution_shape(self):
        """指派问题解的形状。"""
        solver = AssignmentSolver()
        cost = [[9, 2, 7], [6, 4, 3], [5, 8, 1]]

        result = solver.solve(cost, method="two_phase")

        if result.status == "optimal":
            assert result.solution.shape == (3, 3)
            # 每行每列恰好一个 1
            for i in range(3):
                assert abs(result.solution[i, :].sum() - 1.0) < 1e-6
                assert abs(result.solution[:, i].sum() - 1.0) < 1e-6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
