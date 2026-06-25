"""
最优化组合模块

使用数学优化方法确定因子权重，最大化组合因子的预测能力。
"""

import numpy as np
import pandas as pd
from scipy import stats, optimize
from typing import Optional, List, Dict


class OptimizedCombination:
    """
    最优化组合器

    使用数值优化方法寻找最优因子权重。

    使用示例:
        >>> optimizer = OptimizedCombination()
        >>> combined = optimizer.maximize_ir(factor_df, forward_returns)
    """

    @staticmethod
    def maximize_ir(factors: pd.DataFrame,
                    forward_returns: pd.Series,
                    factor_cols: Optional[List[str]] = None) -> pd.Series:
        """
        最大化 IR 组合: 优化权重使组合因子的 IC_IR 最大

        目标函数: max IR = mean(IC) / std(IC)

        参数:
            factors: 包含多列因子的 DataFrame
            forward_returns: 未来收益率序列
            factor_cols: 要组合的因子列名

        返回:
            最优权重组合因子值序列
        """
        if factor_cols is None:
            factor_cols = factors.columns.tolist()

        sub = factors[factor_cols].dropna()
        common_idx = sub.index.intersection(forward_returns.index)
        sub = sub.loc[common_idx]
        ret = forward_returns.loc[common_idx]

        # 标准化
        z_scores = (sub - sub.mean()) / sub.std().replace(0, np.nan)
        z_scores = z_scores.fillna(0)

        n_factors = len(factor_cols)

        def neg_ir(weights):
            """负 IR (用于最小化)"""
            combined = (z_scores.values * weights).sum(axis=1)
            # 逐期计算 IC
            ics = []
            for i in range(0, len(combined), 20):  # 每 20 期计算一次
                end = min(i + 20, len(combined))
                if end - i >= 5:
                    segment_ic = np.corrcoef(combined[i:end],
                                              ret.values[i:end])[0, 1]
                    ics.append(segment_ic)
            if len(ics) < 2:
                return 0
            ic_arr = np.array(ics)
            ir = ic_arr.mean() / ic_arr.std() if ic_arr.std() > 0 else 0
            return -ir

        # 约束: 权重之和为 1 (绝对值)
        constraints = [{"type": "eq", "fun": lambda w: np.sum(np.abs(w)) - 1}]
        bounds = [(-1, 1)] * n_factors

        # 初始等权
        w0 = np.ones(n_factors) / n_factors

        result = optimize.minimize(
            neg_ir, w0, method="SLSQP",
            bounds=bounds, constraints=constraints,
            options={"maxiter": 100}
        )

        weights = result.x
        combined = (z_scores.values * weights).sum(axis=1)
        return pd.Series(combined, index=sub.index)

    @staticmethod
    def maximize_ic_sum(factors: pd.DataFrame,
                        forward_returns: pd.Series,
                        factor_cols: Optional[List[str]] = None) -> pd.Series:
        """
        最大化 IC 总和组合: 优化权重使平均 IC 最大

        目标函数: max mean(IC)

        参数:
            factors: 包含多列因子的 DataFrame
            forward_returns: 未来收益率序列
            factor_cols: 要组合的因子列名

        返回:
            最优权重组合因子值序列
        """
        if factor_cols is None:
            factor_cols = factors.columns.tolist()

        sub = factors[factor_cols].dropna()
        common_idx = sub.index.intersection(forward_returns.index)
        sub = sub.loc[common_idx]
        ret = forward_returns.loc[common_idx]

        z_scores = (sub - sub.mean()) / sub.std().replace(0, np.nan)
        z_scores = z_scores.fillna(0)

        n_factors = len(factor_cols)

        def neg_mean_ic(weights):
            combined = (z_scores.values * weights).sum(axis=1)
            valid = ~(np.isnan(combined) | np.isnan(ret.values))
            if valid.sum() < 10:
                return 0
            corr = np.corrcoef(combined[valid], ret.values[valid])[0, 1]
            return -abs(corr)

        constraints = [{"type": "eq", "fun": lambda w: np.sum(np.abs(w)) - 1}]
        bounds = [(-1, 1)] * n_factors
        w0 = np.ones(n_factors) / n_factors

        result = optimize.minimize(
            neg_mean_ic, w0, method="SLSQP",
            bounds=bounds, constraints=constraints
        )

        weights = result.x
        combined = (z_scores.values * weights).sum(axis=1)
        return pd.Series(combined, index=sub.index)

    @staticmethod
    def minimum_variance(factors: pd.DataFrame,
                          factor_cols: Optional[List[str]] = None) -> pd.Series:
        """
        最小方差组合: 最小化组合因子的方差

        原理: 最小化因子之间的相关性带来的波动。

        参数:
            factors: 包含多列因子的 DataFrame
            factor_cols: 要组合的因子列名

        返回:
            最小方差组合因子值序列
        """
        if factor_cols is None:
            factor_cols = factors.columns.tolist()

        sub = factors[factor_cols].dropna()
        z_scores = (sub - sub.mean()) / sub.std().replace(0, np.nan)
        z_scores = z_scores.fillna(0)

        n_factors = len(factor_cols)
        cov_matrix = z_scores.cov().values

        def portfolio_variance(weights):
            return weights @ cov_matrix @ weights

        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
        bounds = [(0, 1)] * n_factors
        w0 = np.ones(n_factors) / n_factors

        result = optimize.minimize(
            portfolio_variance, w0, method="SLSQP",
            bounds=bounds, constraints=constraints
        )

        weights = result.x
        combined = (z_scores.values * weights).sum(axis=1)
        return pd.Series(combined, index=sub.index)
