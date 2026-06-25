"""
函数优化示例

演示如何使用模拟退火算法优化多模态测试函数
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.simulated_annealing import SimulatedAnnealing, SAConfig, CoolingSchedule
from src.function_optimization import TestFunctions, ContinuousNeighbor, get_function_specs
from src.visualization import plot_convergence


def optimize_sphere():
    """优化Sphere函数"""
    print("=" * 60)
    print("函数优化示例 - Sphere函数")
    print("=" * 60)

    dim = 2
    config = SAConfig(
        initial_temp=100.0,
        final_temp=0.001,
        cooling_rate=0.995,
        max_iterations=5000,
        cooling_schedule=CoolingSchedule.EXPONENTIAL
    )

    neighbor = ContinuousNeighbor(bounds=(-5.12, 5.12), dim=dim, step_size=0.5)
    initial_solution = np.random.uniform(-5, 5, dim)

    print(f"\n初始解: {initial_solution}")
    print(f"初始值: {TestFunctions.sphere(initial_solution):.6f}")

    optimizer = SimulatedAnnealing(
        config, TestFunctions.sphere, neighbor, initial_solution
    )

    best_solution, best_cost, history = optimizer.optimize()

    print(f"\n最优解: {best_solution}")
    print(f"最优值: {best_cost:.6f}")
    print(f"理论最优: 0.0")
    print(f"误差: {abs(best_cost):.6f}")

    # 绘制收敛曲线
    fig = plot_convergence(history, "Sphere函数优化收敛曲线")
    plt.savefig('sphere_convergence.png', dpi=100, bbox_inches='tight')
    print("\n已保存: sphere_convergence.png")

    return best_solution, best_cost


def optimize_rastrigin():
    """优化Rastrigin函数（多模态）"""
    print("\n" + "=" * 60)
    print("函数优化示例 - Rastrigin函数（多模态）")
    print("=" * 60)

    dim = 2
    config = SAConfig(
        initial_temp=200.0,
        final_temp=0.001,
        cooling_rate=0.997,
        max_iterations=10000,
        cooling_schedule=CoolingSchedule.EXPONENTIAL
    )

    neighbor = ContinuousNeighbor(bounds=(-5.12, 5.12), dim=dim, step_size=1.0)
    initial_solution = np.random.uniform(-5, 5, dim)

    print(f"\n初始解: {initial_solution}")
    print(f"初始值: {TestFunctions.rastrigin(initial_solution):.6f}")

    optimizer = SimulatedAnnealing(
        config, TestFunctions.rastrigin, neighbor, initial_solution
    )

    best_solution, best_cost, history = optimizer.optimize()

    print(f"\n最优解: {best_solution}")
    print(f"最优值: {best_cost:.6f}")
    print(f"理论最优: 0.0")
    print(f"误差: {abs(best_cost):.6f}")

    # 绘制收敛曲线
    fig = plot_convergence(history, "Rastrigin函数优化收敛曲线")
    plt.savefig('rastrigin_convergence.png', dpi=100, bbox_inches='tight')
    print("\n已保存: rastrigin_convergence.png")

    return best_solution, best_cost


def compare_functions():
    """对比不同函数的优化效果"""
    print("\n" + "=" * 60)
    print("函数优化对比")
    print("=" * 60)

    dim = 2
    specs = get_function_specs(dim)

    config = SAConfig(
        initial_temp=100.0,
        final_temp=0.001,
        cooling_rate=0.995,
        max_iterations=5000,
        cooling_schedule=CoolingSchedule.EXPONENTIAL
    )

    results = []

    for name, spec in specs.items():
        print(f"\n优化 {spec.name}...")
        neighbor = ContinuousNeighbor(spec.bounds, dim, step_size=0.5)
        initial_solution = np.random.uniform(
            spec.bounds[0], spec.bounds[1], dim
        )

        optimizer = SimulatedAnnealing(
            config, spec.func, neighbor, initial_solution
        )

        best_solution, best_cost, history = optimizer.optimize()

        results.append({
            'name': spec.name,
            'best_cost': best_cost,
            'global_minimum': spec.global_minimum,
            'error': abs(best_cost - spec.global_minimum)
        })

        print(f"  最优值: {best_cost:.6f}")
        print(f"  理论最优: {spec.global_minimum}")
        print(f"  误差: {abs(best_cost - spec.global_minimum):.6f}")

    # 打印汇总
    print("\n" + "-" * 60)
    print("优化结果汇总")
    print("-" * 60)
    print(f"{'函数':<15} {'最优值':<15} {'理论最优':<15} {'误差':<15}")
    print("-" * 60)
    for r in results:
        print(f"{r['name']:<15} {r['best_cost']:<15.6f} {r['global_minimum']:<15.6f} {r['error']:<15.6f}")

    return results


def plot_3d_surface():
    """绘制3D函数曲面"""
    print("\n绘制3D函数曲面...")

    fig = plt.figure(figsize=(15, 5))

    functions = [
        ('Sphere', TestFunctions.sphere, (-5, 5)),
        ('Rastrigin', TestFunctions.rastrigin, (-5.12, 5.12)),
        ('Ackley', TestFunctions.ackley, (-5, 5)),
    ]

    for idx, (name, func, bounds) in enumerate(functions):
        ax = fig.add_subplot(1, 3, idx + 1, projection='3d')

        x = np.linspace(bounds[0], bounds[1], 50)
        y = np.linspace(bounds[0], bounds[1], 50)
        X, Y = np.meshgrid(x, y)
        Z = np.array([func(np.array([xi, yi])) for xi, yi in zip(X.ravel(), Y.ravel())])
        Z = Z.reshape(X.shape)

        ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.8)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title(name)

    plt.tight_layout()
    plt.savefig('function_surfaces.png', dpi=100, bbox_inches='tight')
    print("已保存: function_surfaces.png")


if __name__ == "__main__":
    # 设置随机种子
    np.random.seed(42)

    # 优化Sphere函数
    optimize_sphere()

    # 优化Rastrigin函数
    optimize_rastrigin()

    # 对比不同函数
    compare_functions()

    # 绘制3D曲面（需要matplotlib支持3D）
    try:
        plot_3d_surface()
    except Exception as e:
        print(f"3D绘图跳过: {e}")
