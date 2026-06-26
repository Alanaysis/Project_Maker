"""
示例 5: 灵敏度分析演示 (Sensitivity Analysis Demo)

演示如何使用灵敏度分析来理解 LP 问题的稳健性。

主要演示:
    1. 目标系数变化对最优解的影响
    2. 约束右侧变化对最优解的影响
    3. 100% 规则的应用
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from src.problem import create_problem, maximize, format_problem_text
from src.simplex import SimplexSolver
from src.sensitivity import SensitivityAnalyzer


def main():
    print("=" * 60)
    print("示例 5: 灵敏度分析演示 (Sensitivity Analysis)")
    print("=" * 60)
    print()

    # 生产计划问题
    prob = maximize(
        c=[3, 2],
        A=[
            [1, 1],
            [1, 0],
            [0, 1],
        ],
        b=[4, 3, 2],
        variable_names=["产品1", "产品2"],
        constraint_names=["机器时间", "产能1", "产能2"],
    )

    print("原始问题:")
    print(format_problem_text(prob))

    # 求解
    solver = SimplexSolver(prob)
    result = solver.solve()
    print(f"\n原始最优解: z = {result.optimal_value:.4f}")
    print(f"  产品1: {result.solution[0]:.4f}")
    print(f"  产品2: {result.solution[1]:.4f}")

    # 灵敏度分析
    print("\n" + "=" * 60)
    print("灵敏度分析结果")
    print("=" * 60)

    analyzer = SensitivityAnalyzer(prob, result)
    analysis = analyzer.analyze()

    # 1. 影子价格
    print("\n1. 影子价格 (Shadow Prices):")
    print("-" * 40)
    shadow_prices = analysis["shadow_prices"]
    for i, price in enumerate(shadow_prices):
        cons_name = prob.constraint_names[i] if prob.constraint_names else f"约束 {i+1}"
        print(f"  {cons_name}: {price:.4f}")
    print("\n  解释: 机器时间每增加 1 小时，利润增加 {:.4f} 元".format(shadow_prices[0]))
    print("  解释: 产能1每增加 1 单位，利润增加 {:.4f} 元".format(shadow_prices[1]))
    print("  解释: 产能2每增加 1 单位，利润增加 {:.4f} 元".format(shadow_prices[2]))

    # 2. 目标系数变化范围
    print("\n2. 目标系数允许变化范围:")
    print("-" * 40)
    for r in analysis["objective_ranges"]:
        var_name = prob.variable_names[r["variable"]] if prob.variable_names else f"变量 {r['variable']+1}"
        lb = r["lower_bound"]
        ub = r["upper_bound"]
        if lb == float("-inf"):
            lb_str = "-inf"
        else:
            lb_str = f"{lb:.4f}"
        if ub == float("inf"):
            ub_str = "inf"
        else:
            ub_str = f"{ub:.4f}"
        print(f"  {var_name}: [{lb_str}, {ub_str}] (当前值: {r['current_value']:.4f})")

    # 3. 约束右侧变化范围
    print("\n3. 约束右侧允许变化范围:")
    print("-" * 40)
    for r in analysis["rhs_ranges"]:
        cons_name = prob.constraint_names[r["constraint"]] if prob.constraint_names else f"约束 {r['constraint']+1}"
        lb = r["lower_bound"]
        ub = r["upper_bound"]
        sp = r["shadow_price"]
        if lb == float("-inf"):
            lb_str = "-inf"
        else:
            lb_str = f"{lb:.4f}"
        if ub == float("inf"):
            ub_str = "inf"
        else:
            ub_str = f"{ub:.4f}"
        print(f"  {cons_name}: [{lb_str}, {ub_str}] (影子价格: {sp:.4f})")

    # 4. 100% 规则演示
    print("\n4. 100% 规则演示 (多系数同时变化):")
    print("-" * 40)

    # 同时改变两个目标系数
    change1 = (0, 1.0)   # x1 的系数增加 1
    change2 = (1, -0.5)  # x2 的系数减少 0.5

    pct_result = analyzer.check_100pct_rule([change1, change2])
    print(f"  变化: x1系数 +{change1[1]:.1f}, x2系数 {change2[1]:.1f}")
    print(f"  总变化比例: {pct_result['total_ratio']:.4f}")
    print(f"  满足 100% 规则: {pct_result['within_100pct_range']}")

    # 5. 实际变化演示
    print("\n5. 实际变化演示:")
    print("-" * 40)

    # 改变机器时间约束
    original_b = prob.b.copy()
    for delta in [0.5, 1.0, 2.0, -1.0]:
        prob.b[0] = original_b[0] + delta
        solver2 = SimplexSolver(prob)
        result2 = solver2.solve()
        print(f"  机器时间 +{delta:.1f}: z = {result2.optimal_value:.4f}, "
              f"产品1={result2.solution[0]:.4f}, 产品2={result2.solution[1]:.4f}")

    # 恢复原始问题
    prob.b = original_b


if __name__ == "__main__":
    main()
