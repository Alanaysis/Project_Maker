"""基础因子分析示例

演示如何使用因子挖掘框架进行完整的因子分析流程:
1. 生成模拟数据
2. 计算多种因子
3. IC 评估
4. 分组回测
5. 输出结果
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data import generate_stock_data
from src.factors import FactorCalculator
from src.evaluation import FactorEvaluator


def main():
    print("=" * 60)
    print("因子挖掘框架 - 基础因子分析示例")
    print("=" * 60)

    # 1. 生成模拟数据
    print("\n[1] 生成模拟股票数据...")
    data = generate_stock_data(n_stocks=50, n_days=500, seed=42)
    print(f"    股票数: {data['price'].shape[1]}")
    print(f"    交易日: {data['price'].shape[0]}")
    print(f"    价格范围: {data['price'].min().min():.2f} ~ {data['price'].max().max():.2f}")

    # 2. 计算因子
    print("\n[2] 计算因子...")
    calc = FactorCalculator(
        price=data['price'],
        volume=data['volume'],
        high=data['high'],
        low=data['low'],
    )

    factors = {
        'MOM_20': calc.momentum(window=20),
        'MOM_5': calc.momentum(window=5),
        'REV_5': calc.short_term_reversal(window=5),
        'VOL_20': calc.volatility(window=20),
        'AMIHUD': calc.amihud_illiquidity(window=20),
        'RSI_14': calc.rsi(window=14),
        'BOLL': calc.bollinger_width(window=20),
        'PMA_20': calc.price_to_ma(window=20),
        'VOLMOM': calc.volume_momentum(window=20),
    }

    for name, df in factors.items():
        print(f"    {name}: shape={df.shape}, "
              f"valid_ratio={df.notna().mean().mean():.2%}")

    # 3. IC 分析
    print("\n[3] 因子 IC 分析...")
    future_returns = data['returns'].shift(-1)

    print(f"{'因子':<12} {'IC均值':>8} {'IC标准差':>8} {'ICIR':>8} "
          f"{'t统计量':>8} {'IC>0占比':>8}")
    print("-" * 60)

    ic_results = {}
    for name, factor_df in factors.items():
        evaluator = FactorEvaluator(factor_df, future_returns)
        summary = evaluator.ic_summary()
        ic_results[name] = summary
        print(f"{name:<12} {summary['IC_mean']:>8.4f} {summary['IC_std']:>8.4f} "
              f"{summary['ICIR']:>8.4f} {summary['IC_tstat']:>8.4f} "
              f"{summary['IC_positive_ratio']:>8.4f}")

    # 4. 最佳因子分组收益
    print("\n[4] 最佳因子分组收益分析...")
    best_factor_name = max(ic_results.keys(),
                           key=lambda k: abs(ic_results[k].get('ICIR', 0)))
    print(f"    最佳因子 (按ICIR): {best_factor_name}")

    best_factor = factors[best_factor_name]
    evaluator = FactorEvaluator(best_factor, future_returns)

    # 分组收益
    group_ret = evaluator.group_returns(n_groups=5)
    cum_ret = evaluator.cumulative_returns(n_groups=5)

    print("\n    分组累计收益:")
    for col in cum_ret.columns:
        final_ret = cum_ret[col].iloc[-1] if not cum_ret[col].isna().all() else 0
        print(f"      {col}: {final_ret:.4f}")

    # 多空收益
    ls_ret = evaluator.long_short_return(n_groups=5)
    if len(ls_ret) > 0:
        cum_ls = (1 + ls_ret).prod() - 1
        print(f"\n    多空累计收益: {cum_ls:.4f}")

    # 5. 绩效摘要
    print("\n[5] 综合绩效摘要...")
    perf = evaluator.performance_summary(n_groups=5)
    for k, v in perf.items():
        print(f"    {k}: {v}")

    print("\n" + "=" * 60)
    print("分析完成!")


if __name__ == '__main__':
    main()
