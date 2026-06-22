"""
风险管理测试

⭐ 重点：测试风险规则和风险管理器
"""

import pytest
from datetime import datetime
from src.core.events import OrderEvent
from src.risk.rules import (
    MaxPositionRule,
    MaxOrderSizeRule,
    StopLossRule,
    MaxDrawdownRule,
    CashReserveRule
)
from src.risk.manager import RiskManager


class TestMaxPositionRule:
    """最大仓位规则测试"""

    def test_pass(self):
        """测试通过"""
        rule = MaxPositionRule(max_position_pct=0.3)

        order = OrderEvent(
            symbol="AAPL",
            direction="BUY",
            quantity=100,
            price=150.0
        )

        portfolio = {
            "total_equity": 100000.0,
            "positions": {}
        }

        passed, reason = rule.check_order(order, portfolio)
        assert passed is True
        assert reason == ""

    def test_reject(self):
        """测试拒绝"""
        rule = MaxPositionRule(max_position_pct=0.2)

        order = OrderEvent(
            symbol="AAPL",
            direction="BUY",
            quantity=200,
            price=150.0
        )

        portfolio = {
            "total_equity": 100000.0,
            "positions": {}
        }

        passed, reason = rule.check_order(order, portfolio)
        assert passed is False
        assert "exceed" in reason.lower()

    def test_sell_always_pass(self):
        """测试卖出总是通过"""
        rule = MaxPositionRule(max_position_pct=0.1)

        order = OrderEvent(
            symbol="AAPL",
            direction="SELL",
            quantity=100,
            price=150.0
        )

        portfolio = {
            "total_equity": 100000.0,
            "positions": {}
        }

        passed, reason = rule.check_order(order, portfolio)
        assert passed is True


class TestMaxOrderSizeRule:
    """最大订单规模规则测试"""

    def test_pass(self):
        """测试通过"""
        rule = MaxOrderSizeRule(max_order_value=50000)

        order = OrderEvent(
            symbol="AAPL",
            direction="BUY",
            quantity=100,
            price=150.0
        )

        portfolio = {"total_equity": 100000.0}

        passed, reason = rule.check_order(order, portfolio)
        assert passed is True

    def test_reject(self):
        """测试拒绝"""
        rule = MaxOrderSizeRule(max_order_value=10000)

        order = OrderEvent(
            symbol="AAPL",
            direction="BUY",
            quantity=100,
            price=150.0
        )

        portfolio = {"total_equity": 100000.0}

        passed, reason = rule.check_order(order, portfolio)
        assert passed is False


class TestStopLossRule:
    """止损规则测试"""

    def test_no_position(self):
        """测试无持仓"""
        rule = StopLossRule(stop_loss_pct=0.05)

        order = OrderEvent(
            symbol="AAPL",
            direction="SELL",
            quantity=100,
            price=150.0
        )

        portfolio = {"positions": {}}

        passed, reason = rule.check_order(order, portfolio)
        assert passed is True

    def test_within_stop_loss(self):
        """测试未触发止损"""
        rule = StopLossRule(stop_loss_pct=0.05)

        order = OrderEvent(
            symbol="AAPL",
            direction="SELL",
            quantity=100,
            price=145.0
        )

        portfolio = {
            "positions": {
                "AAPL": {"avg_cost": 150.0}
            }
        }

        passed, reason = rule.check_order(order, portfolio)
        assert passed is True

    def test_trigger_stop_loss(self):
        """测试触发止损"""
        rule = StopLossRule(stop_loss_pct=0.05)

        order = OrderEvent(
            symbol="AAPL",
            direction="SELL",
            quantity=100,
            price=140.0
        )

        portfolio = {
            "positions": {
                "AAPL": {"avg_cost": 150.0}
            }
        }

        passed, reason = rule.check_order(order, portfolio)
        assert passed is False
        assert "stop loss" in reason.lower()


class TestMaxDrawdownRule:
    """最大回撤规则测试"""

    def test_pass(self):
        """测试通过"""
        rule = MaxDrawdownRule(max_drawdown_pct=0.1)

        order = OrderEvent(
            symbol="AAPL",
            direction="BUY",
            quantity=100,
            price=150.0
        )

        portfolio = {
            "total_equity": 95000.0,
            "peak_equity": 100000.0
        }

        passed, reason = rule.check_order(order, portfolio)
        assert passed is True

    def test_reject(self):
        """测试拒绝"""
        rule = MaxDrawdownRule(max_drawdown_pct=0.05)

        order = OrderEvent(
            symbol="AAPL",
            direction="BUY",
            quantity=100,
            price=150.0
        )

        portfolio = {
            "total_equity": 90000.0,
            "peak_equity": 100000.0
        }

        passed, reason = rule.check_order(order, portfolio)
        assert passed is False
        assert "drawdown" in reason.lower()


class TestCashReserveRule:
    """现金储备规则测试"""

    def test_pass(self):
        """测试通过"""
        rule = CashReserveRule(min_cash_pct=0.1)

        order = OrderEvent(
            symbol="AAPL",
            direction="BUY",
            quantity=100,
            price=150.0
        )

        portfolio = {
            "total_equity": 100000.0,
            "cash": 50000.0
        }

        passed, reason = rule.check_order(order, portfolio)
        assert passed is True

    def test_reject(self):
        """测试拒绝"""
        rule = CashReserveRule(min_cash_pct=0.2)

        order = OrderEvent(
            symbol="AAPL",
            direction="BUY",
            quantity=100,
            price=150.0
        )

        portfolio = {
            "total_equity": 100000.0,
            "cash": 20000.0
        }

        passed, reason = rule.check_order(order, portfolio)
        assert passed is False
        assert "cash reserve" in reason.lower()


class TestRiskManager:
    """风险管理器测试"""

    def test_check_order_pass(self):
        """测试订单通过"""
        manager = RiskManager()

        order = OrderEvent(
            symbol="AAPL",
            direction="BUY",
            quantity=10,
            price=150.0
        )

        portfolio = {
            "total_equity": 100000.0,
            "cash": 80000.0,
            "positions": {}
        }

        passed, reason = manager.check_order(order, portfolio)
        assert passed is True

    def test_check_order_reject(self):
        """测试订单拒绝"""
        manager = RiskManager()

        order = OrderEvent(
            symbol="AAPL",
            direction="BUY",
            quantity=1000,
            price=150.0
        )

        portfolio = {
            "total_equity": 100000.0,
            "cash": 80000.0,
            "positions": {}
        }

        passed, reason = manager.check_order(order, portfolio)
        assert passed is False

    def test_risk_events(self):
        """测试风险事件记录"""
        manager = RiskManager()

        order = OrderEvent(
            symbol="AAPL",
            direction="BUY",
            quantity=1000,
            price=150.0
        )

        portfolio = {
            "total_equity": 100000.0,
            "cash": 80000.0,
            "positions": {}
        }

        manager.check_order(order, portfolio)

        events = manager.get_risk_events()
        assert len(events) > 0

    def test_risk_summary(self):
        """测试风险摘要"""
        manager = RiskManager()

        summary = manager.get_risk_summary()

        assert "total_risk_events" in summary
        assert "peak_equity" in summary
        assert "rules_count" in summary
        assert "rules" in summary
        assert summary["rules_count"] > 0
