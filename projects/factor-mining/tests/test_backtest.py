"""回测框架测试"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pandas as pd
import pytest
from src.data import generate_stock_data
from src.factors import FactorCalculator
from src.backtest import BacktestEngine, BacktestConfig, multi_factor_backtest
from src.evaluation import FactorEvaluator


@pytest.fixture
def sample_data():
    return generate_stock_data(n_stocks=30, n_days=200, seed=789)


@pytest.fixture
def momentum_factor(sample_data):
    calc = FactorCalculator(
        price=sample_data['price'],
        volume=sample_data['volume'],
        high=sample_data['high'],
        low=sample_data['low'],
    )
    return calc.momentum(window=20)


class TestBacktestEngine:
    """回测引擎测试"""

    def test_run_returns_result(self, sample_data, momentum_factor):
        engine = BacktestEngine(momentum_factor, sample_data['returns'])
        result = engine.run()
        assert result is not None
        assert len(result.daily_returns) > 0

    def test_result_summary_keys(self, sample_data, momentum_factor):
        engine = BacktestEngine(momentum_factor, sample_data['returns'])
        result = engine.run()
        summary = result.summary()
        expected_keys = {'total_return', 'ann_return', 'sharpe_ratio',
                         'max_drawdown', 'win_rate'}
        assert expected_keys.issubset(set(summary.keys()))

    def test_nav_starts_near_one(self, sample_data, momentum_factor):
        engine = BacktestEngine(momentum_factor, sample_data['returns'])
        result = engine.run()
        assert abs(result.portfolio_values.iloc[0] - 1.0) < 0.1

    def test_to_dataframe(self, sample_data, momentum_factor):
        engine = BacktestEngine(momentum_factor, sample_data['returns'])
        result = engine.run()
        df = result.to_dataframe()
        assert 'daily_return' in df.columns
        assert 'nav' in df.columns
        assert 'drawdown' in df.columns

    def test_top_group_only(self, sample_data, momentum_factor):
        config = BacktestConfig(top_group_only=True, n_groups=5)
        engine = BacktestEngine(momentum_factor, sample_data['returns'], config)
        result = engine.run()
        assert len(result.daily_returns) > 0

    def test_rebalance_freq(self, sample_data, momentum_factor):
        config = BacktestConfig(rebalance_freq=5, n_groups=5)
        engine = BacktestEngine(momentum_factor, sample_data['returns'], config)
        result = engine.run()
        assert len(result.daily_returns) > 0

    def test_transaction_cost_effect(self, sample_data, momentum_factor):
        # 无成本
        config_no_cost = BacktestConfig(transaction_cost=0, n_groups=5)
        engine_no = BacktestEngine(momentum_factor, sample_data['returns'],
                                    config_no_cost)
        result_no = engine_no.run()

        # 高成本
        config_high_cost = BacktestConfig(transaction_cost=0.01, n_groups=5)
        engine_high = BacktestEngine(momentum_factor, sample_data['returns'],
                                      config_high_cost)
        result_high = engine_high.run()

        # 高成本下总收益应更低 (或至少不更高)
        assert result_high.summary()['total_return'] <= \
               result_no.summary()['total_return'] + 0.01


class TestMultiFactorBacktest:
    """多因子回测测试"""

    def test_multi_factor(self, sample_data):
        calc = FactorCalculator(
            price=sample_data['price'],
            volume=sample_data['volume'],
            high=sample_data['high'],
            low=sample_data['low'],
        )
        factors = {
            'momentum': calc.momentum(20),
            'volatility': calc.volatility(20),
            'reversal': calc.short_term_reversal(5),
        }
        result = multi_factor_backtest(factors, sample_data['returns'])
        assert result is not None
        assert len(result.daily_returns) > 0

    def test_multi_factor_with_weights(self, sample_data):
        calc = FactorCalculator(
            price=sample_data['price'],
            volume=sample_data['volume'],
        )
        factors = {
            'momentum': calc.momentum(20),
            'volatility': calc.volatility(20),
        }
        weights = {'momentum': 0.6, 'volatility': 0.4}
        result = multi_factor_backtest(factors, sample_data['returns'],
                                        weights=weights)
        assert result is not None
