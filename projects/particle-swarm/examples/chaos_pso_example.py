"""
混沌 PSO 示例

演示混沌粒子群优化算法的使用。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from src import ChaosSwarm, ChaosPSOConfig, sphere, rastrigin


def main():
    print("=" * 60)
    print("混沌 PSO 示例")
    print("=" * 60)

    # 测试不同的混沌映射
    chaos_maps = ["logistic", "tent", "sinusoidal"]

    for chaos_map in chaos_maps:
        print(f"\n[{chaos_map.upper()} 混沌映射]")
        print("-" * 40)

        config = ChaosPSOConfig(
            n_particles=30,
            dimensions=2,
            bounds=(-10.0, 10.0),
            chaos_map=chaos_map,
            chaos_weight=0.1,
            chaos_decay=0.99,
            max_iterations=100,
            random_seed=42,
        )

        swarm = ChaosSwarm(config)
        result = swarm.optimize(sphere, verbose=False)

        print(f"最佳适应度: {result['best_fitness']:.6f}")
        print(f"迭代次数: {result['iterations']}")

    # 对比不同混沌映射
    print("\n[对比不同混沌映射]")
    print("-" * 40)

    results = {}
    for chaos_map in chaos_maps:
        config = ChaosPSOConfig(
            n_particles=30,
            dimensions=2,
            bounds=(-10.0, 10.0),
            chaos_map=chaos_map,
            max_iterations=100,
            random_seed=42,
        )

        swarm = ChaosSwarm(config)
        result = swarm.optimize(sphere, verbose=False)
        results[chaos_map] = result['convergence_history']

    print(f"{'混沌映射':<15} {'最终适应度':<15}")
    print("-" * 30)
    for name, history in results.items():
        print(f"{name:<15} {history[-1]:<15.6f}")

    # 优化 Rastrigin 函数
    print("\n[优化 Rastrigin 函数]")
    print("-" * 40)

    config = ChaosPSOConfig(
        n_particles=50,
        dimensions=2,
        bounds=(-5.12, 5.12),
        chaos_map="logistic",
        chaos_weight=0.2,
        max_iterations=200,
        random_seed=42,
    )

    swarm = ChaosSwarm(config)
    result = swarm.optimize(rastrigin, verbose=True)

    print(f"\n最佳位置: {result['best_position']}")
    print(f"最佳适应度: {result['best_fitness']:.6f}")

    # 对比标准 PSO
    print("\n[对比标准 PSO]")
    print("-" * 40)
    from src import Swarm, PSOConfig

    standard_config = PSOConfig(
        n_particles=50,
        dimensions=2,
        bounds=(-5.12, 5.12),
        w_strategy="linear_decay",
        max_iterations=200,
        random_seed=42,
    )

    standard_swarm = Swarm(standard_config)
    standard_result = standard_swarm.optimize(rastrigin, verbose=False)

    print(f"混沌 PSO 适应度: {result['best_fitness']:.6f}")
    print(f"标准 PSO 适应度: {standard_result.best_fitness:.6f}")


if __name__ == "__main__":
    main()
