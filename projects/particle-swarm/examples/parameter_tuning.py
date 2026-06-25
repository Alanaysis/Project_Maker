"""
参数调优示例

演示不同 PSO 参数设置对优化性能的影响，帮助理解参数调优。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from src import Swarm, PSOConfig, rastrigin


def run_experiment(name: str, config: PSOConfig, objective, verbose: bool = False):
    """
    运行一次实验

    参数:
        name: 实验名称
        config: PSO 配置
        objective: 目标函数
        verbose: 是否打印详细信息

    返回:
        (名称, 最佳适应度, 收敛历史)
    """
    swarm = Swarm(config)
    result = swarm.optimize(objective, verbose=verbose)
    return name, result.best_fitness, result.convergence_history


def main():
    print("=" * 70)
    print("PSO 参数调优示例")
    print("=" * 70)

    objective = rastrigin
    bounds = (-5.12, 5.12)
    results = {}

    # 实验 1: 不同粒子数量
    print("\n[实验 1] 不同粒子数量的影响")
    print("-" * 40)
    for n_particles in [10, 20, 50, 100]:
        config = PSOConfig(
            n_particles=n_particles,
            dimensions=2,
            bounds=bounds,
            max_iterations=100,
            random_seed=42,
        )
        name, fitness, history = run_experiment(f"n={n_particles}", config, objective)
        results[name] = history
        print(f"  粒子数={n_particles:>3}: 最佳适应度={fitness:.6f}")

    # 实验 2: 不同惯性权重
    print("\n[实验 2] 不同惯性权重的影响")
    print("-" * 40)
    for w in [0.4, 0.6, 0.8, 1.0]:
        config = PSOConfig(
            n_particles=30,
            dimensions=2,
            bounds=bounds,
            w=w,
            max_iterations=100,
            random_seed=42,
        )
        name, fitness, history = run_experiment(f"w={w}", config, objective)
        results[name] = history
        print(f"  惯性权重={w:.1f}: 最佳适应度={fitness:.6f}")

    # 实验 3: 不同学习因子
    print("\n[实验 3] 不同学习因子的影响")
    print("-" * 40)
    for c1, c2 in [(0.5, 0.5), (1.0, 1.0), (1.5, 1.5), (2.0, 2.0)]:
        config = PSOConfig(
            n_particles=30,
            dimensions=2,
            bounds=bounds,
            c1=c1,
            c2=c2,
            max_iterations=100,
            random_seed=42,
        )
        name, fitness, history = run_experiment(f"c1={c1},c2={c2}", config, objective)
        results[name] = history
        print(f"  c1={c1:.1f}, c2={c2:.1f}: 最佳适应度={fitness:.6f}")

    # 实验 4: 不同惯性权重策略
    print("\n[实验 4] 不同惯性权重策略的影响")
    print("-" * 40)
    for strategy in ["fixed", "linear_decay"]:
        config = PSOConfig(
            n_particles=30,
            dimensions=2,
            bounds=bounds,
            w_strategy=strategy,
            max_iterations=100,
            random_seed=42,
        )
        name, fitness, history = run_experiment(strategy, config, objective)
        results[name] = history
        print(f"  策略={strategy:<15}: 最佳适应度={fitness:.6f}")

    # 实验 5: 不同维度
    print("\n[实验 5] 不同维度的影响")
    print("-" * 40)
    for dim in [2, 5, 10, 20]:
        config = PSOConfig(
            n_particles=50,
            dimensions=dim,
            bounds=bounds,
            w_strategy="linear_decay",
            max_iterations=200,
            random_seed=42,
        )
        name, fitness, history = run_experiment(f"d={dim}", config, objective)
        results[name] = history
        print(f"  维度={dim:>2}: 最佳适应度={fitness:.6f}")

    # 尝试绘制对比图（如果 matplotlib 可用）
    try:
        from src.visualizer import PSOVisualizer

        # 绘制粒子数量对比
        n_particles_results = {k: v for k, v in results.items() if k.startswith("n=")}
        if n_particles_results:
            PSOVisualizer.compare_parameters(
                n_particles_results, title="不同粒子数量的收敛对比"
            )
    except ImportError:
        print("\n提示: 安装 matplotlib 可以查看对比图可视化")


if __name__ == "__main__":
    main()
