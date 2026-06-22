"""
DQN 单元测试

测试 DQN 各个组件的正确性。
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import torch
import pytest

from src.dqn import DQN
from src.replay_buffer import ReplayBuffer
from src.agent import DQNAgent


class TestDQN:
    """DQN 神经网络测试"""

    def test_forward(self):
        """测试前向传播"""
        model = DQN(state_dim=4, action_dim=2, hidden_dim=64)
        state = torch.randn(1, 4)
        q_values = model(state)

        assert q_values.shape == (1, 2)
        assert not torch.isnan(q_values).any()

    def test_batch_forward(self):
        """测试批量前向传播"""
        model = DQN(state_dim=4, action_dim=2, hidden_dim=64)
        states = torch.randn(32, 4)
        q_values = model(states)

        assert q_values.shape == (32, 2)

    def test_get_action(self):
        """测试动作选择"""
        model = DQN(state_dim=4, action_dim=2, hidden_dim=64)
        state = torch.randn(4)

        # 测试贪婪策略
        action = model.get_action(state, epsilon=0.0)
        assert 0 <= action < 2

        # 测试随机策略
        actions = set()
        for _ in range(100):
            action = model.get_action(state, epsilon=1.0)
            actions.add(action)
        assert len(actions) == 2  # 应该两个动作都被选择过


class TestReplayBuffer:
    """经验回放缓冲区测试"""

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


class TestDQNAgent:
    """DQN 代理测试"""

    def test_select_action(self):
        """测试动作选择"""
        agent = DQNAgent(state_dim=4, action_dim=2, buffer_size=100, batch_size=32)

        state = np.random.randn(4)

        # 测试训练模式
        action = agent.select_action(state, training=True)
        assert 0 <= action < 2

        # 测试评估模式
        action = agent.select_action(state, training=False)
        assert 0 <= action < 2

    def test_store_experience(self):
        """测试经验存储"""
        agent = DQNAgent(state_dim=4, action_dim=2, buffer_size=100, batch_size=32)

        state = np.random.randn(4)
        agent.store_experience(state, 0, 1.0, state, False)

        assert len(agent.replay_buffer) == 1

    def test_train(self):
        """测试训练"""
        agent = DQNAgent(
            state_dim=4,
            action_dim=2,
            buffer_size=100,
            batch_size=32,
            epsilon_start=0.0,  # 禁用探索
        )

        # 填充缓冲区
        for _ in range(50):
            state = np.random.randn(4)
            agent.store_experience(state, 0, 1.0, state, False)

        # 训练
        loss = agent.train()
        assert loss is not None
        assert isinstance(loss, float)
        assert loss >= 0

    def test_target_network_update(self):
        """测试目标网络更新"""
        agent = DQNAgent(
            state_dim=4,
            action_dim=2,
            buffer_size=100,
            batch_size=32,
            target_update_freq=5,
        )

        # 填充缓冲区
        for _ in range(50):
            state = np.random.randn(4)
            agent.store_experience(state, 0, 1.0, state, False)

        # 训练多次
        for _ in range(10):
            agent.train()

        # 检查目标网络是否更新
        assert agent.train_step == 10

    def test_epsilon_decay(self):
        """测试探索率衰减"""
        agent = DQNAgent(
            state_dim=4,
            action_dim=2,
            buffer_size=100,
            batch_size=32,
            epsilon_start=1.0,
            epsilon_end=0.01,
            epsilon_decay=0.9,
        )

        # 填充缓冲区
        for _ in range(50):
            state = np.random.randn(4)
            agent.store_experience(state, 0, 1.0, state, False)

        initial_epsilon = agent.epsilon

        # 训练多次
        for _ in range(10):
            agent.train()

        assert agent.epsilon < initial_epsilon
        assert agent.epsilon >= 0.01

    def test_save_load(self, tmp_path):
        """测试模型保存和加载"""
        agent = DQNAgent(state_dim=4, action_dim=2, buffer_size=100, batch_size=32)

        # 保存
        save_path = os.path.join(tmp_path, "model.pth")
        agent.save(save_path)
        assert os.path.exists(save_path)

        # 加载
        new_agent = DQNAgent(state_dim=4, action_dim=2, buffer_size=100, batch_size=32)
        new_agent.load(save_path)

        # 验证参数
        assert agent.epsilon == new_agent.epsilon
        assert agent.train_step == new_agent.train_step


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
