"""
参数估计器测试

测试各种参数估计方法。
"""

import pytest
import numpy as np
from src.parameter_estimator import (
    ParameterEstimator,
    RecursiveLeastSquares,
    EstimationMethod,
)


class TestParameterEstimator:
    """参数估计器测试类"""

    def test_rls_estimation(self):
        """测试 RLS 估计"""
        n_params = 3
        estimator = ParameterEstimator(
            n_params=n_params,
            estimation_method=EstimationMethod.RLS,
            adaptation_gain=0.1,
        )

        # 生成测试数据: y = 2*x1 + 3*x2 + 1*x3 + noise
        true_params = np.array([2.0, 3.0, 1.0])
        n_samples = 100

        for i in range(n_samples):
            phi = np.random.randn(n_params)
            y = np.dot(phi, true_params) + np.random.randn() * 0.1
            estimator.update(phi, y, 0.1)

        # 检查估计参数接近真实参数
        estimated = estimator.get_parameters()
        assert np.allclose(estimated, true_params, atol=0.5)

    def test_gradient_estimation(self):
        """测试梯度下降估计"""
        n_params = 2
        estimator = ParameterEstimator(
            n_params=n_params,
            estimation_method=EstimationMethod.GRADIENT,
            adaptation_gain=0.5,
        )

        # 生成测试数据: y = 1.5*x1 + 2.5*x2
        true_params = np.array([1.5, 2.5])
        n_samples = 200

        for i in range(n_samples):
            phi = np.random.randn(n_params)
            y = np.dot(phi, true_params) + np.random.randn() * 0.05
            estimator.update(phi, y, 0.1)

        # 检查估计参数接近真实参数
        estimated = estimator.get_parameters()
        assert np.allclose(estimated, true_params, atol=1.0)

    def test_forgetting_factor(self):
        """测试带遗忘因子的 RLS"""
        n_params = 2
        estimator = ParameterEstimator(
            n_params=n_params,
            estimation_method=EstimationMethod.FORGETTING_FACTOR,
            forgetting_factor=0.95,
        )

        # 第一阶段: y = 1*x1 + 2*x2
        true_params_1 = np.array([1.0, 2.0])
        for _ in range(100):
            phi = np.random.randn(n_params)
            y = np.dot(phi, true_params_1)
            estimator.update(phi, y, 0.1)

        # 第二阶段: 参数变化 y = 3*x1 + 4*x2
        true_params_2 = np.array([3.0, 4.0])
        for _ in range(100):
            phi = np.random.randn(n_params)
            y = np.dot(phi, true_params_2)
            estimator.update(phi, y, 0.1)

        # 检查估计参数接近新参数
        estimated = estimator.get_parameters()
        assert np.allclose(estimated, true_params_2, atol=1.0)

    def test_estimation_history(self):
        """测试估计历史记录"""
        estimator = ParameterEstimator(n_params=2, estimation_method=EstimationMethod.RLS)

        n_steps = 50
        for _ in range(n_steps):
            phi = np.random.randn(2)
            y = np.dot(phi, np.array([1.0, 2.0]))
            estimator.update(phi, y, 0.1)

        times, params = estimator.get_estimation_history()
        assert len(times) == n_steps
        assert params.shape == (n_steps, 2)

    def test_error_history(self):
        """测试误差历史记录"""
        estimator = ParameterEstimator(n_params=2, estimation_method=EstimationMethod.RLS)

        n_steps = 50
        for _ in range(n_steps):
            phi = np.random.randn(2)
            y = np.dot(phi, np.array([1.0, 2.0]))
            estimator.update(phi, y, 0.1)

        times, errors = estimator.get_error_history()
        assert len(times) == n_steps
        assert len(errors) == n_steps

    def test_parameter_variance(self):
        """测试参数方差"""
        estimator = ParameterEstimator(n_params=3, estimation_method=EstimationMethod.RLS)

        # 运行一些估计
        for _ in range(100):
            phi = np.random.randn(3)
            y = np.dot(phi, np.array([1.0, 2.0, 3.0]))
            estimator.update(phi, y, 0.1)

        variance = estimator.get_parameter_variance()
        assert len(variance) == 3
        assert all(v > 0 for v in variance)

    def test_reset(self):
        """测试重置功能"""
        estimator = ParameterEstimator(n_params=2, estimation_method=EstimationMethod.RLS)

        # 运行一些估计
        for _ in range(50):
            phi = np.random.randn(2)
            y = np.dot(phi, np.array([1.0, 2.0]))
            estimator.update(phi, y, 0.1)

        # 重置
        estimator.reset()

        # 检查状态已重置
        assert np.all(estimator.get_parameters() == 0)
        assert len(estimator._history) == 0


class TestRecursiveLeastSquares:
    """递归最小二乘测试类"""

    def test_basic_estimation(self):
        """测试基本估计功能"""
        rls = RecursiveLeastSquares(n_params=2)

        # 生成数据: y = 2*x1 + 3*x2
        true_params = np.array([2.0, 3.0])

        for _ in range(100):
            phi = np.random.randn(2)
            y = np.dot(phi, true_params) + np.random.randn() * 0.1
            params, error = rls.estimate(phi, y)

        # 检查估计参数
        assert np.allclose(params, true_params, atol=0.5)

    def test_prediction(self):
        """测试预测功能"""
        rls = RecursiveLeastSquares(n_params=2)

        # 训练
        true_params = np.array([1.0, 2.0])
        for _ in range(100):
            phi = np.random.randn(2)
            y = np.dot(phi, true_params)
            rls.estimate(phi, y)

        # 预测
        test_phi = np.array([1.0, 1.0])
        prediction = rls.predict(test_phi)
        expected = np.dot(test_phi, true_params)

        assert abs(prediction - expected) < 0.5

    def test_forgetting_factor_effect(self):
        """测试遗忘因子效果"""
        # 无遗忘
        rls_no_ff = RecursiveLeastSquares(n_params=2, forgetting_factor=1.0)

        # 有遗忘
        rls_with_ff = RecursiveLeastSquares(n_params=2, forgetting_factor=0.9)

        # 第一阶段
        true_params_1 = np.array([1.0, 2.0])
        for _ in range(100):
            phi = np.random.randn(2)
            y = np.dot(phi, true_params_1)
            rls_no_ff.estimate(phi, y)
            rls_with_ff.estimate(phi, y)

        # 第二阶段 (参数变化)
        true_params_2 = np.array([3.0, 4.0])
        for _ in range(100):
            phi = np.random.randn(2)
            y = np.dot(phi, true_params_2)
            rls_no_ff.estimate(phi, y)
            rls_with_ff.estimate(phi, y)

        # 有遗忘的应该更快适应新参数
        error_no_ff = np.linalg.norm(rls_no_ff.theta - true_params_2)
        error_with_ff = np.linalg.norm(rls_with_ff.theta - true_params_2)

        assert error_with_ff < error_no_ff

    def test_reset(self):
        """测试重置功能"""
        rls = RecursiveLeastSquares(n_params=2)

        # 运行一些估计
        for _ in range(50):
            phi = np.random.randn(2)
            y = np.dot(phi, np.array([1.0, 2.0]))
            rls.estimate(phi, y)

        # 重置
        rls.reset()

        # 检查状态已重置
        assert np.all(rls.theta == 0)
        assert np.allclose(rls.P, np.eye(2) * 1000.0)


class TestEstimationMethods:
    """估计方法对比测试"""

    def test_rls_vs_gradient(self):
        """对比 RLS 和梯度下降"""
        n_params = 3
        true_params = np.array([1.0, 2.0, 3.0])
        n_samples = 200

        # RLS
        rls_estimator = ParameterEstimator(
            n_params=n_params,
            estimation_method=EstimationMethod.RLS,
        )

        # 梯度下降
        gradient_estimator = ParameterEstimator(
            n_params=n_params,
            estimation_method=EstimationMethod.GRADIENT,
            adaptation_gain=0.1,
        )

        # 生成数据
        np.random.seed(42)
        for _ in range(n_samples):
            phi = np.random.randn(n_params)
            y = np.dot(phi, true_params) + np.random.randn() * 0.1
            rls_estimator.update(phi, y, 0.1)
            gradient_estimator.update(phi, y, 0.1)

        # 比较误差
        rls_error = np.linalg.norm(rls_estimator.get_parameters() - true_params)
        gradient_error = np.linalg.norm(gradient_estimator.get_parameters() - true_params)

        # RLS 通常更准确
        print(f"RLS 误差: {rls_error:.4f}, 梯度下降误差: {gradient_error:.4f}")

    def test_convergence_speed(self):
        """测试收敛速度"""
        n_params = 2
        true_params = np.array([2.0, 3.0])

        estimators = {
            "RLS": ParameterEstimator(n_params=n_params, estimation_method=EstimationMethod.RLS),
            "Gradient": ParameterEstimator(n_params=n_params, estimation_method=EstimationMethod.GRADIENT, adaptation_gain=0.5),
            "FF-RLS": ParameterEstimator(n_params=n_params, estimation_method=EstimationMethod.FORGETTING_FACTOR, forgetting_factor=0.95),
        }

        errors = {name: [] for name in estimators}

        for _ in range(100):
            phi = np.random.randn(n_params)
            y = np.dot(phi, true_params) + np.random.randn() * 0.1

            for name, estimator in estimators.items():
                estimator.update(phi, y, 0.1)
                error = np.linalg.norm(estimator.get_parameters() - true_params)
                errors[name].append(error)

        # 验证误差在减小
        for name, error_list in errors.items():
            assert error_list[-1] < error_list[0], f"{name} 未收敛"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
