"""
因子挖掘框架 - 基础使用示例

演示因子挖掘的完整流程:
1. 生成模拟数据
2. 计算各类因子
3. 因子预处理 (标准化、去极值)
4. 因子评估 (IC、分组回测)
5. 因子组合
6. 组合回测
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

# 导入框架模块
from src.factors.technical import TechnicalFactors
from src.factors.alternative import AlternativeFactors
from src.optimization.standardizer import FactorStandardizer
from src.optimization.winsorizer import FactorWinsorizer
from src.evaluation.ic_analysis import ICAnalysis
from src.evaluation.group_backtest import GroupBacktest
from src.combination.equal_weight import EqualWeightCombination
from src.backtest.portfolio_backtest import PortfolioBacktest
from src.backtest.performance import PerformanceAnalyzer
from src.backtest.data_replay import DataReplay


def main():
    print("=" * 60)
    print("  因子挖掘框架 - 基础使用示例")
    print("=" * 60)

    # =========================================================================
    # 步骤 1: 生成模拟数据
    # =========================================================================
    print("\n[步骤 1] 生成模拟数据...")

    np.random.seed(42)
    n_days = 500
    n_stocks = 100

    dates = pd.bdate_range(start="2022-01-01", periods=n_days)
    stocks = [f"STOCK_{i:04d}" for i in range(n_stocks)]

    # 生成价格数据 (几何布朗运动)
    daily_returns = np.random.normal(0.0003, 0.02, (n_days, n_stocks))
    # 添加一些因子结构 (动量效应)
    momentum_factor = np.random.randn(n_stocks) * 0.001
    for t in range(1, n_days):
        daily_returns[t] += momentum_factor * 0.1

    prices = 100 * np.exp(np.cumsum(daily_returns, axis=0))

    price_df = pd.DataFrame(prices, index=dates, columns=stocks)
    return_df = price_df.pct_change()

    # 生成成交量数据
    volume_df = pd.DataFrame(
        np.random.lognormal(15, 0.5, (n_days, n_stocks)),
        index=dates, columns=stocks
    )

    print(f"  价格数据: {price_df.shape}")
    print(f"  日期范围: {dates[0].date()} ~ {dates[-1].date()}")

    # =========================================================================
    # 步骤 2: 计算技术因子
    # =========================================================================
    print("\n[步骤 2] 计算技术因子...")

    tf = TechnicalFactors()

    # 为每只股票计算因子
    factor_dict = {}
    for stock in stocks[:20]:  # 取前 20 只股票演示
        stock_data = pd.DataFrame({
            "close": price_df[stock],
            "volume": volume_df[stock],
        })
        stock_data["high"] = stock_data["close"] * (1 + abs(np.random.randn(n_days)) * 0.01)
        stock_data["low"] = stock_data["close"] * (1 - abs(np.random.randn(n_days)) * 0.01)

        factors = tf.compute_all(stock_data, windows=[5, 20])
        factor_dict[stock] = factors

    # 构造因子面板 (以 momentum_5d 为例)
    momentum_panel = pd.DataFrame({
        stock: factor_dict[stock]["momentum_5d"]
        for stock in factor_dict
    })

    volatility_panel = pd.DataFrame({
        stock: factor_dict[stock]["volatility_20d"]
        for stock in factor_dict
    })

    print(f"  计算了 {len(factor_dict)} 只股票的技术因子")
    print(f"  因子面板形状: {momentum_panel.shape}")

    # =========================================================================
    # 步骤 3: 因子预处理
    # =========================================================================
    print("\n[步骤 3] 因子预处理...")

    winsorizer = FactorWinsorizer()
    standardizer = FactorStandardizer()

    # 去极值
    momentum_winsorized = winsorizer.winsorize_panel(momentum_panel, method="mad")
    # 标准化
    momentum_standardized = standardizer.standardize_panel(momentum_winsorized, method="zscore")

    print(f"  去极值和标准化完成")

    # =========================================================================
    # 步骤 4: 因子评估
    # =========================================================================
    print("\n[步骤 4] 因子评估...")

    # IC 分析
    ic_analyzer = ICAnalysis()
    return_subset = return_df[stocks[:20]]

    ic_summary = ic_analyzer.compute_ic_summary(momentum_standardized, return_subset)
    print(f"  动量因子 IC 分析:")
    print(f"    IC 均值: {ic_summary['ic_mean']:.4f}")
    print(f"    IC_IR:   {ic_summary['ic_ir']:.4f}")
    print(f"    IC > 0:  {ic_summary['ic_pos_pct']:.2%}")

    # 分组回测
    group_bt = GroupBacktest(n_groups=5)
    group_result = group_bt.run(momentum_standardized, return_subset)
    print(f"\n  分组回测:")
    print(f"    单调性: {group_result['monotonicity']:.4f}")
    print(f"    多空年化收益: {group_result['group_stats'].loc[5, 'annualized_return'] - group_result['group_stats'].loc[1, 'annualized_return']:.2%}")

    # =========================================================================
    # 步骤 5: 因子组合
    # =========================================================================
    print("\n[步骤 5] 因子组合...")

    # 准备多个因子
    factor_df = pd.DataFrame({
        "momentum": momentum_standardized.stack(),
        "volatility": volatility_panel.stack(),
    })

    # 等权组合
    combined = EqualWeightCombination.combine(factor_df)

    # 还原为面板格式
    combined_panel = combined.unstack()
    print(f"  等权组合因子形状: {combined_panel.shape}")

    # =========================================================================
    # 步骤 6: 组合回测
    # =========================================================================
    print("\n[步骤 6] 组合回测...")

    portfolio_bt = PortfolioBacktest(top_n=10, rebalance_freq=20)
    bt_result = portfolio_bt.run(combined_panel, return_subset)

    # 性能分析
    analyzer = PerformanceAnalyzer()
    metrics = analyzer.compute_metrics(bt_result["portfolio_returns"])

    print(f"\n  组合回测结果:")
    print(f"    总收益率:   {metrics['total_return']:.2%}")
    print(f"    年化收益率: {metrics['annual_return']:.2%}")
    print(f"    夏普比率:   {metrics['sharpe_ratio']:.2f}")
    print(f"    最大回撤:   {metrics['max_drawdown']:.2%}")

    print("\n" + "=" * 60)
    print("  示例完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
