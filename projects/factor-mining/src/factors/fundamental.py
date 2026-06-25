"""
基本面因子计算模块

实现基于财务数据的基本面因子，包括估值、盈利质量、成长性、
资本结构等经典基本面因子。

输入数据需包含财务报表相关字段 (PE, PB, ROE, 营收增长率等)。
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, List


class FundamentalFactors:
    """
    基本面因子计算器

    基于财务数据计算各类基本面因子。输入数据通常为截面数据:
        - pe_ttm:           市盈率 (TTM)
        - pb:               市净率
        - ps_ttm:           市销率 (TTM)
        - pcf_ttm:          市现率 (TTM)
        - roe:              净资产收益率
        - roa:              总资产收益率
        - gross_margin:     毛利率
        - net_margin:       净利率
        - revenue_growth:   营收增长率
        - profit_growth:    利润增长率
        - debt_to_equity:   资产负债率
        - current_ratio:    流动比率
        - total_market_cap: 总市值

    使用示例:
        >>> ff = FundamentalFactors()
        >>> value = ff.value_score(financial_df)
        >>> quality = ff.quality_score(financial_df)
    """

    # ========================================================================
    # 估值因子
    # ========================================================================

    @staticmethod
    def earnings_yield(df: pd.DataFrame) -> pd.Series:
        """
        盈利收益率因子: PE 的倒数

        原理: 高盈利收益率的股票相对便宜，具有均值回归潜力。
        计算: EY = 1 / PE_TTM

        参数:
            df: 包含 pe_ttm 列的 DataFrame

        返回:
            盈利收益率因子值序列
        """
        ey = 1.0 / df["pe_ttm"].replace(0, np.nan)
        return ey

    @staticmethod
    def book_to_price(df: pd.DataFrame) -> pd.Series:
        """
        账面市值比因子: PB 的倒数

        原理: 低 PB 股票可能被市场低估 (价值效应)。
        计算: BTP = 1 / PB

        参数:
            df: 包含 pb 列的 DataFrame

        返回:
            账面市值比因子值序列
        """
        return 1.0 / df["pb"].replace(0, np.nan)

    @staticmethod
    def sales_to_price(df: pd.DataFrame) -> pd.Series:
        """
        营收市值比因子: PS 的倒数

        原理: 高营收相对于市值的股票可能被低估。
        计算: STP = 1 / PS_TTM

        参数:
            df: 包含 ps_ttm 列的 DataFrame

        返回:
            营收市值比因子值序列
        """
        return 1.0 / df["ps_ttm"].replace(0, np.nan)

    @staticmethod
    def composite_value(df: pd.DataFrame) -> pd.Series:
        """
        综合估值因子: 多个估值指标的标准化均值

        原理: 单一估值指标可能有偏差，综合多个指标更稳健。
        计算: 对 EY, BTP, STP 各自标准化后取均值

        参数:
            df: 包含 pe_ttm, pb, ps_ttm 列的 DataFrame

        返回:
            综合估值因子值序列
        """
        ey = 1.0 / df["pe_ttm"].replace(0, np.nan)
        btp = 1.0 / df["pb"].replace(0, np.nan)
        stp = 1.0 / df["ps_ttm"].replace(0, np.nan)

        # Z-score 标准化
        def zscore(s):
            return (s - s.mean()) / s.std()

        return (zscore(ey) + zscore(btp) + zscore(stp)) / 3.0

    # ========================================================================
    # 盈利质量因子
    # ========================================================================

    @staticmethod
    def roe_factor(df: pd.DataFrame) -> pd.Series:
        """
        ROE 因子: 净资产收益率

        原理: 高 ROE 公司盈利能力强，长期来看能为股东创造更多价值。
        计算: 直接使用 ROE

        参数:
            df: 包含 roe 列的 DataFrame

        返回:
            ROE 因子值序列
        """
        return df["roe"]

    @staticmethod
    def roa_factor(df: pd.DataFrame) -> pd.Series:
        """
        ROA 因子: 总资产收益率

        原理: 衡量公司运用全部资产创造利润的效率。
        计算: 直接使用 ROA

        参数:
            df: 包含 roa 列的 DataFrame

        返回:
            ROA 因子值序列
        """
        return df["roa"]

    @staticmethod
    def gross_profitability(df: pd.DataFrame) -> pd.Series:
        """
        毛利率因子

        原理: 高毛利率反映公司产品定价能力和竞争优势。
        计算: 直接使用毛利率

        参数:
            df: 包含 gross_margin 列的 DataFrame

        返回:
            毛利率因子值序列
        """
        return df["gross_margin"]

    @staticmethod
    def quality_score(df: pd.DataFrame) -> pd.Series:
        """
        综合质量因子: ROE + ROA + 毛利率 的标准化均值

        原理: 综合多个盈利质量指标，构建更稳健的质量因子。

        参数:
            df: 包含 roe, roa, gross_margin 列的 DataFrame

        返回:
            综合质量因子值序列
        """
        def zscore(s):
            return (s - s.mean()) / s.std()

        return (zscore(df["roe"]) + zscore(df["roa"]) +
                zscore(df["gross_margin"])) / 3.0

    # ========================================================================
    # 成长性因子
    # ========================================================================

    @staticmethod
    def revenue_growth_factor(df: pd.DataFrame) -> pd.Series:
        """
        营收增长因子

        原理: 高营收增长的公司通常处于成长期，未来盈利增长潜力大。
        计算: 直接使用营收增长率

        参数:
            df: 包含 revenue_growth 列的 DataFrame

        返回:
            营收增长因子值序列
        """
        return df["revenue_growth"]

    @staticmethod
    def profit_growth_factor(df: pd.DataFrame) -> pd.Series:
        """
        利润增长因子

        原理: 利润增长比营收增长更能反映公司实际成长质量。
        计算: 直接使用利润增长率

        参数:
            df: 包含 profit_growth 列的 DataFrame

        返回:
            利润增长因子值序列
        """
        return df["profit_growth"]

    @staticmethod
    def growth_score(df: pd.DataFrame) -> pd.Series:
        """
        综合成长因子: 营收增长 + 利润增长 的标准化均值

        参数:
            df: 包含 revenue_growth, profit_growth 列的 DataFrame

        返回:
            综合成长因子值序列
        """
        def zscore(s):
            return (s - s.mean()) / s.std()

        return (zscore(df["revenue_growth"]) +
                zscore(df["profit_growth"])) / 2.0

    # ========================================================================
    # 杠杆/安全因子
    # ========================================================================

    @staticmethod
    def leverage_factor(df: pd.DataFrame) -> pd.Series:
        """
        杠杆因子: 资产负债率的负值

        原理: 低杠杆公司财务风险小，在经济下行时更有韧性。
        计算: LEV = -Debt_to_Equity

        参数:
            df: 包含 debt_to_equity 列的 DataFrame

        返回:
            杠杆因子值序列 (越高越好)
        """
        return -df["debt_to_equity"]

    @staticmethod
    def liquidity_factor(df: pd.DataFrame) -> pd.Series:
        """
        流动性因子: 流动比率

        原理: 高流动比率意味着公司短期偿债能力强。
        计算: 直接使用流动比率

        参数:
            df: 包含 current_ratio 列的 DataFrame

        返回:
            流动性因子值序列
        """
        return df["current_ratio"]

    # ========================================================================
    # 规模因子
    # ========================================================================

    @staticmethod
    def size_factor(df: pd.DataFrame) -> pd.Series:
        """
        规模因子: 总市值的负对数

        原理: 小市值股票长期来看有超额收益 (小盘效应)。
        计算: SIZE = -ln(MarketCap)

        参数:
            df: 包含 total_market_cap 列的 DataFrame

        返回:
            规模因子值序列 (越高代表越小)
        """
        return -np.log(df["total_market_cap"].replace(0, np.nan))

    # ========================================================================
    # 批量计算
    # ========================================================================

    @classmethod
    def compute_all(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        批量计算所有基本面因子

        参数:
            df: 包含财务数据的 DataFrame

        返回:
            包含所有基本面因子的 DataFrame
        """
        factors = pd.DataFrame(index=df.index)

        # 估值因子
        if "pe_ttm" in df.columns:
            factors["earnings_yield"] = cls.earnings_yield(df)
        if "pb" in df.columns:
            factors["book_to_price"] = cls.book_to_price(df)
        if "ps_ttm" in df.columns:
            factors["sales_to_price"] = cls.sales_to_price(df)
        if all(c in df.columns for c in ["pe_ttm", "pb", "ps_ttm"]):
            factors["composite_value"] = cls.composite_value(df)

        # 盈利质量因子
        if "roe" in df.columns:
            factors["roe"] = cls.roe_factor(df)
        if "roa" in df.columns:
            factors["roa"] = cls.roa_factor(df)
        if "gross_margin" in df.columns:
            factors["gross_profitability"] = cls.gross_profitability(df)
        if all(c in df.columns for c in ["roe", "roa", "gross_margin"]):
            factors["quality_score"] = cls.quality_score(df)

        # 成长性因子
        if "revenue_growth" in df.columns:
            factors["revenue_growth"] = cls.revenue_growth_factor(df)
        if "profit_growth" in df.columns:
            factors["profit_growth"] = cls.profit_growth_factor(df)
        if all(c in df.columns for c in ["revenue_growth", "profit_growth"]):
            factors["growth_score"] = cls.growth_score(df)

        # 杠杆/安全因子
        if "debt_to_equity" in df.columns:
            factors["leverage"] = cls.leverage_factor(df)
        if "current_ratio" in df.columns:
            factors["liquidity"] = cls.liquidity_factor(df)

        # 规模因子
        if "total_market_cap" in df.columns:
            factors["size"] = cls.size_factor(df)

        return factors
