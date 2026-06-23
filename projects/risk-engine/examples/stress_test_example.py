"""压力测试详细示例

演示压力测试的各种用法。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from src import Portfolio, Position, StressTester
from src.stress_tester import StressScenario


def main():
    # 创建投资组合
    portfolio = Portfolio("压力测试示例组合")
    portfolio.add_position(Position("SPY", 1000, 450.0, "equity"))
    portfolio.add_position(Position("QQQ", 500, 380.0, "equity"))
    portfolio.add_position(Position("TLT", 2000, 100.0, "bond"))
    portfolio.add_position(Position("GLD", 500, 180.0, "commodity"))

    print("投资组合:")
    print(f"  总市值: ${portfolio.total_value:,.2f}")

    # 计算资产类别权重
    weights = {
        "equity": sum(p.market_value for p in portfolio.positions if p.asset_class == "equity") / portfolio.total_value,
        "bond": sum(p.market_value for p in portfolio.positions if p.asset_class == "bond") / portfolio.total_value,
        "commodity": sum(p.market_value for p in portfolio.positions if p.asset_class == "commodity") / portfolio.total_value
    }

    print(f"  资产权重: {weights}")

    tester = StressTester(portfolio.total_value)

    # 1. 历史情景压力测试
    print("\n" + "=" * 60)
    print("1. 历史情景压力测试")
    print("=" * 60)

    for scenario_name, scenario in StressTester.HISTORICAL_SCENARIOS.items():
        result = tester.historical_stress_test(scenario_name, weights)
        print(f"\n{scenario.name}:")
        print(f"  {scenario.description}")
        print(f"  冲击: {scenario.shocks}")
        print(f"  组合损失: {abs(result.portfolio_loss):.2%}")
        print(f"  损失金额: ${abs(result.portfolio_loss_amount):,.2f}")

    # 2. 自定义假设情景
    print("\n" + "=" * 60)
    print("2. 自定义假设情景")
    print("=" * 60)

    scenarios = [
        StressScenario(
            name="温和下跌",
            description="股市下跌 10%",
            shocks={"equity": -0.10, "bond": 0.02, "commodity": -0.05}
        ),
        StressScenario(
            name="中度下跌",
            description="股市下跌 20%",
            shocks={"equity": -0.20, "bond": 0.05, "commodity": -0.10}
        ),
        StressScenario(
            name="严重下跌",
            description="股市下跌 30%",
            shocks={"equity": -0.30, "bond": 0.08, "commodity": -0.20}
        ),
        StressScenario(
            name="极端下跌",
            description="股市下跌 40%",
            shocks={"equity": -0.40, "bond": 0.10, "commodity": -0.25}
        )
    ]

    results = tester.run_multiple_scenarios(scenarios, weights)

    print("\n不同冲击水平的影响:")
    print("-" * 40)
    for result in results:
        print(f"{result.scenario.name}: {abs(result.portfolio_loss):.2%} "
              f"(${abs(result.portfolio_loss_amount):,.2f})")

    # 3. 反向压力测试
    print("\n" + "=" * 60)
    print("3. 反向压力测试")
    print("=" * 60)

    target_losses = [-0.10, -0.20, -0.30, -0.40]

    print("\n要达到不同损失水平，股市需要下跌:")
    print("-" * 40)
    for target in target_losses:
        scenario = tester.reverse_stress_test(target, weights, "equity")
        print(f"  {abs(target):.0%} 损失 → 股市下跌 {abs(scenario.shocks['equity']):.1%}")

    # 4. 敏感性分析
    print("\n" + "=" * 60)
    print("4. 敏感性分析")
    print("=" * 60)

    print("\n股市不同涨跌幅对组合的影响:")
    print("-" * 40)

    sensitivity = tester.sensitivity_analysis(
        weights, "equity", shock_range=(-0.50, 0.30), num_steps=9
    )

    for shock, loss in sensitivity:
        print(f"  股市 {shock:+.0%} → 组合 {loss:+.2%}")

    # 5. 多因子压力测试
    print("\n" + "=" * 60)
    print("5. 多因子压力测试")
    print("=" * 60)

    multi_factor_scenarios = [
        StressScenario(
            name="股债双杀",
            description="股市和债市同时下跌",
            shocks={"equity": -0.20, "bond": -0.10, "commodity": -0.05}
        ),
        StressScenario(
            name="滞胀",
            description="股市下跌，商品上涨",
            shocks={"equity": -0.15, "bond": -0.05, "commodity": 0.30}
        ),
        StressScenario(
            name="通缩",
            description="所有资产下跌",
            shocks={"equity": -0.25, "bond": -0.15, "commodity": -0.20}
        ),
        StressScenario(
            name="避险模式",
            description="股市下跌，债券和黄金上涨",
            shocks={"equity": -0.30, "bond": 0.15, "commodity": 0.20}
        )
    ]

    print("\n多因子情景分析:")
    print("-" * 40)
    for scenario in multi_factor_scenarios:
        result = tester.hypothetical_stress_test(scenario, weights)
        print(f"\n{scenario.name}:")
        print(f"  {scenario.description}")
        print(f"  冲击: {scenario.shocks}")
        print(f"  组合影响: {result.portfolio_loss:+.2%}")
        print(f"  金额影响: ${result.portfolio_loss_amount:+,.2f}")

    print("\n压力测试完成!")


if __name__ == "__main__":
    main()
