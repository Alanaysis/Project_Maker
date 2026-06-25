"""
Branin 函数优化示例
==================

Branin 函数是一个常用的优化测试函数：
f(x1, x2) = a(x2 - bx1^2 + cx1 - d)^2 + e(1-f)cos(x1) + e

其中：
- a = 1, b = 5.1/(4π^2), c = 5/π, d = 6, e = 10, f = 1/(8π)

全局最小值：
- f(x*) ≈ 0.397887
- x* = (-π, 12.275), (π, 2.275), (9.42478, 2.475)
"""

import numpy as np
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.optimizer import BayesianOptimizer
from src.acquisition import ExpectedImprovement, UpperConfidenceBound, ProbabilityOfImprovement


def branin(x):
    """
    Branin 函数

    参数：
        x: 输入向量 [x1, x2]

    返回：
        函数值
    """
    x1, x2 = x[0], x[1]

    a = 1.0
    b = 5.1 / (4 * np.pi**2)
    c = 5.0 / np.pi
    d = 6.0
    e = 10.0
    f = 1.0 / (8 * np.pi)

    return a * (x2 - b * x1**2 + c * x1 - d)**2 + e * (1 - f) * np.cos(x1) + e


def main():
    """主函数"""
    print("=" * 60)
    print("贝叶斯优化 - Branin 函数优化示例")
    print("=" * 60)

    # 搜索空间
    bounds = [(-5, 10), (0, 15)]

    # 创建优化器
    optimizer = BayesianOptimizer(
        objective_function=branin,
        bounds=bounds,
        acquisition=ExpectedImprovement(xi=0.01),
        kernel='rbf',
        n_initial=10,
        maximize=False,
        random_state=42
    )

    # 运行优化
    print("\n开始优化...")
    result = optimizer.optimize(n_iterations=30, verbose=True)

    # 打印结果
    print("\n" + "=" * 60)
    print("优化结果")
    print("=" * 60)
    print(f"最优解: x = {result['best_x']}")
    print(f"最优值: f(x) = {result['best_y']:.6f}")
    print(f"真实最小值: 0.397887")
    print(f"评估次数: {result['n_evaluations']}")

    # 绘制收敛曲线
    try:
        import matplotlib.pyplot as plt

        iterations, best_values = optimizer.get_convergence_data()

        plt.figure(figsize=(10, 6))
        plt.plot(iterations, best_values, 'b-', linewidth=2)
        plt.axhline(y=0.397887, color='r', linestyle='--', label='真实最小值')
        plt.xlabel('迭代次数')
        plt.ylabel('最优值')
        plt.title('Branin 函数优化收敛曲线')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig('branin_convergence.png', dpi=150, bbox_inches='tight')
        print("\n收敛曲线已保存到 branin_convergence.png")
    except ImportError:
        print("\nmatplotlib 未安装，跳过绘图")


if __name__ == '__main__':
    main()
