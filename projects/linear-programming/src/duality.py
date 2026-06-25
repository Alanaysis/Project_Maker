"""
对偶理论与对偶单纯形法。

数学基础：
    原问题 (Primal):      max c^T x,  s.t. Ax <= b, x >= 0
    对偶问题 (Dual):      min b^T y,  s.t. A^T y >= c, y >= 0

    弱对偶定理: c^T x <= b^T y (任何可行解)
    强对偶定理: 如果原问题有最优解，则对偶也有，且 c^T x* = b^T y*
    互补松弛:   y_i*(b_i - a_i^T x*) = 0,  x_j*(a_j^T y* - c_j) = 0

对偶单纯形法：
    保持对偶可行性（检验数 <= 0），逐步恢复原始可行性。
    适用于右端项变化后重新优化。
"""

import numpy as np
from typing import Optional
from .linear_program import (
    LinearProgram, LPResult, ConstraintType, ObjectiveType
)


class DualProblem:
    """
    对偶问题构造器。

    将原问题转换为对偶问题。
    """

    @staticmethod
    def construct_dual(primal: LinearProgram) -> LinearProgram:
        """
        构造对偶问题。

        原问题:                    对偶问题:
        max c^T x                  min b^T y
        s.t. Ax <= b               s.t. A^T y >= c
             x >= 0                      y >= 0

        对于一般形式的转换规则：
        - max 问题的 <= 约束 -> 对偶变量 y_i >= 0
        - max 问题的 >= 约束 -> 对偶变量 y_i <= 0
        - max 问题的 == 约束 -> 对偶变量 y_i 无约束
        - max 问题的 x_j >= 0 -> 对偶约束 >= c_j
        - max 问题的 x_j <= 0 -> 对偶约束 <= c_j
        - max 问题的 x_j 无约束 -> 对偶约束 == c_j

        Parameters
        ----------
        primal : LinearProgram
            原问题

        Returns
        -------
        dual : LinearProgram
            对偶问题
        """
        c = primal.c
        A = primal.A
        b = primal.b
        m, n = A.shape

        # 对偶目标类型与原问题相反
        if primal.objective_type == ObjectiveType.MAX:
            dual_type = ObjectiveType.MIN
            dual_constraint_type = ConstraintType.GE
        else:
            dual_type = ObjectiveType.MAX
            dual_constraint_type = ConstraintType.LE

        # 对偶问题目标函数系数 = 原问题右端项
        dual = LinearProgram(dual_type)
        dual.set_objective(b)

        # 对偶约束: A^T y >= c (max问题) 或 A^T y <= c (min问题)
        A_dual = A.T  # n x m
        for j in range(n):
            dual.add_constraint(A_dual[j], c[j], dual_constraint_type)

        return dual

    @staticmethod
    def verify_strong_duality(primal_result: LPResult,
                               dual_result: LPResult) -> bool:
        """验证强对偶定理。"""
        if primal_result.status != "optimal" or dual_result.status != "optimal":
            return False
        return abs(primal_result.optimal_value - dual_result.optimal_value) < 1e-6

    @staticmethod
    def check_weak_duality(primal_solution: np.ndarray,
                            dual_solution: np.ndarray,
                            c: np.ndarray, b: np.ndarray) -> tuple:
        """
        验证弱对偶定理: c^T x <= b^T y。

        Returns
        -------
        primal_obj : float
        dual_obj : float
        is_valid : bool
        """
        primal_obj = c @ primal_solution
        dual_obj = b @ dual_solution
        return primal_obj, dual_obj, primal_obj <= dual_obj + 1e-6

    @staticmethod
    def complementary_slackness(primal_solution: np.ndarray,
                                 dual_solution: np.ndarray,
                                 primal_slack: np.ndarray,
                                 dual_slack: np.ndarray,
                                 tol: float = 1e-6) -> dict:
        """
        互补松弛条件检查。

        原始互补松弛: y_i * (b_i - A_i x) = 0
        对偶互补松弛: x_j * (A^T_j y - c_j) = 0

        Returns
        -------
        dict with 'primal_cs' and 'dual_cs' boolean arrays
        """
        primal_cs = np.abs(dual_solution * primal_slack) < tol
        dual_cs = np.abs(primal_solution * dual_slack) < tol

        return {
            "primal_complementary_slackness": primal_cs,
            "dual_complementary_slackness": dual_cs,
            "all_satisfied": np.all(primal_cs) and np.all(dual_cs)
        }


class DualSimplexSolver:
    """
    对偶单纯形法。

    适用场景：
    1. 已有最优解，右端项变化后重新求解
    2. 初始解对偶可行但原始不可行
    3. 割平面法中添加新约束后重新优化

    数学原理：
        对偶可行性: 检验数 sigma_j = c_j - c_B^T B^{-1} a_j <= 0
        原始可行性: B^{-1} b >= 0
        选择 b_i < 0 的行对应的基变量出基
        用最大比值检验选择入基变量
    """

    EPS = 1e-10
    MAX_ITER = 1000

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def solve(self, lp: LinearProgram) -> LPResult:
        """
        用对偶单纯形法求解。

        要求初始解对偶可行（所有检验数 <= 0）。
        """
        c_orig = lp.c.copy()
        A = lp.A.copy()
        b = lp.b.copy()
        n_orig = lp.num_vars
        m = lp.num_constraints

        if lp.objective_type == ObjectiveType.MIN:
            c_work = -c_orig.copy()
        else:
            c_work = c_orig.copy()

        # 构造初始单纯形表
        # 假设约束已经是 <= 形式，引入松弛变量
        tableau = np.zeros((m + 1, n_orig + m + 1))
        tableau[:m, :n_orig] = A
        tableau[:m, n_orig:n_orig + m] = np.eye(m)
        tableau[:m, -1] = b
        tableau[-1, :n_orig] = c_work

        # 初始基为松弛变量
        basis = list(range(n_orig, n_orig + m))

        # 检查对偶可行性 (检验数 <= 0)
        if np.any(tableau[-1, :n_orig + m] > self.EPS):
            return LPResult(
                status="error",
                message="初始解不满足对偶可行性，对偶单纯形法不适用"
            )

        return self._dual_simplex_iterations(tableau, basis, n_orig, lp)

    def _dual_simplex_iterations(self, tableau: np.ndarray, basis: list,
                                  n_orig: int, lp: LinearProgram) -> LPResult:
        """对偶单纯形法核心迭代。"""
        m = tableau.shape[0] - 1
        n_full = tableau.shape[1] - 1
        history = [tableau.copy()]
        iterations = 0

        for _ in range(self.MAX_ITER):
            iterations += 1

            # 1. 检查原始可行性: b >= 0?
            rhs = tableau[:-1, -1]
            leaving = -1
            min_rhs = 0
            for i in range(m):
                if rhs[i] < -self.EPS and rhs[i] < min_rhs:
                    min_rhs = rhs[i]
                    leaving = i

            if leaving == -1:
                # 所有 b >= 0，原始可行，已达最优
                break

            # 2. 选择入基变量: 最大比值检验
            # 比值 = sigma_j / a_{leaving,j}, 对 a_{leaving,j} < 0
            row = tableau[leaving, :-1]
            sigma = tableau[-1, :-1]

            entering = -1
            min_ratio = np.inf
            for j in range(n_full):
                if row[j] < -self.EPS:
                    ratio = sigma[j] / row[j]  # sigma_j <= 0, row_j < 0, ratio >= 0
                    if ratio < min_ratio:
                        min_ratio = ratio
                        entering = j

            if entering == -1:
                return LPResult(
                    status="infeasible",
                    iterations=iterations,
                    tableau_history=history,
                    message="对偶问题无界，原问题不可行"
                )

            basis[leaving] = entering

            # 3. 枢轴运算
            pivot = tableau[leaving, entering]
            tableau[leaving] /= pivot

            for i in range(m + 1):
                if i != leaving:
                    tableau[i] -= tableau[i, entering] * tableau[leaving]

            history.append(tableau.copy())

            if self.verbose:
                print(f"Iteration {iterations}: entering={entering}, leaving={leaving}")
                print(f"  Basis: {basis}")

        # 提取结果
        solution = np.zeros(n_orig)
        for i, var_idx in enumerate(basis):
            if var_idx < n_orig:
                solution[var_idx] = tableau[i, -1]

        optimal_value = tableau[-1, -1]
        if lp.objective_type == ObjectiveType.MIN:
            optimal_value = -optimal_value

        slack = np.zeros(m)
        dual_sol = np.zeros(m)
        for i, var_idx in enumerate(basis):
            if var_idx >= n_orig:
                slack_idx = var_idx - n_orig
                if slack_idx < m:
                    slack[slack_idx] = tableau[i, -1]

        for i in range(m):
            dual_sol[i] = tableau[-1, n_orig + i]

        return LPResult(
            status="optimal",
            optimal_value=optimal_value,
            solution=solution,
            dual_solution=dual_sol,
            slack=slack,
            iterations=iterations,
            tableau_history=history,
            message="对偶单纯形法找到最优解"
        )

    def resolve_with_rhs_change(self, lp: LinearProgram,
                                 prev_tableau: np.ndarray,
                                 prev_basis: list,
                                 delta_b: np.ndarray) -> LPResult:
        """
        右端项变化后重新求解。

        利用之前的最优基，更新右端项后用对偶单纯形法重新优化。

        Parameters
        ----------
        lp : LinearProgram
            原问题
        prev_tableau : np.ndarray
            之前的最优单纯形表
        prev_basis : list
            之前的基变量索引
        delta_b : np.ndarray
            右端项变化量
        """
        tableau = prev_tableau.copy()
        basis = list(prev_basis)
        n_orig = lp.num_vars

        # 更新 B^{-1} b
        m = tableau.shape[0] - 1
        B_inv = tableau[:m, n_orig:n_orig + m]
        new_b = tableau[:m, -1] + B_inv @ delta_b
        tableau[:m, -1] = new_b

        return self._dual_simplex_iterations(tableau, basis, n_orig, lp)
