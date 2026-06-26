"""
对偶问题求解器 (Dual Problem Solver)

线性规划的对偶理论 (Duality Theory) 是线性规划的核心概念之一。

每个线性规划问题 (原问题/Primal) 都有对应的对偶问题 (Dual)。

原问题 (Primal) - 最小化:
    minimize    c^T * x
    subject to  A * x >= b
                x >= 0

对偶问题 (Dual) - 最大化:
    maximize    b^T * y
    subject to  A^T * y <= c
                y >= 0

对偶理论的核心定理:
    1. 弱对偶定理: 对偶问题的任何可行解的目标值 <= 原问题的任何可行解的目标值
    2. 强对偶定理: 如果原问题有最优解，则对偶问题也有最优解，且最优值相等
    3. 互补松弛条件: 最优解满足特定的互补关系

学习要点:
    - 原问题和对偶问题的对应关系
    - 对偶变量的经济解释 (影子价格 / Shadow Price)
    - 对偶单纯形法 (Dual Simplex Method)
"""

import numpy as np
from typing import Dict, Optional

from .problem import LPProblem, create_problem
from .simplex import SimplexSolver, SimplexResult


class DualSolver:
    """
    线性规划对偶问题求解器。

    支持从原问题构造并求解对偶问题，
    以及计算影子价格 (对偶变量值)。
    """

    def __init__(self, problem: LPProblem, tolerance: float = 1e-10):
        """
        初始化对偶求解器。

        Args:
            problem: 原问题 (应为标准形: minimize c^T x, A*x = b, x >= 0)
            tolerance: 数值容差
        """
        self.problem = problem
        self.tolerance = tolerance

    def construct_dual(self) -> LPProblem:
        """
        从原问题构造对偶问题。

        原问题 (<= 形式):
            maximize c^T * x
            subject to A * x <= b
                       x >= 0

        对偶问题:
            minimize b^T * y
            subject to A^T * y >= c
                       y >= 0

        将 A^T * y >= c 转换为求解器形式 (-A^T) * y <= -c:
        如果 -c 中有负值，需要调整符号。

        Returns:
            LPProblem: 对偶问题
        """
        prob = self.problem
        A = prob.A
        b = prob.b
        c = prob.c

        # 对偶问题: minimize b^T * y, subject to A^T * y >= c, y >= 0
        # 转换为求解器形式 (<=): -A^T * y <= -c
        dual_c = b
        dual_A = -A.T
        dual_b = -c

        # 处理 dual_b < 0: 两边乘 -1
        for i in range(len(dual_b)):
            if dual_b[i] < 0:
                dual_A[i] *= -1
                dual_b[i] *= -1

        # 对偶变量名
        dual_var_names = [f"y{i+1}" for i in range(len(b))]

        return create_problem(
            c=dual_c.tolist(),
            A=dual_A.tolist(),
            b=dual_b.tolist(),
            variable_names=dual_var_names,
            problem_type="min",
        )

    def solve_dual(self) -> Dict:
        """
        求解原问题的对偶问题并返回结果。

        Returns:
            包含原问题和对偶问题求解结果的字典
        """
        prob = self.problem

        # 求解原问题
        primal_solver = SimplexSolver(prob, self.tolerance)
        primal_result = primal_solver.solve()

        # 构造并求解对偶问题
        dual_prob = self.construct_dual()
        dual_solver = SimplexSolver(dual_prob, self.tolerance)
        dual_result = dual_solver.solve()

        # 验证强对偶定理
        primal_val = primal_result.optimal_value
        dual_val = dual_result.optimal_value

        duality_gap = abs(primal_val - dual_val)

        return {
            "primal": primal_result.to_dict(),
            "dual": dual_result.to_dict(),
            "duality_gap": duality_gap,
            "strong_duality_holds": duality_gap < self.tolerance,
        }

    def get_shadow_prices(self, simplex_result: SimplexResult) -> np.ndarray:
        """
        从单纯形法的最终单纯形表中计算影子价格 (对偶变量值)。

        影子价格 (Shadow Price) 的含义:
            约束右侧 b_i 增加一个单位时，最优目标值的变化量。
            在经济意义上，影子价格表示资源的边际价值。

        对于最小化问题:
            影子价格 y_i = 最终表中松弛变量 i 的检验数

        Args:
            simplex_result: 原问题的单纯形法求解结果

        Returns:
            np.ndarray: 影子价格向量
        """
        # 从最终单纯形表提取影子价格
        # 影子价格 = 最终表中松弛变量对应的检验数
        tableau = simplex_result.tableau_history[-1] if simplex_result.tableau_history else None

        if tableau is None:
            return np.zeros(self.problem.n_constraints)

        m = self.problem.n_constraints
        n = self.problem.n_vars

        # 影子价格对应于最终表中目标行在松弛变量列的值
        shadow_prices = tableau[-1, n : n + m].copy()

        # 根据问题类型调整符号
        if self.problem.problem_type == "max":
            shadow_prices = -shadow_prices

        return shadow_prices

    def verify_complementary_slackness(
        self,
        primal_result: SimplexResult,
        dual_result: SimplexResult,
    ) -> bool:
        """
        验证互补松弛条件 (Complementary Slackness Condition)。

        互补松弛条件:
            对于最优解 x* 和 y*:
            - x*_j > 0 => 对偶约束 j 取等号
            - y*_i > 0 => 原约束 i 取等号
            - x*_j * (对偶松弛)_j = 0
            - y*_i * (原松弛)_i = 0

        即: 原变量和对偶松弛不能同时为正，反之亦然。

        Returns:
            bool: 是否满足互补松弛条件
        """
        prob = self.problem
        A = prob.A
        b = prob.b
        c = prob.c

        x = primal_result.solution
        y = dual_result.solution

        # 计算原约束的松弛
        primal_slack = A.T @ y - c  # 对偶约束的松弛 = A^T*y - c

        # 计算对偶约束的松弛
        dual_slack = b - A @ x  # 原约束的松弛 = b - A*x

        # 验证互补松弛: x_j * dual_slack_j = 0 和 y_i * primal_slack_i = 0
        comp_slack_product = np.abs(x * primal_slack) + np.abs(y * dual_slack)

        return np.all(comp_slack_product < self.tolerance)
