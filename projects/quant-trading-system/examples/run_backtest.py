"""
回测示例 - 运行一个完整的策略回测

⭐ 重点：这个示例展示了量化交易系统的完整流程
1. 生成模拟数据
2. 创建策略
3. 配置引擎
4. 运行回测
5. 分析结果

💡 值得思考：
- 如何选择策略参数？
- 如何评估回测结果？
- 如何避免过拟合？
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.engine import BacktestEngine
from src.strategies.moving_average import MovingAverageStrategy
from src.strategies.momentum import MomentumStrategy
from src.data.generator import DataGenerator
from src.utils.logger import logger


def run_simple_backtest():
    """
    运行简单的均线策略回测

    ⭐ 重点：这是最基本的回测示例
    """
    logger.info("=" * 60)
    logger.info("Running Simple Moving Average Backtest")
    logger.info("=" * 60)

    # 1. 创建数据生成器
    generator = DataGenerator(seed=42)

    # 2. 生成模拟数据
    data = generator.generate_gbm(
        symbol="AAPL",
        start_price=100.0,
        days=252,  # 一年的交易日
        mu=0.15,   # 15% 年化收益率
        sigma=0.25  # 25% 年化波动率
    )

    logger.info(f"Generated {len(data)} bars of data")
    logger.info(f"Price range: {data['close'].min():.2f} - {data['close'].max():.2f}")

    # 3. 创建引擎
    engine = BacktestEngine(
        initial_capital=100000.0,
        commission_rate=0.001,  # 0.1% 手续费
        slippage_pct=0.001     # 0.1% 滑点
    )

    # 4. 加载数据
    engine.load_data(data, "AAPL")

    # 5. 创建策略
    strategy = MovingAverageStrategy(
        name="MA_Cross",
        symbols=["AAPL"],
        short_window=10,
        long_window=30
    )

    # 6. 添加策略
    engine.add_strategy(strategy)

    # 7. 运行回测
    results = engine.run()

    return results


def run_momentum_backtest():
    """
    运行动量策略回测

    💡 值得思考：动量策略和均线策略哪个更好？
    """
    logger.info("=" * 60)
    logger.info("Running Momentum Strategy Backtest")
    logger.info("=" * 60)

    # 1. 生成数据
    generator = DataGenerator(seed=42)
    data = generator.generate_gbm(
        symbol="TSLA",
        start_price=200.0,
        days=252,
        mu=0.2,
        sigma=0.4  # 高波动率
    )

    # 2. 创建引擎
    engine = BacktestEngine(
        initial_capital=100000.0,
        commission_rate=0.001,
        slippage_pct=0.002
    )

    # 3. 加载数据
    engine.load_data(data, "TSLA")

    # 4. 创建策略
    strategy = MomentumStrategy(
        name="Momentum",
        symbols=["TSLA"],
        lookback=10,
        threshold=0.08
    )

    # 5. 添加策略并运行
    engine.add_strategy(strategy)
    results = engine.run()

    return results


def run_multi_symbol_backtest():
    """
    运行多标的回测

    ⭐ 重点：多标的回测展示组合管理
    """
    logger.info("=" * 60)
    logger.info("Running Multi-Symbol Backtest")
    logger.info("=" * 60)

    # 1. 生成多标的数据
    generator = DataGenerator(seed=42)
    data = generator.generate_multi_symbols(
        symbols=["AAPL", "GOOG", "MSFT"],
        days=252,
        correlation=0.3
    )

    # 2. 创建引擎
    engine = BacktestEngine(
        initial_capital=300000.0,
        commission_rate=0.001,
        slippage_pct=0.001
    )

    # 3. 为每个标的加载数据
    for symbol in ["AAPL", "GOOG", "MSFT"]:
        symbol_data = data[data["symbol"] == symbol].reset_index(drop=True)
        engine.load_data(symbol_data, symbol)

    # 4. 创建策略
    strategy = MovingAverageStrategy(
        name="Multi_MA",
        symbols=["AAPL", "GOOG", "MSFT"],
        short_window=10,
        long_window=30
    )

    # 5. 运行回测
    engine.add_strategy(strategy)
    results = engine.run()

    return results


def analyze_results(results, strategy_name):
    """
    分析回测结果

    💡 值得思考：如何全面评估一个策略？
    """
    if not results:
        logger.error(f"{strategy_name}: No results to analyze")
        return

    logger.info("")
    logger.info("=" * 60)
    logger.info(f"{strategy_name} Analysis")
    logger.info("=" * 60)

    # 基本指标
    logger.info(f"Initial Capital: ${results['initial_capital']:,.2f}")
    logger.info(f"Final Equity: ${results['final_equity']:,.2f}")
    logger.info(f"Total Return: {results['total_return']:.2%}")
    logger.info(f"Annualized Return: {results['annualized_return']:.2%}")
    logger.info(f"Max Drawdown: {results['max_drawdown']:.2%}")
    logger.info(f"Total Trades: {results['total_trades']}")
    logger.info(f"Win Rate: {results['win_rate']:.2%}")

    # 风险摘要
    risk_summary = results.get("risk_summary", {})
    logger.info(f"Risk Events: {risk_summary.get('total_risk_events', 0)}")

    logger.info("=" * 60)


def main():
    """主函数"""
    logger.info("Quantitative Trading System - Backtest Examples")
    logger.info("=" * 60)

    # 运行均线策略回测
    results1 = run_simple_backtest()
    analyze_results(results1, "Simple Moving Average")

    # 运行动量策略回测
    results2 = run_momentum_backtest()
    analyze_results(results2, "Momentum Strategy")

    # 运行多标的回测
    results3 = run_multi_symbol_backtest()
    analyze_results(results3, "Multi-Symbol MA")

    logger.info("")
    logger.info("All backtests completed!")


if __name__ == "__main__":
    main()
