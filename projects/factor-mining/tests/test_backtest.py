"""
回测系统模块测试
"""

import numpy as np
import pandas as pd
import pytest

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.backtest.data_replay import DataReplay
from src.backtest.portfolio_backtest import PortfolioBacktest
from src.backtest.performance import PerformanceAnalyzer


@pytest.fixture
def sample_data():
    """生成测试用数据"""
    np.random.seed(42)
    n_days = 200
    n_stocks = 30
    dates = pd.bdate_range(start="2023-01-01", periods=n_days)
    stocks = [f"S{i:03d}" for i in range(n_stocks)]

    daily_returns = np.random.normal(0.0005, 0.02, (n_days, n_stocks))
    prices = 100 * np.exp(np.cumsum(daily_returns, axis=0))

    price_df = pd.DataFrame(prices, index=dates, columns=stocks)
    return_df = price_df.pct_change()

    # 因子面板
    factor_values = np.random.randn(n_days, n_stocks)
    factor_panel = pd.DataFrame(factor_values, index=dates, columns=stocks)

    return price_df, return_df, factor_panel


class TestDataReplay:
    """数据回放测试"""

    def test_iter_daily(self, sample_data):
        """测试逐日迭代"""
        price_df, _, _ = sample_data
        replay = DataReplay(price_df)

        count = 0
        for date, prices, factors in replay.iter_daily():
            assert isinstance(date, pd.Timestamp)
            assert len(prices) == len(price_df.columns)
            count += 1

        assert count == len(price_df)

    def test_get_history(self, sample_data):
        """测试历史数据获取"""
        price_df, _, _ = sample_data
        replay = DataReplay(price_df)

        date = price_df.index[50]
        history = replay.get_history(date, window=20)
        assert len(history) == 20

    def test_get_forward_return(self, sample_data):
        """测试未来收益获取"""
        price_df, _, _ = sample_data
        replay = DataReplay(price_df)

        date = price_df.index[100]
        forward = replay.get_forward_return(date, horizon=5)
        assert len(forward) == len(price_df.columns)

    def test_generate_sample_data(self):
        """测试样本数据生成"""
        prices, returns = DataReplay.generate_sample_data(n_days=100, n_stocks=20)
        assert prices.shape == (100, 20)
        assert returns.shape == (100, 20)


class TestPortfolioBacktest:
    """组合回测测试"""

    def test_run(self, sample_data):
        """测试组合回测执行"""
        _, return_df, factor_panel = sample_data
        bt = PortfolioBacktest(top_n=10, rebalance_freq=20)
        result = bt.run(factor_panel, return_df)

        assert "portfolio_returns" in result
        assert "benchmark_returns" in result
        assert "excess_returns" in result
        assert "portfolio_cumulative" in result

    def test_long_short_backtest(self, sample_data):
        """测试多空组合回测"""
        _, return_df, factor_panel = sample_data
        result = PortfolioBacktest.long_short_backtest(
            factor_panel, return_df, top_n=10, rebalance_freq=20
        )

        assert "long_returns" in result
        assert "short_returns" in result
        assert "long_short_returns" in result

    def test_transaction_cost(self, sample_data):
        """测试交易成本扣除"""
        _, return_df, factor_panel = sample_data
        bt_no_cost = PortfolioBacktest(top_n=10, rebalance_freq=20, transaction_cost=0)
        bt_with_cost = PortfolioBacktest(top_n=10, rebalance_freq=20, transaction_cost=0.01)

        result_no = bt_no_cost.run(factor_panel, return_df)
        result_with = bt_with_cost.run(factor_panel, return_df)

        # 有交易成本的总收益应该更低
        total_no = result_no["portfolio_returns"].sum()
        total_with = result_with["portfolio_returns"].sum()
        assert total_with <= total_no


class TestPerformanceAnalyzer:
    """性能分析测试"""

    def test_compute_metrics(self):
        """测试性能指标计算"""
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.001, 0.02, 252),
                            index=pd.bdate_range("2023-01-01", periods=252))

        metrics = PerformanceAnalyzer.compute_metrics(returns)

        assert "total_return" in metrics
        assert "annual_return" in metrics
        assert "annual_volatility" in metrics
        assert "sharpe_ratio" in metrics
        assert "max_drawdown" in metrics
        assert "win_rate" in metrics
        assert metrics["max_drawdown"] <= 0
        assert 0 <= metrics["win_rate"] <= 1

    def test_rolling_metrics(self):
        """测试滚动指标"""
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.001, 0.02, 252),
                            index=pd.bdate_range("2023-01-01", periods=252))

        rolling = PerformanceAnalyzer.rolling_metrics(returns, window=60)
        assert "rolling_return" in rolling.columns
        assert "rolling_sharpe" in rolling.columns

    def test_monthly_returns_table(self):
        """测试月度收益表"""
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.001, 0.02, 252),
                            index=pd.bdate_range("2023-01-01", periods=252))

        table = PerformanceAnalyzer.monthly_returns_table(returns)
        assert not table.empty


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
