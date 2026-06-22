"""
策略网络模块

实现用于离散动作空间的策略网络。
网络输出动作的对数概率，用于策略梯度算法。
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical
from typing import List, Optional, Tuple


class PolicyNetwork(nn.Module):
    """
    策略网络

    用于离散动作空间的策略网络，输出动作概率分布。
    网络结构：输入层 -> 隐藏层 -> 输出层（带 Softmax）

    Args:
        state_dim: 状态空间维度
        action_dim: 动作空间维度
        hidden_dims: 隐藏层维度列表
        activation: 激活函数类型
    """

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dims: Optional[List[int]] = None,
        activation: str = "relu",
    ):
        super().__init__()

        if hidden_dims is None:
            hidden_dims = [128, 64]

        # 构建网络层
        layers = []
        prev_dim = state_dim

        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(self._get_activation(activation))
            prev_dim = hidden_dim

        # 输出层：输出每个动作的 logits
        layers.append(nn.Linear(prev_dim, action_dim))

        self.network = nn.Sequential(*layers)
        self.action_dim = action_dim

        # 初始化权重
        self._init_weights()

    def _get_activation(self, activation: str) -> nn.Module:
        """获取激活函数"""
        activations = {
            "relu": nn.ReLU(),
            "tanh": nn.Tanh(),
            "elu": nn.ELU(),
            "leaky_relu": nn.LeakyReLU(),
        }
        if activation not in activations:
            raise ValueError(f"Unknown activation: {activation}")
        return activations[activation]

    def _init_weights(self):
        """初始化网络权重"""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.orthogonal_(module.weight, gain=0.01)
                nn.init.constant_(module.bias, 0)

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        Args:
            state: 状态张量，shape: (batch_size, state_dim)

        Returns:
            动作的对数概率，shape: (batch_size, action_dim)
        """
        logits = self.network(state)
        return F.log_softmax(logits, dim=-1)

    def get_action(self, state: torch.Tensor) -> Tuple[int, torch.Tensor]:
        """
        根据状态选择动作

        Args:
            state: 状态张量，shape: (state_dim,)

        Returns:
            (action, log_prob): 选择的动作和对应的对数概率
        """
        with torch.no_grad():
            log_probs = self.forward(state.unsqueeze(0))
            dist = Categorical(logits=log_probs)
            action = dist.sample()
        return action.item(), log_probs[0, action]

    def get_log_prob(
        self, state: torch.Tensor, action: torch.Tensor
    ) -> torch.Tensor:
        """
        计算给定状态-动作对的对数概率

        Args:
            state: 状态张量，shape: (batch_size, state_dim)
            action: 动作张量，shape: (batch_size,)

        Returns:
            对数概率，shape: (batch_size,)
        """
        log_probs = self.forward(state)
        dist = Categorical(logits=log_probs)
        return dist.log_prob(action)

    def get_entropy(self, state: torch.Tensor) -> torch.Tensor:
        """
        计算策略的熵（用于探索正则化）

        Args:
            state: 状态张量，shape: (batch_size, state_dim)

        Returns:
            熵值，shape: (batch_size,)
        """
        log_probs = self.forward(state)
        dist = Categorical(logits=log_probs)
        return dist.entropy()
