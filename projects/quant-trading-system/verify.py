"""
项目验证脚本

⭐ 重点：验证项目是否可以正常运行
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试所有模块是否可以导入"""
    print("Testing imports...")

    try:
        from src.core.events import EventBus, EventType, MarketDataEvent
        print("  ✓ events module")
    except Exception as e:
        print(f"  ✗ events module: {e}")
        return False

    try:
        from src.core.portfolio import Portfolio, Position
        print("  ✓ portfolio module")
    except Exception as e:
        print(f"  ✗ portfolio module: {e}")
        return False

    try:
        from src.core.engine import BacktestEngine
        print("  ✓ engine module")
    except Exception as e:
        print(f"  ✗ engine module: {e}")
        return False

    try:
        from src.strategies.base import Strategy
        print("  ✓ strategy base module")
    except Exception as e:
        print(f"  ✗ strategy base module: {e}")
        return False

    try:
        from src.strategies.moving_average import MovingAverageStrategy
        print("  ✓ moving average strategy")
    except Exception as e:
        print(f"  ✗ moving average strategy: {e}")
        return False

    try:
        from src.strategies.momentum import MomentumStrategy
        print("  ✓ momentum strategy")
    except Exception as e:
        print(f"  ✗ momentum strategy: {e}")
        return False

    try:
        from src.data.loader import DataLoader
        print("  ✓ data loader")
    except Exception as e:
        print(f"  ✗ data loader: {e}")
        return False

    try:
        from src.data.generator import DataGenerator
        print("  ✓ data generator")
    except Exception as e:
        print(f"  ✗ data generator: {e}")
        return False

    try:
        from src.risk.manager import RiskManager
        print("  ✓ risk manager")
    except Exception as e:
        print(f"  ✗ risk manager: {e}")
        return False

    try:
        from src.risk.rules import RiskRule, MaxPositionRule
        print("  ✓ risk rules")
    except Exception as e:
        print(f"  ✗ risk rules: {e}")
        return False

    try:
        from src.utils.logger import TradingLogger
        print("  ✓ logger")
    except Exception as e:
        print(f"  ✗ logger: {e}")
        return False

    return True


def test_basic_functionality():
    """测试基本功能"""
    print("\nTesting basic functionality...")

    try:
        from src.core.events import EventBus, EventType, MarketDataEvent
        from src.core.portfolio import Portfolio
        from src.core.engine import BacktestEngine
        from src.strategies.moving_average import MovingAverageStrategy
        from src.data.generator import DataGenerator

        # 测试事件总线
        bus = EventBus()
        received = []
        bus.subscribe(EventType.MARKET_DATA, lambda e: received.append(e))
        bus.publish(MarketDataEvent(symbol="TEST", close=100.0))
        bus.process_events()
        assert len(received) == 1
        print("  ✓ EventBus works")

        # 测试投资组合
        portfolio = Portfolio(initial_capital=100000.0)
        assert portfolio.total_equity == 100000.0
        print("  ✓ Portfolio works")

        # 测试数据生成器
        generator = DataGenerator(seed=42)
        data = generator.generate_gbm(symbol="TEST", days=100)
        assert len(data) == 100
        print("  ✓ DataGenerator works")

        # 测试策略
        strategy = MovingAverageStrategy(symbols=["TEST"])
        strategy.on_init()
        assert strategy.is_initialized
        print("  ✓ Strategy works")

        # 测试回测引擎
        engine = BacktestEngine(initial_capital=100000.0)
        engine.load_data(data, "TEST")
        engine.add_strategy(strategy)
        results = engine.run()
        assert "total_return" in results
        print("  ✓ BacktestEngine works")

        return True

    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_backtest():
    """测试完整回测"""
    print("\nTesting full backtest...")

    try:
        from src.core.engine import BacktestEngine
        from src.strategies.moving_average import MovingAverageStrategy
        from src.strategies.momentum import MomentumStrategy
        from src.data.generator import DataGenerator

        # 创建引擎
        engine = BacktestEngine(initial_capital=100000.0)

        # 生成数据
        generator = DataGenerator(seed=42)
        data = generator.generate_gbm(
            symbol="AAPL",
            start_price=100.0,
            days=252,
            mu=0.15,
            sigma=0.25
        )

        # 加载数据
        engine.load_data(data, "AAPL")

        # 创建策略
        strategy = MovingAverageStrategy(
            name="TestMA",
            symbols=["AAPL"],
            short_window=10,
            long_window=30
        )

        # 添加策略并运行
        engine.add_strategy(strategy)
        results = engine.run()

        # 验证结果
        assert "initial_capital" in results
        assert "final_equity" in results
        assert "total_return" in results
        assert "max_drawdown" in results
        assert "total_trades" in results

        print(f"  ✓ Backtest completed")
        print(f"    - Total Return: {results['total_return']:.2%}")
        print(f"    - Max Drawdown: {results['max_drawdown']:.2%}")
        print(f"    - Total Trades: {results['total_trades']}")

        return True

    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("Quantitative Trading System - Verification")
    print("=" * 60)

    # 测试导入
    if not test_imports():
        print("\n❌ Import tests failed!")
        return 1

    # 测试基本功能
    if not test_basic_functionality():
        print("\n❌ Basic functionality tests failed!")
        return 1

    # 测试完整回测
    if not test_full_backtest():
        print("\n❌ Full backtest tests failed!")
        return 1

    print("\n" + "=" * 60)
    print("✅ All verification tests passed!")
    print("=" * 60)
    print("\nThe project is ready to use!")
    print("\nTo run the example backtest:")
    print("  python examples/run_backtest.py")
    print("\nTo run all tests:")
    print("  python run_tests.py")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
