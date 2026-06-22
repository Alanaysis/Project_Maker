"""
DQN 神经网络模型

实现深度 Q 网络，用于近似 Q 值函数。
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class DQN(nn.Module):
    """
    深度 Q 网络

    使用全连接神经网络近似 Q 值函数 Q(s, a)。

    Args:
        state_dim: 状态空间维度
        action_dim: 动作空间维度
        hidden_dim: 隐藏层维度，默认 128
    """

    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 128):
        super(DQN, self).__init__()

        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, action_dim)

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        Args:
            state: 状态张量，形状 (batch_size, state_dim)

        Returns:
            Q 值张量，形状 (batch_size, action_dim)
        """
        x = F.relu(self.fc1(state))
        x = F.relu(self.fc2(x))
        return self.fc3(x)

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
            # 随机探索
            return torch.randint(0, self.fc3.out_features, (1,)).item()
        else:
            # 贪婪选择
            with torch.no_grad():
                q_values = self.forward(state.unsqueeze(0))
                return q_values.argmax(dim=1).item()
