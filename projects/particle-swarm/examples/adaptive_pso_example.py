"""
自适应 PSO 示例

演示自适应粒子群优化算法的使用。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from src import AdaptiveSwarm, AdaptivePSOConfig, sphere, rastrigin


def main():
    print("=" * 60)
    print("自适应 PSO 示例")
    print("=" * 60)

    # 配置自适应 PSO
    config = AdaptivePSOConfig(
        n_particles=30,
        dimensions=2,
        bounds=(-10.0, 10.0),
        w_init=0.9,
        c1_init=2.0,
        c2_init=2.0,
        w_min=0.4,
        w_max=0.9,
        c_min=0.5,
        c_max=2.5,
        max_iterations=100,
        random_seed=42,
    )

    # 优化 Sphere 函数
    print("\n[1] 优化 Sphere 函数")
    print("-" * 40)
    swarm = AdaptiveSwarm(config)
    result = swarm.optimize(sphere, verbose=True)

    print(f"\n最佳位置: {result['best_position']}")
    print(f"最佳适应度: {result['best_fitness']:.6f}")
    print(f"迭代次数: {result['iterations']}")

    # 显示参数变化
    print("\n参数变化:")
    for i in range(0, len(result['parameter_history']), 10):
        params = result['parameter_history'][i]
        print(
            f"  迭代 {params['iteration']}: "
            f"w={params['w']:.3f}, "
            f"c1={params['c1']:.3f}, "
            f"c2={params['c2']:.3f}"
        )

    # 优化 Rastrigin 函数
    print("\n[2] 优化 Rastrigin 函数")
    print("-" * 40)
    config.bounds = (-5.12, 5.12)
    swarm = AdaptiveSwarm(config)
    result = swarm.optimize(rastrigin, verbose=True)

    print(f"\n最佳位置: {result['best_position']}")
    print(f"最佳适应度: {result['best_fitness']:.6f}")

    # 对比标准 PSO
    print("\n[3] 对比标准 PSO")
    print("-" * 40)
    from src import Swarm, PSOConfig

    standard_config = PSOConfig(
        n_particles=30,
        dimensions=2,
        bounds=(-10.0, 10.0),
        w_strategy="linear_decay",
        max_iterations=100,
        random_seed=42,
    )

    standard_swarm = Swarm(standard_config)
    standard_result = standard_swarm.optimize(sphere)

    print(f"自适应 PSO 适应度: {result['best_fitness']:.6f}")
    print(f"标准 PSO 适应度: {standard_result.best_fitness:.6f}")


if __name__ == "__main__":
    main()
