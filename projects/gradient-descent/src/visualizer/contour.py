"""等高线图绘制器"""

import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, Optional


class ContourPlotter:
    """等高线图绘制器

    用于绘制测试函数的等高线图和优化轨迹。

    Args:
        func: 测试函数
        x_range: x 轴范围
        y_range: y 轴范围
        levels: 等高线层数
    """

    def __init__(
        self,
        func,
        x_range: Tuple[float, float] = (-5, 5),
        y_range: Tuple[float, float] = (-5, 5),
        levels: int = 20
    ):
        """初始化等高线图绘制器

        Args:
            func: 测试函数
            x_range: x 轴范围
            y_range: y 轴范围
            levels: 等高线层数
        """
        self.func = func
        self.x_range = x_range
        self.y_range = y_range
        self.levels = levels

    def _create_meshgrid(self, resolution: int = 100) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """创建网格数据

        Args:
            resolution: 网格分辨率

        Returns:
            (X, Y, Z) 网格数据
        """
        x = np.linspace(self.x_range[0], self.x_range[1], resolution)
        y = np.linspace(self.y_range[0], self.y_range[1], resolution)
        X, Y = np.meshgrid(x, y)
        Z = np.zeros_like(X)

        for i in range(resolution):
            for j in range(resolution):
                Z[i, j] = self.func(np.array([X[i, j], Y[i, j]]))

        return X, Y, Z

    def plot(
        self,
        trajectories: Optional[List[np.ndarray]] = None,
        labels: Optional[List[str]] = None,
        colors: Optional[List[str]] = None,
        title: str = "",
        figsize: Tuple[int, int] = (10, 8),
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """绘制等高线图和优化轨迹

        Args:
            trajectories: 优化轨迹列表
            labels: 轨迹标签列表
            colors: 轨迹颜色列表
            title: 图表标题
            figsize: 图表大小
            save_path: 保存路径

        Returns:
            matplotlib Figure 对象
        """
        fig, ax = plt.subplots(figsize=figsize)

        # 创建网格数据
        X, Y, Z = self._create_meshgrid()

        # 绘制等高线
        contour = ax.contourf(X, Y, Z, levels=self.levels, cmap='viridis', alpha=0.8)
        ax.contour(X, Y, Z, levels=self.levels, colors='black', linewidths=0.5, alpha=0.3)

        # 添加颜色条
        plt.colorbar(contour, ax=ax, label='f(x, y)')

        # 绘制优化轨迹
        if trajectories is not None:
            if labels is None:
                labels = [f'Trajectory {i+1}' for i in range(len(trajectories))]
            if colors is None:
                colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']

            for i, (traj, label) in enumerate(zip(trajectories, labels)):
                color = colors[i % len(colors)]
                ax.plot(traj[:, 0], traj[:, 1], '-', color=color, linewidth=2, label=label)
                ax.plot(traj[0, 0], traj[0, 1], 'o', color=color, markersize=8)
                ax.plot(traj[-1, 0], traj[-1, 1], '*', color=color, markersize=12)

        # 绘制最小值点
        min_x, min_val = self.func.minimum()
        ax.plot(min_x[0], min_x[1], 'r*', markersize=15, label='Minimum')

        # 设置图表
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_title(title if title else f'{self.func.name} Function')
        ax.set_xlim(self.x_range)
        ax.set_ylim(self.y_range)
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 保存图表
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig

    def plot_3d(
        self,
        figsize: Tuple[int, int] = (12, 8),
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """绘制 3D 表面图

        Args:
            figsize: 图表大小
            save_path: 保存路径

        Returns:
            matplotlib Figure 对象
        """
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111, projection='3d')

        # 创建网格数据
        X, Y, Z = self._create_meshgrid(resolution=50)

        # 绘制表面
        surf = ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.8)

        # 添加颜色条
        fig.colorbar(surf, ax=ax, label='f(x, y)')

        # 设置图表
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_zlabel('f(x, y)')
        ax.set_title(f'{self.func.name} Function (3D)')

        # 保存图表
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig
