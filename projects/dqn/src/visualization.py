"""
可视化工具

提供奖励曲线绘制、Q 值变化监控等功能。
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import List, Optional, Dict
from collections import defaultdict


class TrainingVisualizer:
    """
    训练可视化器

    记录和可视化训练过程中的指标。

    Args:
        save_dir: 保存目录
    """

    def __init__(self, save_dir: str = "plots"):
        self.save_dir = save_dir
        self.metrics = defaultdict(list)
        self.episode_count = 0

    def record(self, **kwargs) -> None:
        """
        记录指标

        Args:
            **kwargs: 指标名称和值
        """
        for key, value in kwargs.items():
            self.metrics[key].append(value)
        self.episode_count += 1

    def plot_rewards(
        self,
        rewards: Optional[List[float]] = None,
        window_size: int = 100,
        save_path: Optional[str] = None,
        show: bool = False,
    ) -> None:
        """
        绘制奖励曲线

        Args:
            rewards: 奖励列表，如果为 None 则使用记录的奖励
            window_size: 移动平均窗口大小
            save_path: 保存路径
            show: 是否显示
        """
        if rewards is None:
            rewards = self.metrics.get("reward", [])

        if len(rewards) == 0:
            print("没有奖励数据可绘制")
            return

        plt.figure(figsize=(12, 6))

        # 原始奖励
        plt.plot(rewards, alpha=0.3, color="blue", label="Episode Reward")

        # 移动平均
        if len(rewards) >= window_size:
            moving_avg = np.convolve(
                rewards, np.ones(window_size) / window_size, mode="valid"
            )
            plt.plot(
                range(window_size - 1, len(rewards)),
                moving_avg,
                color="red",
                linewidth=2,
                label=f"{window_size}-Episode Moving Avg",
            )

        plt.xlabel("Episode")
        plt.ylabel("Reward")
        plt.title("Training Rewards")
        plt.legend()
        plt.grid(True, alpha=0.3)

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            print(f"奖励曲线已保存到: {save_path}")

        if show:
            plt.show()
        else:
            plt.close()

    def plot_q_values(
        self,
        q_values: Optional[List[float]] = None,
        save_path: Optional[str] = None,
        show: bool = False,
    ) -> None:
        """
        绘制 Q 值变化曲线

        Args:
            q_values: Q 值列表
            save_path: 保存路径
            show: 是否显示
        """
        if q_values is None:
            q_values = self.metrics.get("q_value", [])

        if len(q_values) == 0:
            print("没有 Q 值数据可绘制")
            return

        plt.figure(figsize=(12, 6))

        plt.plot(q_values, alpha=0.6, color="green", label="Mean Q Value")

        # 移动平均
        window_size = min(100, len(q_values) // 10)
        if window_size > 1:
            moving_avg = np.convolve(
                q_values, np.ones(window_size) / window_size, mode="valid"
            )
            plt.plot(
                range(window_size - 1, len(q_values)),
                moving_avg,
                color="darkgreen",
                linewidth=2,
                label=f"{window_size}-Step Moving Avg",
            )

        plt.xlabel("Training Step")
        plt.ylabel("Q Value")
        plt.title("Q Value Over Training")
        plt.legend()
        plt.grid(True, alpha=0.3)

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            print(f"Q 值曲线已保存到: {save_path}")

        if show:
            plt.show()
        else:
            plt.close()

    def plot_loss(
        self,
        losses: Optional[List[float]] = None,
        save_path: Optional[str] = None,
        show: bool = False,
    ) -> None:
        """
        绘制损失曲线

        Args:
            losses: 损失列表
            save_path: 保存路径
            show: 是否显示
        """
        if losses is None:
            losses = self.metrics.get("loss", [])

        if len(losses) == 0:
            print("没有损失数据可绘制")
            return

        plt.figure(figsize=(12, 6))

        plt.plot(losses, alpha=0.3, color="orange", label="Loss")

        # 移动平均
        window_size = min(100, len(losses) // 10)
        if window_size > 1:
            moving_avg = np.convolve(
                losses, np.ones(window_size) / window_size, mode="valid"
            )
            plt.plot(
                range(window_size - 1, len(losses)),
                moving_avg,
                color="red",
                linewidth=2,
                label=f"{window_size}-Step Moving Avg",
            )

        plt.xlabel("Training Step")
        plt.ylabel("Loss")
        plt.title("Training Loss")
        plt.legend()
        plt.grid(True, alpha=0.3)

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            print(f"损失曲线已保存到: {save_path}")

        if show:
            plt.show()
        else:
            plt.close()

    def plot_epsilon(
        self,
        epsilon_values: Optional[List[float]] = None,
        save_path: Optional[str] = None,
        show: bool = False,
    ) -> None:
        """
        绘制探索率变化曲线

        Args:
            epsilon_values: 探索率列表
            save_path: 保存路径
            show: 是否显示
        """
        if epsilon_values is None:
            epsilon_values = self.metrics.get("epsilon", [])

        if len(epsilon_values) == 0:
            print("没有探索率数据可绘制")
            return

        plt.figure(figsize=(12, 6))

        plt.plot(epsilon_values, color="purple", label="Epsilon")
        plt.xlabel("Episode")
        plt.ylabel("Epsilon")
        plt.title("Exploration Rate (Epsilon) Decay")
        plt.legend()
        plt.grid(True, alpha=0.3)

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            print(f"探索率曲线已保存到: {save_path}")

        if show:
            plt.show()
        else:
            plt.close()

    def plot_all(
        self,
        save_dir: Optional[str] = None,
        show: bool = False,
    ) -> None:
        """
        绘制所有指标

        Args:
            save_dir: 保存目录
            show: 是否显示
        """
        if save_dir is None:
            save_dir = self.save_dir

        import os
        os.makedirs(save_dir, exist_ok=True)

        # 绘制奖励曲线
        if "reward" in self.metrics:
            self.plot_rewards(
                save_path=os.path.join(save_dir, "rewards.png"),
                show=show,
            )

        # 绘制 Q 值曲线
        if "q_value" in self.metrics:
            self.plot_q_values(
                save_path=os.path.join(save_dir, "q_values.png"),
                show=show,
            )

        # 绘制损失曲线
        if "loss" in self.metrics:
            self.plot_loss(
                save_path=os.path.join(save_dir, "loss.png"),
                show=show,
            )

        # 绘制探索率曲线
        if "epsilon" in self.metrics:
            self.plot_epsilon(
                save_path=os.path.join(save_dir, "epsilon.png"),
                show=show,
            )

    def plot_comparison(
        self,
        results: Dict[str, List[float]],
        title: str = "Algorithm Comparison",
        save_path: Optional[str] = None,
        show: bool = False,
    ) -> None:
        """
        绘制算法对比图

        Args:
            results: 算法名称到奖励列表的映射
            title: 图表标题
            save_path: 保存路径
            show: 是否显示
        """
        plt.figure(figsize=(12, 6))

        colors = ["blue", "red", "green", "orange", "purple"]

        for i, (name, rewards) in enumerate(results.items()):
            color = colors[i % len(colors)]
            plt.plot(rewards, alpha=0.3, color=color, label=f"{name} (raw)")

            # 移动平均
            window_size = min(100, len(rewards) // 10)
            if window_size > 1:
                moving_avg = np.convolve(
                    rewards, np.ones(window_size) / window_size, mode="valid"
                )
                plt.plot(
                    range(window_size - 1, len(rewards)),
                    moving_avg,
                    color=color,
                    linewidth=2,
                    label=f"{name} ({window_size}-ep avg)",
                )

        plt.xlabel("Episode")
        plt.ylabel("Reward")
        plt.title(title)
        plt.legend()
        plt.grid(True, alpha=0.3)

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            print(f"对比图已保存到: {save_path}")

        if show:
            plt.show()
        else:
            plt.close()


def plot_q_value_distribution(
    q_values: np.ndarray,
    action_names: Optional[List[str]] = None,
    save_path: Optional[str] = None,
    show: bool = False,
) -> None:
    """
    绘制 Q 值分布图

    Args:
        q_values: Q 值数组，形状 (batch_size, action_dim)
        action_names: 动作名称列表
        save_path: 保存路径
        show: 是否显示
    """
    plt.figure(figsize=(10, 6))

    action_dim = q_values.shape[1]

    for a in range(action_dim):
        label = action_names[a] if action_names else f"Action {a}"
        plt.hist(q_values[:, a], bins=50, alpha=0.5, label=label)

    plt.xlabel("Q Value")
    plt.ylabel("Frequency")
    plt.title("Q Value Distribution")
    plt.legend()
    plt.grid(True, alpha=0.3)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Q 值分布图已保存到: {save_path}")

    if show:
        plt.show()
    else:
        plt.close()
