"""
历史数据回放模块

模拟真实交易环境，按时间顺序逐期提供数据，避免未来数据泄露。
"""

import numpy as np
import pandas as pd
from typing import Optional, Generator, Tuple


class DataReplay:
    """
    历史数据回放器

    按时间顺序逐期提供数据，确保不会使用未来数据。

    使用示例:
        >>> replay = DataReplay(price_df, factor_df)
        >>> for date, prices, factors in replay.iter_daily():
        >>>     # 在此处进行因子计算和交易决策
        >>>     pass
    """

    def __init__(self, price_data: pd.DataFrame,
                 factor_data: Optional[pd.DataFrame] = None,
                 frequency: str = "daily"):
        """
        初始化数据回放器

        参数:
            price_data: 价格数据 (index=日期, columns=股票)
            factor_data: 因子数据 (可选)
            frequency: 数据频率 ("daily", "weekly", "monthly")
        """
        self.price_data = price_data.sort_index()
        self.factor_data = factor_data.sort_index() if factor_data is not None else None
        self.frequency = frequency
        self.dates = self.price_data.index.tolist()

    def iter_daily(self) -> Generator[Tuple, None, None]:
        """
        逐日迭代

        生成器，每次返回一个日期及其对应的数据。
        确保不会泄露未来数据。

        Yields:
            (date, price_series, factor_series) 元组
        """
        for date in self.dates:
            prices = self.price_data.loc[date]
            factors = None
            if self.factor_data is not None and date in self.factor_data.index:
                factors = self.factor_data.loc[date]
            yield date, prices, factors

    def get_history(self, date, window: int) -> pd.DataFrame:
        """
        获取截止到指定日期的历史数据窗口

        参数:
            date: 截止日期
            window: 历史窗口大小

        返回:
            历史价格 DataFrame
        """
        date_idx = self.dates.index(date)
        start_idx = max(0, date_idx - window + 1)
        return self.price_data.iloc[start_idx:date_idx + 1]

    def get_forward_return(self, date, horizon: int = 1) -> pd.Series:
        """
        获取未来收益率 (用于因子评估)

        注意: 此方法仅用于回测评估，实际交易中无法获取。

        参数:
            date: 当前日期
            horizon: 持仓天数

        返回:
            未来 horizon 天的累计收益率
        """
        date_idx = self.dates.index(date)
        end_idx = min(date_idx + horizon, len(self.dates) - 1)

        if end_idx <= date_idx:
            return pd.Series(dtype=float)

        current_prices = self.price_data.loc[date]
        future_prices = self.price_data.iloc[end_idx]
        return (future_prices - current_prices) / current_prices

    def get_trade_dates(self, start_date=None, end_date=None) -> list:
        """
        获取交易日列表

        参数:
            start_date: 开始日期
            end_date: 结束日期

        返回:
            交易日列表
        """
        dates = self.dates
        if start_date:
            dates = [d for d in dates if d >= start_date]
        if end_date:
            dates = [d for d in dates if d <= end_date]
        return dates

    @staticmethod
    def generate_sample_data(n_days: int = 500, n_stocks: int = 50,
                              seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        生成模拟数据用于测试

        参数:
            n_days: 交易日数
            n_stocks: 股票数量
            seed: 随机种子

        返回:
            (price_data, return_data) 元组
        """
        np.random.seed(seed)

        dates = pd.bdate_range(start="2022-01-01", periods=n_days)
        stocks = [f"STOCK_{i:04d}" for i in range(n_stocks)]

        # 生成价格数据 (几何布朗运动)
        daily_returns = np.random.normal(0.0005, 0.02, (n_days, n_stocks))
        prices = 100 * np.exp(np.cumsum(daily_returns, axis=0))

        price_df = pd.DataFrame(prices, index=dates, columns=stocks)
        return_df = price_df.pct_change()

        return price_df, return_df
