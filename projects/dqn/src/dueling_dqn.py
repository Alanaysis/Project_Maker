"""
Dueling DQN 实现

将 Q 函数分解为状态价值和动作优势，提高状态价值估计。
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class DuelingDQN(nn.Module):
    """
    Dueling DQN 网络

    将 Q 函数分解为状态价值 V(s) 和动作优势 A(s,a)：
    Q(s,a) = V(s) + A(s,a) - mean(A(s,a))

    Args:
        state_dim: 状态空间维度
        action_dim: 动作空间维度
        hidden_dim: 隐藏层维度，默认 128
    """

    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 128):
        super(DuelingDQN, self).__init__()

        self.action_dim = action_dim

        # 共享特征层
        self.feature_layer = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )

        # 价值流 (Value Stream)
        self.value_stream = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
        )

        # 优势流 (Advantage Stream)
        self.advantage_stream = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, action_dim),
        )

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        Args:
            state: 状态张量，形状 (batch_size, state_dim)

        Returns:
            Q 值张量，形状 (batch_size, action_dim)
        """
        # 共享特征
        features = self.feature_layer(state)

        # 价值流
        value = self.value_stream(features)

        # 优势流
        advantage = self.advantage_stream(features)

        # 组合 Q 值: Q(s,a) = V(s) + A(s,a) - mean(A(s,a))
        q_values = value + advantage - advantage.mean(dim=1, keepdim=True)

        return q_values

    def get_action(self, state: torch.Tensor, epsilon: float = 0.0) -> int:
        """
        获取动作（epsilon-greedy 策略）

        Args:
            state: 状态张量，形状 (state_dim,)
            epsilon: 探索率

        Returns:
            选择的动作索引
        """
        if torch.rand(1).item() < epsilon:
            return torch.randint(0, self.action_dim, (1,)).item()
        else:
            with torch.no_grad():
                q_values = self.forward(state.unsqueeze(0))
                return q_values.argmax(dim=1).item()

    def get_value_and_advantage(
        self, state: torch.Tensor
    ) -> tuple:
        """
        获取状态价值和动作优势

        Args:
            state: 状态张量，形状 (batch_size, state_dim)

        Returns:
            (value, advantage) 元组
        """
        features = self.feature_layer(state)
        value = self.value_stream(features)
        advantage = self.advantage_stream(features)
        return value, advantage
