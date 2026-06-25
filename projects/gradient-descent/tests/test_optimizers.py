"""优化器测试"""

import numpy as np
import pytest
from src.optimizers import BGD, MiniBatchBGD, SGD, Momentum, NesterovMomentum, AdaGrad, RMSProp, Adam, AdamW, Nadam


class TestSGD:
    """SGD 优化器测试"""

    def test_basic_initialization(self):
        """测试基本初始化"""
        optimizer = SGD(learning_rate=0.01)
        assert optimizer.learning_rate == 0.01
        assert optimizer.weight_decay == 0.0

    def test_invalid_learning_rate(self):
        """测试无效学习率"""
        with pytest.raises(ValueError):
            SGD(learning_rate=-0.01)

    def test_basic_step(self):
        """测试基本更新步骤"""
        optimizer = SGD(learning_rate=0.1)
        params = np.array([1.0, 2.0])
        grads = np.array([0.5, 0.5])

        new_params = optimizer.step(params, grads)
        expected = params - 0.1 * grads
        np.testing.assert_array_almost_equal(new_params, expected)

    def test_weight_decay(self):
        """测试权重衰减"""
        optimizer = SGD(learning_rate=0.1, weight_decay=0.01)
        params = np.array([1.0, 2.0])
        grads = np.array([0.5, 0.5])

        new_params = optimizer.step(params, grads)
        expected_grads = grads + 0.01 * params
        expected = params - 0.1 * expected_grads
        np.testing.assert_array_almost_equal(new_params, expected)

    def test_step_count(self):
        """测试迭代计数"""
        optimizer = SGD(learning_rate=0.01)
        params = np.array([1.0, 2.0])
        grads = np.array([0.5, 0.5])

        assert optimizer.step_count == 0
        optimizer.step(params, grads)
        assert optimizer.step_count == 1
        optimizer.step(params, grads)
        assert optimizer.step_count == 2

    def test_reset(self):
        """测试重置"""
        optimizer = SGD(learning_rate=0.01)
        params = np.array([1.0, 2.0])
        grads = np.array([0.5, 0.5])

        optimizer.step(params, grads)
        assert optimizer.step_count == 1

        optimizer.reset()
        assert optimizer.step_count == 0
        assert optimizer.state == {}


class TestMomentum:
    """Momentum 优化器测试"""

    def test_basic_initialization(self):
        """测试基本初始化"""
        optimizer = Momentum(learning_rate=0.01, momentum=0.9)
        assert optimizer.learning_rate == 0.01
        assert optimizer.momentum == 0.9

    def test_invalid_momentum(self):
        """测试无效动量系数"""
        with pytest.raises(ValueError):
            Momentum(momentum=1.0)
        with pytest.raises(ValueError):
            Momentum(momentum=-0.1)

    def test_momentum_step(self):
        """测试动量更新步骤"""
        optimizer = Momentum(learning_rate=0.1, momentum=0.9)
        params = np.array([1.0, 2.0])
        grads = np.array([0.5, 0.5])

        # 第一步
        new_params = optimizer.step(params, grads)
        expected = params - 0.1 * grads
        np.testing.assert_array_almost_equal(new_params, expected)

    def test_momentum_state(self):
        """测试动量状态"""
        optimizer = Momentum(learning_rate=0.1, momentum=0.9)
        params = np.array([1.0, 2.0])
        grads = np.array([0.5, 0.5])

        optimizer.step(params, grads)
        assert 'momentum_buffer' in optimizer.state
        np.testing.assert_array_almost_equal(
            optimizer.state['momentum_buffer'], grads
        )

    def test_nesterov(self):
        """测试 Nesterov 动量"""
        optimizer = Momentum(learning_rate=0.1, momentum=0.9, nesterov=True)
        params = np.array([1.0, 2.0])
        grads = np.array([0.5, 0.5])

        new_params = optimizer.step(params, grads)
        # Nesterov 应该有不同的更新规则
        assert new_params.shape == params.shape


class TestAdaGrad:
    """AdaGrad 优化器测试"""

    def test_basic_initialization(self):
        """测试基本初始化"""
        optimizer = AdaGrad(learning_rate=0.01)
        assert optimizer.learning_rate == 0.01
        assert optimizer.eps == 1e-10

    def test_adaptive_learning_rate(self):
        """测试自适应学习率"""
        optimizer = AdaGrad(learning_rate=0.1)
        params = np.array([1.0, 2.0])
        grads = np.array([0.5, 0.5])

        # 第一步
        new_params1 = optimizer.step(params, grads)
        # 第二步，使用相同梯度
        new_params2 = optimizer.step(new_params1, grads)

        # AdaGrad 应该减小学习率
        step1 = np.linalg.norm(params - new_params1)
        step2 = np.linalg.norm(new_params1 - new_params2)
        assert step2 < step1

    def test_sparse_gradients(self):
        """测试稀疏梯度"""
        optimizer = AdaGrad(learning_rate=0.1)
        params = np.array([1.0, 2.0])

        # 模拟稀疏梯度
        grads1 = np.array([1.0, 0.0])
        grads2 = np.array([0.0, 1.0])

        optimizer.step(params, grads1)
        optimizer.step(params, grads2)

        # 每个参数应该有不同的自适应学习率
        assert 'sum_square_grads' in optimizer.state


class TestRMSProp:
    """RMSProp 优化器测试"""

    def test_basic_initialization(self):
        """测试基本初始化"""
        optimizer = RMSProp(learning_rate=0.01, alpha=0.99)
        assert optimizer.learning_rate == 0.01
        assert optimizer.alpha == 0.99

    def test_invalid_alpha(self):
        """测试无效衰减率"""
        with pytest.raises(ValueError):
            RMSProp(alpha=1.0)
        with pytest.raises(ValueError):
            RMSProp(alpha=-0.1)

    def test_moving_average(self):
        """测试移动平均"""
        optimizer = RMSProp(learning_rate=0.01, alpha=0.9)
        params = np.array([1.0, 2.0])
        grads = np.array([0.5, 0.5])

        optimizer.step(params, grads)
        assert 'square_avg' in optimizer.state

        # 平方平均应该接近梯度平方
        expected = 0.1 * grads**2
        np.testing.assert_array_almost_equal(
            optimizer.state['square_avg'], expected, decimal=5
        )

    def test_momentum_variant(self):
        """测试带动量的 RMSProp"""
        optimizer = RMSProp(learning_rate=0.01, alpha=0.9, momentum=0.9)
        params = np.array([1.0, 2.0])
        grads = np.array([0.5, 0.5])

        optimizer.step(params, grads)
        assert 'momentum_buffer' in optimizer.state


class TestAdam:
    """Adam 优化器测试"""

    def test_basic_initialization(self):
        """测试基本初始化"""
        optimizer = Adam(learning_rate=0.001)
        assert optimizer.learning_rate == 0.001
        assert optimizer.betas == (0.9, 0.999)

    def test_invalid_betas(self):
        """测试无效衰减率"""
        with pytest.raises(ValueError):
            Adam(betas=(1.0, 0.999))
        with pytest.raises(ValueError):
            Adam(betas=(0.9, 1.0))

    def test_bias_correction(self):
        """测试偏差修正"""
        optimizer = Adam(learning_rate=0.001)
        params = np.array([1.0, 2.0])
        grads = np.array([0.5, 0.5])

        # 第一步
        new_params = optimizer.step(params, grads)

        # 检查状态
        assert 'exp_avg' in optimizer.state
        assert 'exp_avg_sq' in optimizer.state

        # 偏差修正后的值应该不同
        bias_correction1 = 1 - 0.9 ** 1
        bias_correction2 = 1 - 0.999 ** 1
        expected_exp_avg = grads * (1 - 0.9) / bias_correction1
        np.testing.assert_array_almost_equal(
            optimizer.state['exp_avg'] / bias_correction1,
            expected_exp_avg
        )

    def test_amsgrad(self):
        """测试 AMSGrad 变体"""
        optimizer = Adam(learning_rate=0.001, amsgrad=True)
        params = np.array([1.0, 2.0])
        grads = np.array([0.5, 0.5])

        optimizer.step(params, grads)
        assert 'max_exp_avg_sq' in optimizer.state

    def test_multiple_steps(self):
        """测试多步更新"""
        optimizer = Adam(learning_rate=0.001)
        params = np.array([1.0, 2.0])
        grads = np.array([0.5, 0.5])

        for _ in range(10):
            params = optimizer.step(params, grads)

        assert optimizer.step_count == 10


class TestAdamW:
    """AdamW 优化器测试"""

    def test_basic_initialization(self):
        """测试基本初始化"""
        optimizer = AdamW(learning_rate=0.001, weight_decay=0.01)
        assert optimizer.learning_rate == 0.001
        assert optimizer.weight_decay == 0.01

    def test_weight_decay_decoupling(self):
        """测试权重衰减解耦"""
        optimizer = AdamW(learning_rate=0.001, weight_decay=0.01)
        params = np.array([1.0, 2.0])
        grads = np.array([0.5, 0.5])

        new_params = optimizer.step(params, grads)

        # AdamW 应该对参数直接应用权重衰减，而不是通过梯度
        assert 'exp_avg' in optimizer.state
        assert 'exp_avg_sq' in optimizer.state

    def test_vs_adam(self):
        """测试与 Adam 的区别"""
        adam = Adam(learning_rate=0.001, weight_decay=0.01)
        adamw = AdamW(learning_rate=0.001, weight_decay=0.01)

        params1 = np.array([1.0, 2.0])
        params2 = params1.copy()
        grads = np.array([0.5, 0.5])

        # 两者应该产生不同的更新
        new_params1 = adam.step(params1, grads)
        new_params2 = adamw.step(params2, grads)

        # 由于权重衰减的实现不同，结果应该不同
        assert not np.array_equal(new_params1, new_params2)


class TestBGD:
    """BGD 优化器测试"""

    def test_basic_initialization(self):
        """测试基本初始化"""
        optimizer = BGD(learning_rate=0.01)
        assert optimizer.learning_rate == 0.01
        assert optimizer.weight_decay == 0.0

    def test_basic_step(self):
        """测试基本更新步骤"""
        optimizer = BGD(learning_rate=0.1)
        params = np.array([1.0, 2.0])
        grads = np.array([0.5, 0.5])

        new_params = optimizer.step(params, grads)
        expected = params - 0.1 * grads
        np.testing.assert_array_almost_equal(new_params, expected)

    def test_weight_decay(self):
        """测试权重衰减"""
        optimizer = BGD(learning_rate=0.1, weight_decay=0.01)
        params = np.array([1.0, 2.0])
        grads = np.array([0.5, 0.5])

        new_params = optimizer.step(params, grads)
        expected_grads = grads + 0.01 * params
        expected = params - 0.1 * expected_grads
        np.testing.assert_array_almost_equal(new_params, expected)


class TestMiniBatchBGD:
    """MiniBatchBGD 优化器测试"""

    def test_basic_initialization(self):
        """测试基本初始化"""
        optimizer = MiniBatchBGD(learning_rate=0.01, batch_size=32)
        assert optimizer.learning_rate == 0.01
        assert optimizer.batch_size == 32

    def test_invalid_batch_size(self):
        """测试无效批量大小"""
        with pytest.raises(ValueError):
            MiniBatchBGD(batch_size=0)
        with pytest.raises(ValueError):
            MiniBatchBGD(batch_size=-1)

    def test_basic_step(self):
        """测试基本更新步骤"""
        optimizer = MiniBatchBGD(learning_rate=0.1, batch_size=32)
        params = np.array([1.0, 2.0])
        grads = np.array([0.5, 0.5])

        new_params = optimizer.step(params, grads)
        expected = params - 0.1 * grads
        np.testing.assert_array_almost_equal(new_params, expected)


class TestNesterovMomentum:
    """NesterovMomentum 优化器测试"""

    def test_basic_initialization(self):
        """测试基本初始化"""
        optimizer = NesterovMomentum(learning_rate=0.01, momentum=0.9)
        assert optimizer.learning_rate == 0.01
        assert optimizer.momentum == 0.9
        assert optimizer.nesterov == True

    def test_nesterov_step(self):
        """测试 Nesterov 更新步骤"""
        optimizer = NesterovMomentum(learning_rate=0.1, momentum=0.9)
        params = np.array([1.0, 2.0])
        grads = np.array([0.5, 0.5])

        new_params = optimizer.step(params, grads)
        # Nesterov 应该有不同的更新规则
        assert new_params.shape == params.shape


class TestNadam:
    """Nadam 优化器测试"""

    def test_basic_initialization(self):
        """测试基本初始化"""
        optimizer = Nadam(learning_rate=0.001)
        assert optimizer.learning_rate == 0.001
        assert optimizer.betas == (0.9, 0.999)

    def test_invalid_betas(self):
        """测试无效衰减率"""
        with pytest.raises(ValueError):
            Nadam(betas=(1.0, 0.999))
        with pytest.raises(ValueError):
            Nadam(betas=(0.9, 1.0))

    def test_basic_step(self):
        """测试基本更新步骤"""
        optimizer = Nadam(learning_rate=0.001)
        params = np.array([1.0, 2.0])
        grads = np.array([0.5, 0.5])

        new_params = optimizer.step(params, grads)

        # 检查状态
        assert 'exp_avg' in optimizer.state
        assert 'exp_avg_sq' in optimizer.state

    def test_nesterov_update(self):
        """测试 Nesterov 更新"""
        optimizer = Nadam(learning_rate=0.001)
        params = np.array([1.0, 2.0])
        grads = np.array([0.5, 0.5])

        # 第一步
        new_params1 = optimizer.step(params, grads)
        # 第二步
        new_params2 = optimizer.step(new_params1, grads)

        # Nadam 应该收敛
        assert optimizer.step_count == 2

    def test_multiple_steps(self):
        """测试多步更新"""
        optimizer = Nadam(learning_rate=0.001)
        params = np.array([1.0, 2.0])
        grads = np.array([0.5, 0.5])

        for _ in range(10):
            params = optimizer.step(params, grads)

        assert optimizer.step_count == 10


class TestNumericalStability:
    """数值稳定性测试"""

    def test_nan_detection(self):
        """测试 NaN 检测"""
        optimizer = Adam(learning_rate=0.001)
        params = np.array([1.0, np.nan])
        grads = np.array([0.5, 0.5])

        with pytest.raises(ValueError, match="NaN"):
            optimizer.step(params, grads)

    def test_inf_detection(self):
        """测试 Inf 检测"""
        optimizer = Adam(learning_rate=0.001)
        params = np.array([1.0, np.inf])
        grads = np.array([0.5, 0.5])

        with pytest.raises(ValueError, match="Inf"):
            optimizer.step(params, grads)

    def test_gradient_clipping(self):
        """测试梯度裁剪"""
        optimizer = SGD(learning_rate=0.01)
        params = np.array([1.0, 2.0])
        grads = np.array([100.0, 200.0])

        # 裁剪梯度
        clipped_grads = optimizer._clip_grads(grads, max_norm=1.0)
        assert np.linalg.norm(clipped_grads) <= 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
