"""因子回测示例

演示如何使用回测框架进行因子回测:
1. 单因子回测
2. 多因子组合回测
3. 参数敏感性分析
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data import generate_stock_data, split_train_test
from src.factors import FactorCalculator
from src.backtest import BacktestEngine, BacktestConfig, multi_factor_backtest


def single_factor_backtest():
    """单因子回测"""
    print("=" * 60)
    print("单因子回测示例")
    print("=" * 60)

    data = generate_stock_data(n_stocks=50, n_days=500, seed=42)
    train_data, test_data = split_train_test(data, train_ratio=0.7)

    calc = FactorCalculator(
        price=train_data['price'],
        volume=train_data['volume'],
        high=train_data['high'],
        low=train_data['low'],
    )
    factor = calc.momentum(window=20)

    # 纯多头策略 (更贴近实际)
    print("\n--- 纯多头策略 (仅做多最高组) ---")
    config_long = BacktestConfig(n_groups=5, top_group_only=True,
                                  transaction_cost=0.001)
    engine_long = BacktestEngine(factor, train_data['returns'], config_long)
    result_long = engine_long.run()
    summary_long = result_long.summary()

    for k, v in summary_long.items():
        print(f"  {k}: {v}")

    # 多空策略
    print("\n--- 多空策略 (做多最高组, 做空最低组) ---")
    print("  注: 在模拟数据中, 多空策略收益会指数增长, 因为")
    print("  有效因子使多头和空头同时贡献正收益。")
    config = BacktestConfig(n_groups=5, transaction_cost=0.001)
    engine = BacktestEngine(factor, train_data['returns'], config)
    result = engine.run()
    summary = result.summary()
    print(f"  total_return: {summary['total_return']:.4f}")
    print(f"  max_drawdown: {summary['max_drawdown']:.4f}")
    print(f"  avg_turnover: {summary['avg_turnover']:.4f}")

    return result_long


def multi_factor_example():
    """多因子组合回测"""
    print("\n" + "=" * 60)
    print("多因子组合回测示例")
    print("=" * 60)

    data = generate_stock_data(n_stocks=50, n_days=500, seed=42)

    calc = FactorCalculator(
        price=data['price'],
        volume=data['volume'],
        high=data['high'],
        low=data['low'],
    )

    factors = {
        'momentum': calc.momentum(window=20),
        'reversal': calc.short_term_reversal(window=5),
        'volatility': calc.volatility(window=20),
        'amihud': calc.amihud_illiquidity(window=20),
    }

    weights = {
        'momentum': 0.3,
        'reversal': 0.3,
        'volatility': 0.2,
        'amihud': 0.2,
    }

    print("\n因子权重:")
    for name, w in weights.items():
        print(f"  {name}: {w}")

    config = BacktestConfig(n_groups=5, top_group_only=True, transaction_cost=0.001)
    result = multi_factor_backtest(factors, data['returns'],
                                    weights=weights, config=config)
    summary = result.summary()

    print("\n回测结果:")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    return result


def parameter_sensitivity():
    """参数敏感性分析"""
    print("\n" + "=" * 60)
    print("参数敏感性分析: 分组数对绩效的影响")
    print("=" * 60)

    data = generate_stock_data(n_stocks=50, n_days=500, seed=42)
    calc = FactorCalculator(
        price=data['price'],
        volume=data['volume'],
    )
    factor = calc.momentum(window=20)

    print(f"\n{'分组数':>6} {'总收益':>10} {'年化收益':>10} {'Sharpe':>10} "
          f"{'最大回撤':>10}")
    print("-" * 50)

    for n_groups in [3, 5, 7, 10]:
        config = BacktestConfig(n_groups=n_groups, top_group_only=True,
                                transaction_cost=0.001)
        engine = BacktestEngine(factor, data['returns'], config)
        result = engine.run()
        s = result.summary()
        print(f"{n_groups:>6} {s['total_return']:>10.4f} "
              f"{s['ann_return']:>10.4f} {s['sharpe_ratio']:>10.4f} "
              f"{s['max_drawdown']:>10.4f}")


def main():
    single_factor_backtest()
    multi_factor_example()
    parameter_sensitivity()

    print("\n" + "=" * 60)
    print("回测示例完成!")


if __name__ == '__main__':
    main()
