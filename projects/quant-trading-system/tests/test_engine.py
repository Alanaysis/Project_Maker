"""
回测引擎测试

⭐ 重点：测试回测引擎的核心功能
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.core.engine import BacktestEngine
from src.strategies.moving_average import MovingAverageStrategy
from src.data.generator import DataGenerator


class TestBacktestEngine:
    """回测引擎测试"""

    def test_initialization(self):
        """测试引擎初始化"""
        engine = BacktestEngine(
            initial_capital=100000.0,
            commission_rate=0.001,
            slippage_pct=0.001
        )

        assert engine.initial_capital == 100000.0
        assert engine.commission_rate == 0.001
        assert engine.slippage_pct == 0.001
        assert engine.is_running is False

    def test_add_strategy(self):
        """测试添加策略"""
        engine = BacktestEngine()
        strategy = MovingAverageStrategy(symbols=["AAPL"])

        engine.add_strategy(strategy)

        assert len(engine.strategies) == 1
        assert engine.strategies[0].name == "MA_Cross"

    def test_load_data(self):
        """测试加载数据"""
        engine = BacktestEngine()

        # 创建测试数据
        data = pd.DataFrame({
            "date": pd.date_range(start="2023-01-01", periods=100),
            "open": np.random.uniform(100, 110, 100),
            "high": np.random.uniform(110, 120, 100),
            "low": np.random.uniform(90, 100, 100),
            "close": np.random.uniform(100, 110, 100),
            "volume": np.random.randint(100000, 1000000, 100)
        })

        engine.load_data(data, "AAPL")

        assert "AAPL" in engine.data_loader.get_symbols()
        assert engine.data_loader.get_bar_count("AAPL") == 100

    def test_full_backtest(self):
        """测试完整回测"""
        engine = BacktestEngine(
            initial_capital=100000.0,
            commission_rate=0.001,
            slippage_pct=0.001
        )

        # 生成测试数据
        generator = DataGenerator(seed=42)
        data = generator.generate_gbm(
            symbol="AAPL",
            start_price=100.0,
            days=100,
            mu=0.1,
            sigma=0.2
        )

        # 加载数据
        engine.load_data(data, "AAPL")

        # 添加策略
        strategy = MovingAverageStrategy(
            symbols=["AAPL"],
            short_window=5,
            long_window=20
        )
        engine.add_strategy(strategy)

        # 运行回测
        results = engine.run()

        # 验证结果
        assert "initial_capital" in results
        assert "final_equity" in results
        assert "total_return" in results
        assert "max_drawdown" in results
        assert "total_trades" in results
        assert "win_rate" in results
        assert "equity_curve" in results

    def test_no_data(self):
        """测试无数据情况"""
        engine = BacktestEngine()
        strategy = MovingAverageStrategy(symbols=["AAPL"])
        engine.add_strategy(strategy)

        results = engine.run()

        assert results == {}

    def test_multiple_symbols(self):
        """测试多标的回测"""
        engine = BacktestEngine(initial_capital=200000.0)

        # 生成多标的数据
        generator = DataGenerator(seed=42)

        data1 = generator.generate_gbm(
            symbol="AAPL",
            start_price=100.0,
            days=50,
            mu=0.1,
            sigma=0.2
        )

        data2 = generator.generate_gbm(
            symbol="GOOG",
            start_price=200.0,
            days=50,
            mu=0.05,
            sigma=0.15
        )

        engine.load_data(data1, "AAPL")
        engine.load_data(data2, "GOOG")

        strategy = MovingAverageStrategy(
            symbols=["AAPL", "GOOG"],
            short_window=5,
            long_window=15
        )
        engine.add_strategy(strategy)

        results = engine.run()

        assert results["total_trades"] >= 0


class TestDataGenerator:
    """数据生成器测试"""

    def test_generate_gbm(self):
        """测试GBM数据生成"""
        generator = DataGenerator(seed=42)

        data = generator.generate_gbm(
            symbol="AAPL",
            start_price=100.0,
            days=100,
            mu=0.1,
            sigma=0.2
        )

        assert len(data) == 100
        assert "open" in data.columns
        assert "high" in data.columns
        assert "low" in data.columns
        assert "close" in data.columns
        assert "volume" in data.columns

        # 检查价格范围合理
        assert data["close"].min() > 0
        assert data["close"].max() < 1000

    def test_generate_multi_symbols(self):
        """测试多标的数据生成"""
        generator = DataGenerator(seed=42)

        data = generator.generate_multi_symbols(
            symbols=["AAPL", "GOOG", "MSFT"],
            days=50,
            correlation=0.5
        )

        assert len(data) == 150  # 3 symbols * 50 days
        assert data["symbol"].nunique() == 3

    def test_generate_trending_data(self):
        """测试趋势数据生成"""
        generator = DataGenerator(seed=42)

        # 上升趋势
        up_data = generator.generate_trending_data(
            symbol="AAPL",
            trend="up",
            days=100,
            start_price=100.0
        )

        # 下降趋势
        down_data = generator.generate_trending_data(
            symbol="AAPL",
            trend="down",
            days=100,
            start_price=100.0
        )

        # 检查趋势方向
        assert up_data["close"].iloc[-1] > up_data["close"].iloc[0]
        assert down_data["close"].iloc[-1] < down_data["close"].iloc[0]

    def test_reproducibility(self):
        """测试数据可重现性"""
        gen1 = DataGenerator(seed=42)
        gen2 = DataGenerator(seed=42)

        data1 = gen1.generate_gbm(symbol="AAPL", days=50)
        data2 = gen2.generate_gbm(symbol="AAPL", days=50)

        pd.testing.assert_frame_equal(data1, data2)
