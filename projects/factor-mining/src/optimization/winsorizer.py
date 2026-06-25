"""
因子去极值模块

处理因子中的极端值 (outliers)，避免极端值对因子分析的影响。
极端值可能来自数据错误、特殊事件或真实但罕见的情况。
"""

import numpy as np
import pandas as pd
from typing import Optional, Tuple


class FactorWinsorizer:
    """
    因子去极值器

    提供多种去极值方法，将因子极端值限制在合理范围内。

    使用示例:
        >>> winsorizer = FactorWinsorizer()
        >>> clean_factor = winsorizer.mad_winsorize(factor, n_mad=3)
    """

    @staticmethod
    def percentile_winsorize(factor: pd.Series,
                              lower: float = 0.01,
                              upper: float = 0.99) -> pd.Series:
        """
        分位数去极值: 将超出指定分位数的值截断

        原理: 将低于 lower 分位数的值设为 lower 分位数值，
              将高于 upper 分位数的值设为 upper 分位数值。
        这是最简单直接的去极值方法。

        参数:
            factor: 因子值序列
            lower: 下分位数 (默认 1%)
            upper: 上分位数 (默认 99%)

        返回:
            去极值后的因子值序列
        """
        q_low = factor.quantile(lower)
        q_high = factor.quantile(upper)
        return factor.clip(lower=q_low, upper=q_high)

    @staticmethod
    def mad_winsorize(factor: pd.Series, n_mad: float = 3.0) -> pd.Series:
        """
        MAD 去极值: 基于中位数绝对偏差 (Median Absolute Deviation)

        原理: MAD 对极端值不敏感，比标准差更适合处理异常值。
              界限 = median ± n_mad * MAD * 1.4826
              其中 1.4826 是正态分布下的转换系数。

        参数:
            factor: 因子值序列
            n_mad: MAD 的倍数 (默认 3)

        返回:
            去极值后的因子值序列
        """
        median = factor.median()
        mad = (factor - median).abs().median()
        scale = mad * 1.4826  # 转换为标准差尺度

        lower = median - n_mad * scale
        upper = median + n_mad * scale
        return factor.clip(lower=lower, upper=upper)

    @staticmethod
    def sigma_winsorize(factor: pd.Series, n_sigma: float = 3.0) -> pd.Series:
        """
        标准差去极值: 基于均值和标准差

        原理: 将超出 mean ± n_sigma * std 范围的值截断。
              简单但对极端值本身敏感 (因为极端值影响均值和标准差)。

        参数:
            factor: 因子值序列
            n_sigma: 标准差的倍数 (默认 3)

        返回:
            去极值后的因子值序列
        """
        mean = factor.mean()
        std = factor.std()
        lower = mean - n_sigma * std
        upper = mean + n_sigma * std
        return factor.clip(lower=lower, upper=upper)

    @staticmethod
    def iqr_winsorize(factor: pd.Series, n_iqr: float = 1.5) -> pd.Series:
        """
        IQR 去极值: 基于四分位距 (Interquartile Range)

        原理: 使用 Q1 - n_iqr * IQR 和 Q3 + n_iqr * IQR 作为界限。
              这是经典的箱线图异常值检测方法。

        参数:
            factor: 因子值序列
            n_iqr: IQR 的倍数 (默认 1.5)

        返回:
            去极值后的因子值序列
        """
        q1 = factor.quantile(0.25)
        q3 = factor.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - n_iqr * iqr
        upper = q3 + n_iqr * iqr
        return factor.clip(lower=lower, upper=upper)

    @staticmethod
    def detect_outliers(factor: pd.Series,
                        method: str = "mad",
                        threshold: float = 3.0) -> pd.Series:
        """
        检测极端值: 返回布尔序列标记极端值位置

        参数:
            factor: 因子值序列
            method: 检测方法 ("mad", "sigma", "iqr")
            threshold: 阈值倍数

        返回:
            布尔序列 (True 表示极端值)
        """
        if method == "mad":
            median = factor.median()
            mad = (factor - median).abs().median()
            scale = mad * 1.4826
            lower = median - threshold * scale
            upper = median + threshold * scale
        elif method == "sigma":
            mean = factor.mean()
            std = factor.std()
            lower = mean - threshold * std
            upper = mean + threshold * std
        elif method == "iqr":
            q1 = factor.quantile(0.25)
            q3 = factor.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - threshold * iqr
            upper = q3 + threshold * iqr
        else:
            raise ValueError(f"Unknown method: {method}")

        return (factor < lower) | (factor > upper)

    @classmethod
    def winsorize_panel(cls, factor_panel: pd.DataFrame,
                         method: str = "mad",
                         **kwargs) -> pd.DataFrame:
        """
        面板数据去极值: 对每一期做截面去极值

        参数:
            factor_panel: 因子面板 (index=日期, columns=股票)
            method: 去极值方法 ("percentile", "mad", "sigma", "iqr")
            **kwargs: 传递给去极值方法的参数

        返回:
            去极值后的因子面板
        """
        method_map = {
            "percentile": cls.percentile_winsorize,
            "mad": cls.mad_winsorize,
            "sigma": cls.sigma_winsorize,
            "iqr": cls.iqr_winsorize,
        }

        if method not in method_map:
            raise ValueError(f"Unknown method: {method}")

        func = method_map[method]
        return factor_panel.apply(lambda x: func(x, **kwargs), axis=1)
