"""
因子补全模块

处理因子中的缺失值，确保因子数据的完整性。
缺失值可能来自停牌、数据延迟、计算失败等原因。
"""

import numpy as np
import pandas as pd
from typing import Optional


class FactorFiller:
    """
    因子补全器

    提供多种缺失值补全方法。

    使用示例:
        >>> filler = FactorFiller()
        >>> filled = filler.forward_fill(factor, limit=5)
        >>> filled = filler.cross_sectional_median(factor, industry)
    """

    @staticmethod
    def forward_fill(factor: pd.Series, limit: int = 5) -> pd.Series:
        """
        前值填充: 用最近的非缺失值填充

        原理: 假设因子值在短期内变化不大，用最近的有效值代替。
              适合基本面因子 (财务数据更新频率低)。

        参数:
            factor: 因子值序列
            limit: 最大连续填充天数

        返回:
            填充后的因子值序列
        """
        return factor.ffill(limit=limit)

    @staticmethod
    def cross_sectional_median(factor: pd.Series,
                                industry: Optional[pd.Series] = None) -> pd.Series:
        """
        截面中位数填充: 用同行业 (或全市场) 的中位数填充

        原理: 用同类公司的因子值填充缺失，比用全市场均值更合理。

        参数:
            factor: 因子值序列 (index=股票代码)
            industry: 行业分类标签 (可选)

        返回:
            填充后的因子值序列
        """
        result = factor.copy()

        if industry is not None:
            # 行业中位数填充
            data = pd.DataFrame({"factor": factor, "industry": industry})
            industry_median = data.groupby("industry")["factor"].transform("median")
            result = result.fillna(industry_median)

        # 全市场中位数填充
        result = result.fillna(factor.median())
        return result

    @staticmethod
    def cross_sectional_mean(factor: pd.Series,
                              industry: Optional[pd.Series] = None) -> pd.Series:
        """
        截面均值填充: 用同行业 (或全市场) 的均值填充

        参数:
            factor: 因子值序列
            industry: 行业分类标签 (可选)

        返回:
            填充后的因子值序列
        """
        result = factor.copy()

        if industry is not None:
            data = pd.DataFrame({"factor": factor, "industry": industry})
            industry_mean = data.groupby("industry")["factor"].transform("mean")
            result = result.fillna(industry_mean)

        result = result.fillna(factor.mean())
        return result

    @staticmethod
    def interpolate_fill(factor: pd.Series,
                          method: str = "linear") -> pd.Series:
        """
        插值填充: 使用线性或样条插值

        原理: 假设因子值随时间平滑变化，用插值估计缺失值。
              适合时序上有连续性的因子。

        参数:
            factor: 因子值序列
            method: 插值方法 ("linear", "cubic", "spline")

        返回:
            填充后的因子值序列
        """
        return factor.interpolate(method=method)

    @staticmethod
    def zero_fill(factor: pd.Series) -> pd.Series:
        """
        零值填充: 用零填充缺失值

        原理: 最简单的方法，但可能导致因子分布偏移。
              仅在缺失比例很低时使用。

        参数:
            factor: 因子值序列

        返回:
            填充后的因子值序列
        """
        return factor.fillna(0)

    @staticmethod
    def neutral_fill(factor: pd.Series) -> pd.Series:
        """
        中性值填充: 用因子的中位数填充

        原理: 中位数对极端值不敏感，填充后不会引入过多噪声。

        参数:
            factor: 因子值序列

        返回:
            填充后的因子值序列
        """
        return factor.fillna(factor.median())

    @classmethod
    def fill_panel(cls, factor_panel: pd.DataFrame,
                    method: str = "forward",
                    limit: int = 5,
                    industry_panel: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        面板数据补全: 对因子面板进行缺失值处理

        参数:
            factor_panel: 因子面板 (index=日期, columns=股票)
            method: 补全方法 ("forward", "median", "mean", "interpolate", "zero", "neutral")
            limit: forward fill 的最大连续填充天数
            industry_panel: 行业面板 (用于截面填充)

        返回:
            补全后的因子面板
        """
        if method == "forward":
            return factor_panel.ffill(limit=limit)
        elif method == "median":
            return factor_panel.apply(
                lambda col: cls.cross_sectional_median(col), axis=0)
        elif method == "mean":
            return factor_panel.fillna(factor_panel.mean())
        elif method == "interpolate":
            return factor_panel.interpolate(method="linear")
        elif method == "zero":
            return factor_panel.fillna(0)
        elif method == "neutral":
            return factor_panel.fillna(factor_panel.median())
        else:
            raise ValueError(f"Unknown method: {method}")
