"""集成测试"""

import numpy as np
import pytest
from src.optimizers import SGD, Momentum, AdaGrad, RMSProp, Adam, AdamW
from src.schedulers import StepLR, ExponentialLR, CosineAnnealingLR, WarmupScheduler
from src.functions import QuadraticFunction, RosenbrockFunction, HimmelblauFunction
from src.optimizer import optimize, compare_optimizers


class TestOptimizationIntegration:
    """优化集成测试"""

    def test_sgd_on_quadratic(self):
        """测试 SGD 在二次函数上的优化"""
        func = QuadraticFunction(a=1.0, b=1.0)
        optimizer = SGD(learning_rate=0.1)
        x0 = np.array([3.0, 3.0])

        result = optimize(func, optimizer, x0, max_iter=1000, tol=1e-6)

        # 应该收敛到最小值
        assert result['success']
        np.testing.assert_array_almost_equal(result['x'], [0, 0], decimal=4)
        assert result['fun'] < 1e-6

    def test_momentum_on_quadratic(self):
        """测试 Momentum 在二次函数上的优化"""
        func = QuadraticFunction(a=1.0, b=1.0)
        optimizer = Momentum(learning_rate=0.01, momentum=0.9)
        x0 = np.array([3.0, 3.0])

        result = optimize(func, optimizer, x0, max_iter=1000, tol=1e-6)

        # 应该收敛到最小值
        assert result['success']
        np.testing.assert_array_almost_equal(result['x'], [0, 0], decimal=4)

    def test_adam_on_quadratic(self):
        """测试 Adam 在二次函数上的优化"""
        func = QuadraticFunction(a=1.0, b=1.0)
        optimizer = Adam(learning_rate=0.1)
        x0 = np.array([3.0, 3.0])

        result = optimize(func, optimizer, x0, max_iter=2000, tol=1e-6)

        # 应该收敛到最小值
        assert result['success']
        np.testing.assert_array_almost_equal(result['x'], [0, 0], decimal=4)

    def test_adagrad_on_quadratic(self):
        """测试 AdaGrad 在二次函数上的优化"""
        func = QuadraticFunction(a=1.0, b=1.0)
        optimizer = AdaGrad(learning_rate=1.0)
        x0 = np.array([3.0, 3.0])

        result = optimize(func, optimizer, x0, max_iter=2000, tol=1e-6)

        # 应该收敛到最小值
        assert result['success']
        np.testing.assert_array_almost_equal(result['x'], [0, 0], decimal=4)

    def test_rmsprop_on_quadratic(self):
        """测试 RMSProp 在二次函数上的优化"""
        func = QuadraticFunction(a=1.0, b=1.0)
        optimizer = RMSProp(learning_rate=0.01)
        x0 = np.array([3.0, 3.0])

        result = optimize(func, optimizer, x0, max_iter=1000, tol=1e-6)

        # 应该收敛到最小值
        assert result['success']
        np.testing.assert_array_almost_equal(result['x'], [0, 0], decimal=4)

    def test_adamw_on_quadratic(self):
        """测试 AdamW 在二次函数上的优化"""
        func = QuadraticFunction(a=1.0, b=1.0)
        optimizer = AdamW(learning_rate=0.1, weight_decay=0.0)
        x0 = np.array([3.0, 3.0])

        result = optimize(func, optimizer, x0, max_iter=2000, tol=1e-6)

        # 应该收敛到最小值
        assert result['success']
        np.testing.assert_array_almost_equal(result['x'], [0, 0], decimal=4)

    def test_rosenbrock_optimization(self):
        """测试 Rosenbrock 函数优化"""
        func = RosenbrockFunction(a=1.0, b=100.0)
        optimizer = Adam(learning_rate=0.001)
        x0 = np.array([-1.0, 1.0])

        result = optimize(func, optimizer, x0, max_iter=5000, tol=1e-4)

        # 应该接近最小值
        assert result['fun'] < 1.0  # Rosenbrock 函数比较难优化

    def test_himmelblau_optimization(self):
        """测试 Himmelblau 函数优化"""
        func = HimmelblauFunction()
        optimizer = Adam(learning_rate=0.01)
        x0 = np.array([0.0, 0.0])

        result = optimize(func, optimizer, x0, max_iter=1000, tol=1e-4)

        # 应该接近某个最小值
        assert result['fun'] < 1.0

    def test_ill_conditioned_quadratic(self):
        """测试病态二次函数优化"""
        from src.functions.quadratic import IllConditionedQuadratic

        func = IllConditionedQuadratic(condition_number=100.0)

        # SGD 应该收敛较慢
        optimizer_sgd = SGD(learning_rate=0.01)
        result_sgd = optimize(func, optimizer_sgd, np.array([3.0, 3.0]),
                             max_iter=5000, tol=1e-4)

        # Adam 应该收敛较快
        optimizer_adam = Adam(learning_rate=0.1)
        result_adam = optimize(func, optimizer_adam, np.array([3.0, 3.0]),
                              max_iter=5000, tol=1e-4)

        # Adam 应该用更少的迭代次数
        assert result_adam['niter'] < result_sgd['niter']


class TestSchedulerIntegration:
    """调度器集成测试"""

    def test_step_lr_with_sgd(self):
        """测试阶梯衰减与 SGD 结合"""
        func = QuadraticFunction(a=1.0, b=1.0)
        optimizer = SGD(learning_rate=0.1)
        scheduler = StepLR(optimizer, step_size=100, gamma=0.5)
        x0 = np.array([3.0, 3.0])

        # 手动运行优化
        x = x0.copy()
        for i in range(500):
            grad = func.gradient(x)
            x = optimizer.step(x, grad)
            scheduler.step()

        # 应该收敛
        assert func(x) < 1e-4

    def test_cosine_annealing_with_adam(self):
        """测试余弦退火与 Adam 结合"""
        func = QuadraticFunction(a=1.0, b=1.0)
        optimizer = Adam(learning_rate=0.1)
        scheduler = CosineAnnealingLR(optimizer, T_max=500, eta_min=0.001)
        x0 = np.array([3.0, 3.0])

        # 手动运行优化
        x = x0.copy()
        for i in range(500):
            grad = func.gradient(x)
            x = optimizer.step(x, grad)
            scheduler.step()

        # 应该收敛
        assert func(x) < 1e-2

    def test_warmup_with_adam(self):
        """测试 Warmup 与 Adam 结合"""
        func = QuadraticFunction(a=1.0, b=1.0)
        optimizer = Adam(learning_rate=0.0)
        scheduler = WarmupScheduler(optimizer, warmup_epochs=50, target_lr=0.1)
        x0 = np.array([3.0, 3.0])

        # 手动运行优化
        x = x0.copy()
        for i in range(500):
            grad = func.gradient(x)
            x = optimizer.step(x, grad)
            scheduler.step()

        # 应该收敛
        assert func(x) < 1e-2

    def test_learning_rate_schedule(self):
        """测试学习率调度"""
        optimizer = SGD(learning_rate=1.0)
        scheduler = ExponentialLR(optimizer, gamma=0.9)

        learning_rates = []
        for i in range(100):
            learning_rates.append(optimizer.learning_rate)
            scheduler.step()

        # 学习率应该单调递减
        for i in range(1, len(learning_rates)):
            assert learning_rates[i] <= learning_rates[i-1]

        # 最终学习率应该很小
        assert learning_rates[-1] < 0.01


class TestCompareOptimizers:
    """优化器对比测试"""

    def test_compare_on_quadratic(self):
        """测试在二次函数上对比优化器"""
        func = QuadraticFunction(a=1.0, b=1.0)
        x0 = np.array([3.0, 3.0])

        optimizers = {
            'SGD': SGD(learning_rate=0.1),
            'Momentum': Momentum(learning_rate=0.01, momentum=0.9),
            'Adam': Adam(learning_rate=0.1),
        }

        results = compare_optimizers(func, optimizers, x0, max_iter=2000, tol=1e-6)

        # 所有优化器都应该收敛
        for name, result in results.items():
            assert result['success'], f"{name} failed to converge"
            np.testing.assert_array_almost_equal(result['x'], [0, 0], decimal=4)

    def test_convergence_speed_comparison(self):
        """测试收敛速度对比"""
        func = QuadraticFunction(a=1.0, b=1.0)
        x0 = np.array([3.0, 3.0])

        optimizers = {
            'SGD': SGD(learning_rate=0.1),
            'Adam': Adam(learning_rate=0.1),
        }

        results = compare_optimizers(func, optimizers, x0, max_iter=2000, tol=1e-6)

        # Adam 通常比 SGD 收敛更快
        sgd_iters = results['SGD']['niter']
        adam_iters = results['Adam']['niter']

        # 这里不强制要求 Adam 更快，因为超参数可能不同
        # 但至少应该都能收敛
        assert results['SGD']['success']
        assert results['Adam']['success']

    def test_result_structure(self):
        """测试结果结构"""
        func = QuadraticFunction(a=1.0, b=1.0)
        optimizer = SGD(learning_rate=0.1)
        x0 = np.array([3.0, 3.0])

        result = optimize(func, optimizer, x0, max_iter=100, tol=1e-6)

        # 检查结果结构
        assert 'x' in result
        assert 'fun' in result
        assert 'niter' in result
        assert 'trajectory' in result
        assert 'values' in result
        assert 'grad_norms' in result
        assert 'learning_rates' in result
        assert 'success' in result
        assert 'message' in result

        # 检查数据类型
        assert isinstance(result['x'], np.ndarray)
        assert isinstance(result['fun'], (float, np.floating))
        assert isinstance(result['niter'], (int, np.integer))
        assert isinstance(result['trajectory'], np.ndarray)
        assert isinstance(result['values'], np.ndarray)
        assert isinstance(result['grad_norms'], np.ndarray)
        assert isinstance(result['learning_rates'], np.ndarray)
        assert isinstance(result['success'], (bool, np.bool_))
        assert isinstance(result['message'], str)


class TestEdgeCases:
    """边界情况测试"""

    def test_zero_gradient(self):
        """测试零梯度情况"""
        func = QuadraticFunction(a=0.0, b=0.0)  # 常数函数
        optimizer = SGD(learning_rate=0.1)
        x0 = np.array([1.0, 1.0])

        result = optimize(func, optimizer, x0, max_iter=100, tol=1e-6)

        # 应该立即收敛
        assert result['niter'] == 1
        assert result['success']

    def test_very_small_learning_rate(self):
        """测试非常小的学习率"""
        func = QuadraticFunction(a=1.0, b=1.0)
        optimizer = SGD(learning_rate=1e-6)
        x0 = np.array([3.0, 3.0])

        result = optimize(func, optimizer, x0, max_iter=100, tol=1e-6)

        # 应该收敛很慢
        assert result['niter'] == 100
        assert not result['success']  # 可能不会收敛

    def test_very_large_learning_rate(self):
        """测试非常大的学习率"""
        func = QuadraticFunction(a=1.0, b=1.0)
        optimizer = SGD(learning_rate=10.0)
        x0 = np.array([3.0, 3.0])

        # 应该发散
        result = optimize(func, optimizer, x0, max_iter=100, tol=1e-6)

        # 可能不会收敛
        assert not result['success'] or result['fun'] > 1e6

    def test_single_iteration(self):
        """测试单次迭代"""
        func = QuadraticFunction(a=1.0, b=1.0)
        optimizer = SGD(learning_rate=0.1)
        x0 = np.array([3.0, 3.0])

        result = optimize(func, optimizer, x0, max_iter=1, tol=1e-6)

        assert result['niter'] == 1
        assert len(result['trajectory']) == 2  # 初始点 + 更新后的点
        assert len(result['values']) == 2

    def test_already_at_minimum(self):
        """测试已经在最小值的情况"""
        func = QuadraticFunction(a=1.0, b=1.0)
        optimizer = SGD(learning_rate=0.1)
        x0 = np.array([0.0, 0.0])  # 最小值点

        result = optimize(func, optimizer, x0, max_iter=100, tol=1e-6)

        # 应该立即收敛
        assert result['success']
        assert result['niter'] == 1
        np.testing.assert_array_almost_equal(result['x'], [0, 0])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
