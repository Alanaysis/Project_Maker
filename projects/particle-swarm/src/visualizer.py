"""
PSO 可视化模块

提供粒子群优化过程的可视化功能：
- 收敛曲线绘制
- 2D 搜索空间粒子分布
- 粒子轨迹动画
- 多函数对比图
"""

import numpy as np
from typing import Optional
from .functions import BENCHMARK_FUNCTIONS


class PSOVisualizer:
    """PSO 可视化工具"""

    @staticmethod
    def plot_convergence(
        history: list[float],
        title: str = "PSO 收敛曲线",
        figsize: tuple[int, int] = (10, 6),
    ) -> None:
        """
        绘制收敛曲线

        参数:
            history: 适应度历史记录
            title: 图表标题
            figsize: 图表大小
        """
        import matplotlib.pyplot as plt

        plt.figure(figsize=figsize)
        plt.plot(history, linewidth=2, color="#2196F3")
        plt.xlabel("迭代次数", fontsize=12)
        plt.ylabel("最佳适应度", fontsize=12)
        plt.title(title, fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.yscale("log")
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_2d_search_space(
        particles: list,
        bounds: tuple[float, float] = (-100.0, 100.0),
        objective_function=None,
        global_best=None,
        title: str = "PSO 搜索空间",
        figsize: tuple[int, int] = (10, 8),
    ) -> None:
        """
        绘制 2D 搜索空间中的粒子分布

        参数:
            particles: 粒子列表
            bounds: 搜索空间边界
            objective_function: 目标函数（用于绘制等高线）
            global_best: 全局最佳位置
            title: 图表标题
            figsize: 图表大小
        """
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=figsize)

        # 绘制等高线（如果提供了目标函数）
        if objective_function is not None:
            x = np.linspace(bounds[0], bounds[1], 100)
            y = np.linspace(bounds[0], bounds[1], 100)
            X, Y = np.meshgrid(x, y)
            Z = np.zeros_like(X)
            for i in range(100):
                for j in range(100):
                    Z[i, j] = objective_function(np.array([X[i, j], Y[i, j]]))
            ax.contourf(X, Y, Z, levels=20, cmap="viridis", alpha=0.3)
            ax.contour(X, Y, Z, levels=20, colors="gray", alpha=0.3, linewidths=0.5)

        # 绘制粒子
        positions = np.array([p.position for p in particles])
        ax.scatter(
            positions[:, 0],
            positions[:, 1],
            c="#FF5722",
            s=50,
            alpha=0.7,
            edgecolors="black",
            linewidths=0.5,
            label="粒子",
        )

        # 绘制全局最佳
        if global_best is not None:
            ax.scatter(
                global_best[0],
                global_best[1],
                c="#4CAF50",
                s=200,
                marker="*",
                edgecolors="black",
                linewidths=1,
                label="全局最佳",
                zorder=5,
            )

        ax.set_xlim(bounds)
        ax.set_ylim(bounds)
        ax.set_xlabel("x₁", fontsize=12)
        ax.set_ylabel("x₂", fontsize=12)
        ax.set_title(title, fontsize=14)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_trajectory(
        trajectories: list[list[np.ndarray]],
        bounds: tuple[float, float] = (-100.0, 100.0),
        objective_function=None,
        global_best=None,
        title: str = "PSO 粒子轨迹",
        figsize: tuple[int, int] = (10, 8),
        n_particles_to_show: int = 5,
    ) -> None:
        """
        绘制粒子轨迹

        参数:
            trajectories: 粒子轨迹列表
            bounds: 搜索空间边界
            objective_function: 目标函数
            global_best: 全局最佳位置
            title: 图表标题
            figsize: 图表大小
            n_particles_to_show: 显示多少个粒子的轨迹
        """
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=figsize)

        # 绘制等高线
        if objective_function is not None:
            x = np.linspace(bounds[0], bounds[1], 100)
            y = np.linspace(bounds[0], bounds[1], 100)
            X, Y = np.meshgrid(x, y)
            Z = np.zeros_like(X)
            for i in range(100):
                for j in range(100):
                    Z[i, j] = objective_function(np.array([X[i, j], Y[i, j]]))
            ax.contourf(X, Y, Z, levels=20, cmap="viridis", alpha=0.3)

        # 绘制轨迹
        colors = plt.cm.tab10(np.linspace(0, 1, min(n_particles_to_show, len(trajectories))))
        for i, color in enumerate(colors):
            if i >= len(trajectories):
                break
            traj = np.array(trajectories[i])
            ax.plot(
                traj[:, 0],
                traj[:, 1],
                color=color,
                linewidth=1.5,
                alpha=0.7,
                label=f"粒子 {i + 1}",
            )
            # 起点
            ax.scatter(traj[0, 0], traj[0, 1], c=color, s=80, marker="o", edgecolors="black")
            # 终点
            ax.scatter(traj[-1, 0], traj[-1, 1], c=color, s=80, marker="s", edgecolors="black")

        # 全局最佳
        if global_best is not None:
            ax.scatter(
                global_best[0],
                global_best[1],
                c="red",
                s=300,
                marker="*",
                edgecolors="black",
                linewidths=1,
                label="全局最佳",
                zorder=5,
            )

        ax.set_xlim(bounds)
        ax.set_ylim(bounds)
        ax.set_xlabel("x₁", fontsize=12)
        ax.set_ylabel("x₂", fontsize=12)
        ax.set_title(title, fontsize=14)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

    @staticmethod
    def compare_functions(
        results: dict[str, list[float]],
        title: str = "不同测试函数的收敛对比",
        figsize: tuple[int, int] = (12, 6),
    ) -> None:
        """
        对比不同测试函数的收敛曲线

        参数:
            results: {函数名: 适应度历史} 字典
            title: 图表标题
            figsize: 图表大小
        """
        import matplotlib.pyplot as plt

        plt.figure(figsize=figsize)
        colors = ["#2196F3", "#FF5722", "#4CAF50", "#9C27B0", "#FF9800"]

        for i, (name, history) in enumerate(results.items()):
            color = colors[i % len(colors)]
            plt.plot(history, linewidth=2, color=color, label=name)

        plt.xlabel("迭代次数", fontsize=12)
        plt.ylabel("最佳适应度", fontsize=12)
        plt.title(title, fontsize=14)
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.yscale("log")
        plt.tight_layout()
        plt.show()

    @staticmethod
    def compare_parameters(
        results: dict[str, list[float]],
        title: str = "不同参数的收敛对比",
        figsize: tuple[int, int] = (12, 6),
    ) -> None:
        """
        对比不同参数设置的收敛曲线

        参数:
            results: {参数描述: 适应度历史} 字典
            title: 图表标题
            figsize: 图表大小
        """
        import matplotlib.pyplot as plt

        plt.figure(figsize=figsize)
        colors = ["#2196F3", "#FF5722", "#4CAF50", "#9C27B0", "#FF9800"]

        for i, (name, history) in enumerate(results.items()):
            color = colors[i % len(colors)]
            plt.plot(history, linewidth=2, color=color, label=name)

        plt.xlabel("迭代次数", fontsize=12)
        plt.ylabel("最佳适应度", fontsize=12)
        plt.title(title, fontsize=14)
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.yscale("log")
        plt.tight_layout()
        plt.show()
