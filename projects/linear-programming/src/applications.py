"""
线性规划实际应用模块。

包含三个经典应用：
1. 生产计划问题 - 多产品、多资源的最优生产安排
2. 运输问题 - 供需平衡的最小成本运输方案
3. 指派问题 - 最优任务分配

数学建模：
    生产计划: max sum(p_j * x_j - c_j * x_j), s.t. 资源约束
    运输问题: min sum(c_ij * x_ij), s.t. 供给约束、需求约束
    指派问题: min sum(c_ij * x_ij), s.t. 每行/列和 = 1, x_ij in {0,1}
    (指派问题是运输问题的特例，可用匈牙利算法高效求解)
"""

import numpy as np
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass, field
from .linear_program import LinearProgram, LPResult, ConstraintType, ObjectiveType
from .simplex import SimplexSolver


# ──────────────────────────────────────────────────
# 生产计划问题
# ──────────────────────────────────────────────────

@dataclass
class Product:
    """产品信息"""
    name: str
    profit: float           # 单位利润
    production_cost: float  # 单位生产成本
    resource_usage: np.ndarray  # 各资源的单位消耗
    max_demand: float = np.inf  # 最大需求量
    min_production: float = 0   # 最小产量

    def __post_init__(self):
        self.resource_usage = np.array(self.resource_usage, dtype=float)


@dataclass
class Resource:
    """资源信息"""
    name: str
    capacity: float  # 可用量


class ProductionPlanner:
    """
    生产计划优化器。

    问题描述：
        企业有 m 种资源，可以生产 n 种产品。
        每种产品消耗不同数量的资源，有不同的利润。
        目标是确定各产品的生产量，使总利润最大。

    数学模型：
        max  sum_j (p_j - c_j) * x_j
        s.t. sum_j a_ij * x_j <= b_i,  i = 1,...,m
             x_j >= 0

    Examples
    --------
    >>> planner = ProductionPlanner()
    >>> planner.add_resource("工时", 100)
    >>> planner.add_resource("原料", 80)
    >>> planner.add_product("产品A", profit=10, cost=3, usage=[2, 1], max_demand=30)
    >>> planner.add_product("产品B", profit=15, cost=5, usage=[3, 2], max_demand=20)
    >>> result = planner.optimize()
    """

    def __init__(self):
        self.products: List[Product] = []
        self.resources: List[Resource] = []

    def add_resource(self, name: str, capacity: float):
        """添加资源。"""
        self.resources.append(Resource(name=name, capacity=capacity))

    def add_product(self, name: str, profit: float, cost: float,
                    usage: List[float], max_demand: float = np.inf,
                    min_production: float = 0):
        """添加产品。"""
        assert len(usage) == len(self.resources), \
            f"资源使用维度 {len(usage)} != 资源数 {len(self.resources)}"
        self.products.append(Product(
            name=name, profit=profit, production_cost=cost,
            resource_usage=usage, max_demand=max_demand,
            min_production=min_production
        ))

    def build_lp(self) -> LinearProgram:
        """构造线性规划模型。"""
        lp = LinearProgram(ObjectiveType.MAX)

        # 目标函数: max sum (profit - cost) * x_j
        net_profits = [p.profit - p.production_cost for p in self.products]
        lp.set_objective(net_profits, names=[p.name for p in self.products])

        # 资源约束: sum a_ij * x_j <= b_i
        for i, res in enumerate(self.resources):
            usage = [p.resource_usage[i] for p in self.products]
            lp.add_constraint(usage, res.capacity, ConstraintType.LE)

        # 需求上限约束
        for j, prod in enumerate(self.products):
            if prod.max_demand < np.inf:
                coeffs = np.zeros(len(self.products))
                coeffs[j] = 1
                lp.add_constraint(coeffs, prod.max_demand, ConstraintType.LE)

        # 最小产量约束
        for j, prod in enumerate(self.products):
            if prod.min_production > 0:
                coeffs = np.zeros(len(self.products))
                coeffs[j] = 1
                lp.add_constraint(coeffs, prod.min_production, ConstraintType.GE)

        return lp

    def optimize(self, method: str = "big_m") -> LPResult:
        """求解生产计划问题。"""
        lp = self.build_lp()
        solver = SimplexSolver(method=method)
        return solver.solve(lp)

    def report(self, result: LPResult) -> str:
        """生成生产计划报告。"""
        if result.status != "optimal":
            return f"求解失败: {result.message}"

        lines = ["=== 生产计划报告 ==="]
        lines.append(f"最大利润: {result.optimal_value:.2f}")
        lines.append("\n各产品产量:")
        total_resource_usage = np.zeros(len(self.resources))

        for j, prod in enumerate(self.products):
            qty = result.solution[j]
            profit = qty * (prod.profit - prod.production_cost)
            lines.append(f"  {prod.name}: {qty:.2f} 单位, 利润 = {profit:.2f}")
            total_resource_usage += prod.resource_usage * qty

        lines.append("\n资源使用情况:")
        for i, res in enumerate(self.resources):
            used = total_resource_usage[i]
            util = used / res.capacity * 100 if res.capacity > 0 else 0
            lines.append(f"  {res.name}: {used:.2f} / {res.capacity:.2f} ({util:.1f}%)")

        if result.dual_solution is not None:
            lines.append("\n资源影子价格 (对偶变量):")
            for i, res in enumerate(self.resources):
                if i < len(result.dual_solution):
                    lines.append(f"  {res.name}: {result.dual_solution[i]:.4f}")

        return "\n".join(lines)


# ──────────────────────────────────────────────────
# 运输问题
# ──────────────────────────────────────────────────

class TransportationSolver:
    """
    运输问题求解器。

    问题描述：
        m 个供应点, n 个需求点。
        每个供应点有固定供给量，每个需求点有固定需求量。
        从供应点 i 到需求点 j 的单位运输成本为 c_ij。
        目标是找到总运输成本最小的方案。

    数学模型：
        min  sum_i sum_j c_ij * x_ij
        s.t. sum_j x_ij = s_i,   i = 1,...,m   (供给约束)
             sum_i x_ij = d_j,   j = 1,...,n   (需求约束)
             x_ij >= 0

    特殊情况：
        - 供需平衡: sum(s_i) = sum(d_j)
        - 供大于求: 添加虚拟需求点
        - 供不应求: 添加虚拟供应点

    Examples
    --------
    >>> solver = TransportationSolver()
    >>> cost = [[2, 3, 1], [4, 1, 5], [3, 2, 4]]
    >>> supply = [30, 40, 20]
    >>> demand = [25, 35, 30]
    >>> result = solver.solve(cost, supply, demand)
    """

    def __init__(self):
        pass

    def solve(self, cost: List[List[float]], supply: List[float],
              demand: List[float], method: str = "big_m") -> LPResult:
        """
        求解运输问题。

        Parameters
        ----------
        cost : list of list
            运输成本矩阵 c[i][j]
        supply : list
            各供应点供给量
        demand : list
            各需求点需求量
        method : str
            单纯形法方法

        Returns
        -------
        result : LPResult
            包含最优运输方案
        """
        cost = np.array(cost, dtype=float)
        supply = np.array(supply, dtype=float)
        demand = np.array(demand, dtype=float)
        m, n = cost.shape

        # 处理供需不平衡
        total_supply = supply.sum()
        total_demand = demand.sum()

        if abs(total_supply - total_demand) > 1e-6:
            # 扩展成本矩阵
            if total_supply > total_demand:
                # 添加虚拟需求点
                diff = total_supply - total_demand
                cost = np.column_stack([cost, np.zeros(m)])
                demand = np.append(demand, diff)
                n += 1
            else:
                # 添加虚拟供应点
                diff = total_demand - total_supply
                cost = np.vstack([cost, np.zeros(n)])
                supply = np.append(supply, diff)
                m += 1

        # 构造LP: 变量 x_ij, i=0..m-1, j=0..n-1
        lp = LinearProgram(ObjectiveType.MIN)

        # 目标函数: min sum c_ij * x_ij
        c_vec = cost.flatten()
        lp.set_objective(c_vec)

        # 供给约束: sum_j x_ij = s_i
        for i in range(m):
            coeffs = np.zeros(m * n)
            for j in range(n):
                coeffs[i * n + j] = 1
            lp.add_constraint(coeffs, supply[i], ConstraintType.EQ)

        # 需求约束: sum_i x_ij = d_j
        for j in range(n):
            coeffs = np.zeros(m * n)
            for i in range(m):
                coeffs[i * n + j] = 1
            lp.add_constraint(coeffs, demand[j], ConstraintType.EQ)

        solver = SimplexSolver(method=method)
        result = solver.solve(lp)

        # 重塑解为矩阵形式
        if result.status == "optimal" and result.solution is not None:
            result.solution = result.solution.reshape(m, n)

        return result

    @staticmethod
    def northwest_corner(supply: np.ndarray, demand: np.ndarray) -> np.ndarray:
        """
        西北角法求初始基可行解。

        从左上角开始，依次满足供给或需求。
        """
        m = len(supply)
        n = len(demand)
        alloc = np.zeros((m, n))
        s = supply.copy()
        d = demand.copy()
        i, j = 0, 0

        while i < m and j < n:
            qty = min(s[i], d[j])
            alloc[i, j] = qty
            s[i] -= qty
            d[j] -= qty

            if abs(s[i]) < 1e-10:
                i += 1
            if abs(d[j]) < 1e-10:
                j += 1

        return alloc

    @staticmethod
    def least_cost_method(cost: np.ndarray, supply: np.ndarray,
                          demand: np.ndarray) -> np.ndarray:
        """
        最小元素法求初始基可行解。

        优先选择成本最低的格子进行分配。
        """
        m, n = cost.shape
        alloc = np.zeros((m, n))
        s = supply.copy().astype(float)
        d = demand.copy().astype(float)
        row_done = np.zeros(m, dtype=bool)
        col_done = np.zeros(n, dtype=bool)

        for _ in range(m + n - 1):
            # 找未完成行列中的最小成本格子
            temp_cost = cost.copy().astype(float)
            for i in range(m):
                if row_done[i]:
                    temp_cost[i, :] = np.inf
            for j in range(n):
                if col_done[j]:
                    temp_cost[:, j] = np.inf

            idx = np.unravel_index(np.argmin(temp_cost), temp_cost.shape)
            i, j = idx

            qty = min(s[i], d[j])
            alloc[i, j] = qty
            s[i] -= qty
            d[j] -= qty

            if abs(s[i]) < 1e-10:
                row_done[i] = True
            if abs(d[j]) < 1e-10:
                col_done[j] = True

        return alloc

    @staticmethod
    def report(result: LPResult, cost_matrix: np.ndarray,
               supply: np.ndarray, demand: np.ndarray) -> str:
        """生成运输方案报告。"""
        if result.status != "optimal":
            return f"求解失败: {result.message}"

        alloc = result.solution
        m, n = alloc.shape

        lines = ["=== 运输方案报告 ==="]
        lines.append(f"最小运输成本: {result.optimal_value:.2f}")
        lines.append(f"\n运输方案 (x_ij):")

        header = "        " + "  ".join(f"D{j+1:>6}" for j in range(n))
        lines.append(header)

        for i in range(m):
            row = f"S{i+1:>2}  "
            for j in range(n):
                row += f"{alloc[i, j]:>8.1f}"
            lines.append(row)

        lines.append(f"\n供给: {supply}")
        lines.append(f"需求: {demand}")

        return "\n".join(lines)


# ──────────────────────────────────────────────────
# 指派问题
# ──────────────────────────────────────────────────

class AssignmentSolver:
    """
    指派问题求解器。

    问题描述：
        n 个工人, n 个任务。
        每个工人完成每个任务有不同的成本。
        每个工人只能分配一个任务，每个任务只能由一个工人完成。
        目标是总成本最小。

    数学模型：
        min  sum_i sum_j c_ij * x_ij
        s.t. sum_j x_ij = 1,   i = 1,...,n   (每个工人一个任务)
             sum_i x_ij = 1,   j = 1,...,n   (每个任务一个工人)
             x_ij in {0, 1}

    注：由于约束矩阵是全幺模矩阵，LP松弛自然得到整数解。

    Examples
    --------
    >>> solver = AssignmentSolver()
    >>> cost = [[9, 2, 7], [6, 4, 3], [5, 8, 1]]
    >>> result = solver.solve(cost)
    """

    def solve(self, cost: List[List[float]], method: str = "two_phase") -> LPResult:
        """
        求解指派问题。

        Parameters
        ----------
        cost : list of list
            成本矩阵 c[i][j]
        method : str
            单纯形法方法

        Returns
        -------
        result : LPResult
        """
        cost = np.array(cost, dtype=float)
        n = cost.shape[0]
        assert cost.shape[0] == cost.shape[1], "指派问题要求方阵"

        # 构造LP
        lp = LinearProgram(ObjectiveType.MIN)
        c_vec = cost.flatten()
        lp.set_objective(c_vec)

        # 每个工人分配一个任务: sum_j x_ij = 1
        for i in range(n):
            coeffs = np.zeros(n * n)
            for j in range(n):
                coeffs[i * n + j] = 1
            lp.add_constraint(coeffs, 1, ConstraintType.EQ)

        # 每个任务分配一个工人: sum_i x_ij = 1
        for j in range(n):
            coeffs = np.zeros(n * n)
            for i in range(n):
                coeffs[i * n + j] = 1
            lp.add_constraint(coeffs, 1, ConstraintType.EQ)

        solver = SimplexSolver(method=method)
        result = solver.solve(lp)

        # 重塑解
        if result.status == "optimal" and result.solution is not None:
            result.solution = result.solution.reshape(n, n)

        return result

    @staticmethod
    def hungarian_algorithm(cost: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        匈牙利算法求解指派问题。

        使用蛮力法对小规模问题 (n <= 8) 求最优解。
        对大规模问题，使用贪心启发式。

        Parameters
        ----------
        cost : np.ndarray
            n x n 成本矩阵

        Returns
        -------
        assignment : np.ndarray
            n 元素数组，assignment[i] = j 表示工人 i 分配任务 j
        total_cost : float
            总成本
        """
        cost = np.array(cost, dtype=float)
        n = cost.shape[0]

        if n <= 8:
            # 小规模: 穷举所有排列
            return AssignmentSolver._brute_force(cost, n)
        else:
            # 大规模: 贪心启发式
            return AssignmentSolver._greedy_assignment(cost, n)

    @staticmethod
    def _brute_force(cost: np.ndarray, n: int) -> Tuple[np.ndarray, float]:
        """穷举所有排列找最优指派。"""
        from itertools import permutations

        best_perm = None
        best_cost = np.inf

        for perm in permutations(range(n)):
            total = sum(cost[i, perm[i]] for i in range(n))
            if total < best_cost:
                best_cost = total
                best_perm = perm

        return np.array(best_perm), best_cost

    @staticmethod
    def _greedy_assignment(cost: np.ndarray, n: int) -> Tuple[np.ndarray, float]:
        """贪心指派：每次选择最小成本的可行配对。"""
        assignment = np.full(n, -1, dtype=int)
        used_cols = set()

        for _ in range(n):
            best_i, best_j = -1, -1
            best_val = np.inf
            for i in range(n):
                if assignment[i] >= 0:
                    continue
                for j in range(n):
                    if j in used_cols:
                        continue
                    if cost[i, j] < best_val:
                        best_val = cost[i, j]
                        best_i, best_j = i, j

            assignment[best_i] = best_j
            used_cols.add(best_j)

        total_cost = sum(cost[i, assignment[i]] for i in range(n))
        return assignment, total_cost

    @staticmethod
    def report(result: LPResult, cost_matrix: np.ndarray) -> str:
        """生成指派方案报告。"""
        if result.status != "optimal":
            return f"求解失败: {result.message}"

        alloc = result.solution
        n = alloc.shape[0]

        lines = ["=== 指派方案报告 ==="]
        lines.append(f"最小总成本: {result.optimal_value:.2f}")
        lines.append("\n指派方案:")

        for i in range(n):
            for j in range(n):
                if alloc[i, j] > 0.5:
                    lines.append(f"  工人 {i+1} -> 任务 {j+1} (成本: {cost_matrix[i, j]:.1f})")

        return "\n".join(lines)
