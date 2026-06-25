"""
因子挖掘框架 - 高级使用示例

演示高级功能:
1. 多因子对比分析
2. ML 因子组合
3. 因子库管理
4. 因子监控
5. 生成报告
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

from src.factors.technical import TechnicalFactors
from src.factors.alternative import AlternativeFactors
from src.optimization.standardizer import FactorStandardizer
from src.optimization.winsorizer import FactorWinsorizer
from src.optimization.neutralizer import FactorNeutralizer
from src.evaluation.ic_analysis import ICAnalysis
from src.evaluation.ir_analysis import IRAnalysis
from src.evaluation.decay_analysis import DecayAnalysis
from src.combination.ml_combination import MLCombination
from src.app.factor_library import FactorLibrary
from src.app.factor_monitor import FactorMonitor
from src.app.factor_report import FactorReport


def main():
    print("=" * 60)
    print("  因子挖掘框架 - 高级使用示例")
    print("=" * 60)

    np.random.seed(42)
    n_days = 500
    n_stocks = 50

    dates = pd.bdate_range(start="2022-01-01", periods=n_days)
    stocks = [f"STOCK_{i:04d}" for i in range(n_stocks)]

    # 生成模拟数据
    daily_returns = np.random.normal(0.0003, 0.02, (n_days, n_stocks))
    prices = 100 * np.exp(np.cumsum(daily_returns, axis=0))
    price_df = pd.DataFrame(prices, index=dates, columns=stocks)
    return_df = price_df.pct_change()
    volume_df = pd.DataFrame(
        np.random.lognormal(15, 0.5, (n_days, n_stocks)),
        index=dates, columns=stocks
    )

    # =========================================================================
    # 1. 多因子计算和对比
    # =========================================================================
    print("\n[1] 多因子计算和对比...")

    tf = TechnicalFactors()
    af = AlternativeFactors()

    # 计算多个因子面板
    factor_panels = {}
    for stock in stocks:
        stock_data = pd.DataFrame({
            "close": price_df[stock],
            "volume": volume_df[stock],
        })
        stock_data["high"] = stock_data["close"] * 1.01
        stock_data["low"] = stock_data["close"] * 0.99

        factors = tf.compute_all(stock_data, windows=[5, 20])
        alt_factors = af.compute_all(stock_data)

        for col in ["momentum_5d", "momentum_20d", "volatility_20d", "rsi_14"]:
            if col not in factor_panels:
                factor_panels[col] = {}
            factor_panels[col][stock] = factors[col]

        for col in ["reversal_5d", "skewness_20d"]:
            if col not in factor_panels:
                factor_panels[col] = {}
            factor_panels[col][stock] = alt_factors[col]

    # 转为 DataFrame
    for col in factor_panels:
        factor_panels[col] = pd.DataFrame(factor_panels[col])

    # 多因子 IC 对比
    ir_analyzer = IRAnalysis()
    ic_dict = {}
    for col, panel in factor_panels.items():
        ic_series = ICAnalysis.compute_ic_series(panel, return_df[stocks])
        ic_dict[col] = ic_series

    comparison = ir_analyzer.multi_factor_ir_comparison(ic_dict)
    print("\n  多因子 IC 对比:")
    print(comparison.to_string(index=False))

    # =========================================================================
    # 2. 因子中性化
    # =========================================================================
    print("\n\n[2] 因子中性化...")

    # 生成行业数据
    industries = np.random.choice(["科技", "金融", "消费", "医药", "制造"], n_stocks)
    industry_series = pd.Series(industries, index=stocks)
    market_cap = pd.Series(np.random.lognormal(23, 1, n_stocks), index=stocks)

    neutralizer = FactorNeutralizer()
    momentum_panel = factor_panels["momentum_5d"]
    last_date = momentum_panel.index[-1]

    neutral_factor = neutralizer.neutralize(
        momentum_panel.loc[last_date],
        industry_series,
        market_cap
    )
    print(f"  中性化前因子均值: {momentum_panel.loc[last_date].mean():.4f}")
    print(f"  中性化后因子均值: {neutral_factor.mean():.4f}")

    # =========================================================================
    # 3. IC 衰减分析
    # =========================================================================
    print("\n\n[3] IC 衰减分析...")

    decay_analyzer = DecayAnalysis()
    decay_df = decay_analyzer.ic_decay_by_horizon(
        factor_panels["momentum_5d"], return_df[stocks], max_horizon=20
    )
    half_life = decay_analyzer.estimate_half_life(decay_df)
    optimal_holding = decay_analyzer.optimal_holding_period(decay_df)
    persistence = decay_analyzer.factor_persistence_score(decay_df)

    print(f"  半衰期: {half_life} 天")
    print(f"  最优持仓期: {optimal_holding} 天")
    print(f"  持续性评分: {persistence:.4f}")

    # =========================================================================
    # 4. ML 因子组合
    # =========================================================================
    print("\n\n[4] ML 因子组合...")

    # 准备因子 DataFrame
    factor_df = pd.DataFrame({
        col: panel.stack()
        for col, panel in factor_panels.items()
    })
    forward_returns = return_df[stocks].shift(-1).stack()
    forward_returns.index = factor_df.index

    # 交叉验证
    cv_results = MLCombination.cross_validate(
        factor_df, forward_returns, n_splits=3, model_type="ridge"
    )
    print(f"  交叉验证 IC: {cv_results['cv_ic_mean']:.4f}")
    print(f"  交叉验证 IR: {cv_results['cv_ir']:.4f}")

    # =========================================================================
    # 5. 因子监控
    # =========================================================================
    print("\n\n[5] 因子监控...")

    monitor = FactorMonitor()
    ic_series = ic_dict["momentum_5d"]

    status = monitor.check_health(
        "momentum_5d",
        ic_series,
        factor_panels["momentum_5d"]
    )
    print(f"  因子状态: {status['status']}")
    print(f"  告警数量: {len(status['alerts'])}")

    # =========================================================================
    # 6. 生成报告
    # =========================================================================
    print("\n\n[6] 生成报告...")

    report = FactorReport("动量因子分析报告")
    report.add_factor_overview(
        "momentum_5d", "technical", "5日动量因子",
        {"ic_mean": ic_dict["momentum_5d"].mean()}
    )
    report.add_ic_analysis(ICAnalysis.compute_ic_summary(
        factor_panels["momentum_5d"], return_df[stocks]
    ))

    report_text = report.generate_text()
    print(report_text[:500] + "...")

    print("\n" + "=" * 60)
    print("  高级示例完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
