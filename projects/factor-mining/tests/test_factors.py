"""因子计算模块测试"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pandas as pd
import pytest
from src.data import generate_stock_data
from src.factors import FactorCalculator


@pytest.fixture
def sample_data():
    """生成测试用数据"""
    data = generate_stock_data(n_stocks=20, n_days=100, seed=123)
    return data


@pytest.fixture
def calculator(sample_data):
    """创建因子计算器实例"""
    return FactorCalculator(
        price=sample_data['price'],
        volume=sample_data['volume'],
        high=sample_data['high'],
        low=sample_data['low'],
    )


class TestMomentumFactors:
    """动量因子测试"""

    def test_momentum_shape(self, calculator):
        result = calculator.momentum(window=20)
        assert result.shape == calculator.price.shape

    def test_momentum_values(self, calculator):
        result = calculator.momentum(window=20)
        # 前19行应为 NaN
        assert result.iloc[:19].isna().all().all()
        # 之后不应全为 NaN
        assert not result.iloc[20:].isna().all().all()

    def test_momentum_manual(self, calculator):
        """验证手动计算结果"""
        result = calculator.momentum(window=5)
        price = calculator.price
        expected = price.iloc[5] / price.iloc[0] - 1
        actual = result.iloc[5]
        pd.testing.assert_series_equal(actual, expected, check_names=False,
                                        atol=1e-10)

    def test_short_term_reversal(self, calculator):
        mom = calculator.momentum(window=5)
        rev = calculator.short_term_reversal(window=5)
        # 反转因子应为动量的负值
        pd.testing.assert_frame_equal(
            rev.iloc[5:], -mom.iloc[5:], check_names=False, atol=1e-10
        )


class TestVolatilityFactors:
    """波动率因子测试"""

    def test_volatility_positive(self, calculator):
        result = calculator.volatility(window=20)
        valid = result.dropna()
        assert (valid >= 0).all().all()

    def test_downside_volatility_properties(self, calculator):
        vol = calculator.volatility(window=20)
        dvol = calculator.downside_volatility(window=20)
        valid = dvol.dropna()
        # 下行波动率应非负
        assert (valid >= 0).all().all()
        # 下行波动率应为有限值
        assert np.isfinite(valid).all().all()

    def test_atr_positive(self, calculator):
        result = calculator.atr(window=14)
        valid = result.dropna()
        assert (valid >= 0).all().all()


class TestLiquidityFactors:
    """流动性因子测试"""

    def test_amihud_positive(self, calculator):
        result = calculator.amihud_illiquidity(window=20)
        valid = result.dropna()
        assert (valid >= 0).all().all()

    def test_volume_momentum_positive(self, calculator):
        result = calculator.volume_momentum(window=20)
        valid = result.dropna()
        assert (valid >= 0).all().all()


class TestTechnicalFactors:
    """技术因子测试"""

    def test_rsi_range(self, calculator):
        result = calculator.rsi(window=14)
        valid = result.dropna()
        assert (valid >= 0).all().all()
        assert (valid <= 100).all().all()

    def test_bollinger_width_positive(self, calculator):
        result = calculator.bollinger_width(window=20)
        valid = result.dropna()
        assert (valid >= 0).all().all()

    def test_price_to_ma_around_one(self, calculator):
        result = calculator.price_to_ma(window=20)
        valid = result.dropna()
        # 价格/均线比应围绕1波动
        assert valid.mean().mean() > 0.5
        assert valid.mean().mean() < 2.0


class TestCompositeFactor:
    """组合因子测试"""

    def test_composite_shape(self, calculator):
        factors = {
            'mom': calculator.momentum(20),
            'vol': calculator.volatility(20),
        }
        result = calculator.composite_score(factors)
        assert result.shape == calculator.price.shape

    def test_composite_custom_weights(self, calculator):
        factors = {
            'mom': calculator.momentum(20),
            'vol': calculator.volatility(20),
        }
        weights = {'mom': 0.7, 'vol': 0.3}
        result = calculator.composite_score(factors, weights)
        assert result.shape == calculator.price.shape
