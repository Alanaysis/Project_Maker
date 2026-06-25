"""轨迹可视化器"""

import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, Optional, Dict


class TrajectoryPlotter:
    """轨迹可视化器

    用于绘制和分析优化轨迹。

    Args:
        无参数
    """

    def __init__(self):
        """初始化轨迹可视化器"""
        pass

    def plot_trajectory(
        self,
        trajectory: np.ndarray,
        label: str = "",
        color: str = "blue",
        alpha: float = 1.0,
        linewidth: float = 2.0,
        show_start: bool = True,
        show_end: bool = True
    ) -> plt.Axes:
        """绘制单个优化轨迹

        Args:
            trajectory: 轨迹点数组 (N, 2)
            label: 标签
            color: 颜色
            alpha: 透明度
            linewidth: 线宽
            show_start: 是否显示起点
            show_end: 是否显示终点

        Returns:
            matplotlib Axes 对象
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        # 绘制轨迹线
        ax.plot(trajectory[:, 0], trajectory[:, 1], '-',
                color=color, linewidth=linewidth, alpha=alpha, label=label)

        # 绘制起点
        if show_start:
            ax.plot(trajectory[0, 0], trajectory[0, 1], 'o',
                    color=color, markersize=10, label='Start')

        # 绘制终点
        if show_end:
            ax.plot(trajectory[-1, 0], trajectory[-1, 1], '*',
                    color=color, markersize=15, label='End')

        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_title('Optimization Trajectory')
        ax.legend()
        ax.grid(True, alpha=0.3)

        return ax

    def compare_trajectories(
        self,
        trajectories: Dict[str, np.ndarray],
        colors: Optional[List[str]] = None,
        title: str = "Optimization Trajectories Comparison",
        figsize: Tuple[int, int] = (12, 8),
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """对比多个优化轨迹

        Args:
            trajectories: 轨迹字典 {name: trajectory}
            colors: 颜色列表
            title: 图表标题
            figsize: 图表大小
            save_path: 保存路径

        Returns:
            matplotlib Figure 对象
        """
        fig, ax = plt.subplots(figsize=figsize)

        if colors is None:
            colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']

        for i, (name, traj) in enumerate(trajectories.items()):
            color = colors[i % len(colors)]
            ax.plot(traj[:, 0], traj[:, 1], '-',
                    color=color, linewidth=2, label=name)
            ax.plot(traj[0, 0], traj[0, 1], 'o', color=color, markersize=8)
            ax.plot(traj[-1, 0], traj[-1, 1], '*', color=color, markersize=12)

        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig

    def plot_convergence(
        self,
        values: Dict[str, np.ndarray],
        title: str = "Convergence Comparison",
        figsize: Tuple[int, int] = (10, 6),
        y_scale: str = 'log',
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """绘制收敛曲线

        Args:
            values: 函数值字典 {name: values}
            title: 图表标题
            figsize: 图表大小
            y_scale: y 轴缩放 ('log' 或 'linear')
            save_path: 保存路径

        Returns:
            matplotlib Figure 对象
        """
        fig, ax = plt.subplots(figsize=figsize)

        colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']

        for i, (name, vals) in enumerate(values.items()):
            color = colors[i % len(colors)]
            ax.plot(vals, '-', color=color, linewidth=2, label=name)

        ax.set_xlabel('Iteration')
        ax.set_ylabel('Function Value')
        ax.set_title(title)
        ax.set_yscale(y_scale)
        ax.legend()
        ax.grid(True, alpha=0.3)

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig

    def plot_gradient_norm(
        self,
        grad_norms: Dict[str, np.ndarray],
        title: str = "Gradient Norm Comparison",
        figsize: Tuple[int, int] = (10, 6),
        y_scale: str = 'log',
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """绘制梯度范数曲线

        Args:
            grad_norms: 梯度范数字典 {name: norms}
            title: 图表标题
            figsize: 图表大小
            y_scale: y 轴缩放 ('log' 或 'linear')
            save_path: 保存路径

        Returns:
            matplotlib Figure 对象
        """
        fig, ax = plt.subplots(figsize=figsize)

        colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']

        for i, (name, norms) in enumerate(grad_norms.items()):
            color = colors[i % len(colors)]
            ax.plot(norms, '-', color=color, linewidth=2, label=name)

        ax.set_xlabel('Iteration')
        ax.set_ylabel('Gradient Norm')
        ax.set_title(title)
        ax.set_yscale(y_scale)
        ax.legend()
        ax.grid(True, alpha=0.3)

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig

    def plot_learning_rate(
        self,
        learning_rates: Dict[str, np.ndarray],
        title: str = "Learning Rate Schedule",
        figsize: Tuple[int, int] = (10, 6),
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """绘制学习率变化曲线

        Args:
            learning_rates: 学习率字典 {name: rates}
            title: 图表标题
            figsize: 图表大小
            save_path: 保存路径

        Returns:
            matplotlib Figure 对象
        """
        fig, ax = plt.subplots(figsize=figsize)

        colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']

        for i, (name, rates) in enumerate(learning_rates.items()):
            color = colors[i % len(colors)]
            ax.plot(rates, '-', color=color, linewidth=2, label=name)

        ax.set_xlabel('Iteration')
        ax.set_ylabel('Learning Rate')
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig
