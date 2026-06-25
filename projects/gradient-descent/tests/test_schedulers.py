"""学习率调度器测试"""

import numpy as np
import pytest
from src.optimizers import SGD, Adam
from src.schedulers import StepLR, ExponentialLR, CosineAnnealingLR, WarmupScheduler


class TestStepLR:
    """阶梯学习率调度器测试"""

    def test_basic_initialization(self):
        """测试基本初始化"""
        optimizer = SGD(learning_rate=0.1)
        scheduler = StepLR(optimizer, step_size=10, gamma=0.1)

        assert scheduler.step_size == 10
        assert scheduler.gamma == 0.1
        assert scheduler.base_lr == 0.1

    def test_invalid_step_size(self):
        """测试无效步长"""
        optimizer = SGD(learning_rate=0.1)
        with pytest.raises(ValueError):
            StepLR(optimizer, step_size=0)

    def test_invalid_gamma(self):
        """测试无效衰减因子"""
        optimizer = SGD(learning_rate=0.1)
        with pytest.raises(ValueError):
            StepLR(optimizer, step_size=10, gamma=1.5)

    def test_step_decay(self):
        """测试阶梯衰减"""
        optimizer = SGD(learning_rate=0.1)
        scheduler = StepLR(optimizer, step_size=10, gamma=0.1)

        # 初始学习率
        assert abs(optimizer.learning_rate - 0.1) < 1e-10

        # 9 步后学习率不变
        for _ in range(9):
            scheduler.step()
        assert abs(optimizer.learning_rate - 0.1) < 1e-10

        # 第 10 步学习率衰减
        scheduler.step()
        assert abs(optimizer.learning_rate - 0.01) < 1e-10

    def test_multiple_decays(self):
        """测试多次衰减"""
        optimizer = SGD(learning_rate=1.0)
        scheduler = StepLR(optimizer, step_size=5, gamma=0.5)

        # 初始学习率
        assert abs(optimizer.learning_rate - 1.0) < 1e-10

        # 第 5 步衰减
        for _ in range(5):
            scheduler.step()
        assert abs(optimizer.learning_rate - 0.5) < 1e-10

        # 第 10 步再次衰减
        for _ in range(5):
            scheduler.step()
        assert abs(optimizer.learning_rate - 0.25) < 1e-10


class TestExponentialLR:
    """指数学习率调度器测试"""

    def test_basic_initialization(self):
        """测试基本初始化"""
        optimizer = SGD(learning_rate=0.1)
        scheduler = ExponentialLR(optimizer, gamma=0.9)

        assert scheduler.gamma == 0.9
        assert scheduler.base_lr == 0.1

    def test_invalid_gamma(self):
        """测试无效衰减因子"""
        optimizer = SGD(learning_rate=0.1)
        with pytest.raises(ValueError):
            ExponentialLR(optimizer, gamma=1.5)
        with pytest.raises(ValueError):
            ExponentialLR(optimizer, gamma=0.0)

    def test_exponential_decay(self):
        """测试指数衰减"""
        optimizer = SGD(learning_rate=1.0)
        scheduler = ExponentialLR(optimizer, gamma=0.9)

        # 初始学习率
        assert optimizer.learning_rate == 1.0

        # 第 1 步
        scheduler.step()
        assert abs(optimizer.learning_rate - 0.9) < 1e-10

        # 第 2 步
        scheduler.step()
        assert abs(optimizer.learning_rate - 0.81) < 1e-10

    def test_continuous_decay(self):
        """测试连续衰减"""
        optimizer = SGD(learning_rate=1.0)
        scheduler = ExponentialLR(optimizer, gamma=0.5)

        # 衰减 10 次
        for _ in range(10):
            scheduler.step()

        expected = 1.0 * (0.5 ** 10)
        assert abs(optimizer.learning_rate - expected) < 1e-10


class TestCosineAnnealingLR:
    """余弦退火学习率调度器测试"""

    def test_basic_initialization(self):
        """测试基本初始化"""
        optimizer = SGD(learning_rate=0.1)
        scheduler = CosineAnnealingLR(optimizer, T_max=100, eta_min=0.001)

        assert scheduler.T_max == 100
        assert scheduler.eta_min == 0.001
        assert scheduler.base_lr == 0.1

    def test_invalid_T_max(self):
        """测试无效最大迭代次数"""
        optimizer = SGD(learning_rate=0.1)
        with pytest.raises(ValueError):
            CosineAnnealingLR(optimizer, T_max=0)

    def test_invalid_eta_min(self):
        """测试无效最小学习率"""
        optimizer = SGD(learning_rate=0.1)
        with pytest.raises(ValueError):
            CosineAnnealingLR(optimizer, T_max=100, eta_min=-0.001)

    def test_cosine_annealing(self):
        """测试余弦退火"""
        optimizer = SGD(learning_rate=0.1)
        scheduler = CosineAnnealingLR(optimizer, T_max=100, eta_min=0.0)

        # 初始学习率
        initial_lr = optimizer.learning_rate

        # 中间点学习率应该接近最小值
        for _ in range(50):
            scheduler.step()
        mid_lr = optimizer.learning_rate
        assert mid_lr < initial_lr
        assert mid_lr >= scheduler.eta_min - 1e-10

        # 结束点学习率应该接近最小值（因为 T_max=100，在 t=100 时 cos(π) = -1）
        for _ in range(50):
            scheduler.step()
        end_lr = optimizer.learning_rate
        # 在 t=T_max 时，lr = eta_min + 0.5 * (lr_max - eta_min) * (1 + cos(π)) = eta_min
        assert abs(end_lr - scheduler.eta_min) < 1e-10

    def test_minimum_learning_rate(self):
        """测试最小学习率"""
        optimizer = SGD(learning_rate=0.1)
        scheduler = CosineAnnealingLR(optimizer, T_max=100, eta_min=0.01)

        # 中间点学习率应该接近最小值
        for _ in range(50):
            scheduler.step()

        # 学习率应该 >= eta_min
        assert optimizer.learning_rate >= scheduler.eta_min - 1e-10


class TestWarmupScheduler:
    """Warmup 学习率调度器测试"""

    def test_basic_initialization(self):
        """测试基本初始化"""
        optimizer = SGD(learning_rate=0.1)
        scheduler = WarmupScheduler(optimizer, warmup_epochs=10, target_lr=0.01)

        assert scheduler.warmup_epochs == 10
        assert scheduler.target_lr == 0.01

    def test_invalid_warmup_epochs(self):
        """测试无效预热轮数"""
        optimizer = SGD(learning_rate=0.1)
        with pytest.raises(ValueError):
            WarmupScheduler(optimizer, warmup_epochs=0)

    def test_warmup_phase(self):
        """测试预热阶段"""
        optimizer = SGD(learning_rate=0.0)
        scheduler = WarmupScheduler(optimizer, warmup_epochs=10, target_lr=0.1)

        # 初始学习率
        initial_lr = optimizer.learning_rate

        # 预热阶段学习率应该线性增加
        for i in range(10):
            scheduler.step()
            expected_lr = 0.0 + (0.1 - 0.0) * (i + 1) / 10
            assert abs(optimizer.learning_rate - expected_lr) < 1e-10

    def test_after_warmup(self):
        """测试预热后阶段"""
        optimizer = SGD(learning_rate=0.0)
        scheduler = WarmupScheduler(optimizer, warmup_epochs=10, target_lr=0.1)

        # 完成预热
        for _ in range(10):
            scheduler.step()

        # 预热后学习率应该保持目标值
        for _ in range(10):
            scheduler.step()
            assert abs(optimizer.learning_rate - 0.1) < 1e-10

    def test_with_scheduler(self):
        """测试与后续调度器结合"""
        optimizer = SGD(learning_rate=0.0)
        step_scheduler = StepLR(optimizer, step_size=5, gamma=0.5)
        warmup_scheduler = WarmupScheduler(
            optimizer, warmup_epochs=10, target_lr=0.1, scheduler=step_scheduler
        )

        # 完成预热
        for _ in range(10):
            warmup_scheduler.step()

        # 预热后应该应用阶梯衰减
        for _ in range(5):
            warmup_scheduler.step()

        # 学习率应该衰减
        assert optimizer.learning_rate < 0.1


class TestSchedulerState:
    """调度器状态测试"""

    def test_state_dict(self):
        """测试状态字典"""
        optimizer = SGD(learning_rate=0.1)
        scheduler = StepLR(optimizer, step_size=10, gamma=0.1)

        # 运行几步
        for _ in range(5):
            scheduler.step()

        # 获取状态
        state = scheduler.state_dict()
        assert 'last_epoch' in state
        assert 'base_lr' in state
        assert state['last_epoch'] == 5

    def test_load_state_dict(self):
        """测试加载状态字典"""
        optimizer = SGD(learning_rate=0.1)
        scheduler = StepLR(optimizer, step_size=10, gamma=0.1)

        # 运行几步
        for _ in range(5):
            scheduler.step()

        # 保存状态
        state = scheduler.state_dict()

        # 创建新的调度器并加载状态
        new_optimizer = SGD(learning_rate=0.1)
        new_scheduler = StepLR(new_optimizer, step_size=10, gamma=0.1)
        new_scheduler.load_state_dict(state)

        # 状态应该相同
        assert new_scheduler.last_epoch == state['last_epoch']
        assert new_scheduler.base_lr == state['base_lr']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
