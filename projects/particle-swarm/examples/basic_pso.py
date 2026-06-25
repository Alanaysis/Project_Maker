"""
PSO 基础示例

演示如何使用粒子群优化算法求解简单的球面函数最小值问题。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from src import Swarm, PSOConfig, sphere


def main():
    print("=" * 60)
    print("PSO 基础示例：求解 Sphere 函数最小值")
    print("=" * 60)

    # 配置 PSO
    config = PSOConfig(
        n_particles=30,
        dimensions=2,
        bounds=(-10.0, 10.0),
        w=0.7,
        c1=1.5,
        c2=1.5,
        max_iterations=100,
        random_seed=42,
    )

    # 创建粒子群并优化
    swarm = Swarm(config)
    result = swarm.optimize(sphere, verbose=True)

    # 输出结果
    print("\n" + "=" * 60)
    print("优化结果")
    print("=" * 60)
    print(f"最佳位置: {result.best_position}")
    print(f"最佳适应度: {result.best_fitness:.6f}")
    print(f"迭代次数: {result.iterations}")
    print(f"理论最优: [0, 0]")
    print(f"误差: {np.linalg.norm(result.best_position):.6f}")


if __name__ == "__main__":
    main()
