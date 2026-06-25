"""
可视化工具

提供模拟退火过程的可视化功能：
- 收敛曲线
- TSP路径可视化
- 优化过程动画
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict
from .tsp import TSP, City


def plot_convergence(history: Dict, title: str = "模拟退火收敛曲线"):
    """
    绘制收敛曲线

    参数:
        history: 历史记录字典
        title: 图表标题
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle(title, fontsize=16)

    iterations = range(len(history['temperature']))

    # 温度变化
    axes[0, 0].plot(iterations, history['temperature'], 'b-', alpha=0.7)
    axes[0, 0].set_xlabel('迭代次数')
    axes[0, 0].set_ylabel('温度')
    axes[0, 0].set_title('温度变化')
    axes[0, 0].set_yscale('log')
    axes[0, 0].grid(True, alpha=0.3)

    # 当前成本
    axes[0, 1].plot(iterations, history['current_cost'], 'g-', alpha=0.7, label='当前成本')
    axes[0, 1].set_xlabel('迭代次数')
    axes[0, 1].set_ylabel('成本')
    axes[0, 1].set_title('当前成本变化')
    axes[0, 1].grid(True, alpha=0.3)

    # 最优成本
    axes[1, 0].plot(iterations, history['best_cost'], 'r-', alpha=0.7, label='最优成本')
    axes[1, 0].set_xlabel('迭代次数')
    axes[1, 0].set_ylabel('成本')
    axes[1, 0].set_title('最优成本变化')
    axes[1, 0].grid(True, alpha=0.3)

    # 综合对比
    axes[1, 1].plot(iterations, history['current_cost'], 'g-', alpha=0.5, label='当前成本')
    axes[1, 1].plot(iterations, history['best_cost'], 'r-', alpha=0.7, label='最优成本')
    axes[1, 1].set_xlabel('迭代次数')
    axes[1, 1].set_ylabel('成本')
    axes[1, 1].set_title('成本对比')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_tsp_path(tsp: TSP, path: List[int], title: str = "TSP路径"):
    """
    绘制TSP路径

    参数:
        tsp: TSP实例
        path: 路径（城市索引列表）
        title: 图表标题
    """
    fig, ax = plt.subplots(1, 1, figsize=(8, 6))

    # 获取城市坐标
    x = [tsp.cities[i].x for i in path]
    y = [tsp.cities[i].y for i in path]

    # 闭合路径
    x.append(x[0])
    y.append(y[0])

    # 绘制路径
    ax.plot(x, y, 'b-', linewidth=2, alpha=0.7)
    ax.plot(x, y, 'ro', markersize=10, alpha=0.8)

    # 标注城市名称
    for i, city_idx in enumerate(path):
        city = tsp.cities[city_idx]
        ax.annotate(
            city.name,
            (city.x, city.y),
            textcoords="offset points",
            xytext=(0, 10),
            ha='center',
            fontsize=9
        )

    # 标注起点
    ax.plot(x[0], y[0], 'g*', markersize=15, label='起点')

    total_distance = tsp.calculate_total_distance(path)
    ax.set_title(f"{title}\n总距离: {total_distance:.2f}", fontsize=12)
    ax.set_xlabel('X坐标')
    ax.set_ylabel('Y坐标')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')

    return fig


def plot_optimization_animation(
    tsp: TSP,
    solutions: List[List[int]],
    title: str = "优化过程"
):
    """
    绘制优化过程动画（静态展示）

    参数:
        tsp: TSP实例
        solutions: 解序列
        title: 图表标题
    """
    n_plots = min(4, len(solutions))
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle(title, fontsize=16)

    indices = np.linspace(0, len(solutions) - 1, n_plots, dtype=int)

    for idx, (ax, sol_idx) in enumerate(zip(axes.flat, indices)):
        path = solutions[sol_idx]
        x = [tsp.cities[i].x for i in path] + [tsp.cities[path[0]].x]
        y = [tsp.cities[i].y for i in path] + [tsp.cities[path[0]].y]

        ax.plot(x, y, 'b-', linewidth=2, alpha=0.7)
        ax.plot(x, y, 'ro', markersize=8, alpha=0.8)

        distance = tsp.calculate_total_distance(path)
        ax.set_title(f"迭代 {sol_idx}\n距离: {distance:.2f}")
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')

    plt.tight_layout()
    return fig


def plot_cooling_schedules(initial_temp=100, final_temp=0.01, max_iter=1000):
    """
    对比不同冷却策略

    参数:
        initial_temp: 初始温度
        final_temp: 终止温度
        max_iter: 最大迭代次数
    """
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))

    iterations = np.arange(max_iter)

    # 指数冷却
    cooling_rate = 0.99
    temp_exp = initial_temp * (cooling_rate ** iterations)
    ax.plot(iterations, temp_exp, 'b-', linewidth=2, label='指数冷却')

    # 线性冷却
    temp_lin = initial_temp - ((initial_temp - final_temp) * iterations / max_iter)
    ax.plot(iterations, temp_lin, 'r-', linewidth=2, label='线性冷却')

    # 对数冷却
    alpha = 1.0
    temp_log = initial_temp / (1 + alpha * np.log(1 + iterations))
    ax.plot(iterations, temp_log, 'g-', linewidth=2, label='对数冷却')

    ax.set_xlabel('迭代次数', fontsize=12)
    ax.set_ylabel('温度', fontsize=12)
    ax.set_title('冷却策略对比', fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_yscale('log')

    return fig


def example_visualization():
    """可视化示例"""
    print("可视化示例")
    print("-" * 40)

    # 创建TSP实例
    tsp = TSP.create_random_instance(10, seed=42)
    path = tsp.generate_random_solution()

    # 绘制路径
    fig1 = plot_tsp_path(tsp, path, "随机初始路径")
    plt.savefig('tsp_initial.png', dpi=100, bbox_inches='tight')
    print("已保存: tsp_initial.png")

    # 绘制冷却策略对比
    fig2 = plot_cooling_schedules()
    plt.savefig('cooling_schedules.png', dpi=100, bbox_inches='tight')
    print("已保存: cooling_schedules.png")

    plt.show()


if __name__ == "__main__":
    example_visualization()
