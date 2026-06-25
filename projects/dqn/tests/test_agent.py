"""
DQN Agent 测试

测试 DQNAgent 的各个功能。
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import torch
import pytest

from src.agent import DQNAgent
from src.dqn import DQN
from src.double_dqn import DoubleDQN
from src.dueling_dqn import DuelingDQN


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


class TestDoubleDQN:
    """Double DQN 测试"""

    def test_compute_target(self):
        """测试目标值计算"""
        double_dqn = DoubleDQN(state_dim=4, action_dim=2, hidden_dim=64)

        next_states = torch.randn(16, 4)
        rewards = torch.randn(16)
        dones = torch.zeros(16)

        target = double_dqn.compute_target(next_states, rewards, dones)

        assert target.shape == (16,)
        assert not torch.isnan(target).any()

    def test_update_target(self):
        """测试目标网络更新"""
        double_dqn = DoubleDQN(state_dim=4, action_dim=2, hidden_dim=64)

        # 修改在线网络参数
        for param in double_dqn.online_net.parameters():
            param.data.fill_(1.0)

        # 更新目标网络
        double_dqn.update_target()

        # 验证目标网络参数已更新
        for param in double_dqn.target_net.parameters():
            assert torch.all(param.data == 1.0)

    def test_soft_update(self):
        """测试软更新"""
        double_dqn = DoubleDQN(state_dim=4, action_dim=2, hidden_dim=64)

        # 记录初始参数
        initial_params = []
        for param in double_dqn.target_net.parameters():
            initial_params.append(param.data.clone())

        # 修改在线网络参数
        for param in double_dqn.online_net.parameters():
            param.data.fill_(1.0)

        # 软更新
        double_dqn.soft_update(tau=0.5)

        # 验证参数已更新
        for param, initial in zip(double_dqn.target_net.parameters(), initial_params):
            # 应该是 0.5 * 1.0 + 0.5 * initial = 0.5 + 0.5 * initial
            expected = 0.5 + 0.5 * initial
            assert torch.allclose(param.data, expected, atol=1e-6)

    def test_get_action(self):
        """测试动作选择"""
        double_dqn = DoubleDQN(state_dim=4, action_dim=2, hidden_dim=64)
        state = torch.randn(4)

        # 测试贪婪策略
        action = double_dqn.get_action(state, epsilon=0.0)
        assert 0 <= action < 2

        # 测试随机策略
        actions = set()
        for _ in range(100):
            action = double_dqn.get_action(state, epsilon=1.0)
            actions.add(action)
        assert len(actions) == 2


class TestDuelingDQN:
    """Dueling DQN 测试"""

    def test_forward(self):
        """测试前向传播"""
        model = DuelingDQN(state_dim=4, action_dim=2, hidden_dim=64)
        state = torch.randn(1, 4)
        q_values = model(state)

        assert q_values.shape == (1, 2)
        assert not torch.isnan(q_values).any()

    def test_batch_forward(self):
        """测试批量前向传播"""
        model = DuelingDQN(state_dim=4, action_dim=2, hidden_dim=64)
        states = torch.randn(32, 4)
        q_values = model(states)

        assert q_values.shape == (32, 2)

    def test_get_value_and_advantage(self):
        """测试获取价值和优势"""
        model = DuelingDQN(state_dim=4, action_dim=2, hidden_dim=64)
        state = torch.randn(8, 4)

        value, advantage = model.get_value_and_advantage(state)

        assert value.shape == (8, 1)
        assert advantage.shape == (8, 2)
        assert not torch.isnan(value).any()
        assert not torch.isnan(advantage).any()

    def test_get_action(self):
        """测试动作选择"""
        model = DuelingDQN(state_dim=4, action_dim=2, hidden_dim=64)
        state = torch.randn(4)

        # 测试贪婪策略
        action = model.get_action(state, epsilon=0.0)
        assert 0 <= action < 2

        # 测试随机策略
        actions = set()
        for _ in range(100):
            action = model.get_action(state, epsilon=1.0)
            actions.add(action)
        assert len(actions) == 2

    def test_dueling_architecture(self):
        """测试 Dueling 架构特性"""
        model = DuelingDQN(state_dim=4, action_dim=2, hidden_dim=64)
        state = torch.randn(1, 4)

        # 获取 Q 值
        q_values = model(state)

        # 获取价值和优势
        value, advantage = model.get_value_and_advantage(state)

        # 验证 Q 值 = V + A - mean(A)
        expected_q = value + advantage - advantage.mean(dim=1, keepdim=True)
        assert torch.allclose(q_values, expected_q, atol=1e-6)


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
