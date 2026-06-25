"""
TSP问题求解示例

演示如何使用模拟退火算法求解旅行商问题
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.simulated_annealing import SimulatedAnnealing, SAConfig, CoolingSchedule
from src.tsp import TSP, City
from src.visualization import plot_tsp_path, plot_convergence


def solve_tsp_example():
    """TSP求解示例"""
    print("=" * 60)
    print("模拟退火算法 - TSP问题求解示例")
    print("=" * 60)

    # 1. 创建TSP实例
    print("\n[1] 创建TSP实例...")
    np.random.seed(42)
    n_cities = 20
    tsp = TSP.create_random_instance(n_cities, seed=42)
    print(f"    城市数量: {n_cities}")

    # 2. 生成初始解
    print("\n[2] 生成初始解...")
    initial_solution = tsp.generate_random_solution()
    initial_distance = tsp.calculate_total_distance(initial_solution)
    print(f"    初始路径: {initial_solution}")
    print(f"    初始距离: {initial_distance:.2f}")

    # 3. 配置模拟退火参数
    print("\n[3] 配置模拟退火参数...")
    config = SAConfig(
        initial_temp=1000.0,
        final_temp=0.1,
        cooling_rate=0.995,
        max_iterations=5000,
        cooling_schedule=CoolingSchedule.EXPONENTIAL
    )
    print(f"    初始温度: {config.initial_temp}")
    print(f"    终止温度: {config.final_temp}")
    print(f"    冷却速率: {config.cooling_rate}")
    print(f"    最大迭代: {config.max_iterations}")

    # 4. 创建优化器
    print("\n[4] 创建优化器...")
    optimizer = SimulatedAnnealing(
        config,
        tsp.calculate_total_distance,
        tsp.random_neighbor,
        initial_solution
    )

    # 5. 执行优化
    print("\n[5] 执行优化...")
    best_solution, best_distance, history = optimizer.optimize()
    print(f"    最优路径: {best_solution}")
    print(f"    最优距离: {best_distance:.2f}")
    print(f"    距离减少: {initial_distance - best_distance:.2f} ({(initial_distance - best_distance) / initial_distance * 100:.1f}%)")
    print(f"    迭代次数: {optimizer.iteration}")

    # 6. 可视化结果
    print("\n[6] 生成可视化...")

    # 绘制初始路径
    fig1 = plot_tsp_path(tsp, initial_solution, "初始路径")
    plt.savefig('tsp_initial_path.png', dpi=100, bbox_inches='tight')
    print("    已保存: tsp_initial_path.png")

    # 绘制最优路径
    fig2 = plot_tsp_path(tsp, best_solution, "最优路径")
    plt.savefig('tsp_best_path.png', dpi=100, bbox_inches='tight')
    print("    已保存: tsp_best_path.png")

    # 绘制收敛曲线
    fig3 = plot_convergence(history, "TSP优化收敛曲线")
    plt.savefig('tsp_convergence.png', dpi=100, bbox_inches='tight')
    print("    已保存: tsp_convergence.png")

    print("\n" + "=" * 60)
    print("示例完成！")
    print("=" * 60)

    return tsp, best_solution, best_distance


def compare_cooling_schedules():
    """对比不同冷却策略"""
    print("\n" + "=" * 60)
    print("冷却策略对比")
    print("=" * 60)

    # 创建TSP实例
    np.random.seed(42)
    tsp = TSP.create_random_instance(15, seed=42)
    initial_solution = tsp.generate_random_solution()

    schedules = [
        ("指数冷却", CoolingSchedule.EXPONENTIAL),
        ("线性冷却", CoolingSchedule.LINEAR),
        ("对数冷却", CoolingSchedule.LOGARITHMIC),
    ]

    results = []

    for name, schedule in schedules:
        print(f"\n运行 {name}...")
        config = SAConfig(
            initial_temp=1000.0,
            final_temp=0.1,
            cooling_rate=0.995,
            max_iterations=3000,
            cooling_schedule=schedule
        )

        optimizer = SimulatedAnnealing(
            config,
            tsp.calculate_total_distance,
            tsp.random_neighbor,
            initial_solution.copy()
        )

        best_solution, best_distance, history = optimizer.optimize()
        results.append((name, best_distance, history))
        print(f"  最优距离: {best_distance:.2f}")

    # 绘制对比图
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for name, distance, history in results:
        axes[0].plot(history['best_cost'], label=f'{name}: {distance:.2f}')
    axes[0].set_xlabel('迭代次数')
    axes[0].set_ylabel('最优成本')
    axes[0].set_title('冷却策略对比 - 收敛曲线')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    for name, distance, history in results:
        axes[1].plot(history['temperature'], label=name)
    axes[1].set_xlabel('迭代次数')
    axes[1].set_ylabel('温度')
    axes[1].set_title('冷却策略对比 - 温度变化')
    axes[1].set_yscale('log')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('cooling_comparison.png', dpi=100, bbox_inches='tight')
    print("\n已保存: cooling_comparison.png")

    return results


if __name__ == "__main__":
    # 运行TSP示例
    tsp, best_solution, best_distance = solve_tsp_example()

    # 对比冷却策略
    compare_cooling_schedules()
