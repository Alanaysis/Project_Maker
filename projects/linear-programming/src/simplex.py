"""
单纯形算法模块 (Simplex Algorithm)

实现使用单纯形表 (Tableau) 方法的单纯形算法。

单纯形法核心思想:
    1. 从可行域的一个顶点 (基本可行解) 出发
    2. 沿着可行域的边移动到相邻顶点
    3. 每次移动都使目标函数值改善
    4. 当无法再改进时，当前解即为最优解

关键概念:
    - 基变量 (Basic Variables): 对应单位矩阵列的变量
    - 非基变量 (Non-basic Variables): 值为 0 的变量
    - 检验数 (Reduced Cost): 非基变量增加一个单位时目标函数的变化率
    - 进基变量 (Entering Variable): 检验数最负的变量
    - 出基变量 (Leaving Variable): 通过最小比值测试确定
"""

import numpy as np
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass, field

from .problem import LPProblem


@dataclass
class SimplexResult:
    """单纯形算法求解结果."""
    optimal_value: float
    solution: np.ndarray
    basis: List[int]
    iterations: int
    status: str  # 'optimal', 'unbounded', 'infeasible'
    tableau_history: List[np.ndarray] = field(default_factory=list)
    pivot_history: List[Tuple[int, int]] = field(default_factory=list)
    variable_names: Optional[List[str]] = None

    def __str__(self):
        lines = []
        lines.append(f"状态: {self.status}")
        lines.append(f"最优值: {self.optimal_value:.6f}")
        lines.append(f"迭代次数: {self.iterations}")
        if self.variable_names:
            lines.append("\n变量值:")
            for i, (name, val) in enumerate(zip(self.variable_names, self.solution)):
                if abs(val) > 1e-10:
                    lines.append(f"  {name} = {val:.6f}")
        else:
            lines.append(f"\n解向量: {self.solution}")
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        """转换为字典格式."""
        return {
            "status": self.status,
            "optimal_value": float(self.optimal_value),
            "solution": self.solution.tolist(),
            "basis": self.basis,
            "iterations": self.iterations,
        }


class SimplexSolver:
    """
    使用单纯形表方法求解线性规划问题。

    支持 A*x <= b, x >= 0 形式的标准 LP 问题。
    内部自动添加松弛变量并将问题转换为标准形。
    """

    def __init__(
        self,
        problem: LPProblem,
        tolerance: float = 1e-10,
        max_iterations: int = 1000,
    ):
        self.problem = problem
        self.tolerance = tolerance
        self.max_iterations = max_iterations
        self.result: Optional[SimplexResult] = None

    def solve(self) -> SimplexResult:
        """
        求解线性规划问题。

        自动添加松弛变量，构造标准形，然后使用单纯形法求解。

        Returns:
            SimplexResult: 求解结果
        """
        prob = self.problem
        m = prob.n_constraints
        n = prob.n_vars

        # 处理最大化问题
        if prob.problem_type == "max":
            c_orig = -prob.c.copy()
        else:
            c_orig = prob.c.copy()

        # 处理 b < 0 的约束
        A = prob.A.copy()
        b = prob.b.copy()
        for i in range(m):
            if b[i] < 0:
                A[i] *= -1
                b[i] *= -1

        # 添加松弛变量: A*x + I*s = b
        # 松弛变量提供初始单位基
        A_aug = np.hstack([A, np.eye(m)])
        c_aug = np.concatenate([c_orig, np.zeros(m)])
        n_total = n + m

        # 使用单纯形表求解
        result = self._simplex_tableau(A_aug, b, c_aug, m, n_total, n, prob)
        self.result = result
        return result

    def _simplex_tableau(
        self,
        A: np.ndarray,
        b: np.ndarray,
        c: np.ndarray,
        m: int,
        n: int,  # 总变量数 (含松弛变量)
        n_original: int,  # 原始变量数
        prob: LPProblem,
    ) -> SimplexResult:
        """
        单纯形表法核心求解过程。

        单纯形表结构:
            [ A | I | b ]    (约束行, m 行)
            [ c | 0 | 0 ]    (目标行/检验数行, 1 行)
        """
        # 初始化单纯形表
        tableau = np.zeros((m + 1, n + 1))
        tableau[:m, :n] = A
        tableau[:m, -1] = b
        tableau[m, :n] = c  # 检验数行

        # 初始基: 松弛变量对应的列 (n-m, n-m+1, ..., n-1)
        slack_start = n - m
        basis = list(range(slack_start, n))
        tableau_history = [tableau.copy()]
        pivot_history = []
        iteration = 0

        while iteration < self.max_iterations:
            # 读取检验数
            reduced_costs = tableau[m, :n].copy()

            # 检查最优性: 所有检验数 >= -tolerance
            if np.all(reduced_costs >= -self.tolerance):
                # 最优解找到
                solution = np.zeros(n)
                for i, idx in enumerate(basis):
                    if i < m:
                        solution[idx] = max(0, tableau[i, -1])

                # 目标值 = -tableau[m, -1] (因为 c 已取负)
                optimal_val = -tableau[m, -1]
                if prob.problem_type == "max":
                    optimal_val = -optimal_val

                return SimplexResult(
                    optimal_value=optimal_val,
                    solution=solution[:n_original],
                    basis=basis,
                    iterations=iteration,
                    status="optimal",
                    tableau_history=tableau_history,
                    pivot_history=pivot_history,
                    variable_names=prob.variable_names,
                )

            # 选择进基变量: 最负的检验数
            entering_col = np.argmin(reduced_costs)
            min_rc = reduced_costs[entering_col]

            if min_rc >= -self.tolerance:
                break

            # 最小比值测试确定出基变量
            pivot_col = tableau[:m, entering_col]
            ratios = np.full(m, float("inf"))
            for i in range(m):
                if pivot_col[i] > self.tolerance:
                    ratios[i] = tableau[i, -1] / pivot_col[i]

            min_ratio_idx = np.argmin(ratios)

            if ratios[min_ratio_idx] == float("inf"):
                return SimplexResult(
                    optimal_value=float("inf"),
                    solution=np.zeros(n_original),
                    basis=basis,
                    iterations=iteration,
                    status="unbounded",
                    tableau_history=tableau_history,
                    pivot_history=pivot_history,
                    variable_names=prob.variable_names,
                )

            leaving_row = min_ratio_idx

            # 记录主元
            pivot_history.append((entering_col, leaving_row))

            # 主元运算 (Pivot)
            pivot_element = tableau[leaving_row, entering_col]
            tableau[leaving_row, :] /= pivot_element

            for i in range(m + 1):
                if i != leaving_row:
                    factor = tableau[i, entering_col]
                    tableau[i, :] -= factor * tableau[leaving_row, :]

            basis[leaving_row] = entering_col
            tableau_history.append(tableau.copy())
            iteration += 1

        return SimplexResult(
            optimal_value=float("nan"),
            solution=np.zeros(n_original),
            basis=basis,
            iterations=iteration,
            status="infeasible",
            tableau_history=tableau_history,
            pivot_history=pivot_history,
            variable_names=prob.variable_names,
        )

    def _two_phase_method(
        self, A, b, c, m, n, n_original, prob
    ) -> SimplexResult:
        """
        两阶段单纯形法。
        当没有明显的初始基时使用。
        """
        num_artificial = 0
        for i in range(m):
            has_positive = False
            for j in range(n + num_artificial):
                if j < n:
                    if A[i, j] > self.tolerance:
                        has_positive = True
                        break
                else:
                    if i == (j - n):
                        has_positive = True
                        break
            if not has_positive:
                num_artificial += 1

        if num_artificial == 0:
            return self._simplex_tableau(A, b, c, m, n, n_original, prob)

        # 第一阶段
        A_phase1 = np.hstack([A, np.eye(num_artificial)])
        n_phase1 = A_phase1.shape[1]
        c_phase1 = np.zeros(n_phase1)
        c_phase1[n:] = 1.0

        phase1_prob = LPProblem(
            c=c_phase1, A=A_phase1, b=b.copy(),
            variable_names=[*(prob.variable_names or [f"x{i+1}" for i in range(n)]),
                           *(f"a{i+1}" for i in range(num_artificial))],
            problem_type="min",
        )

        phase1_solver = SimplexSolver(phase1_prob, self.tolerance, self.max_iterations)
        phase1_result = phase1_solver.solve()

        if phase1_result.status != "optimal" or phase1_result.optimal_value > self.tolerance:
            return SimplexResult(
                optimal_value=float("inf"), solution=np.zeros(n_original),
                basis=[], iterations=phase1_result.iterations + 1,
                status="infeasible", variable_names=prob.variable_names,
            )

        # 第二阶段
        phase2_prob = LPProblem(
            c=c, A=A, b=b, variable_names=prob.variable_names,
            problem_type=prob.problem_type,
        )
        phase2_solver = SimplexSolver(phase2_prob, self.tolerance, self.max_iterations)
        phase2_result = phase2_solver.solve()

        total_iterations = phase1_result.iterations + phase2_result.iterations
        return SimplexResult(
            optimal_value=phase2_result.optimal_value,
            solution=phase2_result.solution,
            basis=phase2_result.basis,
            iterations=total_iterations,
            status=phase2_result.status,
            tableau_history=phase1_result.tableau_history + phase2_result.tableau_history,
            pivot_history=phase1_result.pivot_history + phase2_result.pivot_history,
            variable_names=prob.variable_names,
        )
