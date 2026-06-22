"""
投资组合测试

⭐ 重点：测试投资组合管理的核心功能
"""

import pytest
from datetime import datetime
from src.core.portfolio import Portfolio, Position
from src.core.events import FillEvent


class TestPosition:
    """持仓测试"""

    def test_initialization(self):
        """测试初始化"""
        pos = Position(symbol="AAPL")
        assert pos.symbol == "AAPL"
        assert pos.quantity == 0
        assert pos.avg_cost == 0.0

    def test_market_value(self):
        """测试市值计算"""
        pos = Position(symbol="AAPL", quantity=100, current_price=150.0)
        assert pos.market_value == 15000.0

    def test_cost_basis(self):
        """测试成本计算"""
        pos = Position(symbol="AAPL", quantity=100, avg_cost=140.0)
        assert pos.cost_basis == 14000.0

    def test_update_price(self):
        """测试价格更新"""
        pos = Position(symbol="AAPL", quantity=100, avg_cost=140.0)
        pos.update_price(150.0)

        assert pos.current_price == 150.0
        assert pos.unrealized_pnl == 1000.0  # (150 - 140) * 100

    def test_update_price_zero_quantity(self):
        """测试零持仓时的价格更新"""
        pos = Position(symbol="AAPL", quantity=0)
        pos.update_price(150.0)

        assert pos.unrealized_pnl == 0.0


class TestPortfolio:
    """投资组合测试"""

    def test_initialization(self):
        """测试初始化"""
        portfolio = Portfolio(initial_capital=100000.0)

        assert portfolio.initial_capital == 100000.0
        assert portfolio.cash == 100000.0
        assert portfolio.total_equity == 100000.0
        assert portfolio.total_pnl == 0.0
        assert portfolio.returns == 0.0

    def test_buy_fill(self):
        """测试买入成交"""
        portfolio = Portfolio(initial_capital=100000.0)

        fill = FillEvent(
            symbol="AAPL",
            direction="BUY",
            quantity=100,
            fill_price=150.0,
            commission=15.0,
            order_id="test-001"
        )

        portfolio.update_fill(fill)

        # 检查持仓
        position = portfolio.get_position("AAPL")
        assert position.quantity == 100
        assert position.avg_cost == 150.0

        # 检查资金
        expected_cash = 100000.0 - (100 * 150.0) - 15.0
        assert portfolio.cash == expected_cash

        # 检查总资产
        assert portfolio.total_equity == 100000.0 - 15.0  # 手续费

    def test_sell_fill(self):
        """测试卖出成交"""
        portfolio = Portfolio(initial_capital=100000.0)

        # 先买入
        buy_fill = FillEvent(
            symbol="AAPL",
            direction="BUY",
            quantity=100,
            fill_price=150.0,
            commission=15.0,
            order_id="test-001"
        )
        portfolio.update_fill(buy_fill)

        # 再卖出
        sell_fill = FillEvent(
            symbol="AAPL",
            direction="SELL",
            quantity=100,
            fill_price=160.0,
            commission=16.0,
            order_id="test-002"
        )
        portfolio.update_fill(sell_fill)

        # 检查持仓
        position = portfolio.get_position("AAPL")
        assert position.quantity == 0

        # 检查盈亏
        assert position.realized_pnl == 1000.0  # (160 - 150) * 100

        # 检查资金
        expected_cash = 100000.0 - 15000.0 - 15.0 + 16000.0 - 16.0
        assert portfolio.cash == expected_cash

    def test_multiple_buys(self):
        """测试多次买入"""
        portfolio = Portfolio(initial_capital=100000.0)

        # 第一次买入
        fill1 = FillEvent(
            symbol="AAPL",
            direction="BUY",
            quantity=100,
            fill_price=150.0,
            commission=15.0,
            order_id="test-001"
        )
        portfolio.update_fill(fill1)

        # 第二次买入
        fill2 = FillEvent(
            symbol="AAPL",
            direction="BUY",
            quantity=100,
            fill_price=160.0,
            commission=16.0,
            order_id="test-002"
        )
        portfolio.update_fill(fill2)

        # 检查持仓
        position = portfolio.get_position("AAPL")
        assert position.quantity == 200
        assert position.avg_cost == 155.0  # (150*100 + 160*100) / 200

    def test_update_market_data(self):
        """测试更新市场价格"""
        portfolio = Portfolio(initial_capital=100000.0)

        # 买入
        fill = FillEvent(
            symbol="AAPL",
            direction="BUY",
            quantity=100,
            fill_price=150.0,
            commission=15.0,
            order_id="test-001"
        )
        portfolio.update_fill(fill)

        # 更新价格
        portfolio.update_market_data("AAPL", 160.0)

        position = portfolio.get_position("AAPL")
        assert position.current_price == 160.0
        assert position.unrealized_pnl == 1000.0

    def test_record_equity(self):
        """测试记录权益曲线"""
        portfolio = Portfolio(initial_capital=100000.0)

        timestamp = datetime.now()
        portfolio.record_equity(timestamp)

        assert len(portfolio.equity_curve) == 1
        assert portfolio.equity_curve[0]["equity"] == 100000.0

    def test_get_summary(self):
        """测试获取摘要"""
        portfolio = Portfolio(initial_capital=100000.0)

        fill = FillEvent(
            symbol="AAPL",
            direction="BUY",
            quantity=100,
            fill_price=150.0,
            commission=15.0,
            order_id="test-001"
        )
        portfolio.update_fill(fill)

        summary = portfolio.get_summary()

        assert summary["initial_capital"] == 100000.0
        assert summary["trade_count"] == 1
        assert "AAPL" in summary["positions"]

    def test_returns_calculation(self):
        """测试收益率计算"""
        portfolio = Portfolio(initial_capital=100000.0)

        # 买入
        fill = FillEvent(
            symbol="AAPL",
            direction="BUY",
            quantity=100,
            fill_price=150.0,
            commission=15.0,
            order_id="test-001"
        )
        portfolio.update_fill(fill)

        # 更新价格
        portfolio.update_market_data("AAPL", 160.0)

        # 收益率 = (总资产 - 初始资金) / 初始资金
        expected_returns = (portfolio.total_equity - 100000.0) / 100000.0
        assert abs(portfolio.returns - expected_returns) < 0.0001
