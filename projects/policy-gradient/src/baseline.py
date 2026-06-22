"""
基线模块

实现用于减少策略梯度方差的基线方法。
基线不改变梯度的期望值，但可以显著降低方差。
"""

import torch
import torch.nn as nn
from abc import ABC, abstractmethod
from typing import List


class Baseline(ABC):
    """
    基线抽象基类

    基线 b(s) 用于计算优势函数：A(s,a) = R - b(s)
    理论上，任何不依赖于动作的基线都不会引入偏差。
    """

    @abstractmethod
    def get_baseline(self, returns: torch.Tensor) -> torch.Tensor:
        """
        获取基线值

        Args:
            returns: 回报值张量

        Returns:
            基线值，与 returns 形状相同
        """
        pass

    def compute_advantage(self, returns: torch.Tensor) -> torch.Tensor:
        """
        计算优势函数

        Args:
            returns: 回报值张量

        Returns:
            优势值 = 回报值 - 基线值
        """
        baseline = self.get_baseline(returns)
        return returns - baseline


class NoBaseline(Baseline):
    """
    无基线

    直接使用回报值作为优势，不做任何减法。
    这是最简单的策略梯度方法。
    """

    def get_baseline(self, returns: torch.Tensor) -> torch.Tensor:
        return torch.zeros_like(returns)


class ConstantBaseline(Baseline):
    """
    常数基线

    使用固定的常数作为基线。
    通常使用回报的平均值。

    Args:
        value: 基线常数值
    """

    def __init__(self, value: float = 0.0):
        self.value = value

    def get_baseline(self, returns: torch.Tensor) -> torch.Tensor:
        return torch.full_like(returns, self.value)


class MovingAverageBaseline(Baseline):
    """
    移动平均基线

    使用历史回报的移动平均作为基线。
    这是一种自适应基线，不需要额外的网络。

    Args:
        alpha: 移动平均系数（0到1之间）
    """

    def __init__(self, alpha: float = 0.01):
        self.alpha = alpha
        self.running_mean: float = 0.0
        self.initialized: bool = False

    def get_baseline(self, returns: torch.Tensor) -> torch.Tensor:
        # 更新移动平均
        batch_mean = returns.mean().item()
        if not self.initialized:
            self.running_mean = batch_mean
            self.initialized = True
        else:
            self.running_mean = (
                (1 - self.alpha) * self.running_mean
                + self.alpha * batch_mean
            )
        return torch.full_like(returns, self.running_mean)

    def reset(self):
        """重置基线状态"""
        self.running_mean = 0.0
        self.initialized = False


class ValueBaseline(Baseline):
    """
    价值网络基线

    使用独立的价值网络 V(s) 作为基线。
    价值网络通过最小化均方误差来学习状态价值函数。

    Args:
        value_network: 价值网络
        optimizer: 优化器
        loss_fn: 损失函数
    """

    def __init__(
        self,
        value_network: nn.Module,
        optimizer: torch.optim.Optimizer,
        loss_fn: nn.Module = None,
    ):
        self.value_network = value_network
        self.optimizer = optimizer
        self.loss_fn = loss_fn or nn.MSELoss()

    def get_baseline(self, returns: torch.Tensor) -> torch.Tensor:
        # 这里需要状态信息，实际使用时需要调用 train_step
        # 返回零作为默认值
        return torch.zeros_like(returns)

    def get_value(self, states: torch.Tensor) -> torch.Tensor:
        """
        获取状态价值

        Args:
            states: 状态张量

        Returns:
            状态价值估计
        """
        return self.value_network(states).squeeze(-1)

    def train_step(
        self, states: torch.Tensor, returns: torch.Tensor
    ) -> float:
        """
        训练价值网络

        Args:
            states: 状态张量
            returns: 目标回报值

        Returns:
            损失值
        """
        values = self.get_value(states)
        loss = self.loss_fn(values, returns.detach())

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return loss.item()


class ValueNetwork(nn.Module):
    """
    价值网络

    用于估计状态价值函数 V(s)。

    Args:
        state_dim: 状态空间维度
        hidden_dims: 隐藏层维度列表
    """

    def __init__(
        self,
        state_dim: int,
        hidden_dims: List[int] = None,
    ):
        super().__init__()

        if hidden_dims is None:
            hidden_dims = [128, 64]

        layers = []
        prev_dim = state_dim

        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            prev_dim = hidden_dim

        layers.append(nn.Linear(prev_dim, 1))

        self.network = nn.Sequential(*layers)

        # 初始化权重
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.orthogonal_(module.weight, gain=1.0)
                nn.init.constant_(module.bias, 0)

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        return self.network(state)
