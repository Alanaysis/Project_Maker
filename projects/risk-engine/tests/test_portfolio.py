"""测试持仓数据管理模块"""

import pytest
import numpy as np
import pandas as pd
from src.portfolio import Portfolio, Position


class TestPosition:
    """Position 类测试"""

    def test_position_creation(self):
        """测试持仓创建"""
        pos = Position("AAPL", 100, 150.0)
        assert pos.symbol == "AAPL"
        assert pos.quantity == 100
        assert pos.current_price == 150.0
        assert pos.asset_class == "equity"

    def test_market_value(self):
        """测试市值计算"""
        pos = Position("AAPL", 100, 150.0)
        assert pos.market_value == 15000.0

    def test_custom_asset_class(self):
        """测试自定义资产类别"""
        pos = Position("GLD", 50, 180.0, "commodity")
        assert pos.asset_class == "commodity"


class TestPortfolio:
    """Portfolio 类测试"""

    def test_portfolio_creation(self):
        """测试组合创建"""
        portfolio = Portfolio("Test Portfolio")
        assert portfolio.name == "Test Portfolio"
        assert len(portfolio.positions) == 0

    def test_add_position(self):
        """测试添加持仓"""
        portfolio = Portfolio("Test")
        pos = Position("AAPL", 100, 150.0)
        portfolio.add_position(pos)
        assert len(portfolio.positions) == 1
        assert portfolio.positions[0].symbol == "AAPL"

    def test_remove_position(self):
        """测试移除持仓"""
        portfolio = Portfolio("Test")
        portfolio.add_position(Position("AAPL", 100, 150.0))
        portfolio.add_position(Position("GOOGL", 50, 2800.0))

        result = portfolio.remove_position("AAPL")
        assert result is True
        assert len(portfolio.positions) == 1
        assert portfolio.positions[0].symbol == "GOOGL"

    def test_remove_nonexistent_position(self):
        """测试移除不存在的持仓"""
        portfolio = Portfolio("Test")
        result = portfolio.remove_position("AAPL")
        assert result is False

    def test_get_position(self):
        """测试获取持仓"""
        portfolio = Portfolio("Test")
        portfolio.add_position(Position("AAPL", 100, 150.0))

        pos = portfolio.get_position("AAPL")
        assert pos is not None
        assert pos.symbol == "AAPL"

        pos = portfolio.get_position("GOOGL")
        assert pos is None

    def test_total_value(self):
        """测试组合总市值"""
        portfolio = Portfolio("Test")
        portfolio.add_position(Position("AAPL", 100, 150.0))
        portfolio.add_position(Position("GOOGL", 50, 2800.0))

        expected = 100 * 150.0 + 50 * 2800.0
        assert portfolio.total_value == expected

    def test_symbols(self):
        """测试获取标的代码列表"""
        portfolio = Portfolio("Test")
        portfolio.add_position(Position("AAPL", 100, 150.0))
        portfolio.add_position(Position("GOOGL", 50, 2800.0))

        symbols = portfolio.symbols
        assert len(symbols) == 2
        assert "AAPL" in symbols
        assert "GOOGL" in symbols

    def test_weights(self):
        """测试权重计算"""
        portfolio = Portfolio("Test")
        portfolio.add_position(Position("AAPL", 100, 100.0))  # 10000
        portfolio.add_position(Position("GOOGL", 10, 1000.0))  # 10000

        weights = portfolio.weights
        assert len(weights) == 2
        assert weights["AAPL"] == pytest.approx(0.5)
        assert weights["GOOGL"] == pytest.approx(0.5)

    def test_weights_empty_portfolio(self):
        """测试空组合的权重"""
        portfolio = Portfolio("Test")
        weights = portfolio.weights
        assert len(weights) == 0

    def test_calculate_portfolio_returns(self):
        """测试组合收益率计算"""
        portfolio = Portfolio("Test")
        portfolio.add_position(Position("AAPL", 100, 100.0))  # weight 0.5
        portfolio.add_position(Position("GOOGL", 10, 1000.0))  # weight 0.5

        # 创建收益率数据
        returns_df = pd.DataFrame({
            "AAPL": [0.01, -0.02, 0.03],
            "GOOGL": [0.02, -0.01, 0.01]
        })

        portfolio_returns = portfolio.calculate_portfolio_returns(returns_df)
        expected = np.array([0.015, -0.015, 0.02])

        np.testing.assert_array_almost_equal(portfolio_returns, expected)

    def test_to_dict(self):
        """测试转换为字典"""
        portfolio = Portfolio("Test")
        portfolio.add_position(Position("AAPL", 100, 150.0))

        data = portfolio.to_dict()
        assert data["name"] == "Test"
        assert data["num_positions"] == 1
        assert data["total_value"] == 15000.0
        assert len(data["positions"]) == 1
        assert data["positions"][0]["symbol"] == "AAPL"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
