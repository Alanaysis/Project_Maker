#!/usr/bin/env python3
"""
2D 函数可视化与动画 (2D Function Visualization with Animation)

使用 matplotlib 可视化模拟退火算法在 2D 函数上的搜索过程。

功能：
1. 绘制目标函数的 3D 表面图
2. 可视化搜索轨迹
3. 动画展示搜索过程
4. 对比不同冷却策略的效果
"""

import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
try:
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def rosenbrock_2d(x, y):
    """2D Rosenbrock 函数"""
    return (1 - x) ** 2 + 100 * (y - x ** 2) ** 2


def rastrigin_2d(x, y):
    """2D Rastrigin 函数"""
    A = 10
    return (
        2 * A
        + x ** 2 - A * math.cos(2 * math.pi * x)
        + y ** 2 - A * math.cos(2 * math.pi * y)
    )


def sphere_2d(x, y):
    """2D Sphere 函数"""
    return x ** 2 + y ** 2


def griewank_2d(x, y):
    """2D Griewank 函数"""
    return 1 + (x ** 2 + y ** 2) / 4000 - math.cos(x) * math.cos(y / math.sqrt(2))


# 测试函数字典
TEST_FUNCTIONS = {
    "Sphere": sphere_2d,
    "Rastrigin": rastrigin_2d,
    "Rosenbrock": rosenbrock_2d,
    "Griewank": griewank_2d,
}


def create_grid(func, x_range=(-5, 5), y_range=(-5, 5), resolution=100):
    """创建函数值的网格"""
    x = np.linspace(x_range[0], x_range[1], resolution)
    y = np.linspace(y_range[0], y_range[1], resolution)
    X, Y = np.meshgrid(x, y)
    Z = np.array([[func(xi, yi) for xi in x] for yi in y])
    return X, Y, Z


def visualize_search_trajectory(func_name, trajectory, energy_history, temperature_history):
    """
    可视化搜索轨迹

    Args:
        func_name: 函数名称
        trajectory: 搜索轨迹 [(x, y), ...]
        energy_history: 能量历史
        temperature_history: 温度历史
    """
    if not HAS_MATPLOTLIB:
        print("需要安装 matplotlib: pip install matplotlib")
        return

    func = TEST_FUNCTIONS[func_name]
    X, Y, Z = create_grid(func)

    fig, axes = plt.subplots(2, 2, figsize=(14, 12))

    # 1. 函数表面 + 搜索轨迹
    ax1 = axes[0, 0]
    ax1.contourf(X, Y, Z, levels=50, cmap="viridis")
    traj_x = [p[0] for p in trajectory]
    traj_y = [p[1] for p in trajectory]
    ax1.plot(traj_x, traj_y, "r-", alpha=0.3, linewidth=0.5)
    ax1.plot(traj_x[:1], traj_y[:1], "go", markersize=10, label="起点")
    ax1.plot(traj_x[-1], traj_y[-1], "ro", markersize=10, label="终点")
    ax1.set_title(f"{func_name} - 搜索轨迹")
    ax1.legend()
    ax1.set_xlabel("x")
    ax1.set_ylabel("y")

    # 2. 能量变化曲线
    ax2 = axes[0, 1]
    ax2.plot(energy_history, "b-", linewidth=0.5, alpha=0.7)
    ax2.set_title("能量变化曲线")
    ax2.set_xlabel("迭代次数")
    ax2.set_ylabel("能量值")
    ax2.set_yscale("log")

    # 3. 温度变化曲线
    ax3 = axes[1, 0]
    ax3.plot(temperature_history, "r-", linewidth=0.5, alpha=0.7)
    ax3.set_title("温度变化曲线")
    ax3.set_xlabel("迭代次数")
    ax3.set_ylabel("温度")
    ax3.set_yscale("log")

    # 4. 等高线图 + 轨迹
    ax4 = axes[1, 1]
    levels = np.logspace(math.log10(max(Z.min(), 1e-10)), math.log10(Z.max()), 30)
    ax4.contour(X, Y, Z, levels=levels, cmap="viridis", alpha=0.8)
    ax4.plot(traj_x, traj_y, "r-", alpha=0.5, linewidth=0.5)
    ax4.plot(traj_x[:1], traj_y[:1], "go", markersize=8, label="起点")
    ax4.plot(traj_x[-1], traj_y[-1], "ro", markersize=8, label="终点")
    ax4.set_title(f"{func_name} - 等高线图")
    ax4.legend()
    ax4.set_xlabel("x")
    ax4.set_ylabel("y")

    plt.tight_layout()
    plt.savefig("search_trajectory.png", dpi=150, bbox_inches="tight")
    print("搜索轨迹图已保存到: search_trajectory.png")
    plt.show()


def animate_search(func_name, trajectory, energy_history, temperature_history, output_file="sa_animation.mp4"):
    """
    动画展示搜索过程

    Args:
        func_name: 函数名称
        trajectory: 搜索轨迹
        energy_history: 能量历史
        temperature_history: 温度历史
        output_file: 输出动画文件
    """
    if not HAS_MATPLOTLIB:
        print("需要安装 matplotlib: pip install matplotlib")
        return

    func = TEST_FUNCTIONS[func_name]
    X, Y, Z = create_grid(func)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # 左图：函数 + 轨迹动画
    contour = ax1.contourf(X, Y, Z, levels=50, cmap="viridis")
    ax1.set_title(f"{func_name} - 搜索动画")
    ax1.set_xlabel("x")
    ax1.set_ylabel("y")
    plt.colorbar(contour, ax=ax1)

    line, = ax1.plot([], [], "r-", linewidth=1.5)
    dot, = ax1.plot([], [], "ro", markersize=8)
    best_dot, = ax1.plot([], [], "go", markersize=10, label="最优")

    def init():
        line.set_data([], [])
        dot.set_data([], [])
        best_dot.set_data([], [])
        return line, dot, best_dot

    def update(frame):
        traj_x = [trajectory[i][0] for i in range(min(frame + 1, len(trajectory)))]
        traj_y = [trajectory[i][1] for i in range(min(frame + 1, len(trajectory)))]
        line.set_data(traj_x, traj_y)
        if traj_x:
            dot.set_data([traj_x[-1]], [traj_y[-1]])
            best_x = [trajectory[i][0] for i in range(frame + 1)]
            best_y = [trajectory[i][1] for i in range(frame + 1)]
            best_idx = min(range(len(best_x)), key=lambda i: energy_history[i])
            best_dot.set_data([best_x[best_idx]], [best_y[best_idx]])
        return line, dot, best_dot

    n_frames = min(len(trajectory), 500)
    anim = FuncAnimation(
        fig, update, frames=n_frames, init_func=init, blit=True, interval=10
    )

    # 右图：能量和温度
    ax2.plot(energy_history, "b-", linewidth=0.5, alpha=0.7, label="能量")
    ax2.plot(temperature_history, "r-", linewidth=0.5, alpha=0.7, label="温度")
    ax2.set_title("能量和温度变化")
    ax2.set_xlabel("迭代次数")
    ax2.set_ylabel("值")
    ax2.set_yscale("log")
    ax2.legend()

    plt.tight_layout()
    try:
        anim.save(output_file, writer="ffmpeg", fps=30)
        print(f"动画已保存到: {output_file}")
    except Exception as e:
        print(f"保存动画失败: {e}")
        print("尝试保存为 GIF...")
        try:
            anim.save("sa_animation.gif", writer="pillow", fps=30)
            print("GIF 已保存到: sa_animation.gif")
        except Exception:
            print("无法保存动画，显示图形窗口...")
    plt.show()


def compare_strategies(func_name="Rastrigin"):
    """
    比较不同策略的效果

    Args:
        func_name: 测试函数名称
    """
    if not HAS_MATPLOTLIB:
        print("需要安装 matplotlib: pip install matplotlib")
        return

    func = TEST_FUNCTIONS[func_name]

    # 生成函数网格
    X, Y, Z = create_grid(func)

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    strategies = [
        ("交换策略 (Swap)", 10000.0, 0.995, "swap"),
        ("插入策略 (Insert)", 10000.0, 0.995, "insert"),
        ("反转策略 (Reverse)", 10000.0, 0.995, "reverse"),
    ]

    for idx, (name, temp, rate, strategy) in enumerate(strategies):
        ax = axes[idx]
        ax.contourf(X, Y, Z, levels=50, cmap="viridis")
        ax.set_title(f"{name}\n最优值: TBD")
        ax.set_xlabel("x")
        ax.set_ylabel("y")

    plt.tight_layout()
    plt.savefig("strategy_comparison.png", dpi=150, bbox_inches="tight")
    print(f"策略对比图已保存到: strategy_comparison.png")
    plt.show()


def main():
    """主函数"""
    print("=" * 60)
    print("2D 函数可视化与动画")
    print("=" * 60)

    if not HAS_MATPLOTLIB:
        print("请先安装 matplotlib: pip install matplotlib")
        return

    # 使用 Rosenbrock 函数演示
    func_name = "Rosenbrock"

    # 生成搜索轨迹（简化版）
    trajectory = [(0.5, 0.5)]
    energy_history = [rosenbrock_2d(0.5, 0.5)]
    temperature_history = [10000.0]

    # 模拟搜索过程
    random_seed = 42
    x, y = 0.5, 0.5
    temp = 10000.0
    best_x, best_y = x, y
    best_energy = rosenbrock_2d(x, y)

    for i in range(2000):
        temp *= 0.995
        # 邻域搜索
        x_new = x + random.gauss(0, max(temp * 0.001, 0.01))
        y_new = y + random.gauss(0, max(temp * 0.001, 0.01))

        # 接受准则
        e_new = rosenbrock_2d(x_new, y_new)
        delta_e = e_new - rosenbrock_2d(x, y)

        if delta_e < 0 or random.random() < math.exp(-delta_e / max(temp, 1e-10)):
            x, y = x_new, y_new

        if rosenbrock_2d(x, y) < best_energy:
            best_x, best_y = x, y
            best_energy = rosenbrock_2d(x, y)

        trajectory.append((x, y))
        energy_history.append(rosenbrock_2d(x, y))
        temperature_history.append(temp)

    print(f"最优解: ({best_x:.6f}, {best_y:.6f})")
    print(f"最优值: {best_energy:.8f}")

    # 可视化
    visualize_search_trajectory(func_name, trajectory, energy_history, temperature_history)

    # 动画
    try:
        animate_search(func_name, trajectory, energy_history, temperature_history)
    except Exception as e:
        print(f"动画生成跳过: {e}")


if __name__ == "__main__":
    import random
    main()
