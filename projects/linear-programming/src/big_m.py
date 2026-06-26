"""
大M法求解器 (Big-M Method Solver)

大M法是一种处理人工变量的方法，用于在单纯形法中处理无初始可行解的情况。

核心思想:
    在目标函数中给人工变量赋予一个极大的惩罚系数 M，
    迫使算法在优化过程中尽可能地将人工变量变为 0。

    原问题:     minimize c^T * x
    添加人工变量后: minimize c^T * x + M * sum(a_i)

    其中 M 是一个足够大的正数。

    如果最优解中人工变量 > 0，则原问题无可行解。

学习要点:
    - 与两阶段法的区别: 两阶段法分两步求解，大M法一步求解
    - M 的选择: 需要足够大但不能过大 (数值稳定性问题)
    - 适用场景: 人工变量数量较少时
"""

import numpy as np
from typing import Optional, List, Dict

from .problem import LPProblem, create_problem
from .simplex import SimplexSolver, SimplexResult


class BigMSolver:
    """
    使用大M法求解线性规划问题。

    适用于没有明显初始基本可行解的问题。
    """

    # 大M的值: 需要足够大以惩罚人工变量，但不过大以保证数值稳定性
    DEFAULT_M = 1e6

    def __init__(
        self,
        problem: LPProblem,
        M: float = DEFAULT_M,
        tolerance: float = 1e-10,
        max_iterations: int = 1000,
    ):
        """
        初始化大M法求解器。

        Args:
            problem: 线性规划问题
            M: 惩罚系数 (大数)
            tolerance: 数值容差
            max_iterations: 最大迭代次数
        """
        self.original_problem = problem
        self.M = M
        self.tolerance = tolerance
        self.max_iterations = max_iterations

    def solve(self) -> SimplexResult:
        """
        使用大M法求解问题。

        Returns:
            SimplexResult: 求解结果
        """
        prob = self.original_problem
        m = prob.n_constraints
        n = prob.n_vars

        A = prob.A.copy()
        b = prob.b.copy()
        c = prob.c.copy()

        # 处理最大化问题
        if prob.problem_type == "max":
            c = -c

        # 处理 b < 0 的约束
        for i in range(m):
            if b[i] < 0:
                A[i] *= -1
                b[i] *= -1

        # 确定需要添加人工变量的约束
        artificial_cols = []
        for i in range(m):
            if b[i] >= -self.tolerance:
                # 检查该行是否已有可以作为基的列
                has_positive_col = False
                for j in range(n + len(artificial_cols)):
                    if j < n:
                        if A[i, j] > self.tolerance:
                            has_positive_col = True
                            break
                    else:
                        # 之前添加的人工变量
                        if i == (j - n):
                            has_positive_col = True
                            break
                if not has_positive_col:
                    art_col = np.zeros(n + len(artificial_cols) + 1)
                    art_col[n + len(artificial_cols)] = 1.0
                    artificial_cols.append(art_col)

        if not artificial_cols:
            # 不需要人工变量，直接求解
            solver = SimplexSolver(prob, self.tolerance, self.max_iterations)
            return solver.solve()

        # 构造大M问题的增广矩阵
        A_aug = np.hstack([A, np.column_stack(artificial_cols)])
        n_aug = A_aug.shape[1]

        # 构造大M目标函数
        # 最小化 c^T * x + M * sum(artificial variables)
        c_aug = np.zeros(n_aug)
        c_aug[:n] = c
        c_aug[n:] = self.M  # 人工变量系数为 M

        big_m_prob = create_problem(
            c=c_aug.tolist(),
            A=A_aug.tolist(),
            b=b.tolist(),
            variable_names=[
                *(prob.variable_names or [f"x{i+1}" for i in range(n)]),
                *(f"a{i+1}" for i in range(len(artificial_cols))),
            ],
            problem_type="min",
        )

        # 求解
        solver = SimplexSolver(big_m_prob, self.tolerance, self.max_iterations)
        result = solver.solve()

        if result.status == "optimal":
            # 检查人工变量是否为 0
            art_values = result.solution[n:]
            if np.any(np.abs(art_values) > self.tolerance):
                # 人工变量不为 0，原问题无可行解
                return SimplexResult(
                    optimal_value=float("inf"),
                    solution=np.zeros(n),
                    basis=[],
                    iterations=result.iterations,
                    status="infeasible",
                    variable_names=prob.variable_names,
                )

            # 返回原问题的解
            return SimplexResult(
                optimal_value=result.optimal_value,
                solution=result.solution[:n],
                basis=result.basis,
                iterations=result.iterations,
                status="optimal",
                variable_names=prob.variable_names,
            )

        return result

    def get_method_info(self) -> Dict:
        """获取大M法的说明信息."""
        return {
            "method": "Big-M Method",
            "M_value": self.M,
            "description": (
                "大M法通过在目标函数中添加人工变量的惩罚项 "
                "(M * sum(a_i)) 来处理无初始可行解的情况。"
            ),
        }
