"""
基线测试

测试各种基线实现。
"""

import pytest
import torch
import numpy as np

from src.baseline import (
    NoBaseline,
    ConstantBaseline,
    MovingAverageBaseline,
    ValueBaseline,
    ValueNetwork,
)


class TestNoBaseline:
    """NoBaseline 测试类"""

    def test_get_baseline(self):
        """测试返回零基线"""
        baseline = NoBaseline()
        returns = torch.tensor([1.0, 2.0, 3.0])
        result = baseline.get_baseline(returns)

        assert torch.allclose(result, torch.zeros_like(returns))

    def test_compute_advantage(self):
        """测试优势计算（应该等于回报）"""
        baseline = NoBaseline()
        returns = torch.tensor([1.0, 2.0, 3.0])
        advantages = baseline.compute_advantage(returns)

        assert torch.allclose(advantages, returns)


class TestConstantBaseline:
    """ConstantBaseline 测试类"""

    def test_default_value(self):
        """测试默认值"""
        baseline = ConstantBaseline()
        returns = torch.tensor([1.0, 2.0, 3.0])
        result = baseline.get_baseline(returns)

        assert torch.allclose(result, torch.zeros_like(returns))

    def test_custom_value(self):
        """测试自定义值"""
        baseline = ConstantBaseline(value=2.0)
        returns = torch.tensor([1.0, 2.0, 3.0])
        result = baseline.get_baseline(returns)

        expected = torch.tensor([2.0, 2.0, 2.0])
        assert torch.allclose(result, expected)

    def test_compute_advantage(self):
        """测试优势计算"""
        baseline = ConstantBaseline(value=2.0)
        returns = torch.tensor([1.0, 2.0, 3.0])
        advantages = baseline.compute_advantage(returns)

        expected = torch.tensor([-1.0, 0.0, 1.0])
        assert torch.allclose(advantages, expected)


class TestMovingAverageBaseline:
    """MovingAverageBaseline 测试类"""

    def test_initial_state(self):
        """测试初始状态"""
        baseline = MovingAverageBaseline()
        assert baseline.running_mean == 0.0
        assert not baseline.initialized

    def test_first_update(self):
        """测试第一次更新"""
        baseline = MovingAverageBaseline(alpha=0.1)
        returns = torch.tensor([1.0, 2.0, 3.0])

        result = baseline.get_baseline(returns)

        # 第一次应该使用批次均值
        expected = torch.full_like(returns, 2.0)
        assert torch.allclose(result, expected)
        assert baseline.initialized
        assert baseline.running_mean == 2.0

    def test_subsequent_updates(self):
        """测试后续更新"""
        baseline = MovingAverageBaseline(alpha=0.1)

        # 第一次更新
        returns1 = torch.tensor([1.0, 2.0, 3.0])  # mean = 2.0
        baseline.get_baseline(returns1)

        # 第二次更新
        returns2 = torch.tensor([4.0, 5.0, 6.0])  # mean = 5.0
        result = baseline.get_baseline(returns2)

        # 运行平均 = 0.9 * 2.0 + 0.1 * 5.0 = 2.3
        expected_mean = 0.9 * 2.0 + 0.1 * 5.0
        expected = torch.full_like(returns2, expected_mean)
        assert torch.allclose(result, expected, atol=1e-5)

    def test_alpha_effect(self):
        """测试 alpha 系数的影响"""
        # 大 alpha：快速适应
        baseline_fast = MovingAverageBaseline(alpha=0.5)

        # 小 alpha：缓慢适应
        baseline_slow = MovingAverageBaseline(alpha=0.01)

        returns = torch.tensor([1.0, 2.0, 3.0])  # mean = 2.0

        # 第一次更新
        baseline_fast.get_baseline(returns)
        baseline_slow.get_baseline(returns)

        # 新数据
        new_returns = torch.tensor([10.0, 20.0, 30.0])  # mean = 20.0

        result_fast = baseline_fast.get_baseline(new_returns)
        result_slow = baseline_slow.get_baseline(new_returns)

        # 快速基线应该更接近新数据
        assert result_fast.mean() > result_slow.mean()

    def test_reset(self):
        """测试重置"""
        baseline = MovingAverageBaseline()
        returns = torch.tensor([1.0, 2.0, 3.0])

        baseline.get_baseline(returns)
        assert baseline.initialized

        baseline.reset()
        assert not baseline.initialized
        assert baseline.running_mean == 0.0

    def test_compute_advantage(self):
        """测试优势计算"""
        baseline = MovingAverageBaseline(alpha=0.1)
        returns = torch.tensor([1.0, 2.0, 3.0])

        advantages = baseline.compute_advantage(returns)

        # 基线是均值 2.0
        expected = torch.tensor([-1.0, 0.0, 1.0])
        assert torch.allclose(advantages, expected, atol=1e-5)


class TestValueNetwork:
    """ValueNetwork 测试类"""

    def test_init(self):
        """测试初始化"""
        network = ValueNetwork(state_dim=4)
        assert isinstance(network, torch.nn.Module)

    def test_custom_hidden_dims(self):
        """测试自定义隐藏层"""
        network = ValueNetwork(state_dim=4, hidden_dims=[64, 32])
        linear_count = sum(
            1 for m in network.modules() if isinstance(m, torch.nn.Linear)
        )
        assert linear_count == 3  # 2 hidden + 1 output

    def test_forward_shape(self):
        """测试前向传播形状"""
        network = ValueNetwork(state_dim=4)
        state = torch.randn(8, 4)
        value = network(state)

        assert value.shape == (8, 1)

    def test_single_state(self):
        """测试单个状态"""
        network = ValueNetwork(state_dim=4)
        state = torch.randn(1, 4)
        value = network(state)

        assert value.shape == (1, 1)

    def test_gradient_flow(self):
        """测试梯度流"""
        network = ValueNetwork(state_dim=4)
        state = torch.randn(1, 4)
        value = network(state)

        loss = value.sum()
        loss.backward()

        for param in network.parameters():
            assert param.grad is not None


class TestValueBaseline:
    """ValueBaseline 测试类"""

    @pytest.fixture
    def setup(self):
        """创建测试用组件"""
        value_network = ValueNetwork(state_dim=4)
        optimizer = torch.optim.Adam(value_network.parameters(), lr=0.01)
        baseline = ValueBaseline(
            value_network=value_network,
            optimizer=optimizer,
        )
        return baseline

    def test_init(self, setup):
        """测试初始化"""
        baseline = setup
        assert baseline.value_network is not None
        assert baseline.optimizer is not None

    def test_get_value(self, setup):
        """测试获取价值"""
        baseline = setup
        states = torch.randn(4, 4)
        values = baseline.get_value(states)

        assert values.shape == (4,)

    def test_train_step(self, setup):
        """测试训练步骤"""
        baseline = setup
        states = torch.randn(8, 4)
        returns = torch.randn(8)

        # 记录更新前的参数
        old_params = {
            name: param.clone()
            for name, param in baseline.value_network.named_parameters()
        }

        # 执行训练
        loss = baseline.train_step(states, returns)

        assert isinstance(loss, float)
        assert loss >= 0

        # 检查参数已更新
        for name, param in baseline.value_network.named_parameters():
            assert not torch.equal(param, old_params[name])

    def test_multiple_train_steps(self, setup):
        """测试多次训练步骤"""
        baseline = setup
        states = torch.randn(8, 4)
        returns = torch.randn(8)

        losses = []
        for _ in range(5):
            loss = baseline.train_step(states, returns)
            losses.append(loss)

        # 损失应该下降
        assert losses[-1] <= losses[0]

    def test_get_baseline(self, setup):
        """测试基线获取（默认返回零）"""
        baseline = setup
        returns = torch.tensor([1.0, 2.0, 3.0])
        result = baseline.get_baseline(returns)

        assert torch.allclose(result, torch.zeros_like(returns))


class TestBaselineComparison:
    """基线比较测试"""

    def test_no_baseline_highest_variance(self):
        """测试无基线的方差最大"""
        torch.manual_seed(42)
        returns = torch.randn(100) * 10 + 50  # 明显的偏移

        no_baseline = NoBaseline()
        constant_baseline = ConstantBaseline(value=returns.mean().item())

        advantages_no = no_baseline.compute_advantage(returns)
        advantages_const = constant_baseline.compute_advantage(returns)

        # 常数基线应该减少方差（因为减去了均值）
        assert advantages_const.var() <= advantages_no.var() + 1e-6

    def test_moving_average_adapts(self):
        """测试移动平均基线适应性"""
        baseline = MovingAverageBaseline(alpha=0.5)

        # 第一批数据
        returns1 = torch.randn(10) + 10
        baseline.get_baseline(returns1)

        # 第二批数据
        returns2 = torch.randn(10) + 20
        baseline.get_baseline(returns2)

        # 基线应该在两批数据之间
        assert 10 < baseline.running_mean < 20
