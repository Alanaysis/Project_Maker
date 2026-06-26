"""
示例 4: 图解法可视化 (Graphical Method Visualization)

对于 2 变量线性规划问题，可以用图解法直观展示:
    - 可行域 (Feasible Region)
    - 约束线 (Constraint Lines)
    - 目标函数等值线 (Objective Function Level Curves)
    - 最优解 (Optimal Solution)

这个示例演示如何用 matplotlib 可视化 2D LP 问题。
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from src.problem import create_problem, maximize, format_problem_text
from src.simplex import SimplexSolver


def solve_and_visualize():
    """
    求解 2D LP 问题并绘制图解。
    """
    try:
        import matplotlib
        matplotlib.use("Agg")  # 非交互式后端
        import matplotlib.pyplot as plt
        from matplotlib.patches import Polygon
        has_matplotlib = True
    except ImportError:
        print("matplotlib 未安装，跳过可视化。")
        print("安装: pip install matplotlib")
        return

    # 问题: 最大化 z = 3x1 + 2x2
    # 约束:
    #   x1 + x2 <= 4
    #   x1 <= 3
    #   x2 <= 2
    #   x1, x2 >= 0

    prob = maximize(
        c=[3, 2],
        A=[
            [1, 1],
            [1, 0],
            [0, 1],
        ],
        b=[4, 3, 2],
        variable_names=["x1", "x2"],
        constraint_names=["C1: x1+x2<=4", "C2: x1<=3", "C3: x2<=2"],
    )

    print("问题描述:")
    print(format_problem_text(prob))

    # 求解
    solver = SimplexSolver(prob)
    result = solver.solve()
    print(f"\n最优解: {result}")

    # 可视化
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))

    # 定义网格
    x1_range = np.linspace(0, 4.5, 200)
    x2_range = np.linspace(0, 4.5, 200)
    X1, X2 = np.meshgrid(x1_range, x2_range)

    # 绘制约束
    # C1: x1 + x2 <= 4
    ax.fill_between(x1_range, 0, 4 - x1_range, alpha=0.1, color="blue", label="C1: x1+x2 ≤ 4")
    ax.plot(x1_range, 4 - x1_range, "b-", linewidth=2)

    # C2: x1 <= 3
    ax.axvline(x=3, color="green", linewidth=2, label="C2: x1 ≤ 3")
    ax.fill_between([0, 3], 0, 5, alpha=0.05, color="green")

    # C3: x2 <= 2
    ax.axhline(y=2, color="red", linewidth=2, label="C3: x2 ≤ 2")
    ax.fill_between([0, 4.5], 0, 2, alpha=0.05, color="red")

    # 确定可行域顶点
    feasible_vertices = [
        (0, 0),
        (3, 0),
        (3, 1),  # x1=3, x1+x2=4 -> x2=1
        (2, 2),  # x2=2, x1+x2=4 -> x1=2
        (0, 2),
    ]

    # 绘制可行域
    feasible_poly = Polygon(feasible_vertices, closed=True, fill=True,
                           facecolor="lightblue", edgecolor="darkblue",
                           linewidth=2, alpha=0.5)
    ax.add_patch(feasible_poly)

    # 绘制目标函数等值线
    z_values = [0, 3, 6, 9, 12]
    for z in z_values:
        if z > 0:
            x2_line = (z - 3 * x1_range) / 2
            ax.plot(x1_range, x2_line, "k--", alpha=0.3, linewidth=0.8)

    # 标记顶点
    for i, (x1, x2) in enumerate(feasible_vertices):
        ax.plot(x1, x2, "ko", markersize=8)
        ax.text(x1 + 0.1, x2 + 0.1, f"({x1},{x2})", fontsize=9)

    # 标记最优解
    opt_x1, opt_x2 = result.solution[0], result.solution[1]
    ax.plot(opt_x1, opt_x2, "r*", markersize=20, label=f"最优解 ({opt_x1:.1f}, {opt_x2:.1f})")
    ax.text(opt_x1 + 0.1, opt_x2 - 0.3, f"z={result.optimal_value:.1f}",
            fontsize=12, color="red", fontweight="bold")

    ax.set_xlabel("x1 (产品1产量)", fontsize=12)
    ax.set_ylabel("x2 (产品2产量)", fontsize=12)
    ax.set_title("图解法: 生产计划问题", fontsize=14)
    ax.legend(loc="upper right", fontsize=10)
    ax.set_xlim(0, 4.5)
    ax.set_ylim(0, 4.5)
    ax.grid(True, alpha=0.3)
    ax.set_aspect("equal")

    plt.tight_layout()
    plt.savefig("/home/siok/project_copyninja/projects/linear-programming/examples/graphical_method.png",
                dpi=150, bbox_inches="tight")
    print("\n可视化已保存: graphical_method.png")


if __name__ == "__main__":
    solve_and_visualize()
