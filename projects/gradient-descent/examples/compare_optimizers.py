"""优化器对比示例 - 对比不同优化器的性能"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt
from src.optimizers import SGD, Momentum, AdaGrad, RMSProp, Adam, AdamW
from src.functions import QuadraticFunction, RosenbrockFunction, HimmelblauFunction
from src.optimizer import compare_optimizers
from src.visualizer import ContourPlotter, ComparisonPlotter


def compare_on_quadratic():
    """在二次函数上对比优化器"""
    print("\n" + "=" * 60)
    print("在二次函数上对比优化器")
    print("=" * 60)

    func = QuadraticFunction(a=1.0, b=1.0)
    x0 = np.array([3.0, 3.0])

    optimizers = {
        'SGD': SGD(learning_rate=0.1),
        'Momentum': Momentum(learning_rate=0.01, momentum=0.9),
        'AdaGrad': AdaGrad(learning_rate=0.1),
        'RMSProp': RMSProp(learning_rate=0.01),
        'Adam': Adam(learning_rate=0.01),
        'AdamW': AdamW(learning_rate=0.01, weight_decay=0.0)
    }

    results = compare_optimizers(func, optimizers, x0, max_iter=200, tol=1e-6)

    # 打印结果
    print(f"\n{'优化器':<15} {'迭代次数':<12} {'最终函数值':<15} {'最终梯度范数':<15}")
    print("-" * 60)
    for name, result in results.items():
        print(f"{name:<15} {result['niter']:<12} {result['fun']:<15.6e} "
              f"{result['grad_norms'][-1]:<15.6e}")

    # 可视化
    plotter = ContourPlotter(func, x_range=(-4, 4), y_range=(-4, 4))
    trajectories = [results[name]['trajectory'] for name in results.keys()]
    labels = list(results.keys())

    fig = plotter.plot(
        trajectories=trajectories,
        labels=labels,
        title="二次函数 - 优化器对比"
    )
    fig.savefig('examples/compare_quadratic.png', dpi=150, bbox_inches='tight')

    return results


def compare_on_rosenbrock():
    """在 Rosenbrock 函数上对比优化器"""
    print("\n" + "=" * 60)
    print("在 Rosenbrock 函数上对比优化器")
    print("=" * 60)

    func = RosenbrockFunction(a=1.0, b=100.0)
    x0 = np.array([-1.0, 1.0])

    optimizers = {
        'SGD': SGD(learning_rate=0.0001),
        'Momentum': Momentum(learning_rate=0.0001, momentum=0.9),
        'AdaGrad': AdaGrad(learning_rate=0.01),
        'RMSProp': RMSProp(learning_rate=0.001),
        'Adam': Adam(learning_rate=0.001),
        'AdamW': AdamW(learning_rate=0.001, weight_decay=0.0)
    }

    results = compare_optimizers(func, optimizers, x0, max_iter=2000, tol=1e-4)

    # 打印结果
    print(f"\n{'优化器':<15} {'迭代次数':<12} {'最终函数值':<15} {'最终梯度范数':<15}")
    print("-" * 60)
    for name, result in results.items():
        print(f"{name:<15} {result['niter']:<12} {result['fun']:<15.6e} "
              f"{result['grad_norms'][-1]:<15.6e}")

    # 可视化
    plotter = ContourPlotter(func, x_range=(-2, 2), y_range=(-1, 3))
    trajectories = [results[name]['trajectory'] for name in results.keys()]
    labels = list(results.keys())

    fig = plotter.plot(
        trajectories=trajectories,
        labels=labels,
        title="Rosenbrock 函数 - 优化器对比"
    )
    fig.savefig('examples/compare_rosenbrock.png', dpi=150, bbox_inches='tight')

    return results


def compare_on_himmelblau():
    """在 Himmelblau 函数上对比优化器"""
    print("\n" + "=" * 60)
    print("在 Himmelblau 函数上对比优化器")
    print("=" * 60)

    func = HimmelblauFunction()
    x0 = np.array([0.0, 0.0])

    optimizers = {
        'SGD': SGD(learning_rate=0.001),
        'Momentum': Momentum(learning_rate=0.001, momentum=0.9),
        'AdaGrad': AdaGrad(learning_rate=0.01),
        'RMSProp': RMSProp(learning_rate=0.001),
        'Adam': Adam(learning_rate=0.01),
        'AdamW': AdamW(learning_rate=0.01, weight_decay=0.0)
    }

    results = compare_optimizers(func, optimizers, x0, max_iter=1000, tol=1e-4)

    # 打印结果
    print(f"\n{'优化器':<15} {'迭代次数':<12} {'最终函数值':<15} {'最终梯度范数':<15}")
    print("-" * 60)
    for name, result in results.items():
        print(f"{name:<15} {result['niter']:<12} {result['fun']:<15.6e} "
              f"{result['grad_norms'][-1]:<15.6e}")

    # 可视化
    plotter = ContourPlotter(func, x_range=(-5, 5), y_range=(-5, 5))
    trajectories = [results[name]['trajectory'] for name in results.keys()]
    labels = list(results.keys())

    fig = plotter.plot(
        trajectories=trajectories,
        labels=labels,
        title="Himmelblau 函数 - 优化器对比"
    )
    fig.savefig('examples/compare_himmelblau.png', dpi=150, bbox_inches='tight')

    return results


def plot_convergence_comparison(all_results):
    """绘制收敛对比图"""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    for idx, (func_name, results) in enumerate(all_results.items()):
        ax = axes[idx]
        for name, result in results.items():
            ax.plot(result['values'], '-', linewidth=2, label=name)

        ax.set_xlabel('Iteration')
        ax.set_ylabel('Function Value')
        ax.set_title(f'{func_name} - 收敛曲线')
        ax.set_yscale('log')
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    fig.savefig('examples/convergence_comparison.png', dpi=150, bbox_inches='tight')


def main():
    """运行优化器对比示例"""
    print("=" * 60)
    print("优化器对比示例 - 梯度下降家族")
    print("=" * 60)

    # 在不同函数上对比
    all_results = {}

    all_results['Quadratic'] = compare_on_quadratic()
    all_results['Rosenbrock'] = compare_on_rosenbrock()
    all_results['Himmelblau'] = compare_on_himmelblau()

    # 绘制收敛对比图
    print("\n生成收敛对比图...")
    plot_convergence_comparison(all_results)

    # 总结
    print("\n" + "=" * 60)
    print("总结")
    print("=" * 60)
    print("\n观察:")
    print("1. Adam 通常收敛最快，但可能在某些问题上泛化性较差")
    print("2. SGD + Momentum 收敛稳定，但需要仔细调整学习率")
    print("3. AdaGrad 对稀疏特征友好，但学习率会过早衰减")
    print("4. RMSProp 解决了 AdaGrad 的学习率衰减问题")
    print("5. AdamW 通过解耦权重衰减提供更好的泛化性能")

    print("\n示例完成!")


if __name__ == '__main__':
    main()
