"""基础优化示例 - 展示基本的梯度下降优化过程"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt
from src.optimizers import SGD, Momentum, Adam
from src.functions import QuadraticFunction
from src.optimizer import optimize
from src.visualizer import ContourPlotter


def main():
    """运行基础优化示例"""
    print("=" * 60)
    print("基础优化示例 - 梯度下降家族")
    print("=" * 60)

    # 创建测试函数
    func = QuadraticFunction(a=1.0, b=1.0)
    print(f"\n测试函数: {func}")
    print(f"最小值点: {func.minimum()[0]}")
    print(f"最小值: {func.minimum()[1]}")

    # 初始点
    x0 = np.array([3.0, 3.0])
    print(f"初始点: {x0}")
    print(f"初始函数值: {func(x0):.6f}")

    # 创建优化器
    optimizers = {
        'SGD': SGD(learning_rate=0.1),
        'Momentum': Momentum(learning_rate=0.1, momentum=0.9),
        'Adam': Adam(learning_rate=0.1)
    }

    # 运行优化
    results = {}
    for name, optimizer in optimizers.items():
        print(f"\nRunning {name}...")
        result = optimize(func, optimizer, x0.copy(), max_iter=1000, tol=1e-6)
        results[name] = result

        print(f"  Iterations: {result['niter']}")
        print(f"  Final value: {result['fun']:.6e}")
        print(f"  Final grad norm: {result['grad_norms'][-1]:.6e}")
        print(f"  Converged: {'Yes' if result['success'] else 'No'}")

    # 可视化
    print("\n生成可视化图表...")

    # 创建等高线图
    plotter = ContourPlotter(func, x_range=(-4, 4), y_range=(-4, 4))

    # 绘制优化轨迹
    trajectories = [results[name]['trajectory'] for name in results.keys()]
    labels = list(results.keys())

    fig = plotter.plot(
        trajectories=trajectories,
        labels=labels,
        title="Basic Optimization - Trajectory Comparison"
    )

    # 保存图表
    fig.savefig('examples/basic_optimization.png', dpi=150, bbox_inches='tight')
    print("Chart saved to examples/basic_optimization.png")

    # 显示收敛曲线
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    for name, result in results.items():
        ax2.plot(result['values'], '-', linewidth=2, label=name)

    ax2.set_xlabel('Iteration')
    ax2.set_ylabel('Function Value')
    ax2.set_title('Convergence Comparison')
    ax2.set_yscale('log')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    fig2.savefig('examples/basic_convergence.png', dpi=150, bbox_inches='tight')
    print("Convergence chart saved to examples/basic_convergence.png")

    # 打印总结
    print("\n" + "=" * 60)
    print("Optimization Summary")
    print("=" * 60)
    print(f"{'Optimizer':<15} {'Iterations':<12} {'Final Value':<15} {'Converged':<10}")
    print("-" * 60)
    for name, result in results.items():
        status = 'Yes' if result['success'] else 'No'
        print(f"{name:<15} {result['niter']:<12} {result['fun']:<15.6e} {status:<10}")

    print("\nExample completed!")


if __name__ == '__main__':
    main()
