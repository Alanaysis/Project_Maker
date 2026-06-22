"""
经验回放缓冲区

实现循环缓冲区，用于存储和采样经验数据。
"""

import random
from collections import deque
from typing import List, Tuple

import numpy as np


class ReplayBuffer:
    """
    经验回放缓冲区

    使用循环缓冲区存储经验 (state, action, reward, next_state, done)，
    并支持随机采样用于训练。

    Args:
        capacity: 缓冲区容量
    """

    def __init__(self, capacity: int):
        self.buffer: deque = deque(maxlen=capacity)

    def push(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
    ) -> None:
        """
        添加经验到缓冲区

        Args:
            state: 当前状态
            action: 执行的动作
            reward: 获得的奖励
            next_state: 下一个状态
            done: 是否结束
        """
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size: int) -> Tuple[np.ndarray, ...]:
        """
        随机采样一批经验

        Args:
            batch_size: 批次大小

        Returns:
            (states, actions, rewards, next_states, dones) 元组
        """
        batch = random.sample(self.buffer, batch_size)

        states = np.array([t[0] for t in batch])
        actions = np.array([t[1] for t in batch])
        rewards = np.array([t[2] for t in batch])
        next_states = np.array([t[3] for t in batch])
        dones = np.array([t[4] for t in batch])

        return states, actions, rewards, next_states, dones

    def __len__(self) -> int:
        """返回缓冲区当前大小"""
        return len(self.buffer)

    @property
    def is_ready(self) -> bool:
        """检查缓冲区是否已满"""
        return len(self.buffer) == self.buffer.maxlen
