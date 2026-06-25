"""
组合回测模块

基于因子构建投资组合并进行历史回测，评估实际投资表现。
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, List


class PortfolioBacktest:
    """
    组合回测器

    基于因子值构建投资组合，模拟实际交易过程。

    使用示例:
        >>> backtest = PortfolioBacktest(top_n=50, rebalance_freq=20)
        >>> result = backtest.run(factor_panel, return_panel)
    """

    def __init__(self, top_n: int = 50, rebalance_freq: int = 20,
                 transaction_cost: float = 0.001):
        """
        初始化组合回测器

        参数:
            top_n: 每期选取的股票数量
            rebalance_freq: 调仓频率 (天)
            transaction_cost: 单边交易成本 (默认 0.1%)
        """
        self.top_n = top_n
        self.rebalance_freq = rebalance_freq
        self.transaction_cost = transaction_cost

    def run(self, factor_panel: pd.DataFrame,
            return_panel: pd.DataFrame) -> Dict:
        """
        执行组合回测

        每个调仓日，选择因子值最高的 top_n 只股票等权持有。

        参数:
            factor_panel: 因子面板
            return_panel: 日收益率面板

        返回:
            包含回测结果的字典
        """
        common_dates = factor_panel.index.intersection(return_panel.index)

        portfolio_returns = []
        benchmark_returns = []
        holdings_history = []
        turnover_history = []

        prev_holdings = set()

        for i, date in enumerate(common_dates):
            if i % self.rebalance_freq == 0:
                # 调仓日: 选择因子值最高的 top_n 只股票
                factor_values = factor_panel.loc[date].dropna()
                if len(factor_values) < self.top_n:
                    top_stocks = factor_values.nlargest(len(factor_values)).index
                else:
                    top_stocks = factor_values.nlargest(self.top_n).index

                # 计算换手率
                current_holdings = set(top_stocks)
                if prev_holdings:
                    turnover = len(current_holdings.symmetric_difference(prev_holdings)) / \
                               (2 * max(len(current_holdings), 1))
                    turnover_history.append({"date": date, "turnover": turnover})

                prev_holdings = current_holdings
                holdings_history.append({"date": date, "stocks": list(top_stocks)})

            # 计算当日组合收益 (等权)
            daily_returns = return_panel.loc[date]
            portfolio_ret = daily_returns.reindex(list(prev_holdings)).mean()
            benchmark_ret = daily_returns.mean()  # 全市场等权作为基准

            # 扣除交易成本 (仅在调仓日)
            if i % self.rebalance_freq == 0 and turnover_history:
                cost = turnover_history[-1]["turnover"] * self.transaction_cost * 2
                portfolio_ret -= cost

            portfolio_returns.append({"date": date, "return": portfolio_ret})
            benchmark_returns.append({"date": date, "return": benchmark_ret})

        # 构造结果
        port_df = pd.DataFrame(portfolio_returns).set_index("date")
        bench_df = pd.DataFrame(benchmark_returns).set_index("date")

        # 超额收益
        excess = port_df["return"] - bench_df["return"]

        return {
            "portfolio_returns": port_df["return"],
            "benchmark_returns": bench_df["return"],
            "excess_returns": excess,
            "portfolio_cumulative": (1 + port_df["return"]).cumprod(),
            "benchmark_cumulative": (1 + bench_df["return"]).cumprod(),
            "excess_cumulative": (1 + excess).cumprod(),
            "holdings_history": holdings_history,
            "turnover_history": pd.DataFrame(turnover_history),
        }

    @staticmethod
    def long_short_backtest(factor_panel: pd.DataFrame,
                             return_panel: pd.DataFrame,
                             top_n: int = 50,
                             rebalance_freq: int = 20) -> Dict:
        """
        多空组合回测: 做多因子值最高的股票，做空最低的股票

        参数:
            factor_panel: 因子面板
            return_panel: 日收益率面板
            top_n: 每边选取的股票数量
            rebalance_freq: 调仓频率

        返回:
            回测结果字典
        """
        common_dates = factor_panel.index.intersection(return_panel.index)

        long_returns = []
        short_returns = []
        ls_returns = []

        for i, date in enumerate(common_dates):
            if i % rebalance_freq == 0:
                factor_values = factor_panel.loc[date].dropna()
                if len(factor_values) < 2 * top_n:
                    n = len(factor_values) // 2
                else:
                    n = top_n

                long_stocks = factor_values.nlargest(n).index
                short_stocks = factor_values.nsmallest(n).index

            daily_returns = return_panel.loc[date]
            long_ret = daily_returns.reindex(list(long_stocks)).mean()
            short_ret = daily_returns.reindex(list(short_stocks)).mean()
            ls_ret = long_ret - short_ret

            long_returns.append(long_ret)
            short_returns.append(short_ret)
            ls_returns.append(ls_ret)

        return {
            "long_returns": pd.Series(long_returns, index=common_dates),
            "short_returns": pd.Series(short_returns, index=common_dates),
            "long_short_returns": pd.Series(ls_returns, index=common_dates),
            "long_cumulative": (1 + pd.Series(long_returns, index=common_dates)).cumprod(),
            "short_cumulative": (1 + pd.Series(short_returns, index=common_dates)).cumprod(),
            "long_short_cumulative": (1 + pd.Series(ls_returns, index=common_dates)).cumprod(),
        }
