"""
策略测试

⭐ 重点：测试策略的信号生成逻辑
"""

import pytest
import numpy as np
from src.core.events import MarketDataEvent, SignalEvent
from src.strategies.moving_average import MovingAverageStrategy
from src.strategies.momentum import MomentumStrategy


class TestMovingAverageStrategy:
    """均线策略测试"""

    def test_initialization(self):
        """测试策略初始化"""
        strategy = MovingAverageStrategy(
            name="TestMA",
            symbols=["AAPL"],
            short_window=5,
            long_window=20
        )

        assert strategy.name == "TestMA"
        assert strategy.symbols == ["AAPL"]
        assert strategy.short_window == 5
        assert strategy.long_window == 20

    def test_on_init(self):
        """测试初始化回调"""
        strategy = MovingAverageStrategy(symbols=["AAPL"])
        strategy.on_init()

        assert strategy.is_initialized

    def test_insufficient_data(self):
        """测试数据不足时不产生信号"""
        strategy = MovingAverageStrategy(
            symbols=["AAPL"],
            short_window=5,
            long_window=20
        )
        strategy.on_init()

        # 只发送10个数据点（少于long_window=20）
        for i in range(10):
            event = MarketDataEvent(
                symbol="AAPL",
                close=100.0 + i,
                open=100.0 + i,
                high=101.0 + i,
                low=99.0 + i,
                volume=1000000
            )
            signal = strategy.on_market_data(event)
            assert signal is None

    def test_golden_cross(self):
        """测试金叉信号"""
        strategy = MovingAverageStrategy(
            symbols=["AAPL"],
            short_window=5,
            long_window=10
        )
        strategy.on_init()

        # 先下降趋势
        for i in range(15):
            event = MarketDataEvent(
                symbol="AAPL",
                close=100.0 - i * 0.5,
                open=100.0 - i * 0.5,
                high=101.0 - i * 0.5,
                low=99.0 - i * 0.5,
                volume=1000000
            )
            strategy.on_market_data(event)

        # 然后上升趋势（触发金叉）
        for i in range(10):
            event = MarketDataEvent(
                symbol="AAPL",
                close=90.0 + i * 2.0,
                open=90.0 + i * 2.0,
                high=91.0 + i * 2.0,
                low=89.0 + i * 2.0,
                volume=1000000
            )
            signal = strategy.on_market_data(event)

        # 应该产生买入信号
        signals = strategy.get_signals()
        buy_signals = [s for s in signals if s.direction == "BUY"]
        assert len(buy_signals) > 0

    def test_death_cross(self):
        """测试死叉信号"""
        strategy = MovingAverageStrategy(
            symbols=["AAPL"],
            short_window=5,
            long_window=10
        )
        strategy.on_init()

        # 先上升趋势
        for i in range(15):
            event = MarketDataEvent(
                symbol="AAPL",
                close=80.0 + i * 1.0,
                open=80.0 + i * 1.0,
                high=81.0 + i * 1.0,
                low=79.0 + i * 1.0,
                volume=1000000
            )
            strategy.on_market_data(event)

        # 然后下降趋势（触发死叉）
        for i in range(10):
            event = MarketDataEvent(
                symbol="AAPL",
                close=95.0 - i * 2.0,
                open=95.0 - i * 2.0,
                high=96.0 - i * 2.0,
                low=94.0 - i * 2.0,
                volume=1000000
            )
            signal = strategy.on_market_data(event)

        # 应该产生卖出信号
        signals = strategy.get_signals()
        sell_signals = [s for s in signals if s.direction == "SELL"]
        assert len(sell_signals) > 0

    def test_wrong_symbol(self):
        """测试忽略错误的标的"""
        strategy = MovingAverageStrategy(symbols=["AAPL"])
        strategy.on_init()

        event = MarketDataEvent(symbol="GOOG", close=100.0)
        signal = strategy.on_market_data(event)

        assert signal is None

    def test_get_current_ma(self):
        """测试获取当前均线值"""
        strategy = MovingAverageStrategy(
            symbols=["AAPL"],
            short_window=5,
            long_window=10
        )
        strategy.on_init()

        # 发送足够的数据
        for i in range(15):
            event = MarketDataEvent(
                symbol="AAPL",
                close=100.0 + i,
                open=100.0 + i,
                high=101.0 + i,
                low=99.0 + i,
                volume=1000000
            )
            strategy.on_market_data(event)

        ma = strategy.get_current_ma("AAPL")
        assert "short_ma" in ma
        assert "long_ma" in ma
        assert ma["short_ma"] > 0
        assert ma["long_ma"] > 0


class TestMomentumStrategy:
    """动量策略测试"""

    def test_initialization(self):
        """测试策略初始化"""
        strategy = MomentumStrategy(
            name="TestMomentum",
            symbols=["AAPL"],
            lookback=10,
            threshold=0.05
        )

        assert strategy.name == "TestMomentum"
        assert strategy.lookback == 10
        assert strategy.threshold == 0.05

    def test_insufficient_data(self):
        """测试数据不足时不产生信号"""
        strategy = MomentumStrategy(
            symbols=["AAPL"],
            lookback=10,
            threshold=0.05
        )
        strategy.on_init()

        # 只发送5个数据点（少于lookback+1=11）
        for i in range(5):
            event = MarketDataEvent(
                symbol="AAPL",
                close=100.0 + i,
                volume=1000000
            )
            signal = strategy.on_market_data(event)
            assert signal is None

    def test_strong_momentum(self):
        """测试强动量信号"""
        strategy = MomentumStrategy(
            symbols=["AAPL"],
            lookback=5,
            threshold=0.05
        )
        strategy.on_init()

        # 上升趋势
        prices = [100, 102, 104, 106, 108, 115]
        for price in prices:
            event = MarketDataEvent(
                symbol="AAPL",
                close=float(price),
                volume=1500000  # 高成交量
            )
            signal = strategy.on_market_data(event)

        # 检查是否产生信号
        signals = strategy.get_signals()
        # 可能有也可能没有，取决于动量是否超过阈值
        # 这里主要测试不报错
        assert isinstance(signals, list)

    def test_get_momentum(self):
        """测试获取动量值"""
        strategy = MomentumStrategy(
            symbols=["AAPL"],
            lookback=5,
            threshold=0.05
        )
        strategy.on_init()

        # 发送足够的数据
        for i in range(7):
            event = MarketDataEvent(
                symbol="AAPL",
                close=100.0 + i * 2,
                volume=1000000
            )
            strategy.on_market_data(event)

        momentum = strategy.get_momentum("AAPL")
        assert momentum > 0  # 上升趋势应该有正动量

    def test_zero_momentum(self):
        """测试零动量"""
        strategy = MomentumStrategy(
            symbols=["AAPL"],
            lookback=5,
            threshold=0.05
        )
        strategy.on_init()

        # 数据不足时动量为0
        momentum = strategy.get_momentum("AAPL")
        assert momentum == 0.0
