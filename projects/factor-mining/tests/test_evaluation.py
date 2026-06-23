"""因子评估模块测试"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pandas as pd
import pytest
from src.data import generate_stock_data
from src.factors import FactorCalculator
from src.evaluation import FactorEvaluator


@pytest.fixture
def evaluator():
    """创建因子评估器实例"""
    data = generate_stock_data(n_stocks=30, n_days=200, seed=456)
    calc = FactorCalculator(
        price=data['price'],
        volume=data['volume'],
        high=data['high'],
        low=data['low'],
    )
    factor = calc.momentum(window=20)
    future_returns = data['returns'].shift(-1)
    return FactorEvaluator(factor, future_returns, periods=1)


class TestICAnalysis:
    """IC 分析测试"""

    def test_rank_ic_returns_series(self, evaluator):
        ic = evaluator.rank_ic()
        assert isinstance(ic, pd.Series)
        assert len(ic) > 0

    def test_rank_ic_range(self, evaluator):
        ic = evaluator.rank_ic()
        # IC 应在 -1 到 1 之间
        assert (ic >= -1).all()
        assert (ic <= 1).all()

    def test_ic_summary_keys(self, evaluator):
        summary = evaluator.ic_summary()
        expected_keys = {'IC_mean', 'IC_std', 'ICIR', 'IC_tstat',
                         'IC_positive_ratio', 'IC_count'}
        assert expected_keys.issubset(set(summary.keys()))

    def test_pearson_ic(self, evaluator):
        ic = evaluator.rank_ic(method='pearson')
        assert isinstance(ic, pd.Series)
        assert len(ic) > 0


class TestGroupReturns:
    """分组收益测试"""

    def test_group_returns_shape(self, evaluator):
        result = evaluator.group_returns(n_groups=5)
        assert result.shape[1] == 5

    def test_group_returns_columns(self, evaluator):
        result = evaluator.group_returns(n_groups=3)
        assert list(result.columns) == ['G1', 'G2', 'G3']

    def test_long_short_return(self, evaluator):
        ls = evaluator.long_short_return(n_groups=5)
        assert isinstance(ls, pd.Series)
        assert len(ls) > 0

    def test_cumulative_returns(self, evaluator):
        cum = evaluator.cumulative_returns(n_groups=5)
        assert isinstance(cum, pd.DataFrame)
        # 累计收益应有合理的值
        assert not cum.isna().all().all()


class TestFactorProperties:
    """因子属性测试"""

    def test_turnover(self, evaluator):
        turnover = evaluator.factor_turnover(n_groups=5)
        assert isinstance(turnover, pd.Series)
        # 换手率应在 0~1 之间
        if len(turnover) > 0:
            assert (turnover >= 0).all()
            assert (turnover <= 1).all()

    def test_factor_decay(self, evaluator):
        decay = evaluator.factor_decay(max_lag=5, n_groups=5)
        assert isinstance(decay, pd.DataFrame)
        assert len(decay) == 5
        assert 'IC' in decay.columns
        assert 'long_short_return' in decay.columns


class TestPerformanceSummary:
    """绩效摘要测试"""

    def test_performance_summary_keys(self, evaluator):
        result = evaluator.performance_summary(n_groups=5)
        expected_keys = {'long_short_ann_return', 'long_short_sharpe',
                         'long_only_ann_return', 'IC_mean', 'ICIR'}
        assert expected_keys.issubset(set(result.keys()))

    def test_sharpe_reasonable(self, evaluator):
        result = evaluator.performance_summary(n_groups=5)
        # Sharpe 不应极端 (在 -10 到 10 之间)
        assert -10 < result['long_short_sharpe'] < 10
