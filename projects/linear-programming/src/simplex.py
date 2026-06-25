"""
单纯形法实现。

包含三种变体：
1. 标准单纯形法 - 适用于已经是标准形式的问题
2. 大M法 (Big-M Method) - 通过引入人工变量和惩罚项处理一般形式
3. 两阶段法 (Two-Phase Method) - 第一阶段找可行解，第二阶段优化

数学基础：
    标准形式: max c^T x, s.t. Ax <= b, x >= 0
    引入松弛变量: Ax + Is = b, x >= 0, s >= 0
    初始基: 松弛变量构成初始可行基

单纯形表约定 (标准教材形式):
    表结构: [A | I | b]       (约束部分)
            [-c | 0 | 0]      (目标函数行，存储 -c)
    选择入基: 找目标行中最负的元素
    停止条件: 目标行所有元素 >= 0
    最优值: z = -tableau[-1, -1]
    对偶解: y_i = -tableau[-1, n_orig + i] (松弛变量列的负值)
"""

import numpy as np
from typing import List, Optional, Tuple
from .linear_program import (
    LinearProgram, LPResult, ConstraintType, ObjectiveType
)


class SimplexSolver:
    """
    单纯形法求解器。

    支持三种方法：
    - "standard": 标准单纯形法（仅适用于 <= 约束）
    - "big_m": 大M法
    - "two_phase": 两阶段法

    Examples
    --------
    >>> lp = LinearProgram(ObjectiveType.MAX)
    >>> lp.set_objective([3, 5])
    >>> lp.add_constraint([1, 0], 4, ConstraintType.LE)
    >>> lp.add_constraint([0, 2], 12, ConstraintType.LE)
    >>> lp.add_constraint([3, 5], 25, ConstraintType.LE)
    >>> solver = SimplexSolver(method="standard")
    >>> result = solver.solve(lp)
    """

    EPS = 1e-10
    MAX_ITER = 1000

    def __init__(self, method: str = "standard", M: float = 1e6, verbose: bool = False):
        """
        Parameters
        ----------
        method : str
            求解方法: "standard", "big_m", "two_phase"
        M : float
            大M法的惩罚系数
        verbose : bool
            是否打印迭代过程
        """
        assert method in ("standard", "big_m", "two_phase"), \
            f"未知方法: {method}"
        self.method = method
        self.M = M
        self.verbose = verbose

    def solve(self, lp: LinearProgram) -> LPResult:
        """求解线性规划问题。"""
        if self.method == "standard":
            return self._solve_standard(lp)
        elif self.method == "big_m":
            return self._solve_big_m(lp)
        elif self.method == "two_phase":
            return self._solve_two_phase(lp)

    # ──────────────────────────────────────────────
    # 标准单纯形法
    # ──────────────────────────────────────────────

    def _solve_standard(self, lp: LinearProgram) -> LPResult:
        """
        标准单纯形法。

        要求所有约束为 <= 且 b >= 0。
        """
        c_orig, A, b, n_orig = lp.to_standard_form()

        # 检查是否所有 b >= 0
        if np.any(b < -self.EPS):
            return LPResult(
                status="error",
                message="标准单纯形法要求所有右端项 >= 0，请使用 big_m 或 two_phase 方法"
            )

        m, n = A.shape

        # 构造初始单纯形表
        # 表结构: [A | I | b]   (约束部分)
        #         [-c | 0 | 0]  (目标函数行，标准教材形式)
        tableau = np.zeros((m + 1, n + m + 1))

        # 约束部分
        tableau[:m, :n] = A
        tableau[:m, n:n + m] = np.eye(m)
        tableau[:m, -1] = b

        # 目标函数行: 存储 -c (标准教材形式)
        tableau[m, :n] = -c_orig

        # 基变量索引 (初始基为松弛变量)
        basis = list(range(n, n + m))

        result = self._simplex_iterations(tableau, basis, n_orig, lp)
        return result

    def _simplex_iterations(self, tableau: np.ndarray, basis: List[int],
                            n_orig: int, lp: LinearProgram) -> LPResult:
        """
        核心单纯形迭代。

        单纯形表约定:
        - 目标行存储 -z 的系数
        - 入基选择: 目标行中最负的元素 (Bland规则: 取最小索引)
        - 停止条件: 目标行所有元素 >= 0
        - 最优值: z = -tableau[-1, -1]
        - 对偶解: y_i = -tableau[-1, n_orig + i]
        """
        m = tableau.shape[0] - 1
        n_full = tableau.shape[1] - 1
        history = [tableau.copy()]
        iterations = 0

        for _ in range(self.MAX_ITER):
            iterations += 1

            # 1. 选择入基变量: 目标行中最负的元素 (Bland规则)
            obj_row = tableau[-1, :-1]
            entering = -1
            for j in range(n_full):
                if obj_row[j] < -self.EPS:
                    entering = j
                    break

            if entering == -1:
                # 所有检验数 >= 0，已达最优
                break

            # 2. 最小比值检验选择出基变量
            col = tableau[:-1, entering]
            rhs = tableau[:-1, -1]
            ratios = np.full(m, np.inf)

            for i in range(m):
                if col[i] > self.EPS:
                    ratios[i] = rhs[i] / col[i]

            leaving = np.argmin(ratios)
            if ratios[leaving] == np.inf:
                return LPResult(
                    status="unbounded",
                    iterations=iterations,
                    tableau_history=history,
                    message="问题无界"
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
                print(f"  Tableau:\n{np.round(tableau, 4)}\n")

        # 提取结果
        solution = np.zeros(n_orig)
        for i, var_idx in enumerate(basis):
            if var_idx < n_orig:
                solution[var_idx] = tableau[i, -1]

        # 最优值: z = tableau[-1, -1]
        # 目标行存储的是 z_j - c_j (reduced costs), 最后一列是 z
        optimal_value = tableau[-1, -1]
        if lp.objective_type == ObjectiveType.MIN:
            optimal_value = -optimal_value

        # 提取松弛变量和对偶解
        slack = np.zeros(m)
        dual_sol = np.zeros(m)
        for i, var_idx in enumerate(basis):
            if var_idx >= n_orig:
                slack_idx = var_idx - n_orig
                if slack_idx < m:
                    slack[slack_idx] = tableau[i, -1]

        # 对偶解 = 目标行中松弛变量列的值 (z_j - c_j for slack vars)
        num_cols = tableau.shape[1] - 1  # 不含右端项
        for i in range(m):
            col = n_orig + i
            if col < num_cols:
                dual_sol[i] = tableau[-1, col]

        return LPResult(
            status="optimal",
            optimal_value=optimal_value,
            solution=solution,
            dual_solution=dual_sol,
            slack=slack,
            iterations=iterations,
            tableau_history=history,
            message="找到最优解"
        )

    # ──────────────────────────────────────────────
    # 大M法
    # ──────────────────────────────────────────────

    def _solve_big_m(self, lp: LinearProgram) -> LPResult:
        """
        大M法。

        对于 >= 和 == 约束，引入人工变量并赋予大惩罚系数。
        """
        c_orig = lp.c.copy()
        A_orig = lp.A.copy()
        b_orig = lp.b.copy()
        n_orig = lp.num_vars
        m = lp.num_constraints

        if lp.objective_type == ObjectiveType.MIN:
            c_work = -c_orig.copy()
        else:
            c_work = c_orig.copy()

        # Pass 1: 计算需要的松弛变量和人工变量数量
        num_slack = 0
        num_artificial = 0
        for constr in lp.constraints:
            if constr.constraint_type == ConstraintType.LE:
                num_slack += 1
            elif constr.constraint_type == ConstraintType.GE:
                num_slack += 1  # 剩余变量
                num_artificial += 1
            elif constr.constraint_type == ConstraintType.EQ:
                num_artificial += 1

        total_vars = n_orig + num_slack + num_artificial

        # Pass 2: 构造完整矩阵
        A_full = np.zeros((m, total_vars))
        b_full = np.zeros(m)
        basis = []
        slack_idx = n_orig
        art_idx = n_orig + num_slack

        for i, constr in enumerate(lp.constraints):
            A_full[i, :n_orig] = A_orig[i]
            b_full[i] = b_orig[i]

            if constr.constraint_type == ConstraintType.LE:
                A_full[i, slack_idx] = 1.0
                basis.append(slack_idx)
                slack_idx += 1

            elif constr.constraint_type == ConstraintType.GE:
                A_full[i, slack_idx] = -1.0  # 剩余变量
                slack_idx += 1
                A_full[i, art_idx] = 1.0  # 人工变量
                basis.append(art_idx)
                art_idx += 1

            elif constr.constraint_type == ConstraintType.EQ:
                A_full[i, art_idx] = 1.0  # 人工变量
                basis.append(art_idx)
                art_idx += 1

        # 确保 b >= 0
        for i in range(m):
            if b_full[i] < 0:
                A_full[i] = -A_full[i]
                b_full[i] = -b_full[i]

        # 构造目标函数行: 存储 -c_work 对原始变量, +M 对人工变量
        c_full = np.zeros(total_vars)
        c_full[:n_orig] = -c_work
        for j in range(n_orig + num_slack, total_vars):
            c_full[j] = self.M

        # 构造单纯形表
        tableau = np.zeros((m + 1, total_vars + 1))
        tableau[:m, :total_vars] = A_full
        tableau[:m, -1] = b_full
        tableau[-1, :total_vars] = c_full

        # 消除基变量在目标函数中的系数
        for i in range(m):
            tableau[-1] -= tableau[-1, basis[i]] * tableau[i]

        result = self._simplex_iterations(tableau, basis, n_orig, lp)

        # 检查人工变量是否在基中且非零
        if result.status == "optimal" and result.solution is not None:
            for i, var_idx in enumerate(basis):
                if var_idx >= n_orig + num_slack:
                    if abs(tableau[i, -1]) > self.EPS:
                        result.status = "infeasible"
                        result.message = "原问题不可行（人工变量未被驱出）"
                        result.optimal_value = None
                        result.solution = None
                        break

        return result

    # ──────────────────────────────────────────────
    # 两阶段法
    # ──────────────────────────────────────────────

    def _solve_two_phase(self, lp: LinearProgram) -> LPResult:
        """
        两阶段法。

        第一阶段：最小化人工变量之和，找初始可行解。
        第二阶段：在可行解基础上优化原目标函数。
        """
        c_orig = lp.c.copy()
        A_orig = lp.A.copy()
        b_orig = lp.b.copy()
        n_orig = lp.num_vars
        m = lp.num_constraints

        if lp.objective_type == ObjectiveType.MIN:
            c_work = -c_orig.copy()
        else:
            c_work = c_orig.copy()

        # Pass 1: 计算变量数量
        num_slack = 0
        num_artificial = 0
        for constr in lp.constraints:
            if constr.constraint_type == ConstraintType.LE:
                num_slack += 1
            elif constr.constraint_type == ConstraintType.GE:
                num_slack += 1
                num_artificial += 1
            elif constr.constraint_type == ConstraintType.EQ:
                num_artificial += 1

        total_vars = n_orig + num_slack + num_artificial

        # Pass 2: 构造 Phase I 问题
        A_full = np.zeros((m, total_vars))
        b_full = np.zeros(m)
        basis = []
        slack_idx = n_orig
        art_idx = n_orig + num_slack

        for i, constr in enumerate(lp.constraints):
            A_full[i, :n_orig] = A_orig[i]
            b_full[i] = b_orig[i]

            if constr.constraint_type == ConstraintType.LE:
                A_full[i, slack_idx] = 1.0
                basis.append(slack_idx)
                slack_idx += 1

            elif constr.constraint_type == ConstraintType.GE:
                A_full[i, slack_idx] = -1.0
                slack_idx += 1
                A_full[i, art_idx] = 1.0
                basis.append(art_idx)
                art_idx += 1

            elif constr.constraint_type == ConstraintType.EQ:
                A_full[i, art_idx] = 1.0
                basis.append(art_idx)
                art_idx += 1

        # 确保 b >= 0
        for i in range(m):
            if b_full[i] < 0:
                A_full[i] = -A_full[i]
                b_full[i] = -b_full[i]

        # Phase I 目标: max -sum(artificial)
        # 目标行存储 +1 对人工变量 (因为 -(-1) = +1)
        c_phase1 = np.zeros(total_vars)
        for j in range(n_orig + num_slack, total_vars):
            c_phase1[j] = 1.0

        tableau_p1 = np.zeros((m + 1, total_vars + 1))
        tableau_p1[:m, :total_vars] = A_full
        tableau_p1[:m, -1] = b_full
        tableau_p1[-1, :total_vars] = c_phase1

        # 消除基中人工变量在目标行的系数
        for i in range(m):
            tableau_p1[-1] -= tableau_p1[-1, basis[i]] * tableau_p1[i]

        basis_p1 = list(basis)
        result_p1 = self._simplex_iterations(tableau_p1, basis_p1, total_vars,
                                               LinearProgram(ObjectiveType.MAX))

        if result_p1.status != "optimal":
            return LPResult(
                status="infeasible",
                iterations=result_p1.iterations,
                message="Phase I 未能找到可行解，原问题不可行"
            )

        # Phase I 最优值
        phase1_opt = tableau_p1[-1, -1]
        if abs(phase1_opt) > self.EPS:
            return LPResult(
                status="infeasible",
                optimal_value=phase1_opt,
                iterations=result_p1.iterations,
                message=f"Phase I 最优值 = {phase1_opt:.6f} != 0，原问题不可行"
            )

        # === Phase II ===
        # 用 Phase I 的 B^{-1}A 和 B^{-1}b 构造 Phase II。
        # 先替换基中的人工变量，再重建目标行。

        # 提取 B^{-1}A 和 B^{-1}b
        tableau_p2 = np.zeros((m + 1, n_orig + num_slack + 1))
        tableau_p2[:m, :n_orig + num_slack] = tableau_p1[:m, :n_orig + num_slack]
        tableau_p2[:m, -1] = tableau_p1[:m, -1]

        basis_p2 = list(basis_p1)

        # 替换基中的人工变量
        for i in range(m):
            if basis_p2[i] >= n_orig + num_slack:
                for j in range(n_orig + num_slack):
                    if j not in basis_p2 and abs(tableau_p2[i, j]) > self.EPS:
                        pivot_val = tableau_p2[i, j]
                        tableau_p2[i] /= pivot_val
                        for k in range(m):
                            if k != i:
                                tableau_p2[k] -= tableau_p2[k, j] * tableau_p2[i]
                        basis_p2[i] = j
                        break

        # 重建目标行 (在替换枢轴之后)
        tableau_p2[-1, :n_orig + num_slack] = 0
        tableau_p2[-1, :n_orig] = -c_work
        tableau_p2[-1, -1] = 0

        # 消除基变量在目标行的系数
        for i in range(m):
            if basis_p2[i] >= 0 and basis_p2[i] < n_orig + num_slack:
                tableau_p2[-1] -= tableau_p2[-1, basis_p2[i]] * tableau_p2[i]

        result_p2 = self._simplex_iterations(tableau_p2, basis_p2, n_orig, lp)
        result_p2.iterations += result_p1.iterations
        return result_p2
