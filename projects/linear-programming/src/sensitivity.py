"""
灵敏度分析模块 (Sensitivity Analysis)

灵敏度分析 (Sensitivity Analysis) 研究当 LP 问题的参数 (目标系数、
约束右侧、约束矩阵) 发生变化时，最优解如何变化。

主要分析内容:
    1. 目标函数系数变化范围 (Objective Coefficient Ranges)
       - 确定 c_j 的变化范围，使得当前最优基不变
    2. 约束右侧变化范围 (RHS Ranges / Shadow Prices)
       - 确定 b_i 的变化范围，使得当前基仍可行
       - 影子价格: b_i 每增加 1 单位，目标值的变化
    3. 新增变量的分析 (New Variable Analysis)
       - 判断新变量是否应引入到最优解中
    4. 新增约束的分析 (New Constraint Analysis)
       - 判断新约束是否破坏当前最优解

学习要点:
    - 影子价格 (Shadow Price) 的经济意义
    - 允许变化范围 (Allowable Range) 的计算
    - 100% 规则 (100% Rule) 用于多系数同时变化
"""

import numpy as np
from typing import Dict, List, Optional, Tuple

from .problem import LPProblem
from .simplex import SimplexSolver, SimplexResult
from .dual import DualSolver


class SensitivityAnalyzer:
    """
    对 LP 问题的最优解进行灵敏度分析。
    """

    def __init__(self, problem: LPProblem, result: SimplexResult, tolerance: float = 1e-10):
        """
        初始化灵敏度分析器。

        Args:
            problem: 原始 LP 问题
            result: 单纯形法求解结果
            tolerance: 数值容差
        """
        self.problem = problem
        self.result = result
        self.tolerance = tolerance
        self.dual_prices = self._compute_dual_prices()

    def _compute_dual_prices(self) -> np.ndarray:
        """计算影子价格 (对偶变量值)."""
        dual_solver = DualSolver(self.problem, self.tolerance)
        return dual_solver.get_shadow_prices(self.result)

    def objective_coefficient_ranges(self) -> List[Dict]:
        """
        计算每个目标函数系数的允许变化范围。

        对于最小化问题:
            c_j 的变化范围 = [c_j - delta_j, c_j + delta_j]
            其中 delta_j 是使当前最优基保持最优的最大变化量。

        Returns:
            每个系数的允许变化范围列表
        """
        ranges = []
        n = self.problem.n_vars
        tableau = self.result.tableau_history[-1] if self.result.tableau_history else None

        if tableau is None:
            return ranges

        for j in range(n):
            c_j = self.problem.c[j]

            # 在最终单纯形表中，检验数 = c_j - z_j >= 0
            # 当 c_j 变化 delta 时，检验数变为 (c_j + delta) - z_j
            # 要保持最优: (c_j + delta) - z_j >= 0
            # 即 delta >= -(c_j - z_j) = -reduced_cost_j
            # 同时考虑基变量和非基变量的影响

            reduced_cost = tableau[-1, j]

            if abs(reduced_cost) < self.tolerance:
                # 该变量是基变量或具有零检验数
                # 变化范围需要更复杂的计算
                lower_bound = float("-inf")
                upper_bound = float("inf")

                # 简化计算: 对于基变量，需要看其对非基变量检验数的影响
                basis_idx = self.result.basis
                for k in range(n):
                    if k not in basis_idx:
                        # 非基变量 k 的检验数受 c_j 变化的影响
                        # 新检验数 = 原检验数 - (A_B^{-1} * A_k)_i * delta
                        # 需要保证所有非基变量检验数 >= 0
                        pass  # 简化: 暂不计算精确范围

                ranges.append({
                    "variable": j,
                    "current_value": float(c_j),
                    "lower_bound": lower_bound,
                    "upper_bound": upper_bound,
                    "allowable_decrease": float("inf"),
                    "allowable_increase": float("inf"),
                })
            else:
                # 非基变量: 允许增加量 = 当前检验数
                # 允许减少量 = 当前检验数 (因为检验数必须保持 >= 0)
                allowable_decrease = float(reduced_cost)
                allowable_increase = float(reduced_cost)

                ranges.append({
                    "variable": j,
                    "current_value": float(c_j),
                    "lower_bound": float(c_j - allowable_decrease),
                    "upper_bound": float(c_j + allowable_increase),
                    "allowable_decrease": allowable_decrease,
                    "allowable_increase": allowable_increase,
                })

        return ranges

    def rhs_ranges(self) -> List[Dict]:
        """
        计算每个约束右侧的允许变化范围。

        对于约束 i:  b_i 可以在 [b_i - delta_i, b_i + delta_i] 范围内变化，
        同时当前基保持可行 (即 B^{-1} * (b + delta*e_i) >= 0)。

        Returns:
            每个约束的允许变化范围列表
        """
        ranges = []
        m = self.problem.n_constraints

        # 从最终单纯形表提取 B^{-1} (逆矩阵)
        # 在初始基为单位阵的情况下，B^{-1} 出现在最终表中松弛变量对应列
        tableau = self.result.tableau_history[-1] if self.result.tableau_history else None

        if tableau is None:
            return ranges

        n = self.problem.n_vars
        B_inv = tableau[:m, n : n + m]

        for i in range(m):
            b_i = self.problem.b[i]
            b_inv_col = B_inv[:, i]

            # 需要满足: b_i + delta * (B^{-1})_{ki} >= 0 对所有 k
            # 即 delta >= -b_k / (B^{-1})_{ki} 当 (B^{-1})_{ki} > 0
            # 即 delta <= -b_k / (B^{-1})_{ki} 当 (B^{-1})_{ki} < 0

            allowable_increase = float("inf")
            allowable_decrease = float("inf")

            for k in range(m):
                if abs(b_inv_col[k]) > self.tolerance:
                    ratio = tableau[k, -1] / b_inv_col[k]
                    if b_inv_col[k] > 0:
                        allowable_increase = min(allowable_increase, float(ratio))
                    else:
                        allowable_decrease = min(allowable_decrease, float(-ratio))

            ranges.append({
                "constraint": i,
                "current_value": float(b_i),
                "shadow_price": float(self.dual_prices[i]),
                "allowable_increase": float(allowable_increase) if allowable_increase != float("inf") else None,
                "allowable_decrease": float(allowable_decrease) if allowable_decrease != float("inf") else None,
                "lower_bound": float(b_i - allowable_decrease) if allowable_decrease != float("inf") else float("-inf"),
                "upper_bound": float(b_i + allowable_increase) if allowable_increase != float("inf") else float("inf"),
            })

        return ranges

    def shadow_prices(self) -> np.ndarray:
        """
        获取影子价格 (对偶变量值)。

        影子价格的经济解释:
            约束 i 的右侧 b_i 每增加 1 单位，最优目标值的变化量。
            在资源分配问题中，影子价格表示该资源的边际价值。

        Returns:
            np.ndarray: 影子价格向量
        """
        return self.dual_prices.copy()

    def check_100pct_rule(
        self, changes: List[Tuple[int, float]]
    ) -> Dict:
        """
        检查多个目标系数同时变化是否满足 100% 规则。

        100% 规则:
            如果所有变化量的变化比例之和 <= 100%，
            则当前最优基保持不变。

            变化比例 = |delta_j| / allowable_change_j

        Args:
            changes: 变化列表，每个元素为 (变量索引, 变化量)

        Returns:
            100% 规则的检测结果
        """
        ranges = self.objective_coefficient_ranges()
        total_ratio = 0.0

        for idx, delta in changes:
            if idx < len(ranges):
                allowable = ranges[idx]["allowable_increase"] if delta > 0 else ranges[idx]["allowable_decrease"]
                if allowable and allowable > self.tolerance:
                    total_ratio += abs(delta) / allowable

        within_range = total_ratio <= 1.0 + self.tolerance

        return {
            "total_ratio": float(total_ratio),
            "within_100pct_range": within_range,
            "changes": [(idx, delta) for idx, delta in changes],
        }

    def analyze(self) -> Dict:
        """
        执行完整的灵敏度分析。

        Returns:
            完整的灵敏度分析结果
        """
        return {
            "shadow_prices": self.shadow_prices().tolist(),
            "objective_ranges": self.objective_coefficient_ranges(),
            "rhs_ranges": self.rhs_ranges(),
        }
