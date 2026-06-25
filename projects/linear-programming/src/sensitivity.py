"""
敏感性分析。

分析最优解对参数变化的敏感程度：
1. 目标函数系数变化 (c_j 变化范围)
2. 右端项变化 (b_i 变化范围)
3. 新增变量/约束的影响

数学基础：
    最优基 B 对应的条件：
    - 原始可行性: B^{-1} b >= 0
    - 对偶可行性: c_B^T B^{-1} A_j - c_j >= 0 (对非基变量)

    c_j 变化范围: 保持当前基最优的最大变化范围
    b_i 变化范围: 保持当前基可行的最大变化范围
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from .linear_program import LinearProgram, LPResult, ObjectiveType


@dataclass
class SensitivityRange:
    """敏感性分析范围"""
    param_name: str
    current_value: float
    lower_bound: Optional[float]
    upper_bound: Optional[float]
    allowable_increase: Optional[float]
    allowable_decrease: Optional[float]

    def __repr__(self):
        return (f"{self.param_name}: current={self.current_value:.4f}, "
                f"range=[{self.lower_bound}, {self.upper_bound}], "
                f"increase={self.allowable_increase}, "
                f"decrease={self.allowable_decrease}")


@dataclass
class SensitivityReport:
    """敏感性分析报告"""
    objective_coefficients: List[SensitivityRange]
    rhs_values: List[SensitivityRange]
    shadow_prices: np.ndarray
    reduced_costs: np.ndarray
    is_degenerate: bool

    def __repr__(self):
        lines = ["=== Sensitivity Report ==="]
        lines.append("\nObjective Coefficient Ranges:")
        for r in self.objective_coefficients:
            lines.append(f"  {r}")
        lines.append("\nRight-Hand Side Ranges:")
        for r in self.rhs_values:
            lines.append(f"  {r}")
        lines.append(f"\nShadow Prices: {np.round(self.shadow_prices, 4)}")
        lines.append(f"Reduced Costs: {np.round(self.reduced_costs, 4)}")
        lines.append(f"Degenerate: {self.is_degenerate}")
        return "\n".join(lines)


class SensitivityAnalyzer:
    """
    敏感性分析器。

    基于最优单纯形表进行参数变化分析。

    Examples
    --------
    >>> analyzer = SensitivityAnalyzer()
    >>> report = analyzer.analyze(lp, result)
    >>> print(report)
    """

    EPS = 1e-10

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def analyze(self, lp: LinearProgram, result: LPResult) -> SensitivityReport:
        """
        对最优解进行敏感性分析。

        Parameters
        ----------
        lp : LinearProgram
            原问题
        result : LPResult
            求解结果（必须是最优的）

        Returns
        -------
        report : SensitivityReport
        """
        if result.status != "optimal":
            raise ValueError("只能对最优解进行敏感性分析")

        tableau = result.tableau_history[-1]
        m = tableau.shape[0] - 1
        n_orig = lp.num_vars

        # 提取基信息
        basis = self._extract_basis(tableau, n_orig, m)

        # 1. 目标函数系数变化范围
        obj_ranges = self._objective_coefficient_ranges(
            lp, tableau, basis, n_orig, m
        )

        # 2. 右端项变化范围
        rhs_ranges = self._rhs_ranges(lp, tableau, basis, n_orig, m)

        # 3. 影子价格 (对偶变量)
        shadow_prices = np.zeros(m)
        for i in range(m):
            shadow_prices[i] = tableau[-1, n_orig + i]

        # 4. 约简成本 (Reduced Costs)
        reduced_costs = tableau[-1, :n_orig].copy()

        # 5. 检查退化性
        is_degenerate = self._check_degeneracy(tableau, basis, n_orig, m)

        return SensitivityReport(
            objective_coefficients=obj_ranges,
            rhs_values=rhs_ranges,
            shadow_prices=shadow_prices,
            reduced_costs=reduced_costs,
            is_degenerate=is_degenerate
        )

    def _extract_basis(self, tableau: np.ndarray, n_orig: int, m: int) -> List[int]:
        """从单纯形表提取基变量索引。"""
        basis = []
        n_full = tableau.shape[1] - 1
        for i in range(m):
            for j in range(n_full):
                if abs(tableau[i, j] - 1.0) < self.EPS:
                    # 检查是否是该列唯一的非零元素
                    col = tableau[:, j]
                    non_zero = np.sum(np.abs(col) > self.EPS)
                    if non_zero == 1 and abs(col[i] - 1.0) < self.EPS:
                        basis.append(j)
                        break
        return basis

    def _objective_coefficient_ranges(self, lp: LinearProgram,
                                       tableau: np.ndarray,
                                       basis: List[int],
                                       n_orig: int, m: int) -> List[SensitivityRange]:
        """
        计算目标函数系数的允许变化范围。

        对于基变量 c_j:
            保持对偶可行性的条件:
            c_B^T B^{-1} A_k - c_k <= 0 对所有非基变量 k
            即 c_j 变化时，B^{-1} A_k 的行不会变，但 c_B 会变

        对于非基变量 c_j:
            只需保持 sigma_j = c_j - c_B^T B^{-1} A_j <= 0
        """
        ranges = []
        c = lp.c.copy()

        for j in range(n_orig):
            current = c[j]

            if j in basis:
                # 基变量: 需要保证所有非基变量的检验数 >= 0 (z_k - c_k >= 0)
                basis_pos = basis.index(j)

                # B^{-1} A 的第 basis_pos 行
                b_inv_row = tableau[basis_pos, :n_orig]

                # 当 c_j 变化 delta 时, sigma_k = z_k - c_k 变化为 delta * b_inv_row[k]
                # 要求 sigma_k + delta * b_inv_row[k] >= 0

                lower = -np.inf
                upper = np.inf

                for k in range(n_orig):
                    if k not in basis:
                        sigma_k = tableau[-1, k]  # z_k - c_k
                        coeff = b_inv_row[k]

                        if abs(coeff) > self.EPS:
                            bound = -sigma_k / coeff
                            if coeff > 0:
                                lower = max(lower, bound)
                            else:
                                upper = min(upper, -bound)

                ranges.append(SensitivityRange(
                    param_name=f"c_{j}",
                    current_value=current,
                    lower_bound=current + lower if lower > -np.inf else -np.inf,
                    upper_bound=current + upper if upper < np.inf else np.inf,
                    allowable_increase=upper if upper < np.inf else None,
                    allowable_decrease=-lower if lower > -np.inf else None
                ))
            else:
                # 非基变量: 只需 sigma_j = z_j - c_j >= 0
                sigma_j = tableau[-1, j]  # z_j - c_j
                z_j = current + sigma_j  # z_j = c_j + (z_j - c_j)

                ranges.append(SensitivityRange(
                    param_name=f"c_{j}",
                    current_value=current,
                    lower_bound=-np.inf,
                    upper_bound=z_j,
                    allowable_increase=z_j - current if z_j < np.inf else None,
                    allowable_decrease=None
                ))

        return ranges

    def _rhs_ranges(self, lp: LinearProgram, tableau: np.ndarray,
                     basis: List[int], n_orig: int, m: int) -> List[SensitivityRange]:
        """
        计算右端项的允许变化范围。

        b_i 变化时，需要保持原始可行性: B^{-1}(b + delta_i e_i) >= 0
        即 B^{-1} b + delta_i * B^{-1}[:, i] >= 0
        """
        ranges = []
        b = lp.b.copy()
        B_inv = tableau[:m, n_orig:n_orig + m].copy()
        current_b_bar = tableau[:m, -1].copy()

        for i in range(m):
            col_i = B_inv[:, i]
            current = b[i]

            lower = -np.inf
            upper = np.inf

            for k in range(m):
                if abs(col_i[k]) > self.EPS:
                    bound = -current_b_bar[k] / col_i[k]
                    if col_i[k] > 0:
                        lower = max(lower, bound)
                    else:
                        upper = min(upper, -bound)

            ranges.append(SensitivityRange(
                param_name=f"b_{i}",
                current_value=current,
                lower_bound=current + lower if lower > -np.inf else -np.inf,
                upper_bound=current + upper if upper < np.inf else np.inf,
                allowable_increase=upper if upper < np.inf else None,
                allowable_decrease=-lower if lower > -np.inf else None
            ))

        return ranges

    def _check_degeneracy(self, tableau: np.ndarray, basis: List[int],
                           n_orig: int, m: int) -> bool:
        """检查是否存在退化（某个基变量值为 0）。"""
        for i, var_idx in enumerate(basis):
            if abs(tableau[i, -1]) < self.EPS:
                return True
        return False

    def analyze_objective_change(self, lp: LinearProgram, result: LPResult,
                                  delta_c: np.ndarray) -> LPResult:
        """
        分析目标函数系数变化后的影响。

        Parameters
        ----------
        lp : LinearProgram
            原问题
        result : LPResult
            当前最优解
        delta_c : np.ndarray
            目标函数系数变化量

        Returns
        -------
        new_result : LPResult
            如果仍在允许范围内，返回更新后的结果
        """
        tableau = result.tableau_history[-1].copy()
        m = tableau.shape[0] - 1
        n_orig = lp.num_vars
        basis = self._extract_basis(tableau, n_orig, m)

        # 更新检验数 (目标行存储 z_j - c_j)
        for j in range(n_orig):
            if j not in basis:
                tableau[-1, j] -= delta_c[j]

        # 更新目标函数值
        for i, var_idx in enumerate(basis):
            if var_idx < n_orig:
                tableau[-1, -1] += delta_c[var_idx] * tableau[i, -1]

        # 检查是否仍然最优 (z_j - c_j >= 0)
        if np.all(tableau[-1, :n_orig + m] >= -self.EPS):
            # 仍然最优，更新解
            solution = np.zeros(n_orig)
            for i, var_idx in enumerate(basis):
                if var_idx < n_orig:
                    solution[var_idx] = tableau[i, -1]

            optimal_value = tableau[-1, -1]
            if lp.objective_type == ObjectiveType.MIN:
                optimal_value = -optimal_value

            return LPResult(
                status="optimal",
                optimal_value=optimal_value,
                solution=solution,
                iterations=result.iterations,
                tableau_history=[tableau],
                message="目标函数变化后仍在最优"
            )
        else:
            return LPResult(
                status="need_reoptimize",
                message="目标函数超出允许范围，需要重新优化"
            )

    def analyze_rhs_change(self, lp: LinearProgram, result: LPResult,
                            delta_b: np.ndarray) -> LPResult:
        """
        分析右端项变化后的影响。

        利用 B^{-1} 更新:
        x_B_new = B^{-1}(b + delta_b)
        z_new = c_B^T B^{-1}(b + delta_b)
        """
        tableau = result.tableau_history[-1].copy()
        m = tableau.shape[0] - 1
        n_orig = lp.num_vars
        basis = self._extract_basis(tableau, n_orig, m)

        B_inv = tableau[:m, n_orig:n_orig + m]

        # 更新右端项
        new_rhs = tableau[:m, -1] + B_inv @ delta_b
        tableau[:m, -1] = new_rhs

        # 检查可行性
        if np.all(new_rhs >= -self.EPS):
            # 仍然可行
            solution = np.zeros(n_orig)
            for i, var_idx in enumerate(basis):
                if var_idx < n_orig:
                    solution[var_idx] = max(0, new_rhs[i])

            optimal_value = 0
            for i, var_idx in enumerate(basis):
                if var_idx < n_orig:
                    optimal_value += lp.c[var_idx] * solution[var_idx]

            return LPResult(
                status="optimal",
                optimal_value=optimal_value if lp.objective_type == ObjectiveType.MAX else -optimal_value,
                solution=solution,
                iterations=result.iterations,
                tableau_history=[tableau],
                message="右端项变化后仍可行"
            )
        else:
            return LPResult(
                status="need_dual_simplex",
                message="右端项变化导致不可行，需要对偶单纯形法重新优化"
            )
