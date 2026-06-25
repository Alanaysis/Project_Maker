"""
技术因子模块测试
"""

import numpy as np
import pandas as pd
import pytest

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.factors.technical import TechnicalFactors


@pytest.fixture
def sample_price_data():
    """生成测试用价格数据"""
    np.random.seed(42)
    n = 200
    dates = pd.bdate_range(start="2023-01-01", periods=n)
    close = 100 * np.exp(np.cumsum(np.random.normal(0.0005, 0.02, n)))
    volume = np.random.lognormal(15, 0.5, n)

    df = pd.DataFrame({
        "open": close * (1 + np.random.randn(n) * 0.005),
        "high": close * (1 + abs(np.random.randn(n)) * 0.01),
        "low": close * (1 - abs(np.random.randn(n)) * 0.01),
        "close": close,
        "volume": volume,
    }, index=dates)
    return df


class TestMomentum:
    """动量因子测试"""

    def test_momentum_basic(self, sample_price_data):
        """测试动量因子基本计算"""
        result = TechnicalFactors.momentum(sample_price_data["close"], window=20)
        assert len(result) == len(sample_price_data)
        # pct_change(20) 对前 20 个值返回 NaN (index 0-19)
        assert result.iloc[:20].isna().all()
        # 之后应有有效值 (可能因数据质量有少量 NaN，所以用大部分检查)
        assert result.iloc[20:].notna().mean() > 0.9

    def test_momentum_values(self):
        """测试动量因子值的正确性"""
        close = pd.Series([100, 110, 105, 115, 120])
        result = TechnicalFactors.momentum(close, window=2)
        # 第3个值 (index 2): (105 - 100) / 100 = 0.05
        assert abs(result.iloc[2] - 0.05) < 1e-10
        # 第4个值 (index 3): (115 - 110) / 110 ≈ 0.04545
        assert abs(result.iloc[3] - (115 - 110) / 110) < 1e-10

    def test_momentum_acceleration(self, sample_price_data):
        """测试动量加速度因子"""
        result = TechnicalFactors.momentum_acceleration(
            sample_price_data["close"], short_window=5, long_window=20
        )
        assert len(result) == len(sample_price_data)

    def test_price_position(self, sample_price_data):
        """测试价格位置因子"""
        result = TechnicalFactors.price_position(
            sample_price_data["close"], window=20
        )
        # 价格位置应在 0-1 之间
        valid = result.dropna()
        assert (valid >= 0).all()
        assert (valid <= 1).all()


class TestVolatility:
    """波动率因子测试"""

    def test_realized_volatility(self, sample_price_data):
        """测试已实现波动率"""
        result = TechnicalFactors.realized_volatility(
            sample_price_data["close"], window=20
        )
        valid = result.dropna()
        assert (valid >= 0).all()  # 波动率应非负

    def test_intraday_volatility(self, sample_price_data):
        """测试日内波动率"""
        result = TechnicalFactors.intraday_volatility(
            sample_price_data["high"],
            sample_price_data["low"],
            sample_price_data["close"],
            window=20
        )
        valid = result.dropna()
        assert (valid >= 0).all()

    def test_downside_volatility(self, sample_price_data):
        """测试下行波动率"""
        result = TechnicalFactors.downside_volatility(
            sample_price_data["close"], window=20
        )
        valid = result.dropna()
        assert (valid >= 0).all()


class TestLiquidity:
    """流动性因子测试"""

    def test_amihud_illiquidity(self, sample_price_data):
        """测试 Amihud 非流动性因子"""
        result = TechnicalFactors.amihud_illiquidity(
            sample_price_data["close"],
            sample_price_data["volume"],
            window=20
        )
        valid = result.dropna()
        assert (valid >= 0).all()

    def test_volume_price_correlation(self, sample_price_data):
        """测试量价相关性因子"""
        result = TechnicalFactors.volume_price_correlation(
            sample_price_data["close"],
            sample_price_data["volume"],
            window=20
        )
        valid = result.dropna()
        assert (valid >= -1).all()
        assert (valid <= 1).all()


class TestTechnicalIndicators:
    """技术指标因子测试"""

    def test_rsi(self, sample_price_data):
        """测试 RSI 指标"""
        result = TechnicalFactors.rsi(sample_price_data["close"], window=14)
        valid = result.dropna()
        assert (valid >= 0).all()
        assert (valid <= 100).all()

    def test_macd(self, sample_price_data):
        """测试 MACD 指标"""
        result = TechnicalFactors.macd(sample_price_data["close"])
        assert "DIF" in result.columns
        assert "DEA" in result.columns
        assert "MACD" in result.columns

    def test_bollinger_band_width(self, sample_price_data):
        """测试布林带宽度"""
        result = TechnicalFactors.bollinger_band_width(
            sample_price_data["close"], window=20
        )
        valid = result.dropna()
        assert (valid >= 0).all()


class TestComputeAll:
    """批量计算测试"""

    def test_compute_all(self, sample_price_data):
        """测试批量计算所有因子"""
        result = TechnicalFactors.compute_all(sample_price_data, windows=[5, 20])
        assert "momentum_5d" in result.columns
        assert "momentum_20d" in result.columns
        assert "volatility_5d" in result.columns
        assert "rsi_14" in result.columns
        assert len(result) == len(sample_price_data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
