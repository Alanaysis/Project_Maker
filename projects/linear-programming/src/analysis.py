"""
无界解检测与多重最优解检测模块 (Unbounded & Multiple Optimal Solutions)

无界解检测:
    在单纯形法的迭代过程中，如果选中的进基变量对应的列
    所有系数都 <= 0，则说明该变量可以无限增大而不违反任何约束，
    目标函数值可以无限改善 (无界解)。

多重最优解检测:
    在最优单纯形表中，如果存在非基变量的检验数为 0，
    则说明存在多个最优解 (无穷多最优解)。
    这些解的凸组合也都是最优解。

学习要点:
    - 无界解的几何意义: 可行域无界且目标函数可沿某个方向无限改善
    - 多重最优解的几何意义: 目标函数等值线与可行域的某条边平行
    - 如何从单纯形表中检测这两种情况
"""

import numpy as np
from typing import List, Tuple, Optional, Dict

from .problem import LPProblem
from .simplex import SimplexSolver, SimplexResult


class SolutionAnalyzer:
    """
    分析单纯形法求解结果，检测无界解和多重最优解。
    """

    def __init__(self, problem: LPProblem, tolerance: float = 1e-10):
        """
        初始化分析器。

        Args:
            problem: 线性规划问题
            tolerance: 数值容差
        """
        self.problem = problem
        self.tolerance = tolerance

    def check_unbounded(self, tableau: np.ndarray, basis: List[int]) -> Tuple[bool, int]:
        """
        检查单纯形表是否指示无界解。

        无界条件:
            存在非基变量 j，其检验数 < 0 (可改善目标)，
            且该列所有系数 <= 0 (无约束限制其增大)。

        Args:
            tableau: 单纯形表
            basis: 基变量索引

        Returns:
            (is_unbounded, entering_var_index): 是否无界及进基变量索引
        """
        m = len(basis)
        n = self.problem.n_vars

        # 检查目标行 (检验数)
        reduced_costs = tableau[-1, :n]

        for j in range(n):
            if reduced_costs[j] < -self.tolerance:
                # 检验数为负，可能改善
                # 检查该列是否有正系数
                if np.all(tableau[:m, j] <= self.tolerance):
                    return True, j

        return False, -1

    def check_multiple_optimal(
        self, tableau: np.ndarray
    ) -> Tuple[bool, List[int]]:
        """
        检查是否存在多重最优解。

        多重最优解条件:
            在最优单纯形表中，存在非基变量的检验数 = 0。

        Args:
            tableau: 最终的单纯形表

        Returns:
            (has_multiple, zero_reduced_cost_vars): 是否有多个最优解及对应的变量
        """
        n = self.problem.n_vars
        reduced_costs = tableau[-1, :n]

        # 在最优表中，检验数 >= 0
        # 检验数 = 0 的非基变量表示可以 pivot 到另一个最优解
        zero_reduced_cost_vars = []
        for j in range(n):
            if abs(reduced_costs[j]) < self.tolerance:
                zero_reduced_cost_vars.append(j)

        return len(zero_reduced_cost_vars) > 0, zero_reduced_cost_vars

    def find_alternate_optimal_solutions(
        self, tableau: np.ndarray, basis: List[int]
    ) -> List[np.ndarray]:
        """
        如果存在多重最优解，找到另一个最优解。

        通过将检验数为 0 的非基变量进基，可以得到另一个最优顶点。

        Args:
            tableau: 单纯形表
            basis: 基变量索引

        Returns:
            另一个最优解的列表
        """
        n = self.problem.n_vars
        m = len(basis)
        solutions = []

        zero_rc_vars, _ = self.check_multiple_optimal(tableau)
        if not zero_rc_vars:
            return solutions

        # 尝试将每个检验数为 0 的非基变量进基
        for j in zero_rc_vars:
            # 检查是否可以 pivot
            if np.any(tableau[:m, j] > self.tolerance):
                # 执行 pivot
                new_tableau = tableau.copy()
                ratios = np.full(m, float("inf"))
                for i in range(m):
                    if new_tableau[i, j] > self.tolerance:
                        ratios[i] = new_tableau[i, -1] / new_tableau[i, j]

                min_ratio_idx = np.argmin(ratios)
                pivot_elem = new_tableau[min_ratio_idx, j]

                new_tableau[min_ratio_idx, :] /= pivot_elem
                for i in range(m + 1):
                    if i != min_ratio_idx:
                        factor = new_tableau[i, j]
                        new_tableau[i, :] -= factor * new_tableau[min_ratio_idx, :]

                # 提取解
                new_basis = list(basis)
                new_basis[min_ratio_idx] = j

                solution = np.zeros(n)
                for i, idx in enumerate(new_basis):
                    if i < len(new_tableau) - 1:
                        solution[idx] = new_tableau[i, -1]

                solutions.append(solution)

        return solutions

    def analyze(self, result: SimplexResult) -> Dict:
        """
        综合分析求解结果。

        Args:
            result: 单纯形法求解结果

        Returns:
            分析结果的字典
        """
        analysis = {
            "status": result.status,
            "optimal_value": result.optimal_value,
        }

        if result.status != "optimal":
            analysis["unbounded_detected"] = result.status == "unbounded"
            return analysis

        if result.tableau_history:
            final_tableau = result.tableau_history[-1]

            # 检查无界
            is_unbounded, unbounded_var = self.check_unbounded(
                final_tableau, result.basis
            )
            analysis["unbounded_detected"] = is_unbounded

            # 检查多重最优解
            has_multiple, zero_vars = self.check_multiple_optimal(final_tableau)
            analysis["multiple_optimal_solutions"] = has_multiple
            analysis["zero_reduced_cost_vars"] = zero_vars

            if has_multiple:
                alternate = self.find_alternate_optimal_solutions(
                    final_tableau, result.basis
                )
                analysis["alternate_solutions"] = [s.tolist() for s in alternate]

        return analysis
