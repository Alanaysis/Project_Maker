"""常用因子计算模块

实现经典的 Alpha 因子，包括动量、反转、波动率、流动性等类别。
"""

import numpy as np
import pandas as pd
from typing import Optional


class FactorCalculator:
    """因子计算器，提供常用量化因子的计算方法"""

    def __init__(self, price: pd.DataFrame, volume: pd.DataFrame,
                 returns: Optional[pd.DataFrame] = None,
                 high: Optional[pd.DataFrame] = None,
                 low: Optional[pd.DataFrame] = None):
        """
        Args:
            price: 收盘价 DataFrame, index=日期, columns=股票代码
            volume: 成交量 DataFrame, 同上结构
            returns: 日收益率 DataFrame, 若为 None 则自动计算
            high: 最高价 DataFrame (可选)
            low: 最低价 DataFrame (可选)
        """
        self.price = price
        self.volume = volume
        self.high = high if high is not None else price
        self.low = low if low is not None else price
        if returns is None:
            self.returns = price.pct_change()
        else:
            self.returns = returns

    # ==================== 动量因子 ====================

    def momentum(self, window: int = 20) -> pd.DataFrame:
        """动量因子: 过去 window 日的累计收益率

        MOM_t = Price_t / Price_{t-window} - 1
        """
        return self.price / self.price.shift(window) - 1

    def short_term_reversal(self, window: int = 5) -> pd.DataFrame:
        """短期反转因子: 过去 window 日收益率的负值

        STR_t = - (Price_t / Price_{t-window} - 1)
        """
        return -(self.price / self.price.shift(window) - 1)

    def weighted_momentum(self, window: int = 20) -> pd.DataFrame:
        """加权动量因子: 近期权重更大的动量

        权重线性递增，最近一天权重最大
        """
        weights = np.arange(1, window + 1, dtype=float)
        weights /= weights.sum()

        def _apply(series):
            if series.isna().sum() > len(series) - window:
                return np.nan
            recent = series.iloc[-window:]
            if recent.isna().any():
                return np.nan
            return (recent * weights).sum()

        return self.returns.rolling(window=window).apply(_apply, raw=False)

    # ==================== 波动率因子 ====================

    def volatility(self, window: int = 20) -> pd.DataFrame:
        """波动率因子: 过去 window 日收益率的标准差

        VOL_t = Std(Ret, window)
        """
        return self.returns.rolling(window=window).std()

    def downside_volatility(self, window: int = 20) -> pd.DataFrame:
        """下行波动率: 仅对窗口内负收益计算标准差

        若窗口内负收益不足2个, 返回 NaN。
        """
        def _downside_std(series):
            neg = series[series < 0]
            if len(neg) < 2:
                return np.nan
            return neg.std()

        return self.returns.rolling(window=window).apply(_downside_std, raw=False)

    def atr(self, window: int = 14) -> pd.DataFrame:
        """Average True Range (ATR)

        TR = max(High-Low, |High-PrevClose|, |Low-PrevClose|)
        ATR = MA(TR, window)
        """
        prev_close = self.price.shift(1)
        tr1 = self.high - self.low
        tr2 = (self.high - prev_close).abs()
        tr3 = (self.low - prev_close).abs()
        true_range = pd.DataFrame(
            np.maximum(np.maximum(tr1.values, tr2.values), tr3.values),
            index=self.price.index, columns=self.price.columns
        )
        return true_range.rolling(window=window).mean()

    # ==================== 流动性因子 ====================

    def turnover_rate(self, shares_outstanding: pd.Series,
                      window: int = 20) -> pd.DataFrame:
        """换手率因子: 成交量 / 流通股本 的均值"""
        turnover = self.volume.div(shares_outstanding, axis=1)
        return turnover.rolling(window=window).mean()

    def amihud_illiquidity(self, window: int = 20) -> pd.DataFrame:
        """Amihud 非流动性因子

        ILLIQ = Mean(|Ret| / Volume, window)
        """
        illiq = self.returns.abs() / (self.volume + 1e-10)
        return illiq.rolling(window=window).mean()

    def volume_momentum(self, window: int = 20) -> pd.DataFrame:
        """成交量动量: 当前成交量相对历史均值的比值

        VMOM = Volume / MA(Volume, window)
        """
        ma_vol = self.volume.rolling(window=window).mean()
        return self.volume / (ma_vol + 1e-10)

    # ==================== 技术因子 ====================

    def rsi(self, window: int = 14) -> pd.DataFrame:
        """RSI 相对强弱指标

        RSI = 100 - 100 / (1 + AvgGain / AvgLoss)
        """
        delta = self.price.diff()
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)
        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        return 100 - 100 / (1 + rs)

    def bollinger_width(self, window: int = 20,
                        num_std: float = 2.0) -> pd.DataFrame:
        """布林带宽度: 波动率的标准化度量

        BW = (Upper - Lower) / Middle
        """
        ma = self.price.rolling(window=window).mean()
        std = self.price.rolling(window=window).std()
        upper = ma + num_std * std
        lower = ma - num_std * std
        return (upper - lower) / (ma + 1e-10)

    def price_to_ma(self, window: int = 20) -> pd.DataFrame:
        """价格/均线比: 偏离均线程度

        PMA = Price / MA(Price, window)
        """
        ma = self.price.rolling(window=window).mean()
        return self.price / (ma + 1e-10)

    # ==================== 价值因子（基于价格） ====================

    def high_low_ratio(self, window: int = 20) -> pd.DataFrame:
        """最高最低价比值: 反映价格区间

        HLR = MA(High, window) / MA(Low, window)
        """
        ma_high = self.high.rolling(window=window).mean()
        ma_low = self.low.rolling(window=window).mean()
        return ma_high / (ma_low + 1e-10)

    # ==================== 组合因子 ====================

    def composite_score(self, factors: dict, weights: Optional[dict] = None) -> pd.DataFrame:
        """组合因子评分: 将多个因子标准化后加权组合

        Args:
            factors: {名称: DataFrame} 因子字典
            weights: {名称: float} 权重字典, 若为 None 则等权
        """
        if weights is None:
            weights = {k: 1.0 / len(factors) for k in factors}

        normalized = {}
        for name, factor_df in factors.items():
            # 截面标准化 (z-score)
            mean = factor_df.mean(axis=1)
            std = factor_df.std(axis=1)
            normalized[name] = factor_df.sub(mean, axis=0).div(std + 1e-10, axis=0)

        composite = sum(normalized[name] * weights.get(name, 0)
                        for name in factors)
        return composite
