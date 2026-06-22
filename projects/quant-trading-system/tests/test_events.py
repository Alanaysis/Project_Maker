"""
事件系统测试

⭐ 重点：测试事件驱动架构的核心功能
"""

import pytest
from datetime import datetime
from src.core.events import (
    EventBus, EventType, Event,
    MarketDataEvent, SignalEvent, OrderEvent, FillEvent
)


class TestEventBus:
    """事件总线测试"""

    def test_subscribe_and_publish(self):
        """测试订阅和发布"""
        bus = EventBus()
        received_events = []

        def handler(event):
            received_events.append(event)

        bus.subscribe(EventType.MARKET_DATA, handler)

        event = MarketDataEvent(symbol="AAPL", close=150.0)
        bus.publish(event)
        bus.process_events()

        assert len(received_events) == 1
        assert received_events[0].symbol == "AAPL"

    def test_multiple_handlers(self):
        """测试多个处理器"""
        bus = EventBus()
        results = []

        def handler1(event):
            results.append("handler1")

        def handler2(event):
            results.append("handler2")

        bus.subscribe(EventType.MARKET_DATA, handler1)
        bus.subscribe(EventType.MARKET_DATA, handler2)

        bus.publish(MarketDataEvent())
        bus.process_events()

        assert "handler1" in results
        assert "handler2" in results

    def test_unsubscribe(self):
        """测试取消订阅"""
        bus = EventBus()
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe(EventType.MARKET_DATA, handler)
        bus.unsubscribe(EventType.MARKET_DATA, handler)

        bus.publish(MarketDataEvent())
        bus.process_events()

        assert len(received) == 0

    def test_event_filtering(self):
        """测试事件过滤"""
        bus = EventBus()
        market_events = []
        signal_events = []

        def market_handler(event):
            market_events.append(event)

        def signal_handler(event):
            signal_events.append(event)

        bus.subscribe(EventType.MARKET_DATA, market_handler)
        bus.subscribe(EventType.SIGNAL, signal_handler)

        bus.publish(MarketDataEvent())
        bus.publish(SignalEvent())
        bus.process_events()

        assert len(market_events) == 1
        assert len(signal_events) == 1

    def test_pending_count(self):
        """测试待处理事件数量"""
        bus = EventBus()

        assert bus.pending_count == 0

        bus.publish(MarketDataEvent())
        assert bus.pending_count == 1

        bus.publish(SignalEvent())
        assert bus.pending_count == 2

        bus.process_events()
        assert bus.pending_count == 0


class TestMarketDataEvent:
    """市场数据事件测试"""

    def test_creation(self):
        """测试创建市场数据事件"""
        event = MarketDataEvent(
            symbol="AAPL",
            open=150.0,
            high=155.0,
            low=149.0,
            close=153.0,
            volume=1000000
        )

        assert event.symbol == "AAPL"
        assert event.open == 150.0
        assert event.high == 155.0
        assert event.low == 149.0
        assert event.close == 153.0
        assert event.volume == 1000000
        assert event.event_type == EventType.MARKET_DATA

    def test_default_values(self):
        """测试默认值"""
        event = MarketDataEvent()

        assert event.symbol == ""
        assert event.open == 0.0
        assert event.close == 0.0


class TestSignalEvent:
    """信号事件测试"""

    def test_creation(self):
        """测试创建信号事件"""
        event = SignalEvent(
            symbol="AAPL",
            direction="BUY",
            strength=0.8,
            strategy_name="MA_Cross"
        )

        assert event.symbol == "AAPL"
        assert event.direction == "BUY"
        assert event.strength == 0.8
        assert event.strategy_name == "MA_Cross"


class TestOrderEvent:
    """订单事件测试"""

    def test_creation(self):
        """测试创建订单事件"""
        event = OrderEvent(
            symbol="AAPL",
            direction="BUY",
            order_type="MARKET",
            quantity=100,
            price=150.0,
            order_id="test-001"
        )

        assert event.symbol == "AAPL"
        assert event.direction == "BUY"
        assert event.order_type == "MARKET"
        assert event.quantity == 100
        assert event.price == 150.0
        assert event.order_id == "test-001"
        assert event.status == "PENDING"


class TestFillEvent:
    """成交事件测试"""

    def test_creation(self):
        """测试创建成交事件"""
        event = FillEvent(
            symbol="AAPL",
            direction="BUY",
            quantity=100,
            fill_price=150.5,
            commission=15.05,
            order_id="test-001"
        )

        assert event.symbol == "AAPL"
        assert event.direction == "BUY"
        assert event.quantity == 100
        assert event.fill_price == 150.5
        assert event.commission == 15.05
        assert event.order_id == "test-001"
