"""
DQN 代理

实现 DQN 算法的核心逻辑，包括训练和动作选择。
"""

import copy
from typing import Optional

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from .dqn import DQN
from .replay_buffer import ReplayBuffer


class DQNAgent:
    """
    DQN 代理

    实现 DQN 算法，包括：
    - 当前网络和目标网络
    - 经验回放
    - epsilon-greedy 探索策略

    Args:
        state_dim: 状态空间维度
        action_dim: 动作空间维度
        hidden_dim: 隐藏层维度
        learning_rate: 学习率
        gamma: 折扣因子
        epsilon_start: 初始探索率
        epsilon_end: 最终探索率
        epsilon_decay: 探索率衰减
        buffer_size: 经验回放缓冲区大小
        batch_size: 训练批次大小
        target_update_freq: 目标网络更新频率
    """

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 128,
        learning_rate: float = 1e-3,
        gamma: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.01,
        epsilon_decay: float = 0.995,
        buffer_size: int = 10000,
        batch_size: int = 64,
        target_update_freq: int = 10,
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq

        # 设备
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # 当前网络
        self.policy_net = DQN(state_dim, action_dim, hidden_dim).to(self.device)

        # 目标网络（复制当前网络）
        self.target_net = copy.deepcopy(self.policy_net).to(self.device)
        self.target_net.eval()

        # 优化器
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=learning_rate)

        # 经验回放缓冲区
        self.replay_buffer = ReplayBuffer(buffer_size)

        # 训练步数
        self.train_step = 0

    def select_action(self, state: np.ndarray, training: bool = True) -> int:
        """
        选择动作

        Args:
            state: 当前状态
            training: 是否在训练模式

        Returns:
            选择的动作索引
        """
        if training and np.random.random() < self.epsilon:
            # 探索：随机选择动作
            return np.random.randint(self.action_dim)
        else:
            # 利用：选择 Q 值最大的动作
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            with torch.no_grad():
                q_values = self.policy_net(state_tensor)
            return q_values.argmax(dim=1).item()

    def store_experience(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
    ) -> None:
        """存储经验到回放缓冲区"""
        self.replay_buffer.push(state, action, reward, next_state, done)

    def train(self) -> Optional[float]:
        """
        训练一步

        Returns:
            损失值，如果缓冲区不足则返回 None
        """
        # 检查缓冲区是否有足够样本
        if len(self.replay_buffer) < self.batch_size:
            return None

        # 采样批次数据
        states, actions, rewards, next_states, dones = self.replay_buffer.sample(
            self.batch_size
        )

        # 转换为张量
        states = torch.FloatTensor(states).to(self.device)
        actions = torch.LongTensor(actions).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        next_states = torch.FloatTensor(next_states).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)

        # 计算当前 Q 值
        q_values = self.policy_net(states)
        q_values = q_values.gather(1, actions.unsqueeze(1)).squeeze(1)

        # 计算目标 Q 值
        with torch.no_grad():
            next_q_values = self.target_net(next_states)
            next_q_values = next_q_values.max(dim=1)[0]
            target_q_values = rewards + self.gamma * next_q_values * (1 - dones)

        # 计算损失
        loss = nn.MSELoss()(q_values, target_q_values)

        # 反向传播
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # 更新探索率
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

        # 更新目标网络
        self.train_step += 1
        if self.train_step % self.target_update_freq == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())

        return loss.item()

    def save(self, path: str) -> None:
        """保存模型"""
        torch.save(
            {
                "policy_net": self.policy_net.state_dict(),
                "target_net": self.target_net.state_dict(),
                "optimizer": self.optimizer.state_dict(),
                "epsilon": self.epsilon,
                "train_step": self.train_step,
            },
            path,
        )

    def load(self, path: str) -> None:
        """加载模型"""
        checkpoint = torch.load(path)
        self.policy_net.load_state_dict(checkpoint["policy_net"])
        self.target_net.load_state_dict(checkpoint["target_net"])
        self.optimizer.load_state_dict(checkpoint["optimizer"])
        self.epsilon = checkpoint["epsilon"]
        self.train_step = checkpoint["train_step"]
