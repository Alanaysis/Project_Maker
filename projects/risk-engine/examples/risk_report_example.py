"""风险报告生成示例

演示如何生成完整的风险报告。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from src import Portfolio, Position, RiskReporter


def main():
    # 1. 创建投资组合
    print("创建投资组合...")

    portfolio = Portfolio("示例基金")
    portfolio.add_position(Position("AAPL", 2000, 150.0, "equity"))
    portfolio.add_position(Position("MSFT", 1500, 350.0, "equity"))
    portfolio.add_position(Position("GOOGL", 800, 2800.0, "equity"))
    portfolio.add_position(Position("AMZN", 600, 3300.0, "equity"))
    portfolio.add_position(Position("BND", 5000, 85.0, "bond"))
    portfolio.add_position(Position("TLT", 3000, 100.0, "bond"))
    portfolio.add_position(Position("GLD", 1000, 180.0, "commodity"))
    portfolio.add_position(Position("SLV", 2000, 22.0, "commodity"))

    print(f"组合名称: {portfolio.name}")
    print(f"组合市值: ${portfolio.total_value:,.2f}")
    print(f"持仓数量: {len(portfolio.positions)}")

    # 2. 生成模拟收益率数据
    print("\n生成模拟收益率数据...")

    np.random.seed(42)
    n_days = 252 * 3  # 3年

    # 模拟各资产的收益率（带相关性）
    # 首先生成相关的随机数
    n_assets = len(portfolio.symbols)
    correlation_matrix = np.array([
        # AAPL  MSFT  GOOGL AMZN  BND   TLT   GLD   SLV
        [1.00, 0.80, 0.75, 0.70, 0.10, 0.05, 0.05, 0.08],  # AAPL
        [0.80, 1.00, 0.70, 0.65, 0.15, 0.10, 0.08, 0.10],  # MSFT
        [0.75, 0.70, 1.00, 0.75, 0.08, 0.03, 0.06, 0.09],  # GOOGL
        [0.70, 0.65, 0.75, 1.00, 0.12, 0.07, 0.10, 0.12],  # AMZN
        [0.10, 0.15, 0.08, 0.12, 1.00, 0.90, 0.20, 0.15],  # BND
        [0.05, 0.10, 0.03, 0.07, 0.90, 1.00, 0.25, 0.18],  # TLT
        [0.05, 0.08, 0.06, 0.10, 0.20, 0.25, 1.00, 0.85],  # GLD
        [0.08, 0.10, 0.09, 0.12, 0.15, 0.18, 0.85, 1.00],  # SLV
    ])

    # Cholesky 分解
    L = np.linalg.cholesky(correlation_matrix)

    # 生成独立随机数
    z = np.random.randn(n_days, n_assets)

    # 生成相关的随机数
    correlated_z = z @ L.T

    # 转换为收益率
    mu = np.array([0.0008, 0.0007, 0.0006, 0.0009, 0.0002, 0.0001, 0.0003, 0.0002])
    sigma = np.array([0.02, 0.018, 0.022, 0.025, 0.005, 0.008, 0.012, 0.018])

    returns_data = {}
    for i, symbol in enumerate(portfolio.symbols):
        returns_data[symbol] = mu[i] + sigma[i] * correlated_z[:, i]

    returns_df = pd.DataFrame(returns_data)

    # 计算组合收益率
    portfolio_returns = portfolio.calculate_portfolio_returns(returns_df)

    print(f"数据期间: {n_days} 个交易日 ({n_days/252:.1f} 年)")
    print(f"组合年化收益率: {np.mean(portfolio_returns) * 252:.2%}")
    print(f"组合年化波动率: {np.std(portfolio_returns) * np.sqrt(252):.2%}")

    # 3. 计算资产类别权重
    weights = {
        "equity": sum(p.market_value for p in portfolio.positions if p.asset_class == "equity") / portfolio.total_value,
        "bond": sum(p.market_value for p in portfolio.positions if p.asset_class == "bond") / portfolio.total_value,
        "commodity": sum(p.market_value for p in portfolio.positions if p.asset_class == "commodity") / portfolio.total_value
    }

    print(f"\n资产类别权重: {weights}")

    # 4. 生成风险报告
    print("\n生成风险报告...")

    reporter = RiskReporter(portfolio, portfolio_returns, weights)
    report = reporter.generate_report(
        confidence_levels=[0.90, 0.95, 0.99],
        scenarios=["2008_financial_crisis", "2020_covid", "2000_dotcom", "black_monday"]
    )

    # 5. 打印报告
    print("\n" + reporter.format_text_report(report))

    # 6. 导出报告数据
    print("\n导出报告数据...")
    report_dict = report.to_dict()

    print(f"报告包含:")
    print(f"  - VaR 分析: {len(report.var_results)} 个置信水平")
    print(f"  - 压力测试: {len(report.stress_test_results)} 个情景")
    print(f"  - 风险等级: {report.summary['risk_level']}")

    # 显示关键指标
    print("\n关键风险指标:")
    print("-" * 40)

    var_summary = report.summary['var_summary']
    for level, metrics in var_summary.items():
        print(f"\n{level} 置信水平:")
        print(f"  VaR: {metrics['var']} ({metrics['var_amount']})")
        print(f"  CVaR: {metrics['cvar']} ({metrics['cvar_amount']})")

    print("\n压力测试摘要:")
    print("-" * 40)
    stress_summary = report.summary['stress_test_summary']
    for scenario, metrics in stress_summary.items():
        print(f"  {scenario}: {metrics['loss']} ({metrics['loss_amount']})")

    print("\n报告生成完成!")


if __name__ == "__main__":
    main()
