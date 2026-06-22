"""
策略网络测试

测试 PolicyNetwork 的核心功能。
"""

import pytest
import torch
import numpy as np

from src.policy_network import PolicyNetwork


class TestPolicyNetwork:
    """PolicyNetwork 测试类"""

    @pytest.fixture
    def policy(self):
        """创建测试用策略网络"""
        return PolicyNetwork(
            state_dim=4,
            action_dim=2,
            hidden_dims=[32, 16],
        )

    def test_init(self):
        """测试网络初始化"""
        policy = PolicyNetwork(state_dim=4, action_dim=2)
        assert isinstance(policy, torch.nn.Module)

    def test_custom_hidden_dims(self):
        """测试自定义隐藏层维度"""
        policy = PolicyNetwork(
            state_dim=4,
            action_dim=2,
            hidden_dims=[64, 32, 16],
        )
        # 检查网络结构
        linear_count = sum(
            1 for m in policy.modules() if isinstance(m, torch.nn.Linear)
        )
        assert linear_count == 4  # 3 hidden + 1 output

    def test_invalid_activation(self):
        """测试无效的激活函数"""
        with pytest.raises(ValueError):
            PolicyNetwork(
                state_dim=4,
                action_dim=2,
                activation="invalid",
            )

    def test_forward_shape(self, policy):
        """测试前向传播输出形状"""
        batch_size = 8
        state = torch.randn(batch_size, 4)
        log_probs = policy(state)
        assert log_probs.shape == (batch_size, 2)

    def test_forward_log_softmax(self, policy):
        """测试输出是对数概率"""
        state = torch.randn(1, 4)
        log_probs = policy(state)

        # 验证是合法的对数概率
        probs = torch.exp(log_probs)
        assert torch.allclose(probs.sum(dim=-1), torch.ones(1), atol=1e-6)

    def test_get_action(self, policy):
        """测试动作选择"""
        state = torch.randn(4)
        action, log_prob = policy.get_action(state)

        assert isinstance(action, int)
        assert 0 <= action < 2
        assert isinstance(log_prob, torch.Tensor)

    def test_get_action_batch(self, policy):
        """测试多次动作选择的分布"""
        state = torch.randn(4)
        actions = []

        for _ in range(1000):
            action, _ = policy.get_action(state)
            actions.append(action)

        # 应该有多种动作被选择
        unique_actions = set(actions)
        assert len(unique_actions) > 1

    def test_get_log_prob(self, policy):
        """测试对数概率计算"""
        batch_size = 4
        states = torch.randn(batch_size, 4)
        actions = torch.randint(0, 2, (batch_size,))

        log_probs = policy.get_log_prob(states, actions)
        assert log_probs.shape == (batch_size,)

    def test_get_entropy(self, policy):
        """测试熵计算"""
        batch_size = 4
        states = torch.randn(batch_size, 4)

        entropy = policy.get_entropy(states)
        assert entropy.shape == (batch_size,)
        assert (entropy >= 0).all()  # 熵应该非负

    def test_gradient_flow(self, policy):
        """测试梯度可以流过网络"""
        state = torch.randn(1, 4)
        log_probs = policy(state)

        # 计算损失并反向传播
        loss = -log_probs.mean()
        loss.backward()

        # 检查梯度存在
        for param in policy.parameters():
            assert param.grad is not None

    def test_weight_initialization(self, policy):
        """测试权重初始化"""
        for name, param in policy.named_parameters():
            if "weight" in name:
                # 权重应该接近零（小方差初始化）
                assert param.abs().mean() < 0.5
            elif "bias" in name:
                # 偏置应该为零
                assert torch.allclose(param, torch.zeros_like(param))

    def test_different_state_dims(self):
        """测试不同的状态维度"""
        for state_dim in [1, 2, 4, 8, 16]:
            policy = PolicyNetwork(state_dim=state_dim, action_dim=3)
            state = torch.randn(1, state_dim)
            log_probs = policy(state)
            assert log_probs.shape == (1, 3)

    def test_different_action_dims(self):
        """测试不同的动作维度"""
        for action_dim in [2, 3, 5, 10]:
            policy = PolicyNetwork(state_dim=4, action_dim=action_dim)
            state = torch.randn(1, 4)
            log_probs = policy(state)
            assert log_probs.shape == (1, action_dim)

    def test_deterministic_mode(self, policy):
        """测试确定性模式（总是选择概率最高的动作）"""
        state = torch.randn(4)

        with torch.no_grad():
            log_probs = policy(state.unsqueeze(0))
            expected_action = log_probs.argmax(dim=-1).item()

        # 多次采样应该总是返回相同的最高概率动作
        # 注意：get_action 使用采样，所以这里直接测试 argmax
        for _ in range(10):
            with torch.no_grad():
                log_probs = policy(state.unsqueeze(0))
                action = log_probs.argmax(dim=-1).item()
                assert action == expected_action

    def test_training_mode(self, policy):
        """测试训练模式"""
        policy.train()
        assert policy.training

    def test_eval_mode(self, policy):
        """测试评估模式"""
        policy.eval()
        assert not policy.training
