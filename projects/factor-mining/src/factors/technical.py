"""
技术因子计算模块

实现基于量价数据的技术类因子，包括动量、波动率、流动性、
换手率等经典技术因子，以及它们的衍生变体。

所有因子函数接收 DataFrame 格式的行情数据，返回因子值序列。
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, List


class TechnicalFactors:
    """
    技术因子计算器

    基于日频量价数据计算各类技术因子。输入数据需包含以下列:
        - open:   开盘价
        - high:   最高价
        - low:    最低价
        - close:  收盘价
        - volume: 成交量
        - amount: 成交额 (可选)

    使用示例:
        >>> tf = TechnicalFactors()
        >>> momentum = tf.momentum(close_series, window=20)
        >>> volatility = tf.realized_volatility(close_series, window=20)
    """

    # ========================================================================
    # 动量因子
    # ========================================================================

    @staticmethod
    def momentum(close: pd.Series, window: int = 20) -> pd.Series:
        """
        动量因子: 过去 N 日收益率

        原理: 价格趋势具有短期持续性，过去涨得好的股票未来可能继续上涨。
        计算: R_t = (P_t - P_{t-n}) / P_{t-n}

        参数:
            close: 收盘价序列
            window: 回看窗口 (交易日数)

        返回:
            动量因子值序列
        """
        return close.pct_change(periods=window)

    @staticmethod
    def momentum_acceleration(close: pd.Series, short_window: int = 5,
                               long_window: int = 20) -> pd.Series:
        """
        动量加速度因子: 短期动量与长期动量之差

        原理: 动量的加速变化比动量本身更能预测未来收益。
        计算: MA = MOM_short - MOM_long

        参数:
            close: 收盘价序列
            short_window: 短期窗口
            long_window: 长期窗口

        返回:
            动量加速度因子值序列
        """
        short_mom = close.pct_change(periods=short_window)
        long_mom = close.pct_change(periods=long_window)
        return short_mom - long_mom

    @staticmethod
    def price_position(close: pd.Series, window: int = 20) -> pd.Series:
        """
        价格位置因子: 当前价格在近 N 日最高最低价区间中的位置

        原理: 衡量价格在近期波动区间中的相对位置。
        计算: PP = (P - LOW_n) / (HIGH_n - LOW_n)

        参数:
            close: 收盘价序列
            window: 回看窗口

        返回:
            价格位置因子值序列 (0~1 之间)
        """
        rolling_high = close.rolling(window=window).max()
        rolling_low = close.rolling(window=window).min()
        price_range = rolling_high - rolling_low
        # 避免除以零
        price_range = price_range.replace(0, np.nan)
        return (close - rolling_low) / price_range

    # ========================================================================
    # 波动率因子
    # ========================================================================

    @staticmethod
    def realized_volatility(close: pd.Series, window: int = 20) -> pd.Series:
        """
        已实现波动率因子: 过去 N 日对数收益率的标准差

        原理: 低波动率股票往往有更高的风险调整收益 (低波动异象)。
        计算: σ = std(ln(P_t / P_{t-1}), n)

        参数:
            close: 收盘价序列
            window: 回看窗口

        返回:
            已实现波动率因子值序列
        """
        log_returns = np.log(close / close.shift(1))
        return log_returns.rolling(window=window).std()

    @staticmethod
    def intraday_volatility(high: pd.Series, low: pd.Series,
                             close: pd.Series, window: int = 20) -> pd.Series:
        """
        日内波动率因子: 基于 Parkinson 公式的日内波动估计

        原理: 利用日内最高最低价估计波动率，比收盘价波动率更高效。
        计算: σ_park = sqrt(1/(4n*ln2) * Σ(ln(H/L))^2)

        参数:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            window: 回看窗口

        返回:
            日内波动率因子值序列
        """
        log_hl = np.log(high / low)
        parkinson = (log_hl ** 2) / (4 * np.log(2))
        return np.sqrt(parkinson.rolling(window=window).mean())

    @staticmethod
    def downside_volatility(close: pd.Series, window: int = 20) -> pd.Series:
        """
        下行波动率因子: 仅计算负收益部分的波动率

        原理: 投资者更关注下行风险，下行波动率更能反映尾部风险。
        计算: σ_down = std(min(r, 0), n)

        参数:
            close: 收盘价序列
            window: 回看窗口

        返回:
            下行波动率因子值序列
        """
        returns = close.pct_change()
        negative_returns = returns.where(returns < 0, 0)
        return negative_returns.rolling(window=window).std()

    # ========================================================================
    # 流动性因子
    # ========================================================================

    @staticmethod
    def turnover_rate(volume: pd.Series, shares_outstanding: float,
                      window: int = 20) -> pd.Series:
        """
        换手率因子: 过去 N 日平均换手率

        原理: 高换手率往往伴随过度交易，低换手率股票可能有更高收益。
        计算: TR = mean(Volume / SharesOutstanding, n)

        参数:
            volume: 成交量序列
            shares_outstanding: 流通股本
            window: 回看窗口

        返回:
            换手率因子值序列
        """
        daily_turnover = volume / shares_outstanding
        return daily_turnover.rolling(window=window).mean()

    @staticmethod
    def amihud_illiquidity(close: pd.Series, volume: pd.Series,
                            window: int = 20) -> pd.Series:
        """
        Amihud 非流动性因子: 收益率绝对值与成交额的比值

        原理: 衡量单位成交额引起的价格变动，反映市场冲击成本。
        计算: ILLIQ = mean(|r| / Volume, n)

        参数:
            close: 收盘价序列
            volume: 成交量序列 (或成交额序列)
            window: 回看窗口

        返回:
            Amihud 非流动性因子值序列
        """
        returns = close.pct_change().abs()
        # 避免除以零
        volume_safe = volume.replace(0, np.nan)
        illiq = returns / volume_safe
        return illiq.rolling(window=window).mean()

    @staticmethod
    def volume_price_correlation(close: pd.Series, volume: pd.Series,
                                  window: int = 20) -> pd.Series:
        """
        量价相关性因子: 收益率与成交量变化的相关系数

        原理: 量价齐升通常表示趋势健康，量价背离可能预示反转。
        计算: ρ = corr(r, ΔV, n)

        参数:
            close: 收盘价序列
            volume: 成交量序列
            window: 回看窗口

        返回:
            量价相关性因子值序列
        """
        returns = close.pct_change()
        volume_change = volume.pct_change()
        return returns.rolling(window=window).corr(volume_change)

    # ========================================================================
    # 技术指标因子
    # ========================================================================

    @staticmethod
    def rsi(close: pd.Series, window: int = 14) -> pd.Series:
        """
        RSI (相对强弱指标) 因子

        原理: 衡量价格变动的速度和幅度，识别超买超卖状态。
        计算: RSI = 100 - 100/(1 + RS), RS = avg_gain / avg_loss

        参数:
            close: 收盘价序列
            window: 计算窗口

        返回:
            RSI 因子值序列 (0~100)
        """
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        return 100 - 100 / (1 + rs)

    @staticmethod
    def macd(close: pd.Series, fast: int = 12, slow: int = 26,
             signal: int = 9) -> pd.DataFrame:
        """
        MACD 因子: 移动平均收敛/发散指标

        原理: 通过快慢均线的差值及其信号线捕捉趋势变化。
        计算:
            DIF = EMA(close, fast) - EMA(close, slow)
            DEA = EMA(DIF, signal)
            MACD = 2 * (DIF - DEA)

        参数:
            close: 收盘价序列
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期

        返回:
            包含 DIF, DEA, MACD 三列的 DataFrame
        """
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=signal, adjust=False).mean()
        macd_hist = 2 * (dif - dea)
        return pd.DataFrame({"DIF": dif, "DEA": dea, "MACD": macd_hist},
                            index=close.index)

    @staticmethod
    def bollinger_band_width(close: pd.Series, window: int = 20,
                              num_std: float = 2.0) -> pd.Series:
        """
        布林带宽度因子: 布林带上轨与下轨的相对距离

        原理: 布林带收窄通常预示着即将到来的大幅波动。
        计算: BBW = (Upper - Lower) / Middle

        参数:
            close: 收盘价序列
            window: 计算窗口
            num_std: 标准差倍数

        返回:
            布林带宽度因子值序列
        """
        middle = close.rolling(window=window).mean()
        std = close.rolling(window=window).std()
        upper = middle + num_std * std
        lower = middle - num_std * std
        return (upper - lower) / middle.replace(0, np.nan)

    # ========================================================================
    # 批量计算
    # ========================================================================

    @classmethod
    def compute_all(cls, df: pd.DataFrame,
                    windows: Optional[List[int]] = None) -> pd.DataFrame:
        """
        批量计算所有技术因子

        参数:
            df: 包含 OHLCV 列的 DataFrame
            windows: 回看窗口列表，默认 [5, 10, 20, 60]

        返回:
            包含所有技术因子的 DataFrame
        """
        if windows is None:
            windows = [5, 10, 20, 60]

        factors = pd.DataFrame(index=df.index)

        for w in windows:
            # 动量因子
            factors[f"momentum_{w}d"] = cls.momentum(df["close"], window=w)
            factors[f"price_position_{w}d"] = cls.price_position(df["close"], window=w)

            # 波动率因子
            factors[f"volatility_{w}d"] = cls.realized_volatility(df["close"], window=w)
            factors[f"downside_vol_{w}d"] = cls.downside_volatility(df["close"], window=w)

            # 流动性因子
            if "volume" in df.columns:
                factors[f"amihud_{w}d"] = cls.amihud_illiquidity(
                    df["close"], df["volume"], window=w)
                factors[f"vp_corr_{w}d"] = cls.volume_price_correlation(
                    df["close"], df["volume"], window=w)

            if all(col in df.columns for col in ["high", "low"]):
                factors[f"intraday_vol_{w}d"] = cls.intraday_volatility(
                    df["high"], df["low"], df["close"], window=w)

        # 技术指标
        factors["rsi_14"] = cls.rsi(df["close"], window=14)
        macd_df = cls.macd(df["close"])
        factors["macd_dif"] = macd_df["DIF"]
        factors["macd_dea"] = macd_df["DEA"]
        factors["bbw_20"] = cls.bollinger_band_width(df["close"], window=20)

        # 动量加速度
        factors["mom_accel_5_20"] = cls.momentum_acceleration(
            df["close"], short_window=5, long_window=20)

        return factors
