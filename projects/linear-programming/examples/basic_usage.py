"""
线性规划库基本使用示例。

演示：
1. 标准单纯形法求解生产计划
2. 大M法处理混合约束
3. 对偶问题与强对偶验证
4. 敏感性分析
5. 运输问题与指派问题
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
from src.linear_program import LinearProgram, ConstraintType, ObjectiveType
from src.simplex import SimplexSolver
from src.duality import DualProblem, DualSimplexSolver
from src.sensitivity import SensitivityAnalyzer
from src.applications import ProductionPlanner, TransportationSolver, AssignmentSolver


def example_standard_simplex():
    """示例1: 标准单纯形法。"""
    print("=" * 60)
    print("示例1: 标准单纯形法")
    print("=" * 60)

    # 问题: max 3x1 + 5x2
    #       s.t. x1 <= 4
    #            2x2 <= 12
    #            3x1 + 5x2 <= 25
    lp = LinearProgram(ObjectiveType.MAX)
    lp.set_objective([3, 5])
    lp.add_constraint([1, 0], 4, ConstraintType.LE)
    lp.add_constraint([0, 2], 12, ConstraintType.LE)
    lp.add_constraint([3, 5], 25, ConstraintType.LE)

    solver = SimplexSolver(method="standard", verbose=True)
    result = solver.solve(lp)
    print(result)


def example_big_m():
    """示例2: 大M法。"""
    print("\n" + "=" * 60)
    print("示例2: 大M法 (混合约束)")
    print("=" * 60)

    # 问题: max 5x1 + 4x2
    #       s.t. 6x1 + 4x2 <= 24
    #            x1 + 2x2 >= 6
    #            x1, x2 >= 0
    lp = LinearProgram(ObjectiveType.MAX)
    lp.set_objective([5, 4])
    lp.add_constraint([6, 4], 24, ConstraintType.LE)
    lp.add_constraint([1, 2], 6, ConstraintType.GE)

    solver = SimplexSolver(method="big_m", M=1e6)
    result = solver.solve(lp)
    print(result)


def example_two_phase():
    """示例3: 两阶段法。"""
    print("\n" + "=" * 60)
    print("示例3: 两阶段法")
    print("=" * 60)

    # 问题: max 2x1 + 3x2
    #       s.t. x1 + x2 = 5
    #            x1 <= 3
    lp = LinearProgram(ObjectiveType.MAX)
    lp.set_objective([2, 3])
    lp.add_constraint([1, 1], 5, ConstraintType.EQ)
    lp.add_constraint([1, 0], 3, ConstraintType.LE)

    solver = SimplexSolver(method="two_phase")
    result = solver.solve(lp)
    print(result)


def example_duality():
    """示例4: 对偶理论。"""
    print("\n" + "=" * 60)
    print("示例4: 对偶理论")
    print("=" * 60)

    # 原问题
    primal = LinearProgram(ObjectiveType.MAX)
    primal.set_objective([3, 5])
    primal.add_constraint([1, 0], 4, ConstraintType.LE)
    primal.add_constraint([0, 2], 12, ConstraintType.LE)
    primal.add_constraint([3, 5], 25, ConstraintType.LE)

    solver = SimplexSolver(method="standard")
    primal_result = solver.solve(primal)
    print("原问题最优值:", primal_result.optimal_value)

    # 对偶问题
    dual = DualProblem.construct_dual(primal)
    print("\n对偶问题:")
    print(dual)

    dual_result = solver.solve(dual)
    print("\n对偶问题最优值:", dual_result.optimal_value)

    # 强对偶验证
    is_strong = DualProblem.verify_strong_duality(primal_result, dual_result)
    print(f"\n强对偶定理验证: {'通过' if is_strong else '失败'}")


def example_sensitivity():
    """示例5: 敏感性分析。"""
    print("\n" + "=" * 60)
    print("示例5: 敏感性分析")
    print("=" * 60)

    lp = LinearProgram(ObjectiveType.MAX)
    lp.set_objective([3, 5])
    lp.add_constraint([1, 0], 4, ConstraintType.LE)
    lp.add_constraint([0, 2], 12, ConstraintType.LE)
    lp.add_constraint([3, 5], 25, ConstraintType.LE)

    solver = SimplexSolver(method="standard")
    result = solver.solve(lp)

    analyzer = SensitivityAnalyzer()
    report = analyzer.analyze(lp, result)
    print(report)


def example_production_planning():
    """示例6: 生产计划问题。"""
    print("\n" + "=" * 60)
    print("示例6: 生产计划问题")
    print("=" * 60)

    planner = ProductionPlanner()
    planner.add_resource("机器工时", 120)
    planner.add_resource("人工工时", 100)
    planner.add_resource("原材料", 80)

    planner.add_product("产品A", profit=20, cost=5,
                       usage=[4, 2, 1], max_demand=20)
    planner.add_product("产品B", profit=30, cost=8,
                       usage=[2, 4, 3], max_demand=15)
    planner.add_product("产品C", profit=25, cost=6,
                       usage=[3, 3, 2], max_demand=10)

    result = planner.optimize(method="big_m")
    print(planner.report(result))


def example_transportation():
    """示例7: 运输问题。"""
    print("\n" + "=" * 60)
    print("示例7: 运输问题")
    print("=" * 60)

    solver = TransportationSolver()
    cost = [[2, 3, 1], [4, 1, 5], [3, 2, 4]]
    supply = [30, 40, 20]
    demand = [25, 35, 30]

    result = solver.solve(cost, supply, demand, method="two_phase")
    print(TransportationSolver.report(result, np.array(cost),
                                       np.array(supply), np.array(demand)))


def example_assignment():
    """示例8: 指派问题。"""
    print("\n" + "=" * 60)
    print("示例8: 指派问题")
    print("=" * 60)

    solver = AssignmentSolver()
    cost = [[9, 2, 7], [6, 4, 3], [5, 8, 1]]

    result = solver.solve(cost, method="two_phase")
    print(AssignmentSolver.report(result, np.array(cost)))

    # 匈牙利算法对比
    print("\n匈牙利算法结果:")
    assignment, total_cost = AssignmentSolver.hungarian_algorithm(np.array(cost))
    print(f"  指派: {assignment}")
    print(f"  总成本: {total_cost}")


if __name__ == "__main__":
    example_standard_simplex()
    example_big_m()
    example_two_phase()
    example_duality()
    example_sensitivity()
    example_production_planning()
    example_transportation()
    example_assignment()
