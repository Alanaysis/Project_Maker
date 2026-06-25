"""
性能分析模块

计算投资组合的各种风险收益指标，用于评估策略表现。
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict


class PerformanceAnalyzer:
    """
    性能分析器

    计算策略的各类风险收益指标。

    使用示例:
        >>> analyzer = PerformanceAnalyzer()
        >>> metrics = analyzer.compute_metrics(returns_series)
        >>> analyzer.print_report(metrics)
    """

    @staticmethod
    def compute_metrics(returns: pd.Series,
                        risk_free_rate: float = 0.03,
                        annual_factor: int = 252) -> Dict[str, float]:
        """
        计算完整的风险收益指标

        参数:
            returns: 日收益率序列
            risk_free_rate: 年化无风险利率 (默认 3%)
            annual_factor: 年化因子 (日频=252, 周频=52)

        返回:
            包含各指标的字典
        """
        returns = returns.dropna()
        if len(returns) < 2:
            return {}

        # 基本收益指标
        total_return = (1 + returns).prod() - 1
        n_years = len(returns) / annual_factor
        annual_return = (1 + total_return) ** (1 / n_years) - 1 if n_years > 0 else 0

        # 波动率
        annual_vol = returns.std() * np.sqrt(annual_factor)

        # 夏普比率
        daily_rf = (1 + risk_free_rate) ** (1 / annual_factor) - 1
        excess_returns = returns - daily_rf
        sharpe = excess_returns.mean() / returns.std() * np.sqrt(annual_factor) if returns.std() > 0 else 0

        # 最大回撤
        cumulative = (1 + returns).cumprod()
        peak = cumulative.cummax()
        drawdown = (cumulative - peak) / peak
        max_drawdown = drawdown.min()
        max_dd_end = drawdown.idxmin()
        max_dd_start = cumulative.loc[:max_dd_end].idxmax()

        # 最大回撤持续时间
        dd_duration = len(returns.loc[max_dd_start:max_dd_end]) if max_dd_start != max_dd_end else 0

        # Calmar 比率
        calmar = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # Sortino 比率
        downside_returns = returns[returns < 0]
        downside_vol = downside_returns.std() * np.sqrt(annual_factor)
        sortino = (annual_return - risk_free_rate) / downside_vol if downside_vol > 0 else 0

        # 胜率
        win_rate = (returns > 0).mean()

        # 盈亏比
        avg_win = returns[returns > 0].mean() if (returns > 0).any() else 0
        avg_loss = abs(returns[returns < 0].mean()) if (returns < 0).any() else 1e-10
        profit_loss_ratio = avg_win / avg_loss

        # 偏度和峰度
        skewness = returns.skew()
        kurtosis = returns.kurtosis()

        return {
            "total_return": total_return,
            "annual_return": annual_return,
            "annual_volatility": annual_vol,
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "calmar_ratio": calmar,
            "max_drawdown": max_drawdown,
            "max_dd_start": max_dd_start,
            "max_dd_end": max_dd_end,
            "max_dd_duration": dd_duration,
            "win_rate": win_rate,
            "profit_loss_ratio": profit_loss_ratio,
            "skewness": skewness,
            "kurtosis": kurtosis,
            "n_trading_days": len(returns),
        }

    @staticmethod
    def rolling_metrics(returns: pd.Series,
                         window: int = 60,
                         risk_free_rate: float = 0.03) -> pd.DataFrame:
        """
        滚动风险收益指标

        参数:
            returns: 日收益率序列
            window: 滚动窗口
            risk_free_rate: 年化无风险利率

        返回:
            滚动指标 DataFrame
        """
        rolling_return = returns.rolling(window).mean() * 252
        rolling_vol = returns.rolling(window).std() * np.sqrt(252)
        rolling_sharpe = rolling_return / rolling_vol

        # 滚动最大回撤
        cumulative = (1 + returns).cumprod()
        rolling_max = cumulative.rolling(window).max()
        rolling_dd = (cumulative - rolling_max) / rolling_max

        return pd.DataFrame({
            "rolling_return": rolling_return,
            "rolling_volatility": rolling_vol,
            "rolling_sharpe": rolling_sharpe,
            "rolling_drawdown": rolling_dd,
        })

    @staticmethod
    def monthly_returns_table(returns: pd.Series) -> pd.DataFrame:
        """
        月度收益率表

        生成年 x 月的收益率矩阵，便于观察收益的季节性。

        参数:
            returns: 日收益率序列

        返回:
            DataFrame，index=年份, columns=月份 (1-12), values=月度收益率
        """
        returns = returns.copy()
        returns.index = pd.to_datetime(returns.index)

        monthly = (1 + returns).resample("ME").prod() - 1
        monthly.index = monthly.index.to_period("M")

        table = monthly.groupby([monthly.index.year, monthly.index.month]).sum()
        table.index.names = ["year", "month"]
        return table.unstack(level="month")

    @staticmethod
    def print_report(metrics: Dict[str, float]):
        """
        打印性能报告

        参数:
            metrics: compute_metrics 的返回结果
        """
        print("=" * 50)
        print("策略性能报告")
        print("=" * 50)
        print(f"  总收益率:     {metrics['total_return']:.2%}")
        print(f"  年化收益率:   {metrics['annual_return']:.2%}")
        print(f"  年化波动率:   {metrics['annual_volatility']:.2%}")
        print(f"  夏普比率:     {metrics['sharpe_ratio']:.2f}")
        print(f"  Sortino 比率: {metrics['sortino_ratio']:.2f}")
        print(f"  Calmar 比率:  {metrics['calmar_ratio']:.2f}")
        print(f"  最大回撤:     {metrics['max_drawdown']:.2%}")
        print(f"  最大回撤区间: {metrics['max_dd_start']} ~ {metrics['max_dd_end']}")
        print(f"  回撤持续:     {metrics['max_dd_duration']} 天")
        print(f"  胜率:         {metrics['win_rate']:.2%}")
        print(f"  盈亏比:       {metrics['profit_loss_ratio']:.2f}")
        print(f"  偏度:         {metrics['skewness']:.4f}")
        print(f"  峰度:         {metrics['kurtosis']:.4f}")
        print(f"  交易日数:     {metrics['n_trading_days']}")
        print("=" * 50)
