"""
因子优化模块测试
"""

import numpy as np
import pandas as pd
import pytest

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.optimization.neutralizer import FactorNeutralizer
from src.optimization.standardizer import FactorStandardizer
from src.optimization.winsorizer import FactorWinsorizer
from src.optimization.filler import FactorFiller


@pytest.fixture
def sample_data():
    """生成测试用数据"""
    np.random.seed(42)
    n = 100
    stocks = [f"S{i:03d}" for i in range(n)]

    factor = pd.Series(np.random.randn(n), index=stocks)
    industry = pd.Series(np.random.choice(["A", "B", "C"], n), index=stocks)
    market_cap = pd.Series(np.random.lognormal(20, 1, n), index=stocks)

    return factor, industry, market_cap


class TestFactorNeutralizer:
    """中性化测试"""

    def test_industry_neutralize(self, sample_data):
        """测试行业中性化"""
        factor, industry, _ = sample_data
        result = FactorNeutralizer.industry_neutralize(factor, industry)
        assert len(result) == len(factor)

        # 中性化后各行业均值应接近 0
        valid = pd.DataFrame({"f": result, "ind": industry}).dropna()
        industry_means = valid.groupby("ind")["f"].mean()
        assert (industry_means.abs() < 0.1).all()

    def test_market_neutralize(self, sample_data):
        """测试市值中性化"""
        factor, _, market_cap = sample_data
        result = FactorNeutralizer.market_neutralize(factor, market_cap)
        assert len(result) == len(factor)

    def test_neutralize(self, sample_data):
        """测试行业市值联合中性化"""
        factor, industry, market_cap = sample_data
        result = FactorNeutralizer.neutralize(factor, industry, market_cap)
        assert len(result) == len(factor)


class TestFactorStandardizer:
    """标准化测试"""

    def test_zscore(self, sample_data):
        """测试 Z-score 标准化"""
        factor, _, _ = sample_data
        result = FactorStandardizer.zscore(factor)
        assert abs(result.mean()) < 1e-10
        assert abs(result.std() - 1.0) < 1e-10

    def test_rank_percentile(self, sample_data):
        """测试排名百分位标准化"""
        factor, _, _ = sample_data
        result = FactorStandardizer.rank_percentile(factor)
        valid = result.dropna()
        assert (valid >= 0).all()
        assert (valid <= 1).all()

    def test_min_max_scale(self, sample_data):
        """测试 Min-Max 缩放"""
        factor, _, _ = sample_data
        result = FactorStandardizer.min_max_scale(factor)
        assert abs(result.min()) < 1e-10
        assert abs(result.max() - 1.0) < 1e-10

    def test_robust_zscore(self, sample_data):
        """测试稳健 Z-score"""
        factor, _, _ = sample_data
        result = FactorStandardizer.robust_zscore(factor)
        assert len(result) == len(factor)

    def test_normal_score(self, sample_data):
        """测试正态得分标准化"""
        factor, _, _ = sample_data
        result = FactorStandardizer.normal_score(factor)
        valid = result.dropna()
        assert abs(valid.mean()) < 0.5  # 应接近 0

    def test_standardize_panel(self, sample_data):
        """测试面板标准化"""
        factor, _, _ = sample_data
        panel = pd.DataFrame({"A": factor, "B": factor * 2})
        result = FactorStandardizer.standardize_panel(panel, method="zscore")
        assert result.shape == panel.shape


class TestFactorWinsorizer:
    """去极值测试"""

    def test_percentile_winsorize(self, sample_data):
        """测试分位数去极值"""
        factor, _, _ = sample_data
        result = FactorWinsorizer.percentile_winsorize(factor, lower=0.05, upper=0.95)
        q_low = factor.quantile(0.05)
        q_high = factor.quantile(0.95)
        assert (result >= q_low).all()
        assert (result <= q_high).all()

    def test_mad_winsorize(self, sample_data):
        """测试 MAD 去极值"""
        factor, _, _ = sample_data
        result = FactorWinsorizer.mad_winsorize(factor, n_mad=3)
        assert len(result) == len(factor)

    def test_sigma_winsorize(self, sample_data):
        """测试标准差去极值"""
        factor, _, _ = sample_data
        result = FactorWinsorizer.sigma_winsorize(factor, n_sigma=3)
        assert len(result) == len(factor)

    def test_detect_outliers(self, sample_data):
        """测试极端值检测"""
        factor, _, _ = sample_data
        outliers = FactorWinsorizer.detect_outliers(factor, method="mad")
        assert outliers.dtype == bool


class TestFactorFiller:
    """补全测试"""

    def test_forward_fill(self):
        """测试前值填充"""
        factor = pd.Series([1, np.nan, np.nan, 4, np.nan])
        result = FactorFiller.forward_fill(factor, limit=2)
        assert result.iloc[1] == 1
        assert result.iloc[2] == 1
        assert result.iloc[3] == 4
        assert result.iloc[4] == 4

    def test_cross_sectional_median(self, sample_data):
        """测试截面中位数填充"""
        factor, industry, _ = sample_data
        factor_with_nan = factor.copy()
        factor_with_nan.iloc[0:10] = np.nan
        result = FactorFiller.cross_sectional_median(factor_with_nan, industry)
        assert result.isna().sum() == 0

    def test_neutral_fill(self):
        """测试中性值填充"""
        factor = pd.Series([1, 2, np.nan, 4, 5])
        result = FactorFiller.neutral_fill(factor)
        assert result.iloc[2] == 3.0  # 中位数


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
