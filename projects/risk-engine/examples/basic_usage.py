"""风险引擎基本使用示例

演示如何使用风险管理引擎进行 VaR 计算和压力测试。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from src import Portfolio, Position, VaRCalculator, StressTester, RiskReporter
from src.var_calculator import VaRMethod
from src.stress_tester import StressScenario


def main():
    # 1. 创建投资组合
    print("=" * 60)
    print("创建投资组合")
    print("=" * 60)

    portfolio = Portfolio("示例投资组合")
    portfolio.add_position(Position("AAPL", 1000, 150.0, "equity"))
    portfolio.add_position(Position("GOOGL", 500, 2800.0, "equity"))
    portfolio.add_position(Position("BND", 2000, 85.0, "bond"))
    portfolio.add_position(Position("GLD", 300, 180.0, "commodity"))

    print(f"组合名称: {portfolio.name}")
    print(f"组合市值: ${portfolio.total_value:,.2f}")
    print(f"持仓数量: {len(portfolio.positions)}")
    print("\n持仓详情:")
    for pos in portfolio.positions:
        print(f"  {pos.symbol}: {pos.quantity} 股 @ ${pos.current_price:.2f} "
              f"= ${pos.market_value:,.2f} ({portfolio.weights[pos.symbol]:.1%})")

    # 2. 生成模拟收益率数据
    print("\n" + "=" * 60)
    print("生成模拟收益率数据")
    print("=" * 60)

    np.random.seed(42)
    n_days = 252  # 一年

    # 模拟各资产的收益率
    returns_data = {
        "AAPL": np.random.normal(0.0008, 0.02, n_days),
        "GOOGL": np.random.normal(0.0006, 0.018, n_days),
        "BND": np.random.normal(0.0002, 0.005, n_days),
        "GLD": np.random.normal(0.0003, 0.012, n_days)
    }

    # 计算组合收益率
    import pandas as pd
    returns_df = pd.DataFrame(returns_data)
    portfolio_returns = portfolio.calculate_portfolio_returns(returns_df)

    print(f"收益率数据天数: {n_days}")
    print(f"组合平均日收益率: {np.mean(portfolio_returns):.4%}")
    print(f"组合日收益率标准差: {np.std(portfolio_returns):.4%}")

    # 3. VaR 计算
    print("\n" + "=" * 60)
    print("VaR 计算")
    print("=" * 60)

    var_calculator = VaRCalculator(portfolio.total_value)

    # 比较不同方法
    print("\n不同 VaR 方法比较 (95% 置信水平):")
    print("-" * 40)

    for method in VaRMethod:
        result = var_calculator.calculate(portfolio_returns, method)
        print(f"\n{method.value} 方法:")
        print(f"  VaR: {abs(result.var):.2%} (${result.var_amount:,.2f})")
        print(f"  CVaR: {abs(result.cvar):.2%} (${result.cvar_amount:,.2f})")

    # 不同置信水平
    print("\n不同置信水平 (历史模拟法):")
    print("-" * 40)

    confidence_levels = [0.90, 0.95, 0.99]
    results = var_calculator.calculate_multiple_confidence_levels(
        portfolio_returns, VaRMethod.HISTORICAL, confidence_levels
    )

    for result in results:
        level = f"{int(result.confidence_level * 100)}%"
        print(f"  {level}: VaR = {abs(result.var):.2%} (${result.var_amount:,.2f})")

    # 4. 压力测试
    print("\n" + "=" * 60)
    print("压力测试")
    print("=" * 60)

    # 计算资产类别权重
    weights = {
        "equity": sum(p.market_value for p in portfolio.positions if p.asset_class == "equity") / portfolio.total_value,
        "bond": sum(p.market_value for p in portfolio.positions if p.asset_class == "bond") / portfolio.total_value,
        "commodity": sum(p.market_value for p in portfolio.positions if p.asset_class == "commodity") / portfolio.total_value
    }

    print(f"\n资产类别权重: {weights}")

    stress_tester = StressTester(portfolio.total_value)

    # 历史情景压力测试
    print("\n历史情景压力测试:")
    print("-" * 40)

    for scenario_name in StressTester.HISTORICAL_SCENARIOS.keys():
        result = stress_tester.historical_stress_test(scenario_name, weights)
        print(f"\n{result.scenario.name}:")
        print(f"  损失: {abs(result.portfolio_loss):.2%} "
              f"(${abs(result.portfolio_loss_amount):,.2f})")

    # 自定义假设情景
    print("\n假设情景压力测试:")
    print("-" * 40)

    custom_scenario = StressScenario(
        name="市场大幅下跌",
        description="股市下跌 30%，债券上涨 5%",
        shocks={"equity": -0.30, "bond": 0.05, "commodity": -0.15}
    )

    result = stress_tester.hypothetical_stress_test(custom_scenario, weights)
    print(f"  {result.scenario.name}:")
    print(f"  损失: {abs(result.portfolio_loss):.2%} "
          f"(${abs(result.portfolio_loss_amount):,.2f})")

    # 反向压力测试
    print("\n反向压力测试:")
    print("-" * 40)

    reverse_scenario = stress_tester.reverse_stress_test(
        target_loss=-0.20,
        weights=weights,
        risk_factor="equity"
    )
    print(f"  要达到 20% 损失:")
    print(f"  {reverse_scenario.description}")

    # 5. 生成风险报告
    print("\n" + "=" * 60)
    print("风险报告")
    print("=" * 60)

    reporter = RiskReporter(portfolio, portfolio_returns, weights)
    report = reporter.generate_report()

    # 打印格式化报告
    print(reporter.format_text_report(report))

    print("\n风险分析完成!")


if __name__ == "__main__":
    main()
