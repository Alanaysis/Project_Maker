"""
经验回放缓冲区测试

测试 ReplayBuffer 和 PrioritizedReplayBuffer 的正确性。
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pytest

from src.replay_buffer import ReplayBuffer
from src.prioritized_replay_buffer import PrioritizedReplayBuffer


class TestReplayBuffer:
    """ReplayBuffer 测试"""

    def test_push_and_sample(self):
        """测试添加和采样"""
        buffer = ReplayBuffer(capacity=1000)

        # 添加经验
        for i in range(100):
            state = np.random.randn(4)
            action = np.random.randint(2)
            reward = np.random.randn()
            next_state = np.random.randn(4)
            done = i % 10 == 0
            buffer.push(state, action, reward, next_state, done)

        assert len(buffer) == 100

        # 采样
        batch_size = 32
        states, actions, rewards, next_states, dones = buffer.sample(batch_size)

        assert states.shape == (batch_size, 4)
        assert actions.shape == (batch_size,)
        assert rewards.shape == (batch_size,)
        assert next_states.shape == (batch_size, 4)
        assert dones.shape == (batch_size,)

    def test_capacity(self):
        """测试容量限制"""
        buffer = ReplayBuffer(capacity=10)

        # 添加超过容量的经验
        for i in range(20):
            state = np.array([i, i, i, i])
            buffer.push(state, 0, 0.0, state, False)

        assert len(buffer) == 10

    def test_is_ready(self):
        """测试缓冲区就绪状态"""
        buffer = ReplayBuffer(capacity=10)

        assert not buffer.is_ready

        for i in range(10):
            buffer.push(np.zeros(4), 0, 0.0, np.zeros(4), False)

        assert buffer.is_ready


class TestPrioritizedReplayBuffer:
    """PrioritizedReplayBuffer 测试"""

    def test_push_and_sample(self):
        """测试添加和采样"""
        buffer = PrioritizedReplayBuffer(capacity=1000, alpha=0.6, beta=0.4)

        # 添加经验
        for i in range(100):
            state = np.random.randn(4)
            action = np.random.randint(2)
            reward = np.random.randn()
            next_state = np.random.randn(4)
            done = i % 10 == 0
            buffer.push(state, action, reward, next_state, done)

        assert len(buffer) == 100

        # 采样
        batch_size = 32
        result = buffer.sample(batch_size)

        states, actions, rewards, next_states, dones, indices, weights = result

        assert states.shape == (batch_size, 4)
        assert actions.shape == (batch_size,)
        assert rewards.shape == (batch_size,)
        assert next_states.shape == (batch_size, 4)
        assert dones.shape == (batch_size,)
        assert len(indices) == batch_size
        assert weights.shape == (batch_size,)

    def test_update_priorities(self):
        """测试更新优先级"""
        buffer = PrioritizedReplayBuffer(capacity=100, alpha=0.6, beta=0.4)

        # 添加经验
        for i in range(50):
            state = np.random.randn(4)
            buffer.push(state, 0, 1.0, state, False)

        # 采样
        batch_size = 16
        _, _, _, _, _, indices, _ = buffer.sample(batch_size)

        # 更新优先级
        td_errors = np.random.randn(batch_size)
        buffer.update_priorities(indices, td_errors)

        # 再次采样，应该有不同的分布
        result2 = buffer.sample(batch_size)
        assert result2 is not None

    def test_capacity(self):
        """测试容量限制"""
        buffer = PrioritizedReplayBuffer(capacity=10, alpha=0.6, beta=0.4)

        # 添加超过容量的经验
        for i in range(20):
            state = np.array([i, i, i, i])
            buffer.push(state, 0, 0.0, state, False)

        assert len(buffer) == 10

    def test_is_ready(self):
        """测试缓冲区就绪状态"""
        buffer = PrioritizedReplayBuffer(capacity=10, alpha=0.6, beta=0.4)

        assert not buffer.is_ready

        for i in range(10):
            buffer.push(np.zeros(4), 0, 0.0, np.zeros(4), False)

        assert buffer.is_ready

    def test_weights_normalization(self):
        """测试权重归一化"""
        buffer = PrioritizedReplayBuffer(capacity=100, alpha=0.6, beta=0.4)

        # 添加经验
        for i in range(50):
            state = np.random.randn(4)
            buffer.push(state, 0, float(i), state, False)

        # 采样
        _, _, _, _, _, _, weights = buffer.sample(32)

        # 权重应该被归一化
        assert weights.max() == 1.0
        assert weights.min() >= 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
