"""
示例 3: 运输问题 (Transportation Problem)

经典的线性规划问题: 在满足供需平衡的前提下，最小化运输成本。

问题描述:
    3 个工厂向 4 个仓库运输货物，求最小运输成本。

    工厂产量:
        - 工厂 1: 30 单位
        - 工厂 2: 45 单位
        - 工厂 3: 25 单位

    仓库需求:
        - 仓库 1: 20 单位
        - 仓库 2: 30 单位
        - 仓库 3: 35 单位
        - 仓库 4: 15 单位

    单位运输成本矩阵 (工厂 -> 仓库):
        [[ 8,  6, 10, 12],
         [ 9, 12,  7,  8],
         [14,  9, 11, 13]]

数学模型:
    最小化 z = sum(c_ij * x_ij)
    约束:
        sum(x_ij for j) = supply_i  (每个工厂的出货量 = 产量)
        sum(x_ij for i) = demand_j  (每个仓库的收货量 = 需求)
        x_ij >= 0
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from src.problem import create_problem, minimize, format_problem_text
from src.simplex import SimplexSolver
from src.dual import DualSolver


def main():
    print("=" * 60)
    print("示例 3: 运输问题 (Transportation Problem)")
    print("=" * 60)
    print()

    # 数据
    supply = [30, 45, 25]     # 工厂产量
    demand = [20, 30, 35, 15]  # 仓库需求
    cost = [
        [8, 6, 10, 12],
        [9, 12, 7, 8],
        [14, 9, 11, 13],
    ]

    n_factories = len(supply)
    n_warehouses = len(demand)

    # 检查供需平衡
    total_supply = sum(supply)
    total_demand = sum(demand)
    print(f"总产量: {total_supply}")
    print(f"总需求: {total_demand}")
    assert total_supply == total_demand, "运输问题需要供需平衡!"
    print()

    # 构建 LP 问题
    # 决策变量: x_ij = 从工厂 i 运到仓库 j 的数量
    # 共 n_factories * n_warehouses 个变量
    n_vars = n_factories * n_warehouses

    # 目标函数系数
    c = []
    for i in range(n_factories):
        for j in range(n_warehouses):
            c.append(cost[i][j])

    # 约束矩阵
    A = []
    b = []
    constraint_names = []

    # 工厂供应约束 (等式): sum(x_ij for j) = supply_i
    for i in range(n_factories):
        row = [0] * n_vars
        for j in range(n_warehouses):
            row[i * n_warehouses + j] = 1
        A.append(row)
        b.append(supply[i])
        constraint_names.append(f"工厂{i+1}供应")

    # 仓库需求约束 (等式): sum(x_ij for i) = demand_j
    for j in range(n_warehouses):
        row = [0] * n_vars
        for i in range(n_factories):
            row[i * n_warehouses + j] = 1
        A.append(row)
        b.append(demand[j])
        constraint_names.append(f"仓库{j+1}需求")

    variable_names = []
    for i in range(n_factories):
        for j in range(n_warehouses):
            variable_names.append(f"x_{i+1}{j+1}")

    prob = minimize(
        c=c,
        A=A,
        b=b,
        variable_names=variable_names,
        constraint_names=constraint_names,
    )

    print("1. 问题建模:")
    print("-" * 40)
    print(format_problem_text(prob))

    # 求解
    print("\n2. 求解运输问题:")
    print("-" * 40)
    solver = SimplexSolver(prob)
    result = solver.solve()
    print(result)

    # 输出运输方案
    if result.status == "optimal":
        print("\n3. 最优运输方案:")
        print("-" * 40)
        print(f"最小运输成本: {result.optimal_value:.2f}")
        print()
        print("运输矩阵 (工厂 -> 仓库):")
        print(" " + " " * 6 + "  ".join(f"仓库{j+1:>4}" for j in range(n_warehouses)))
        print(" " * 10 + "-" * (n_warehouses * 6))
        for i in range(n_factories):
            row_str = ""
            for j in range(n_warehouses):
                val = result.solution[i * n_warehouses + j]
                row_str += f"{val:>6.1f}  "
            print(f"工厂{i+1} |{row_str}")

    # 对偶分析
    print("\n4. 对偶分析 (影子价格):")
    print("-" * 40)
    dual_solver = DualSolver(prob)
    dual_result = dual_solver.solve_dual()
    print(f"原问题最优值: {dual_result['primal']['optimal_value']:.2f}")
    print(f"对偶问题最优值: {dual_result['dual']['optimal_value']:.2f}")
    print(f"强对偶成立: {dual_result['strong_duality_holds']}")


if __name__ == "__main__":
    main()
