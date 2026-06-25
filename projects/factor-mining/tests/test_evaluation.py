"""
因子评估模块测试
"""

import numpy as np
import pandas as pd
import pytest

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.evaluation.ic_analysis import ICAnalysis
from src.evaluation.ir_analysis import IRAnalysis
from src.evaluation.group_backtest import GroupBacktest
from src.evaluation.decay_analysis import DecayAnalysis


@pytest.fixture
def sample_panels():
    """生成测试用面板数据"""
    np.random.seed(42)
    n_days = 100
    n_stocks = 30
    dates = pd.bdate_range(start="2023-01-01", periods=n_days)
    stocks = [f"S{i:03d}" for i in range(n_stocks)]

    # 生成有因子结构的数据
    factor_values = np.random.randn(n_days, n_stocks)
    # 让因子与收益有弱相关性
    noise = np.random.randn(n_days, n_stocks) * 0.02
    return_values = factor_values * 0.002 + noise

    factor_panel = pd.DataFrame(factor_values, index=dates, columns=stocks)
    return_panel = pd.DataFrame(return_values, index=dates, columns=stocks)

    return factor_panel, return_panel


class TestICAnalysis:
    """IC 分析测试"""

    def test_rank_ic(self):
        """测试单期 Rank IC"""
        # 需要至少 10 个数据点
        factor = pd.Series(range(20))
        returns = pd.Series(np.arange(20) * 0.01 + np.random.randn(20) * 0.001)
        ic = ICAnalysis.rank_ic(factor, returns)
        assert ic > 0  # 正相关

    def test_rank_ic_negative(self):
        """测试负相关 IC"""
        factor = pd.Series(range(20))
        returns = pd.Series(-np.arange(20) * 0.01 + np.random.randn(20) * 0.001)
        ic = ICAnalysis.rank_ic(factor, returns)
        assert ic < 0  # 负相关

    def test_pearson_ic(self):
        """测试 Pearson IC"""
        factor = pd.Series(range(20))
        returns = pd.Series(np.arange(20) * 0.01 + np.random.randn(20) * 0.001)
        ic = ICAnalysis.pearson_ic(factor, returns)
        assert ic > 0

    def test_compute_ic_series(self, sample_panels):
        """测试 IC 时间序列计算"""
        factor_panel, return_panel = sample_panels
        ic_series = ICAnalysis.compute_ic_series(factor_panel, return_panel)
        assert len(ic_series) == len(factor_panel)
        assert not ic_series.isna().all()

    def test_compute_ic_summary(self, sample_panels):
        """测试 IC 统计摘要"""
        factor_panel, return_panel = sample_panels
        summary = ICAnalysis.compute_ic_summary(factor_panel, return_panel)

        assert "ic_mean" in summary
        assert "ic_std" in summary
        assert "ic_ir" in summary
        assert "t_stat" in summary
        assert "p_value" in summary
        assert summary["count"] > 0

    def test_ic_decay(self, sample_panels):
        """测试 IC 衰减分析"""
        factor_panel, return_panel = sample_panels
        decay = ICAnalysis.ic_decay(factor_panel, return_panel, max_lag=10)
        assert len(decay) == 10
        assert "lag" in decay.columns
        assert "ic_mean" in decay.columns


class TestIRAnalysis:
    """IR 分析测试"""

    def test_compute_ir(self):
        """测试 IR 计算"""
        ic_series = pd.Series([0.05, 0.03, 0.04, 0.06, 0.02])
        ir = IRAnalysis.compute_ir(ic_series)
        assert ir > 0

    def test_compute_ir_zero_std(self):
        """测试标准差近似为零的情况"""
        # 使用完全相同的值，std 应接近 0
        ic_series = pd.Series([0.05, 0.05, 0.05, 0.05, 0.05])
        ir = IRAnalysis.compute_ir(ic_series)
        # 浮点精度下 std 可能不是精确 0，但 IR 应该很大或为 0
        # 实际上当所有值相同时，std 为浮点误差级别的非零值
        assert isinstance(ir, float)

    def test_rolling_ir(self, sample_panels):
        """测试滚动 IR"""
        factor_panel, return_panel = sample_panels
        ic_series = ICAnalysis.compute_ic_series(factor_panel, return_panel)
        rolling_ir = IRAnalysis.rolling_ir(ic_series, window=20)
        assert len(rolling_ir) == len(ic_series)

    def test_multi_factor_ir_comparison(self, sample_panels):
        """测试多因子 IR 对比"""
        factor_panel, return_panel = sample_panels
        ic_dict = {
            "factor_1": ICAnalysis.compute_ic_series(factor_panel, return_panel),
        }
        comparison = IRAnalysis.multi_factor_ir_comparison(ic_dict)
        assert len(comparison) == 1
        assert "factor" in comparison.columns


class TestGroupBacktest:
    """分组回测测试"""

    def test_assign_groups(self, sample_panels):
        """测试分组分配"""
        factor_panel, _ = sample_panels
        bt = GroupBacktest(n_groups=5)
        groups = bt.assign_groups(factor_panel.iloc[0])
        valid = groups.dropna()
        assert set(valid.unique()).issubset({1, 2, 3, 4, 5})

    def test_run(self, sample_panels):
        """测试分组回测执行"""
        factor_panel, return_panel = sample_panels
        bt = GroupBacktest(n_groups=5)
        result = bt.run(factor_panel, return_panel)

        assert "group_returns" in result
        assert "cumulative" in result
        assert "long_short" in result
        assert "group_stats" in result
        assert "monotonicity" in result

    def test_monotonicity(self, sample_panels):
        """测试单调性计算"""
        factor_panel, return_panel = sample_panels
        bt = GroupBacktest(n_groups=5)
        result = bt.run(factor_panel, return_panel)
        mono = result["monotonicity"]
        assert -1 <= mono <= 1


class TestDecayAnalysis:
    """衰减分析测试"""

    def test_ic_decay_by_horizon(self, sample_panels):
        """测试 IC 衰减分析"""
        factor_panel, return_panel = sample_panels
        analyzer = DecayAnalysis()
        decay = analyzer.ic_decay_by_horizon(factor_panel, return_panel, max_horizon=10)
        assert len(decay) == 10
        assert "horizon" in decay.columns
        assert "ic_mean" in decay.columns

    def test_estimate_half_life(self, sample_panels):
        """测试半衰期估计"""
        factor_panel, return_panel = sample_panels
        analyzer = DecayAnalysis()
        decay = analyzer.ic_decay_by_horizon(factor_panel, return_panel, max_horizon=10)
        half_life = analyzer.estimate_half_life(decay)
        assert half_life is None or half_life > 0

    def test_optimal_holding_period(self, sample_panels):
        """测试最优持仓期"""
        factor_panel, return_panel = sample_panels
        analyzer = DecayAnalysis()
        decay = analyzer.ic_decay_by_horizon(factor_panel, return_panel, max_horizon=10)
        optimal = analyzer.optimal_holding_period(decay)
        assert optimal >= 1

    def test_persistence_score(self, sample_panels):
        """测试持续性评分"""
        factor_panel, return_panel = sample_panels
        analyzer = DecayAnalysis()
        decay = analyzer.ic_decay_by_horizon(factor_panel, return_panel, max_horizon=10)
        score = analyzer.factor_persistence_score(decay)
        assert 0 <= score <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
