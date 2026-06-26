"""
示例 1: 生产计划问题 (Production Planning Problem)

一个工厂生产两种产品，需要决定每种产品生产多少以最大化利润。

问题描述:
    产品 1: 每件利润 3 元，需要 1 小时机器时间
    产品 2: 每件利润 2 元，需要 1 小时机器时间
    机器总可用时间: 4 小时
    产品 1 最多生产 3 件
    产品 2 最多生产 2 件

数学模型:
    最大化 z = 3*x1 + 2*x2
    约束:
        x1 + x2 <= 4     (机器时间约束)
        x1 <= 3          (产品 1 产能约束)
        x2 <= 2          (产品 2 产能约束)
        x1, x2 >= 0
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from src.problem import create_problem, maximize, format_problem_text
from src.simplex import SimplexSolver
from src.dual import DualSolver
from src.sensitivity import SensitivityAnalyzer


def main():
    print("=" * 60)
    print("示例 1: 生产计划问题 (Production Planning)")
    print("=" * 60)
    print()

    # 1. 问题建模
    print("1. 问题建模:")
    print("-" * 40)
    prob = maximize(
        c=[3, 2],
        A=[
            [1, 1],  # 机器时间约束
            [1, 0],  # 产品 1 产能约束
            [0, 1],  # 产品 2 产能约束
        ],
        b=[4, 3, 2],
        variable_names=["产品1产量", "产品2产量"],
        constraint_names=["机器时间", "产能1", "产能2"],
    )
    print(format_problem_text(prob))

    # 2. 求解
    print("\n2. 单纯形法求解:")
    print("-" * 40)
    solver = SimplexSolver(prob)
    result = solver.solve()
    print(result)

    # 3. 对偶问题分析
    print("\n3. 对偶问题分析 (影子价格):")
    print("-" * 40)
    dual_solver = DualSolver(prob)
    dual_result = dual_solver.solve_dual()
    print(f"原问题最优值: {dual_result['primal']['optimal_value']:.6f}")
    print(f"对偶问题最优值: {dual_result['dual']['optimal_value']:.6f}")
    print(f"对偶间隙: {dual_result['duality_gap']:.2e}")
    print(f"强对偶定理成立: {dual_result['strong_duality_holds']}")

    # 4. 灵敏度分析
    print("\n4. 灵敏度分析:")
    print("-" * 40)
    sens = SensitivityAnalyzer(prob, result)
    analysis = sens.analyze()
    print("影子价格 (约束的边际价值):")
    for i, price in enumerate(analysis["shadow_prices"]):
        cons_name = prob.constraint_names[i] if prob.constraint_names else f"约束 {i+1}"
        print(f"  {cons_name}: {price:.4f}")

    print("\n目标系数允许变化范围:")
    for r in analysis["objective_ranges"]:
        var_name = prob.variable_names[r["variable"]] if prob.variable_names else f"变量 {r['variable']+1}"
        print(f"  {var_name}: [{r['lower_bound']:.4f}, {r['upper_bound']:.4f}]")

    print("\n约束右侧允许变化范围:")
    for r in analysis["rhs_ranges"]:
        cons_name = prob.constraint_names[r["constraint"]] if prob.constraint_names else f"约束 {r['constraint']+1}"
        print(f"  {cons_name}: [{r['lower_bound']:.4f}, {r['upper_bound']:.4f}]")


if __name__ == "__main__":
    main()
