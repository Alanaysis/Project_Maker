"""
投资组合优化示例

演示 Markowitz 均值-方差模型的使用。
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.applications.portfolio import PortfolioOptimizer


def main():
    print("=" * 60)
    print("投资组合优化示例")
    print("=" * 60)

    # 生成模拟收益率数据
    np.random.seed(42)
    n_periods = 252  # 一年交易日
    n_assets = 4

    # 资产参数
    mu = np.array([0.10, 0.15, 0.12, 0.08])  # 年化期望收益
    sigma = np.array([0.20, 0.25, 0.22, 0.15])  # 年化波动率

    # 相关系数矩阵
    corr = np.array([
        [1.0, 0.3, 0.2, 0.1],
        [0.3, 1.0, 0.4, 0.2],
        [0.2, 0.4, 1.0, 0.3],
        [0.1, 0.2, 0.3, 1.0],
    ])

    # 协方差矩阵
    cov = np.outer(sigma, sigma) * corr

    # 生成收益率
    returns = np.random.multivariate_normal(mu / 252, cov / 252, n_periods)

    print(f"资产数量: {n_assets}")
    print(f"历史数据: {n_periods} 天")
    print()
    print("资产统计:")
    print(f"  期望收益: {np.mean(returns, axis=0) * 252}")
    print(f"  波动率: {np.std(returns, axis=0) * np.sqrt(252)}")

    # 创建优化器
    optimizer = PortfolioOptimizer(returns, risk_free_rate=0.03)

    # 1. 最小方差组合
    print("\n" + "-" * 40)
    print("1. 最小方差组合")
    print("-" * 40)

    min_var = optimizer.min_variance_portfolio()
    print(f"权重: {min_var.weights}")
    print(f"期望收益: {min_var.expected_return * 252:.2%}")
    print(f"风险: {min_var.risk * np.sqrt(252):.2%}")
    print(f"夏普比率: {min_var.sharpe_ratio:.2f}")

    # 2. 最大夏普比率组合
    print("\n" + "-" * 40)
    print("2. 最大夏普比率组合")
    print("-" * 40)

    max_sharpe = optimizer.max_sharpe_portfolio()
    print(f"权重: {max_sharpe.weights}")
    print(f"期望收益: {max_sharpe.expected_return * 252:.2%}")
    print(f"风险: {max_sharpe.risk * np.sqrt(252):.2%}")
    print(f"夏普比率: {max_sharpe.sharpe_ratio:.2f}")

    # 3. 风险平价组合
    print("\n" + "-" * 40)
    print("3. 风险平价组合")
    print("-" * 40)

    risk_parity = optimizer.risk_parity()
    print(f"权重: {risk_parity.weights}")
    print(f"期望收益: {risk_parity.expected_return * 252:.2%}")
    print(f"风险: {risk_parity.risk * np.sqrt(252):.2%}")
    print(f"夏普比率: {risk_parity.sharpe_ratio:.2f}")

    # 4. 有效前沿
    print("\n" + "-" * 40)
    print("4. 有效前沿")
    print("-" * 40)

    frontier = optimizer.efficient_frontier(n_points=5)
    print(f"{'收益':<10} {'风险':<10} {'夏普比率':<10}")
    print("-" * 30)
    for p in frontier:
        print(f"{p.expected_return * 252:<10.2%} {p.risk * np.sqrt(252):<10.2%} {p.sharpe_ratio:<10.2f}")

    # 对比
    print("\n" + "=" * 60)
    print("组合对比")
    print("=" * 60)
    print(f"{'组合':<15} {'收益':<10} {'风险':<10} {'夏普比率':<10}")
    print("-" * 45)
    print(f"{'最小方差':<15} {min_var.expected_return * 252:<10.2%} {min_var.risk * np.sqrt(252):<10.2%} {min_var.sharpe_ratio:<10.2f}")
    print(f"{'最大夏普':<15} {max_sharpe.expected_return * 252:<10.2%} {max_sharpe.risk * np.sqrt(252):<10.2%} {max_sharpe.sharpe_ratio:<10.2f}")
    print(f"{'风险平价':<15} {risk_parity.expected_return * 252:<10.2%} {risk_parity.risk * np.sqrt(252):<10.2%} {risk_parity.sharpe_ratio:<10.2f}")


if __name__ == "__main__":
    main()
