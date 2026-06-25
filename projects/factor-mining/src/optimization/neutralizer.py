"""
因子中性化模块

去除因子中的行业和市值暴露，使因子具有纯 alpha 信号。
中性化是因子预处理的关键步骤，避免因子收益被行业或市值因子解释。
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict


class FactorNeutralizer:
    """
    因子中性器

    通过回归方法去除因子中的行业和市值暴露。

    使用示例:
        >>> neutralizer = FactorNeutralizer()
        >>> neutral_factor = neutralizer.neutralize(factor, industry, market_cap)
    """

    @staticmethod
    def neutralize(factor: pd.Series,
                   industry: pd.Series,
                   market_cap: Optional[pd.Series] = None) -> pd.Series:
        """
        行业市值中性化: 回归去除行业和市值的影响

        原理: 对因子值做截面回归:
              Factor = α + Σ(β_i * Industry_i) + γ * ln(MarketCap) + ε
              中性化后的因子 = ε (残差)

        参数:
            factor: 因子值序列 (index=股票代码)
            industry: 行业分类标签 (index=股票代码)
            market_cap: 市值序列 (可选)

        返回:
            中性化后的因子值序列
        """
        # 合并数据
        data = pd.DataFrame({"factor": factor, "industry": industry})
        if market_cap is not None:
            data["ln_cap"] = np.log(market_cap)
        data = data.dropna()

        if len(data) < 10:
            return pd.Series(np.nan, index=factor.index)

        # 构造行业哑变量
        dummies = pd.get_dummies(data["industry"], prefix="ind", drop_first=True)

        # 构造回归矩阵
        X = dummies.astype(float)
        if "ln_cap" in data.columns:
            X["ln_cap"] = data["ln_cap"]

        y = data["factor"]

        # OLS 回归
        try:
            # 添加常数项
            X_with_const = np.column_stack([np.ones(len(X)), X.values])
            beta = np.linalg.lstsq(X_with_const, y.values, rcond=None)[0]
            predicted = X_with_const @ beta
            residual = y.values - predicted
        except np.linalg.LinAlgError:
            return pd.Series(np.nan, index=factor.index)

        result = pd.Series(np.nan, index=factor.index)
        result.loc[data.index] = residual
        return result

    @staticmethod
    def market_neutralize(factor: pd.Series,
                           market_cap: pd.Series) -> pd.Series:
        """
        市值中性化: 仅去除市值的影响

        原理: Factor = α + β * ln(MarketCap) + ε

        参数:
            factor: 因子值序列
            market_cap: 市值序列

        返回:
            市值中性化后的因子值序列
        """
        data = pd.DataFrame({
            "factor": factor,
            "ln_cap": np.log(market_cap)
        }).dropna()

        if len(data) < 10:
            return pd.Series(np.nan, index=factor.index)

        X = np.column_stack([np.ones(len(data)), data["ln_cap"].values])
        beta = np.linalg.lstsq(X, data["factor"].values, rcond=None)[0]
        residual = data["factor"].values - X @ beta

        result = pd.Series(np.nan, index=factor.index)
        result.loc[data.index] = residual
        return result

    @staticmethod
    def industry_neutralize(factor: pd.Series,
                             industry: pd.Series) -> pd.Series:
        """
        行业中性化: 去除行业的影响

        原理: 对每个行业内的因子值做去均值处理。

        参数:
            factor: 因子值序列
            industry: 行业分类标签

        返回:
            行业中性化后的因子值序列
        """
        data = pd.DataFrame({"factor": factor, "industry": industry}).dropna()
        if len(data) < 10:
            return pd.Series(np.nan, index=factor.index)

        # 行业内去均值
        industry_mean = data.groupby("industry")["factor"].transform("mean")
        neutralized = data["factor"] - industry_mean

        result = pd.Series(np.nan, index=factor.index)
        result.loc[data.index] = neutralized
        return result

    @classmethod
    def neutralize_panel(cls, factor_panel: pd.DataFrame,
                          industry_panel: pd.DataFrame,
                          cap_panel: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        面板数据中性化: 对每一期做截面中性化

        参数:
            factor_panel: 因子面板 (index=日期, columns=股票)
            industry_panel: 行业面板 (index=日期, columns=股票)
            cap_panel: 市值面板 (可选)

        返回:
            中性化后的因子面板
        """
        result = pd.DataFrame(index=factor_panel.index,
                               columns=factor_panel.columns)

        for date in factor_panel.index:
            factor = factor_panel.loc[date]
            industry = industry_panel.loc[date]
            cap = cap_panel.loc[date] if cap_panel is not None else None
            result.loc[date] = cls.neutralize(factor, industry, cap)

        return result
