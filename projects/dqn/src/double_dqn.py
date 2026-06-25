"""
Double DQN 实现

解决标准 DQN 的过估计问题，通过分离动作选择和动作评估。
"""

import torch
import torch.nn as nn
from typing import Tuple

from .dqn import DQN


class DoubleDQN:
    """
    Double DQN 算法

    使用在线网络选择动作，目标网络评估动作，减少过估计。

    Args:
        state_dim: 状态空间维度
        action_dim: 动作空间维度
        hidden_dim: 隐藏层维度
    """

    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 128):
        self.state_dim = state_dim
        self.action_dim = action_dim

        # 在线网络
        self.online_net = DQN(state_dim, action_dim, hidden_dim)

        # 目标网络
        self.target_net = DQN(state_dim, action_dim, hidden_dim)

    def compute_target(
        self,
        next_states: torch.Tensor,
        rewards: torch.Tensor,
        dones: torch.Tensor,
        gamma: float = 0.99,
    ) -> torch.Tensor:
        """
        计算 Double DQN 目标值

        使用在线网络选择动作，目标网络评估动作。

        Args:
            next_states: 下一个状态张量
            rewards: 奖励张量
            dones: 结束标志张量
            gamma: 折扣因子

        Returns:
            目标 Q 值张量
        """
        with torch.no_grad():
            # 使用在线网络选择动作
            online_q_values = self.online_net(next_states)
            best_actions = online_q_values.argmax(dim=1, keepdim=True)

            # 使用目标网络评估动作
            target_q_values = self.target_net(next_states)
            next_q_values = target_q_values.gather(1, best_actions).squeeze(1)

            # 计算目标值
            target = rewards + gamma * next_q_values * (1 - dones)

        return target

    def update_target(self) -> None:
        """更新目标网络（硬更新）"""
        self.target_net.load_state_dict(self.online_net.state_dict())

    def soft_update(self, tau: float = 0.005) -> None:
        """
        软更新目标网络

        Args:
            tau: 插值系数
        """
        for target_param, online_param in zip(
            self.target_net.parameters(), self.online_net.parameters()
        ):
            target_param.data.copy_(
                tau * online_param.data + (1 - tau) * target_param.data
            )

    def get_action(self, state: torch.Tensor, epsilon: float = 0.0) -> int:
        """
        获取动作（epsilon-greedy 策略）

        Args:
            state: 状态张量
            epsilon: 探索率

        Returns:
            选择的动作索引
        """
        if torch.rand(1).item() < epsilon:
            return torch.randint(0, self.action_dim, (1,)).item()
        else:
            with torch.no_grad():
                q_values = self.online_net(state.unsqueeze(0))
                return q_values.argmax(dim=1).item()
