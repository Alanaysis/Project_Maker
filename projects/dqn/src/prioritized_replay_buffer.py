"""
优先经验回放缓冲区

基于 TD 误差的优先级采样，重要经验被更频繁地回放。
"""

import random
import numpy as np
from typing import List, Tuple, Optional


class SumTree:
    """
    线段树实现，用于高效采样

    支持 O(log n) 的更新和采样操作。
    """

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.tree = np.zeros(2 * capacity - 1)
        self.data = [None] * capacity
        self.data_pointer = 0
        self.n_entries = 0

    def _propagate(self, idx: int, change: float) -> None:
        """向上传播更新"""
        parent = (idx - 1) // 2
        self.tree[parent] += change
        if parent != 0:
            self._propagate(parent, change)

    def _retrieve(self, idx: int, s: float) -> int:
        """检索叶节点"""
        left = 2 * idx + 1
        right = left + 1

        if left >= len(self.tree):
            return idx

        if s <= self.tree[left]:
            return self._retrieve(left, s)
        else:
            return self._retrieve(right, s - self.tree[left])

    @property
    def total(self) -> float:
        """返回总优先级"""
        return self.tree[0]

    def add(self, priority: float, data) -> None:
        """添加数据"""
        idx = self.data_pointer + self.capacity - 1
        self.data[self.data_pointer] = data
        self.update(idx, priority)
        self.data_pointer = (self.data_pointer + 1) % self.capacity
        if self.n_entries < self.capacity:
            self.n_entries += 1

    def update(self, idx: int, priority: float) -> None:
        """更新优先级"""
        change = priority - self.tree[idx]
        self.tree[idx] = priority
        self._propagate(idx, change)

    def get(self, s: float) -> Tuple[int, float, object]:
        """根据累计优先级采样"""
        idx = self._retrieve(0, s)
        data_idx = idx - self.capacity + 1
        return idx, self.tree[idx], self.data[data_idx]

    @property
    def min_priority(self) -> float:
        """返回最小优先级"""
        leaves = self.tree[self.capacity - 1 : self.capacity - 1 + self.n_entries]
        return np.min(leaves) if self.n_entries > 0 else 0.0


class PrioritizedReplayBuffer:
    """
    优先经验回放缓冲区

    使用 TD 误差作为优先级，重要经验被更频繁地回放。

    Args:
        capacity: 缓冲区容量
        alpha: 优先级指数，控制优先级程度 (0 = 均匀采样, 1 = 完全按优先级)
        beta: 重要性采样指数，用于偏差校正
        beta_increment: beta 的增量
        epsilon: 添加到优先级的小常数，避免零优先级
    """

    def __init__(
        self,
        capacity: int,
        alpha: float = 0.6,
        beta: float = 0.4,
        beta_increment: float = 0.001,
        epsilon: float = 1e-6,
    ):
        self.capacity = capacity
        self.alpha = alpha
        self.beta = beta
        self.beta_increment = beta_increment
        self.epsilon = epsilon

        self.tree = SumTree(capacity)
        self.max_priority = 1.0

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
        experience = (state, action, reward, next_state, done)

        # 使用最大优先级确保新经验被采样
        priority = self.max_priority ** self.alpha
        self.tree.add(priority, experience)

    def sample(self, batch_size: int) -> Tuple[np.ndarray, ...]:
        """
        优先级采样一批经验

        Args:
            batch_size: 批次大小

        Returns:
            (states, actions, rewards, next_states, dones, indices, weights) 元组
        """
        indices = []
        priorities = []
        experiences = []

        # 将总优先级分为 batch_size 个区间
        segment = self.tree.total / batch_size

        # 更新 beta
        self.beta = min(1.0, self.beta + self.beta_increment)

        for i in range(batch_size):
            # 在每个区间内均匀采样
            low = segment * i
            high = segment * (i + 1)
            s = random.uniform(low, high)

            idx, priority, experience = self.tree.get(s)

            # 避免零优先级
            if priority == 0:
                priority = self.epsilon

            indices.append(idx)
            priorities.append(priority)
            experiences.append(experience)

        # 计算重要性采样权重
        priorities = np.array(priorities)
        sampling_probabilities = priorities / self.tree.total
        weights = (self.tree.n_entries * sampling_probabilities) ** (-self.beta)
        weights = weights / weights.max()  # 归一化

        # 提取批次数据
        states = np.array([e[0] for e in experiences])
        actions = np.array([e[1] for e in experiences])
        rewards = np.array([e[2] for e in experiences])
        next_states = np.array([e[3] for e in experiences])
        dones = np.array([e[4] for e in experiences])

        return states, actions, rewards, next_states, dones, indices, weights

    def update_priorities(self, indices: List[int], td_errors: np.ndarray) -> None:
        """
        更新优先级

        Args:
            indices: 经验索引列表
            td_errors: TD 误差数组
        """
        td_errors = np.abs(td_errors) + self.epsilon
        priorities = td_errors ** self.alpha

        for idx, priority in zip(indices, priorities):
            self.max_priority = max(self.max_priority, priority)
            self.tree.update(idx, priority)

    def __len__(self) -> int:
        """返回缓冲区当前大小"""
        return self.tree.n_entries

    @property
    def is_ready(self) -> bool:
        """检查缓冲区是否已满"""
        return self.tree.n_entries == self.capacity


class ProportionalPrioritizedReplayBuffer(PrioritizedReplayBuffer):
    """
    比例优先经验回放缓冲区

    采样概率与优先级成正比，是 PER 的标准实现。
    """

    pass


class RankBasedPrioritizedReplayBuffer:
    """
    基于排名的优先经验回放缓冲区

    采样概率与排名成正比，更稳定但需要排序。

    Args:
        capacity: 缓冲区容量
        alpha: 优先级指数
        beta: 重要性采样指数
        beta_increment: beta 的增量
    """

    def __init__(
        self,
        capacity: int,
        alpha: float = 0.6,
        beta: float = 0.4,
        beta_increment: float = 0.001,
    ):
        self.capacity = capacity
        self.alpha = alpha
        self.beta = beta
        self.beta_increment = beta_increment

        self.buffer = []
        self.priorities = []
        self.max_priority = 1.0

    def push(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
    ) -> None:
        """添加经验"""
        experience = (state, action, reward, next_state, done)

        if len(self.buffer) >= self.capacity:
            # 移除最旧的经验
            self.buffer.pop(0)
            self.priorities.pop(0)

        self.buffer.append(experience)
        self.priorities.append(self.max_priority)

    def sample(self, batch_size: int) -> Tuple[np.ndarray, ...]:
        """基于排名采样"""
        # 更新 beta
        self.beta = min(1.0, self.beta + self.beta_increment)

        # 按优先级排序
        sorted_indices = np.argsort(self.priorities)[::-1]
        n = len(self.buffer)

        # 计算采样概率
        ranks = np.arange(1, n + 1)
        priorities = 1.0 / ranks ** self.alpha
        probabilities = priorities / priorities.sum()

        # 采样
        indices = np.random.choice(
            sorted_indices, size=batch_size, replace=False, p=probabilities[:n]
        )

        # 计算重要性采样权重
        weights = (n * probabilities[indices]) ** (-self.beta)
        weights = weights / weights.max()

        # 提取批次数据
        experiences = [self.buffer[i] for i in indices]
        states = np.array([e[0] for e in experiences])
        actions = np.array([e[1] for e in experiences])
        rewards = np.array([e[2] for e in experiences])
        next_states = np.array([e[3] for e in experiences])
        dones = np.array([e[4] for e in experiences])

        return states, actions, rewards, next_states, dones, indices, weights

    def update_priorities(self, indices: List[int], td_errors: np.ndarray) -> None:
        """更新优先级"""
        td_errors = np.abs(td_errors) + 1e-6
        priorities = td_errors ** self.alpha

        for idx, priority in zip(indices, priorities):
            self.priorities[idx] = priority
            self.max_priority = max(self.max_priority, priority)

    def __len__(self) -> int:
        return len(self.buffer)

    @property
    def is_ready(self) -> bool:
        return len(self.buffer) == self.capacity
