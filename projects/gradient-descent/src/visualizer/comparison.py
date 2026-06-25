"""对比可视化器"""

import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, Optional, Dict, Any


class ComparisonPlotter:
    """对比可视化器

    用于对比多个优化器的性能。

    Args:
        无参数
    """

    def __init__(self):
        """初始化对比可视化器"""
        pass

    def plot_optimization_comparison(
        self,
        results: Dict[str, Dict[str, Any]],
        title: str = "Optimization Comparison",
        figsize: Tuple[int, int] = (15, 10),
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """绘制优化对比图

        Args:
            results: 优化结果字典 {name: {'trajectory': ..., 'values': ..., 'grad_norms': ...}}
            title: 图表标题
            figsize: 图表大小
            save_path: 保存路径

        Returns:
            matplotlib Figure 对象
        """
        fig, axes = plt.subplots(2, 2, figsize=figsize)

        colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']

        # 绘制轨迹对比
        ax1 = axes[0, 0]
        for i, (name, result) in enumerate(results.items()):
            color = colors[i % len(colors)]
            if 'trajectory' in result:
                traj = result['trajectory']
                ax1.plot(traj[:, 0], traj[:, 1], '-',
                        color=color, linewidth=2, label=name)
                ax1.plot(traj[0, 0], traj[0, 1], 'o', color=color, markersize=8)
                ax1.plot(traj[-1, 0], traj[-1, 1], '*', color=color, markersize=12)
        ax1.set_xlabel('x')
        ax1.set_ylabel('y')
        ax1.set_title('Optimization Trajectories')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 绘制收敛曲线
        ax2 = axes[0, 1]
        for i, (name, result) in enumerate(results.items()):
            color = colors[i % len(colors)]
            if 'values' in result:
                ax2.plot(result['values'], '-',
                        color=color, linewidth=2, label=name)
        ax2.set_xlabel('Iteration')
        ax2.set_ylabel('Function Value')
        ax2.set_title('Convergence')
        ax2.set_yscale('log')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 绘制梯度范数
        ax3 = axes[1, 0]
        for i, (name, result) in enumerate(results.items()):
            color = colors[i % len(colors)]
            if 'grad_norms' in result:
                ax3.plot(result['grad_norms'], '-',
                        color=color, linewidth=2, label=name)
        ax3.set_xlabel('Iteration')
        ax3.set_ylabel('Gradient Norm')
        ax3.set_title('Gradient Norm')
        ax3.set_yscale('log')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # 绘制性能统计
        ax4 = axes[1, 1]
        names = list(results.keys())
        iterations = [results[name].get('iterations', 0) for name in names]
        x = np.arange(len(names))
        bars = ax4.bar(x, iterations, color=colors[:len(names)])
        ax4.set_xlabel('Optimizer')
        ax4.set_ylabel('Iterations to Converge')
        ax4.set_title('Convergence Speed')
        ax4.set_xticks(x)
        ax4.set_xticklabels(names, rotation=45, ha='right')
        ax4.grid(True, alpha=0.3, axis='y')

        # 添加数值标签
        for bar, val in zip(bars, iterations):
            ax4.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                    f'{val}', ha='center', va='bottom')

        plt.suptitle(title, fontsize=16)
        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig

    def create_performance_table(
        self,
        results: Dict[str, Dict[str, Any]]
    ) -> str:
        """创建性能对比表

        Args:
            results: 优化结果字典

        Returns:
            性能对比表字符串
        """
        # 表头
        table = "=" * 80 + "\n"
        table += f"{'Optimizer':<20} {'Iterations':<15} {'Final Value':<15} {'Final Grad Norm':<15}\n"
        table += "=" * 80 + "\n"

        # 数据行
        for name, result in results.items():
            iterations = result.get('iterations', 'N/A')
            final_value = result.get('final_value', 'N/A')
            final_grad_norm = result.get('final_grad_norm', 'N/A')

            if isinstance(final_value, float):
                final_value = f"{final_value:.6e}"
            if isinstance(final_grad_norm, float):
                final_grad_norm = f"{final_grad_norm:.6e}"

            table += f"{name:<20} {iterations:<15} {final_value:<15} {final_grad_norm:<15}\n"

        table += "=" * 80

        return table

    def plot_convergence_speed(
        self,
        results: Dict[str, Dict[str, Any]],
        target_value: float,
        title: str = "Convergence Speed Comparison",
        figsize: Tuple[int, int] = (10, 6),
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """绘制收敛速度对比

        Args:
            results: 优化结果字典
            target_value: 目标函数值
            title: 图表标题
            figsize: 图表大小
            save_path: 保存路径

        Returns:
            matplotlib Figure 对象
        """
        fig, ax = plt.subplots(figsize=figsize)

        colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']

        for i, (name, result) in enumerate(results.items()):
            color = colors[i % len(colors)]
            if 'values' in result:
                values = result['values']
                # 找到达到目标值的迭代次数
                reached = np.where(values <= target_value)[0]
                if len(reached) > 0:
                    convergence_iter = reached[0]
                    ax.plot(convergence_iter, target_value, 'o',
                            color=color, markersize=10, label=f'{name} ({convergence_iter} iters)')
                else:
                    ax.plot(len(values), values[-1], 'x',
                            color=color, markersize=10, label=f'{name} (not converged)')

        ax.axhline(y=target_value, color='black', linestyle='--', alpha=0.5, label=f'Target: {target_value:.2e}')
        ax.set_xlabel('Optimizer')
        ax.set_ylabel('Iterations to Reach Target')
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig
