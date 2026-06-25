"""
另类因子计算模块

实现基于非传统数据源的另类因子，包括资金流向、大单行为、
涨停效应、市场情绪等行为金融因子。

这些因子利用市场微观结构信息，捕捉传统量价因子无法覆盖的 alpha。
"""

import numpy as np
import pandas as pd
from typing import Optional


class AlternativeFactors:
    """
    另类因子计算器

    基于市场微观结构和行为金融数据计算另类因子。

    使用示例:
        >>> af = AlternativeFactors()
        >>> smart_money = af.smart_money_flow(df)
        >>> sentiment = af.market_sentiment(df)
    """

    # ========================================================================
    # 资金流向因子
    # ========================================================================

    @staticmethod
    def smart_money_flow(close: pd.Series, volume: pd.Series,
                          window: int = 20) -> pd.Series:
        """
        聪明资金流向因子: 大单净流入占总成交额比例

        原理: 机构投资者通常在尾盘交易，尾盘成交量占比高可能
              意味着机构资金流入。
        计算: 用成交量加权价格 (VWAP) 与收盘价的偏离度代理。

        参数:
            close: 收盘价序列
            volume: 成交量序列
            window: 计算窗口

        返回:
            聪明资金流向因子值序列
        """
        # 用收益率的符号乘以成交量衡量资金方向
        returns = close.pct_change()
        signed_volume = returns.apply(np.sign) * volume
        # 累积净流入
        net_flow = signed_volume.rolling(window=window).sum()
        total_volume = volume.rolling(window=window).sum()
        return net_flow / total_volume.replace(0, np.nan)

    @staticmethod
    def volume_ratio_factor(volume: pd.Series, window: int = 5) -> pd.Series:
        """
        量比因子: 短期成交量与长期成交量的比值

        原理: 量比突然放大通常伴随着重要信息的到来。
        计算: VR = mean(Volume, short) / mean(Volume, long)

        参数:
            volume: 成交量序列
            window: 短期窗口

        返回:
            量比因子值序列
        """
        short_avg = volume.rolling(window=window).mean()
        long_avg = volume.rolling(window=window * 4).mean()
        return short_avg / long_avg.replace(0, np.nan)

    # ========================================================================
    # 市场微观结构因子
    # ========================================================================

    @staticmethod
    def bid_ask_imbalance(bid_volume: pd.Series, ask_volume: pd.Series,
                           window: int = 20) -> pd.Series:
        """
        买卖盘不平衡因子

        原理: 买盘力量强于卖盘时，价格有上涨动力。
        计算: BAI = (BidVol - AskVol) / (BidVol + AskVol)

        参数:
            bid_volume: 买盘成交量序列
            ask_volume: 卖盘成交量序列
            window: 计算窗口

        返回:
            买卖盘不平衡因子值序列 (-1 到 1)
        """
        total = bid_volume + ask_volume
        imbalance = (bid_volume - ask_volume) / total.replace(0, np.nan)
        return imbalance.rolling(window=window).mean()

    @staticmethod
    def effective_spread(close: pd.Series, vwap: pd.Series,
                          window: int = 20) -> pd.Series:
        """
        有效价差因子: 衡量交易执行成本

        原理: 有效价差反映真实交易成本，低有效价差的股票流动性更好。
        计算: ES = 2 * |P - VWAP| / VWAP

        参数:
            close: 收盘价序列
            vwap: 成交量加权均价序列
            window: 计算窗口

        返回:
            有效价差因子值序列
        """
        spread = 2 * (close - vwap).abs() / vwap.replace(0, np.nan)
        return spread.rolling(window=window).mean()

    # ========================================================================
    # 行为金融因子
    # ========================================================================

    @staticmethod
    def reversal_factor(close: pd.Series, window: int = 5) -> pd.Series:
        """
        短期反转因子: 近期收益率的负值

        原理: 短期内涨幅过大的股票倾向于回调 (过度反应)。
        计算: REV = -R_n

        参数:
            close: 收盘价序列
            window: 回看窗口

        返回:
            短期反转因子值序列
        """
        return -close.pct_change(periods=window)

    @staticmethod
    def max_return_factor(close: pd.Series, window: int = 20) -> pd.Series:
        """
        最大日收益因子: 过去 N 日最大单日收益

        原理: 彩票效应 - 包含极端正收益的股票往往被高估。
        计算: MAX = max(r_daily, n)

        参数:
            close: 收盘价序列
            window: 回看窗口

        返回:
            最大日收益因子值序列
        """
        daily_returns = close.pct_change()
        return daily_returns.rolling(window=window).max()

    @staticmethod
    def skewness_factor(close: pd.Series, window: int = 20) -> pd.Series:
        """
        偏度因子: 收益率分布的偏度

        原理: 正偏度股票被高估 (投资者偏好正偏度)，负偏度股票被低估。
        计算: skew(r, n)

        参数:
            close: 收盘价序列
            window: 回看窗口

        返回:
            偏度因子值序列
        """
        returns = close.pct_change()
        return returns.rolling(window=window).skew()

    @staticmethod
    def kurtosis_factor(close: pd.Series, window: int = 20) -> pd.Series:
        """
        峰度因子: 收益率分布的峰度

        原理: 高峰度意味着极端事件频率高，反映尾部风险。
        计算: kurt(r, n)

        参数:
            close: 收盘价序列
            window: 回看窗口

        返回:
            峰度因子值序列
        """
        returns = close.pct_change()
        return returns.rolling(window=window).kurt()

    # ========================================================================
    # 涨跌停因子
    # ========================================================================

    @staticmethod
    def limit_up_ratio(close: pd.Series, limit_pct: float = 0.10,
                        window: int = 20) -> pd.Series:
        """
        涨停比例因子: 过去 N 日触及涨停的天数占比

        原理: 频繁涨停的股票可能受到游资炒作，后续风险较大。
        计算: LUR = count(r >= limit) / n

        参数:
            close: 收盘价序列
            limit_pct: 涨停幅度 (默认 10%)
            window: 回看窗口

        返回:
            涨停比例因子值序列 (0~1)
        """
        returns = close.pct_change()
        is_limit = (returns >= limit_pct - 0.005).astype(float)
        return is_limit.rolling(window=window).mean()

    # ========================================================================
    # 情绪因子
    # ========================================================================

    @staticmethod
    def market_sentiment(volume: pd.Series, close: pd.Series,
                          window: int = 20) -> pd.Series:
        """
        市场情绪因子: 成交量变化与价格变化的综合度量

        原理: 量价齐升反映乐观情绪，量价背离反映悲观情绪。
        计算: 将成交量变化和价格变化标准化后相加。

        参数:
            volume: 成交量序列
            close: 收盘价序列
            window: 计算窗口

        返回:
            市场情绪因子值序列
        """
        vol_change = volume.pct_change()
        price_change = close.pct_change()

        # 标准化
        vol_z = (vol_change - vol_change.rolling(window).mean()) / \
                vol_change.rolling(window).std().replace(0, np.nan)
        price_z = (price_change - price_change.rolling(window).mean()) / \
                  price_change.rolling(window).std().replace(0, np.nan)

        return (vol_z + price_z) / 2.0

    @staticmethod
    def turnover_anomaly(volume: pd.Series, shares_outstanding: float,
                          window: int = 20) -> pd.Series:
        """
        换手率异常因子: 当前换手率相对于历史的偏离程度

        原理: 换手率突然放大可能意味着重大信息或异常交易行为。
        计算: TAnom = (TR_current - TR_mean) / TR_std

        参数:
            volume: 成交量序列
            shares_outstanding: 流通股本
            window: 计算窗口

        返回:
            换手率异常因子值序列
        """
        tr = volume / shares_outstanding
        tr_mean = tr.rolling(window=window).mean()
        tr_std = tr.rolling(window=window).std()
        return (tr - tr_mean) / tr_std.replace(0, np.nan)

    # ========================================================================
    # 批量计算
    # ========================================================================

    @classmethod
    def compute_all(cls, df: pd.DataFrame,
                    shares_outstanding: Optional[float] = None) -> pd.DataFrame:
        """
        批量计算所有另类因子

        参数:
            df: 包含量价数据的 DataFrame
            shares_outstanding: 流通股本 (可选)

        返回:
            包含所有另类因子的 DataFrame
        """
        factors = pd.DataFrame(index=df.index)

        if "close" in df.columns and "volume" in df.columns:
            factors["smart_money_flow"] = cls.smart_money_flow(
                df["close"], df["volume"])
            factors["volume_ratio"] = cls.volume_ratio_factor(df["volume"])
            factors["market_sentiment"] = cls.market_sentiment(
                df["volume"], df["close"])

        if "close" in df.columns:
            for w in [5, 20]:
                factors[f"reversal_{w}d"] = cls.reversal_factor(df["close"], window=w)
            factors["max_return_20d"] = cls.max_return_factor(df["close"])
            factors["skewness_20d"] = cls.skewness_factor(df["close"])
            factors["kurtosis_20d"] = cls.kurtosis_factor(df["close"])
            factors["limit_up_ratio_20d"] = cls.limit_up_ratio(df["close"])

        if shares_outstanding and "volume" in df.columns:
            factors["turnover_anomaly"] = cls.turnover_anomaly(
                df["volume"], shares_outstanding)

        return factors
