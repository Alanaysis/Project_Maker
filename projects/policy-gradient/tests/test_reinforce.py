"""
REINFORCE 算法测试

测试 REINFORCE 的核心功能。
"""

import pytest
import torch
import numpy as np
from unittest.mock import MagicMock, patch

from src.policy_network import PolicyNetwork
from src.reinforce import REINFORCE, REINFORCEWithBaseline, EpisodeResult, TrajectoryStep
from src.baseline import NoBaseline, MovingAverageBaseline


class MockEnv:
    """模拟 Gym 环境"""

    def __init__(self, episode_length=10):
        self.episode_length = episode_length
        self.step_count = 0

    def reset(self):
        self.step_count = 0
        return np.zeros(4), {}

    def step(self, action):
        self.step_count += 1
        done = self.step_count >= self.episode_length
        return np.zeros(4), 1.0, done, False, {}


class TestREINFORCE:
    """REINFORCE 测试类"""

    @pytest.fixture
    def policy(self):
        """创建测试用策略网络"""
        return PolicyNetwork(
            state_dim=4,
            action_dim=2,
            hidden_dims=[32, 16],
        )

    @pytest.fixture
    def optimizer(self, policy):
        """创建优化器"""
        return torch.optim.Adam(policy.parameters(), lr=0.01)

    @pytest.fixture
    def agent(self, policy, optimizer):
        """创建 REINFORCE 智能体"""
        return REINFORCE(
            policy=policy,
            optimizer=optimizer,
            gamma=0.99,
        )

    def test_init(self, policy, optimizer):
        """测试初始化"""
        agent = REINFORCE(policy=policy, optimizer=optimizer)
        assert agent.gamma == 0.99
        assert isinstance(agent.baseline, NoBaseline)

    def test_init_with_baseline(self, policy, optimizer):
        """测试带基线的初始化"""
        baseline = MovingAverageBaseline()
        agent = REINFORCE(
            policy=policy,
            optimizer=optimizer,
            baseline=baseline,
        )
        assert isinstance(agent.baseline, MovingAverageBaseline)

    def test_compute_returns(self, agent):
        """测试折扣回报计算"""
        rewards = [1.0, 1.0, 1.0]
        returns = agent.compute_returns(rewards)

        assert returns.shape == (3,)
        # G_2 = 1.0
        # G_1 = 1.0 + 0.99 * 1.0 = 1.99
        # G_0 = 1.0 + 0.99 * 1.99 = 2.9701
        assert torch.isclose(returns[2], torch.tensor(1.0), atol=1e-4)
        assert torch.isclose(returns[1], torch.tensor(1.99), atol=1e-4)
        assert torch.isclose(returns[0], torch.tensor(2.9701), atol=1e-2)

    def test_compute_returns_discount(self, agent):
        """测试折扣因子正确性"""
        rewards = [0.0, 0.0, 1.0]
        returns = agent.compute_returns(rewards)

        # 只有最后一步有奖励
        # G_2 = 1.0
        # G_1 = 0.0 + 0.99 * 1.0 = 0.99
        # G_0 = 0.0 + 0.99 * 0.99 = 0.9801
        assert torch.isclose(returns[2], torch.tensor(1.0), atol=1e-4)
        assert torch.isclose(returns[1], torch.tensor(0.99), atol=1e-4)
        assert torch.isclose(returns[0], torch.tensor(0.9801), atol=1e-3)

    def test_select_action(self, agent):
        """测试动作选择"""
        state = np.zeros(4)
        action, log_prob = agent.select_action(state)

        assert isinstance(action, int)
        assert 0 <= action < 2
        assert isinstance(log_prob, torch.Tensor)

    def test_collect_episode(self, agent):
        """测试 episode 收集"""
        env = MockEnv(episode_length=5)
        episode = agent.collect_episode(env)

        assert isinstance(episode, EpisodeResult)
        assert episode.length == 5
        assert len(episode.steps) == 5
        assert episode.total_reward == 5.0

    def test_collect_episode_steps(self, agent):
        """测试 episode 步骤数据"""
        env = MockEnv(episode_length=3)
        episode = agent.collect_episode(env)

        for step in episode.steps:
            assert isinstance(step, TrajectoryStep)
            assert isinstance(step.state, np.ndarray)
            assert isinstance(step.action, int)
            assert isinstance(step.reward, float)
            assert isinstance(step.log_prob, torch.Tensor)

    def test_update(self, agent):
        """测试策略更新"""
        env = MockEnv(episode_length=10)
        episode = agent.collect_episode(env)

        # 记录更新前的参数
        old_params = {
            name: param.clone()
            for name, param in agent.policy.named_parameters()
        }

        # 执行多次更新以确保参数变化
        for _ in range(5):
            episode = agent.collect_episode(env)
            metrics = agent.update(episode)

        # 检查返回指标
        assert "policy_loss" in metrics
        assert "total_loss" in metrics
        assert "mean_return" in metrics
        assert "episode_reward" in metrics
        assert "episode_length" in metrics

        # 检查参数已更新（至少一个参数有变化）
        params_changed = False
        for name, param in agent.policy.named_parameters():
            if not torch.equal(param, old_params[name]):
                params_changed = True
                break
        assert params_changed

    def test_update_with_entropy(self, policy, optimizer):
        """测试带熵正则化的更新"""
        agent = REINFORCE(
            policy=policy,
            optimizer=optimizer,
            entropy_coef=0.01,
        )

        env = MockEnv(episode_length=3)
        episode = agent.collect_episode(env)
        metrics = agent.update(episode)

        assert "entropy_loss" in metrics

    def test_update_with_grad_clipping(self, policy, optimizer):
        """测试梯度裁剪"""
        agent = REINFORCE(
            policy=policy,
            optimizer=optimizer,
            max_grad_norm=1.0,
        )

        env = MockEnv(episode_length=3)
        episode = agent.collect_episode(env)
        metrics = agent.update(episode)

        # 检查梯度范数
        total_norm = 0
        for param in policy.parameters():
            if param.grad is not None:
                total_norm += param.grad.data.norm(2).item() ** 2
        total_norm = total_norm ** 0.5

        assert total_norm <= 1.5  # 允许一些误差

    def test_evaluate(self, agent):
        """测试评估功能"""
        env = MockEnv(episode_length=10)
        avg_reward = agent.evaluate(env, num_episodes=3)

        assert isinstance(avg_reward, float)
        assert avg_reward > 0

    def test_save_load(self, agent, tmp_path):
        """测试模型保存和加载"""
        save_path = tmp_path / "model.pt"

        # 先训练几步使参数变化
        env = MockEnv(episode_length=5)
        for _ in range(3):
            episode = agent.collect_episode(env)
            agent.update(episode)

        # 保存模型
        agent.save(str(save_path))
        assert save_path.exists()

        # 创建新智能体
        new_policy = PolicyNetwork(state_dim=4, action_dim=2, hidden_dims=[32, 16])
        new_optimizer = torch.optim.Adam(new_policy.parameters())
        new_agent = REINFORCE(policy=new_policy, optimizer=new_optimizer)

        # 加载模型
        new_agent.load(str(save_path))

        # 加载后检查参数相同
        for (name1, p1), (name2, p2) in zip(
            agent.policy.named_parameters(),
            new_agent.policy.named_parameters(),
        ):
            assert torch.equal(p1, p2)


class TestREINFORCEWithBaseline:
    """带基线的 REINFORCE 测试类"""

    @pytest.fixture
    def setup(self):
        """创建测试用组件"""
        state_dim = 4
        action_dim = 2

        policy = PolicyNetwork(
            state_dim=state_dim,
            action_dim=action_dim,
            hidden_dims=[32, 16],
        )

        value_network = torch.nn.Sequential(
            torch.nn.Linear(state_dim, 32),
            torch.nn.ReLU(),
            torch.nn.Linear(32, 1),
        )

        policy_optimizer = torch.optim.Adam(policy.parameters(), lr=0.01)
        value_optimizer = torch.optim.Adam(value_network.parameters(), lr=0.01)

        agent = REINFORCEWithBaseline(
            policy=policy,
            value_network=value_network,
            policy_optimizer=policy_optimizer,
            value_optimizer=value_optimizer,
            gamma=0.99,
        )

        return agent

    def test_init(self, setup):
        """测试初始化"""
        agent = setup
        assert agent.value_coef == 0.5

    def test_update(self, setup):
        """测试带基线的更新"""
        agent = setup
        env = MockEnv(episode_length=5)
        episode = agent.collect_episode(env)

        metrics = agent.update(episode)

        assert "policy_loss" in metrics
        assert "value_loss" in metrics
        assert "total_loss" in metrics

    def test_value_network_trained(self, setup):
        """测试价值网络被训练"""
        agent = setup
        env = MockEnv(episode_length=10)

        # 记录更新前的价值网络参数
        old_params = {
            name: param.clone()
            for name, param in agent.value_network.named_parameters()
        }

        # 执行多次更新
        for _ in range(5):
            episode = agent.collect_episode(env)
            agent.update(episode)

        # 检查价值网络参数已更新（至少一个参数有变化）
        params_changed = False
        for name, param in agent.value_network.named_parameters():
            if not torch.equal(param, old_params[name]):
                params_changed = True
                break
        assert params_changed


class TestIntegration:
    """集成测试"""

    def test_short_training(self):
        """测试短时间训练"""
        policy = PolicyNetwork(state_dim=4, action_dim=2)
        optimizer = torch.optim.Adam(policy.parameters(), lr=0.01)

        agent = REINFORCE(
            policy=policy,
            optimizer=optimizer,
            gamma=0.99,
        )

        env = MockEnv(episode_length=5)
        history = agent.train(
            env=env,
            num_episodes=5,
            verbose=False,
        )

        assert len(history["episode_rewards"]) == 5
        assert len(history["episode_lengths"]) == 5

    def test_training_with_baseline(self):
        """测试带基线的训练"""
        state_dim = 4
        action_dim = 2

        policy = PolicyNetwork(state_dim=state_dim, action_dim=action_dim)
        value_network = torch.nn.Sequential(
            torch.nn.Linear(state_dim, 32),
            torch.nn.ReLU(),
            torch.nn.Linear(32, 1),
        )

        agent = REINFORCEWithBaseline(
            policy=policy,
            value_network=value_network,
            policy_optimizer=torch.optim.Adam(policy.parameters(), lr=0.01),
            value_optimizer=torch.optim.Adam(value_network.parameters(), lr=0.01),
        )

        env = MockEnv(episode_length=5)
        history = agent.train(
            env=env,
            num_episodes=5,
            verbose=False,
        )

        assert len(history["episode_rewards"]) == 5

    def test_training_with_moving_average_baseline(self):
        """测试带移动平均基线的训练"""
        policy = PolicyNetwork(state_dim=4, action_dim=2)
        optimizer = torch.optim.Adam(policy.parameters(), lr=0.01)
        baseline = MovingAverageBaseline(alpha=0.1)

        agent = REINFORCE(
            policy=policy,
            optimizer=optimizer,
            baseline=baseline,
        )

        env = MockEnv(episode_length=5)
        history = agent.train(
            env=env,
            num_episodes=5,
            verbose=False,
        )

        assert len(history["episode_rewards"]) == 5
