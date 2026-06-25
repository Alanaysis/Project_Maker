"""
分组回测模块

将股票按因子值分为 N 组，比较各组的收益表现。
好的因子应该呈现单调递增/递减的收益分布。
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Tuple


class GroupBacktest:
    """
    分组回测器

    将股票按因子值分组，计算各组的收益和风险指标。

    核心指标:
        - 分组收益: 各组的累计收益
        - 多空收益: 最高组 - 最低组
        - 单调性:   各组收益的单调程度
        - 夏普比率: 风险调整后的收益

    使用示例:
        >>> backtest = GroupBacktest(n_groups=5)
        >>> result = backtest.run(factor_panel, return_panel)
        >>> print(result["group_returns"])
    """

    def __init__(self, n_groups: int = 5):
        """
        初始化分组回测器

        参数:
            n_groups: 分组数量 (默认 5 组)
        """
        self.n_groups = n_groups

    def assign_groups(self, factor: pd.Series) -> pd.Series:
        """
        将股票按因子值分组

        使用分位数分组，确保每组股票数量大致相等。
        组号从 1 (最低) 到 N (最高)。

        参数:
            factor: 单期因子值序列 (index=股票代码)

        返回:
            分组标签序列 (1 到 N)
        """
        valid = factor.dropna()
        if len(valid) < self.n_groups:
            return pd.Series(np.nan, index=factor.index)

        # 分位数分组
        groups = pd.qcut(valid, q=self.n_groups, labels=False,
                          duplicates="drop") + 1
        return groups.reindex(factor.index)

    def run(self, factor_panel: pd.DataFrame,
            return_panel: pd.DataFrame,
            holding_period: int = 1) -> Dict:
        """
        执行分组回测

        参数:
            factor_panel: 因子面板 (index=日期, columns=股票)
            return_panel: 收益率面板 (index=日期, columns=股票)
            holding_period: 持仓周期 (天数)

        返回:
            包含以下字段的字典:
            - group_returns:    各组每日收益率 DataFrame
            - cumulative:       各组累计收益 DataFrame
            - long_short:       多空组合收益率序列
            - group_stats:      各组统计指标 DataFrame
            - monotonicity:     单调性指标
        """
        common_dates = factor_panel.index.intersection(return_panel.index)
        # 按持仓周期采样
        trade_dates = common_dates[::holding_period]

        group_daily_returns = {g: [] for g in range(1, self.n_groups + 1)}
        trade_date_list = []

        for date in trade_dates:
            factor_values = factor_panel.loc[date]
            groups = self.assign_groups(factor_values)

            # 计算未来 holding_period 天的累计收益
            date_idx = common_dates.get_loc(date)
            end_idx = min(date_idx + holding_period, len(common_dates))
            future_dates = common_dates[date_idx:end_idx]

            if len(future_dates) == 0:
                continue

            cum_return = return_panel.loc[future_dates].sum()
            trade_date_list.append(date)

            for g in range(1, self.n_groups + 1):
                stocks_in_group = groups[groups == g].index
                group_return = cum_return.reindex(stocks_in_group).mean()
                group_daily_returns[g].append(group_return)

        if not trade_date_list:
            return {"error": "No valid data for backtest"}

        # 构造结果 DataFrame
        group_returns = pd.DataFrame(
            group_daily_returns, index=trade_date_list
        )
        cumulative = (1 + group_returns).cumprod()

        # 多空组合
        long_short = group_returns[self.n_groups] - group_returns[1]

        # 各组统计
        group_stats = self._compute_group_stats(group_returns)

        # 单调性
        monotonicity = self._compute_monotonicity(group_stats)

        return {
            "group_returns": group_returns,
            "cumulative": cumulative,
            "long_short": long_short,
            "long_short_cumulative": (1 + long_short).cumprod(),
            "group_stats": group_stats,
            "monotonicity": monotonicity,
        }

    def _compute_group_stats(self, group_returns: pd.DataFrame) -> pd.DataFrame:
        """
        计算各组的统计指标

        参数:
            group_returns: 各组每日收益率 DataFrame

        返回:
            统计指标 DataFrame (annualized_return, volatility, sharpe, max_drawdown)
        """
        stats = {}
        for g in group_returns.columns:
            ret = group_returns[g].dropna()
            if len(ret) == 0:
                continue

            annual_factor = 252  # 假设日频
            ann_return = ret.mean() * annual_factor
            ann_vol = ret.std() * np.sqrt(annual_factor)
            sharpe = ann_return / ann_vol if ann_vol > 0 else 0

            # 最大回撤
            cum = (1 + ret).cumprod()
            peak = cum.cummax()
            drawdown = (cum - peak) / peak
            max_dd = drawdown.min()

            stats[g] = {
                "annualized_return": ann_return,
                "annualized_volatility": ann_vol,
                "sharpe_ratio": sharpe,
                "max_drawdown": max_dd,
                "win_rate": (ret > 0).mean(),
                "total_return": (1 + ret).prod() - 1,
            }

        return pd.DataFrame(stats).T

    def _compute_monotonicity(self, group_stats: pd.DataFrame) -> float:
        """
        计算分组收益的单调性

        单调性指标衡量各组收益是否单调递增/递减。
        完美单调 = 1.0 或 -1.0，完全无序 = 0

        计算: 使用 Spearman 秩相关

        参数:
            group_stats: 各组统计指标 DataFrame

        返回:
            单调性指标 (-1 到 1)
        """
        from scipy import stats

        if "annualized_return" not in group_stats.columns:
            return 0.0

        returns = group_stats["annualized_return"].values
        groups = np.arange(1, len(returns) + 1)

        if len(returns) < 3:
            return 0.0

        corr, _ = stats.spearmanr(groups, returns)
        return corr

    @staticmethod
    def quantile_return_plot_data(result: Dict) -> pd.DataFrame:
        """
        生成分组收益柱状图数据

        参数:
            result: run() 方法的返回结果

        返回:
            DataFrame，包含各组的年化收益率和夏普比率
        """
        stats = result["group_stats"]
        plot_data = pd.DataFrame({
            "组别": [f"G{i}" for i in stats.index],
            "年化收益率": stats["annualized_return"].values,
            "夏普比率": stats["sharpe_ratio"].values,
            "最大回撤": stats["max_drawdown"].values,
        })
        return plot_data
