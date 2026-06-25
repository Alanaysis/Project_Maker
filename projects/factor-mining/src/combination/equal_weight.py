"""
等权组合模块

最简单的因子组合方式，假设所有因子同等重要。
在因子相关性不高且质量相近时效果不错。
"""

import numpy as np
import pandas as pd
from typing import Optional, List


class EqualWeightCombination:
    """
    等权组合器

    将多个因子标准化后等权平均。

    使用示例:
        >>> combiner = EqualWeightCombination()
        >>> combined = combiner.combine(factor_df, ["momentum", "volatility", "value"])
    """

    @staticmethod
    def combine(factors: pd.DataFrame,
                factor_cols: Optional[List[str]] = None,
                standardize: bool = True) -> pd.Series:
        """
        等权组合

        参数:
            factors: 包含多列因子的 DataFrame
            factor_cols: 要组合的因子列名 (默认使用所有列)
            standardize: 是否先做 Z-score 标准化

        返回:
            组合因子值序列
        """
        if factor_cols is None:
            factor_cols = factors.columns.tolist()

        sub = factors[factor_cols].copy()

        if standardize:
            sub = (sub - sub.mean()) / sub.std().replace(0, np.nan)

        return sub.mean(axis=1)

    @staticmethod
    def rank_equal_weight(factors: pd.DataFrame,
                           factor_cols: Optional[List[str]] = None) -> pd.Series:
        """
        排名等权组合: 先排名百分位标准化，再等权平均

        原理: 排名标准化对极端值更稳健。

        参数:
            factors: 包含多列因子的 DataFrame
            factor_cols: 要组合的因子列名

        返回:
            组合因子值序列
        """
        if factor_cols is None:
            factor_cols = factors.columns.tolist()

        sub = factors[factor_cols]
        ranked = sub.rank(pct=True)
        return ranked.mean(axis=1)

    @staticmethod
    def sign_adjusted_combine(factors: pd.DataFrame,
                               signs: pd.Series,
                               factor_cols: Optional[List[str]] = None) -> pd.Series:
        """
        符号调整等权组合: 根据因子方向调整符号后组合

        原理: 有些因子值越大越好 (如 ROE)，有些越小越好 (如波动率)。
              需要统一方向后再组合。

        参数:
            factors: 包含多列因子的 DataFrame
            signs: 各因子的符号 (1 或 -1)，index 为因子名
            factor_cols: 要组合的因子列名

        返回:
            组合因子值序列
        """
        if factor_cols is None:
            factor_cols = factors.columns.tolist()

        sub = factors[factor_cols].copy()
        z_scores = (sub - sub.mean()) / sub.std().replace(0, np.nan)

        # 调整符号
        for col in factor_cols:
            if col in signs.index:
                z_scores[col] = z_scores[col] * signs[col]

        return z_scores.mean(axis=1)
