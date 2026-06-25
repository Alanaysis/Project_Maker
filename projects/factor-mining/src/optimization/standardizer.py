"""
因子标准化模块

将因子值标准化到统一的尺度，便于不同因子之间的比较和组合。
"""

import numpy as np
import pandas as pd
from typing import Optional


class FactorStandardizer:
    """
    因子标准化器

    提供多种标准化方法，将因子值转换为可比较的尺度。

    使用示例:
        >>> standardizer = FactorStandardizer()
        >>> z_factor = standardizer.zscore(factor)
        >>> rank_factor = standardizer.rank_percentile(factor)
    """

    @staticmethod
    def zscore(factor: pd.Series) -> pd.Series:
        """
        Z-score 标准化: (x - mean) / std

        原理: 最常用的标准化方法，将因子转换为均值 0、标准差 1 的分布。
              对极端值敏感，建议先做去极值处理。

        参数:
            factor: 因子值序列

        返回:
            Z-score 标准化后的因子值序列
        """
        mean = factor.mean()
        std = factor.std()
        if std == 0 or np.isnan(std):
            return pd.Series(0, index=factor.index)
        return (factor - mean) / std

    @staticmethod
    def rank_percentile(factor: pd.Series) -> pd.Series:
        """
        排名百分位标准化: 将因子转换为 0~1 的排名百分位

        原理: 对极端值不稳健，适合分布不均匀的因子。
              排名标准化后，因子值均匀分布在 [0, 1]。

        参数:
            factor: 因子值序列

        返回:
            排名百分位标准化后的因子值序列 (0~1)
        """
        valid = factor.dropna()
        if len(valid) == 0:
            return pd.Series(np.nan, index=factor.index)
        ranked = valid.rank(pct=True)
        return ranked.reindex(factor.index)

    @staticmethod
    def min_max_scale(factor: pd.Series) -> pd.Series:
        """
        Min-Max 缩放: 将因子缩放到 [0, 1]

        原理: 线性缩放到固定区间，对极端值非常敏感。
        计算: (x - min) / (max - min)

        参数:
            factor: 因子值序列

        返回:
            Min-Max 缩放后的因子值序列 (0~1)
        """
        fmin = factor.min()
        fmax = factor.max()
        frange = fmax - fmin
        if frange == 0:
            return pd.Series(0.5, index=factor.index)
        return (factor - fmin) / frange

    @staticmethod
    def robust_zscore(factor: pd.Series) -> pd.Series:
        """
        稳健 Z-score: 使用中位数和 MAD 代替均值和标准差

        原理: 中位数和 MAD (Median Absolute Deviation) 对极端值不敏感。
        计算: (x - median) / (1.4826 * MAD)

        参数:
            factor: 因子值序列

        返回:
            稳健 Z-score 标准化后的因子值序列
        """
        median = factor.median()
        mad = (factor - median).abs().median()
        # 1.4826 是正态分布下 MAD 到标准差的转换系数
        scaled_mad = mad * 1.4826
        if scaled_mad == 0 or np.isnan(scaled_mad):
            return pd.Series(0, index=factor.index)
        return (factor - median) / scaled_mad

    @staticmethod
    def normal_score(factor: pd.Series) -> pd.Series:
        """
        正态得分标准化: 将排名转换为标准正态分布的分位数

        原理: 假设因子值服从正态分布，将排名映射到标准正态分布。
              这种方法完全消除了原始分布的影响。

        参数:
            factor: 因子值序列

        返回:
            正态得分标准化后的因子值序列
        """
        from scipy import stats

        valid = factor.dropna()
        if len(valid) < 3:
            return pd.Series(np.nan, index=factor.index)

        ranked = valid.rank()
        # 转换为 [0, 1] 再映射到正态分布
        n = len(ranked)
        percentiles = (ranked - 0.5) / n
        # 避免 0 和 1
        percentiles = percentiles.clip(1e-6, 1 - 1e-6)
        normal = percentiles.apply(stats.norm.ppf)

        result = pd.Series(np.nan, index=factor.index)
        result.loc[valid.index] = normal
        return result

    @classmethod
    def standardize_panel(cls, factor_panel: pd.DataFrame,
                           method: str = "zscore") -> pd.DataFrame:
        """
        面板数据标准化: 对每一期做截面标准化

        参数:
            factor_panel: 因子面板 (index=日期, columns=股票)
            method: 标准化方法 ("zscore", "rank", "minmax", "robust", "normal")

        返回:
            标准化后的因子面板
        """
        method_map = {
            "zscore": cls.zscore,
            "rank": cls.rank_percentile,
            "minmax": cls.min_max_scale,
            "robust": cls.robust_zscore,
            "normal": cls.normal_score,
        }

        if method not in method_map:
            raise ValueError(f"Unknown method: {method}. Choose from {list(method_map.keys())}")

        func = method_map[method]
        result = factor_panel.apply(func, axis=1)
        return result
