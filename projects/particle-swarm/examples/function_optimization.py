"""
多函数优化示例

演示 PSO 在不同测试函数上的表现，并对比收敛速度。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from src import Swarm, PSOConfig, get_function, BENCHMARK_FUNCTIONS


def optimize_function(func_name: str, dimensions: int = 2, verbose: bool = False):
    """
    优化指定的测试函数

    参数:
        func_name: 函数名称
        dimensions: 维度
        verbose: 是否打印详细信息

    返回:
        (函数名, 最佳适应度, 迭代次数, 收敛历史)
    """
    func_info = get_function(func_name)
    func = func_info["function"]
    bounds = func_info["bounds"]

    config = PSOConfig(
        n_particles=30,
        dimensions=dimensions,
        bounds=bounds,
        w_strategy="linear_decay",
        w_max=0.9,
        w_min=0.4,
        c1=1.5,
        c2=1.5,
        max_iterations=200,
        random_seed=42,
    )

    swarm = Swarm(config)
    result = swarm.optimize(func, verbose=verbose)

    return func_name, result.best_fitness, result.iterations, result.convergence_history


def main():
    print("=" * 70)
    print("PSO 多函数优化示例")
    print("=" * 70)

    dimensions = 2
    results = {}

    # 优化所有测试函数
    for func_name in BENCHMARK_FUNCTIONS:
        print(f"\n正在优化 {func_name}...")
        name, fitness, iterations, history = optimize_function(
            func_name, dimensions=dimensions
        )
        results[name] = {
            "fitness": fitness,
            "iterations": iterations,
            "history": history,
        }
        print(f"  最佳适应度: {fitness:.6f}")
        print(f"  迭代次数: {iterations}")

    # 汇总结果
    print("\n" + "=" * 70)
    print("汇总结果")
    print("=" * 70)
    print(f"{'函数名':<15} {'最佳适应度':<15} {'迭代次数':<10} {'难度'}")
    print("-" * 55)

    difficulty = {
        "sphere": "简单",
        "rosenbrock": "中等",
        "rastrigin": "困难",
        "ackley": "困难",
        "griewank": "中等",
    }

    for name, result in sorted(results.items(), key=lambda x: x[1]["fitness"]):
        diff = difficulty.get(name, "未知")
        print(f"{name:<15} {result['fitness']:<15.6f} {result['iterations']:<10} {diff}")

    # 尝试绘制收敛曲线（如果 matplotlib 可用）
    try:
        from src.visualizer import PSOVisualizer

        histories = {name: r["history"] for name, r in results.items()}
        PSOVisualizer.compare_functions(histories)
    except ImportError:
        print("\n提示: 安装 matplotlib 可以查看收敛曲线可视化")


if __name__ == "__main__":
    main()
