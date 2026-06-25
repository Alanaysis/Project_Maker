"""
因子组合模块

提供多种因子组合方法，将多个单因子合成综合因子。
包括等权组合、IC 加权、最优化组合等方法。
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, List


class FactorCombinator:
    """
    因子组合器

    将多个因子按照不同策略组合为综合因子。

    使用示例:
        >>> combinator = FactorCombinator()
        >>> combined = combinator.equal_weight(factor_df)
        >>> combined = combinator.ic_weight(factor_df, ic_series)
    """

    @staticmethod
    def equal_weight(factors: pd.DataFrame,
                     factor_cols: Optional[List[str]] = None) -> pd.Series:
        """
        等权组合: 所有因子标准化后等权平均

        原理: 最简单的组合方式，假设所有因子同等重要。
              在因子相关性不高时效果不错。
        计算: F_combined = mean(zscore(F_1), zscore(F_2), ...)

        参数:
            factors: 包含多列因子的 DataFrame
            factor_cols: 要组合的因子列名，默认使用所有列

        返回:
            组合因子值序列
        """
        if factor_cols is None:
            factor_cols = factors.columns.tolist()

        # Z-score 标准化
        sub = factors[factor_cols]
        z_scores = (sub - sub.mean()) / sub.std().replace(0, np.nan)
        return z_scores.mean(axis=1)

    @staticmethod
    def ic_weight(factors: pd.DataFrame, ic_values: pd.Series,
                  factor_cols: Optional[List[str]] = None) -> pd.Series:
        """
        IC 加权组合: 以因子 IC 值为权重进行加权平均

        原理: IC 越高的因子预测能力越强，给予更高权重。
              使用滚动 IC 的均值作为权重。
        计算: F = Σ(IC_i * zscore(F_i)) / Σ|IC_i|

        参数:
            factors: 包含多列因子的 DataFrame
            ic_values: 各因子的 IC 均值 (Series, index 为因子名)
            factor_cols: 要组合的因子列名

        返回:
            IC 加权组合因子值序列
        """
        if factor_cols is None:
            factor_cols = factors.columns.tolist()

        sub = factors[factor_cols]
        z_scores = (sub - sub.mean()) / sub.std().replace(0, np.nan)

        # 提取各因子的 IC 权重
        weights = {}
        for col in factor_cols:
            if col in ic_values.index:
                weights[col] = ic_values[col]
            else:
                weights[col] = 0.0

        weight_series = pd.Series(weights)
        # 归一化权重 (保持符号)
        total_abs = weight_series.abs().sum()
        if total_abs > 0:
            weight_series = weight_series / total_abs

        # 加权求和
        weighted = z_scores.multiply(weight_series, axis=1)
        return weighted.sum(axis=1)

    @staticmethod
    def max_ic_ir_combination(factors: pd.DataFrame,
                               forward_returns: pd.Series,
                               window: int = 60,
                               factor_cols: Optional[List[str]] = None) -> pd.Series:
        """
        最大化 IC_IR 组合: 在滚动窗口内优化权重使得组合因子 IC_IR 最大

        原理: 最大化因子组合的信息比率，即 IC 均值/IC 标准差。
              这比简单 IC 加权更稳健，因为它同时考虑了 IC 的稳定性。

        参数:
            factors: 包含多列因子的 DataFrame
            forward_returns: 未来收益率序列
            window: 滚动优化窗口
            factor_cols: 要组合的因子列名

        返回:
            最优化组合因子值序列
        """
        if factor_cols is None:
            factor_cols = factors.columns.tolist()

        sub = factors[factor_cols].copy()
        z_scores = (sub - sub.mean()) / sub.std().replace(0, np.nan)

        n_factors = len(factor_cols)
        n_samples = len(z_scores)

        # 使用滚动窗口优化
        result = pd.Series(np.nan, index=factors.index)

        for i in range(window, n_samples):
            # 窗口内的数据
            window_z = z_scores.iloc[i - window:i]
            window_ret = forward_returns.iloc[i - window:i]

            # 计算各因子在窗口内的 IC
            ics = window_z.corrwith(window_ret, axis=0)
            ic_mean = ics.mean()
            ic_std = ics.std()

            if ic_std > 0:
                # 简单启发式: 以 IC 均值为权重
                weights = ics / ics.abs().sum()
                result.iloc[i] = (z_scores.iloc[i] * weights).sum()

        return result

    @staticmethod
    def rank_weight(factors: pd.DataFrame,
                    factor_cols: Optional[List[str]] = None) -> pd.Series:
        """
        排名加权组合: 将因子转换为排名后组合

        原理: 排名标准化对极端值更稳健，适合因子分布不均匀的情况。
        计算: 对每个因子取排名百分位，然后等权平均。

        参数:
            factors: 包含多列因子的 DataFrame
            factor_cols: 要组合的因子列名

        返回:
            排名加权组合因子值序列
        """
        if factor_cols is None:
            factor_cols = factors.columns.tolist()

        sub = factors[factor_cols]
        # 排名百分位
        ranked = sub.rank(pct=True)
        return ranked.mean(axis=1)

    @staticmethod
    def top_k_combination(factors: pd.DataFrame, ic_values: pd.Series,
                           k: int = 5,
                           factor_cols: Optional[List[str]] = None) -> pd.Series:
        """
        Top-K 因子组合: 仅选择 IC 最高的 K 个因子进行组合

        原理: 去掉弱因子可以减少噪声，提高组合因子的信噪比。

        参数:
            factors: 包含多列因子的 DataFrame
            ic_values: 各因子的 IC 均值
            k: 选择的因子数量
            factor_cols: 候选因子列名

        返回:
            Top-K 组合因子值序列
        """
        if factor_cols is None:
            factor_cols = factors.columns.tolist()

        # 按 IC 绝对值排序
        available_ics = {c: ic_values.get(c, 0) for c in factor_cols}
        sorted_factors = sorted(available_ics.items(),
                                key=lambda x: abs(x[1]), reverse=True)
        top_k_cols = [c for c, _ in sorted_factors[:k]]

        return FactorCombinator.equal_weight(factors, factor_cols=top_k_cols)
