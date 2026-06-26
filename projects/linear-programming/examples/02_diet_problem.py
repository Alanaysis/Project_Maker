"""
示例 2: 饮食问题 (Diet Problem)

经典的线性规划问题: 在满足营养需求的前提下，最小化食物成本。

问题描述:
    需要选择食物组合，满足每日营养需求，同时成本最低。

    食物:
        - 面包 (bread):  每片 1 元, 含 50g 碳水, 5g 蛋白, 2g 脂肪
        - 牛奶 (milk):   每杯 2 元, 含 100g 碳水, 8g 蛋白, 10g 脂肪
        - 鸡蛋 (egg):    每个 3 元, 含 10g 碳水, 13g 蛋白, 5g 脂肪

    营养需求 (每日):
        - 碳水 >= 200g
        - 蛋白 >= 30g
        - 脂肪 <= 25g

数学模型:
    最小化 z = 1*x1 + 2*x2 + 3*x3
    约束:
        50*x1 + 100*x2 + 10*x3 >= 200   (碳水需求)
        5*x1 + 8*x2 + 13*x3 >= 30       (蛋白需求)
        2*x1 + 10*x2 + 5*x3 <= 25       (脂肪上限)
        x1, x2, x3 >= 0
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from src.problem import create_problem, minimize, format_problem_text
from src.simplex import SimplexSolver
from src.big_m import BigMSolver
from src.analysis import SolutionAnalyzer


def main():
    print("=" * 60)
    print("示例 2: 饮食问题 (Diet Problem)")
    print("=" * 60)
    print()

    # 1. 问题建模
    print("1. 问题建模:")
    print("-" * 40)
    prob = minimize(
        c=[1, 2, 3],
        A=[
            [50, 100, 10],   # 碳水
            [5, 8, 13],      # 蛋白
            [2, 10, 5],      # 脂肪
        ],
        b=[200, 30, 25],
        variable_names=["面包(片)", "牛奶(杯)", "鸡蛋(个)"],
        constraint_names=["碳水需求", "蛋白需求", "脂肪上限"],
    )
    print(format_problem_text(prob))

    # 2. 使用大M法求解 (因为存在 >= 约束，需要人工变量)
    print("\n2. 大M法求解:")
    print("-" * 40)

    # 先尝试标准单纯形法
    solver = SimplexSolver(prob)
    result = solver.solve()

    if result.status == "infeasible":
        # 如果没有明显初始基，使用大M法
        print("检测到需要人工变量，使用大M法...")
        big_m_solver = BigMSolver(prob)
        result = big_m_solver.solve()

    print(result)

    # 3. 分析结果
    print("\n3. 结果分析:")
    print("-" * 40)
    analyzer = SolutionAnalyzer(prob)

    if result.status == "optimal":
        print(f"最低成本: {result.optimal_value:.2f} 元")
        print("\n最优饮食方案:")
        if prob.variable_names:
            for name, val in zip(prob.variable_names, result.solution):
                if val > 1e-6:
                    print(f"  {name}: {val:.4f}")
        else:
            for i, val in enumerate(result.solution):
                if val > 1e-6:
                    print(f"  x{i+1}: {val:.4f}")

        # 检查多重最优解
        if result.tableau_history:
            has_multiple, zero_vars = analyzer.check_multiple_optimal(
                result.tableau_history[-1]
            )
            if has_multiple:
                print("\n检测到多重最优解!")
                solutions = analyzer.find_alternate_optimal_solutions(
                    result.tableau_history[-1], result.basis
                )
                for i, sol in enumerate(solutions):
                    print(f"  替代方案 {i+1}:")
                    for name, val in zip(prob.variable_names or [], sol):
                        if val > 1e-6:
                            print(f"    {name}: {val:.4f}")
    else:
        print(f"问题状态: {result.status}")


if __name__ == "__main__":
    main()
