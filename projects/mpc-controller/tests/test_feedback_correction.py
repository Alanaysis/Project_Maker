"""
反馈校正测试
"""

import pytest
import numpy as np
from src.feedback_correction import (
    FeedbackCorrection,
    CorrectionMethod,
    CorrectionConfig,
    ErrorFeedbackCorrection,
    ModelAdaptiveCorrection,
    ExtendedStateCorrection,
    DisturbanceObserverCorrection,
)


class TestErrorFeedbackCorrection:
    """误差反馈校正测试"""

    def test_initialization(self):
        """测试初始化"""
        corrector = ErrorFeedbackCorrection(n_outputs=2)
        assert corrector.n_outputs == 2

    def test_compute_correction(self):
        """测试校正计算"""
        corrector = ErrorFeedbackCorrection(n_outputs=1)

        y_measured = np.array([1.2])
        y_predicted = np.array([1.0])
        Y_predicted = np.array([[0.9], [0.8], [0.7]])

        Y_corrected = corrector.compute_correction(y_measured, y_predicted, Y_predicted)

        # 误差 = 1.2 - 1.0 = 0.2
        # 校正后第一个元素 = 0.9 + 1.0 * 0.2 = 1.1
        assert Y_corrected.shape == (3, 1)
        assert Y_corrected[0, 0] > 0.9  # 应该被向上修正

    def test_error_decay(self):
        """测试误差衰减"""
        corrector = ErrorFeedbackCorrection(n_outputs=1)

        y_measured = np.array([1.2])
        y_predicted = np.array([1.0])
        Y_predicted = np.array([[0.9], [0.8], [0.7]])

        Y_corrected = corrector.compute_correction(y_measured, y_predicted, Y_predicted)

        # 远处的校正量应该更小
        corrections = Y_corrected[:, 0] - Y_predicted[:, 0]
        assert corrections[0] > corrections[1]
        assert corrections[1] > corrections[2]

    def test_error_trend(self):
        """测试误差趋势"""
        corrector = ErrorFeedbackCorrection(n_outputs=1)

        # 多次校正
        for i in range(5):
            y_measured = np.array([1.0 + 0.1 * i])
            y_predicted = np.array([1.0])
            corrector.compute_correction(y_measured, y_predicted)

        trend = corrector.get_error_trend()
        assert len(trend) == 1

    def test_reset(self):
        """测试重置"""
        corrector = ErrorFeedbackCorrection(n_outputs=1)

        y_measured = np.array([1.2])
        y_predicted = np.array([1.0])
        corrector.compute_correction(y_measured, y_predicted)

        corrector.reset()
        assert len(corrector._error_history) == 0


class TestModelAdaptiveCorrection:
    """自适应模型校正测试"""

    def test_initialization(self):
        """测试初始化"""
        corrector = ModelAdaptiveCorrection(n_params=3)
        assert corrector.n_params == 3
        np.testing.assert_array_equal(corrector._theta, np.zeros(3))

    def test_update(self):
        """测试参数更新"""
        corrector = ModelAdaptiveCorrection(n_params=2)

        # 简单的线性关系: y = 2*x1 + 3*x2
        for _ in range(100):
            phi = np.random.randn(2)
            y_true = 2 * phi[0] + 3 * phi[1]
            y_measured = y_true + np.random.randn() * 0.1
            corrector.update(phi, y_measured)

        # 参数应该接近 [2, 3]
        theta = corrector.get_parameters()
        np.testing.assert_almost_equal(theta[0], 2.0, decimal=0)
        np.testing.assert_almost_equal(theta[1], 3.0, decimal=0)

    def test_predict(self):
        """测试预测"""
        corrector = ModelAdaptiveCorrection(n_params=2)

        # 设置参数
        corrector._theta = np.array([2.0, 3.0])

        phi = np.array([1.0, 1.0])
        y_pred = corrector.predict(phi)

        np.testing.assert_almost_equal(y_pred, 5.0)

    def test_reset(self):
        """测试重置"""
        corrector = ModelAdaptiveCorrection(n_params=2)
        corrector._theta = np.array([1.0, 2.0])

        corrector.reset()
        np.testing.assert_array_equal(corrector._theta, np.zeros(2))


class TestExtendedStateCorrection:
    """增广状态校正测试"""

    def setup_method(self):
        """测试前准备"""
        self.A = np.array([[0.9]])
        self.B = np.array([[1.0]])
        self.C = np.array([[1.0]])

    def test_initialization(self):
        """测试初始化"""
        corrector = ExtendedStateCorrection(self.A, self.B, self.C)

        assert corrector.n_states == 1
        assert corrector.n_inputs == 1
        assert corrector.n_outputs == 1

    def test_update(self):
        """测试状态更新"""
        corrector = ExtendedStateCorrection(self.A, self.B, self.C)

        x = np.array([1.0])
        y_measured = np.array([1.1])
        u = np.array([0.5])

        d = corrector.update(x, y_measured, u)

        assert len(d) == 1

    def test_get_disturbance(self):
        """测试获取扰动"""
        corrector = ExtendedStateCorrection(self.A, self.B, self.C)

        # 多次更新
        for _ in range(10):
            x = np.array([1.0])
            y_measured = np.array([1.2])  # 持续有偏
            u = np.array([0.5])
            corrector.update(x, y_measured, u)

        d = corrector.get_disturbance()
        assert len(d) == 1
        # 扰动应该捕捉到偏移
        assert abs(d[0]) > 0

    def test_correct_prediction(self):
        """测试修正预测"""
        corrector = ExtendedStateCorrection(self.A, self.B, self.C)

        # 设置扰动估计
        corrector.x_aug_est = np.array([1.0, 0.5])

        Y_predicted = np.array([[1.0], [1.1], [1.2]])
        Y_corrected = corrector.correct_prediction(Y_predicted)

        # 应该加上扰动
        np.testing.assert_array_almost_equal(Y_corrected[:, 0] - Y_predicted[:, 0], 0.5)

    def test_reset(self):
        """测试重置"""
        corrector = ExtendedStateCorrection(self.A, self.B, self.C)
        corrector.x_aug_est = np.array([1.0, 0.5])

        corrector.reset()
        np.testing.assert_array_equal(corrector.x_aug_est, np.zeros(2))


class TestDisturbanceObserverCorrection:
    """扰动观测器测试"""

    def setup_method(self):
        """测试前准备"""
        self.A = np.array([[0.9, 0.1], [0.0, 0.8]])
        self.B = np.array([[1.0], [0.5]])
        self.C = np.array([[1.0, 0.0]])

    def test_initialization(self):
        """测试初始化"""
        observer = DisturbanceObserverCorrection(self.A, self.B, self.C)
        assert observer.n_states == 2

    def test_estimate_disturbance(self):
        """测试扰动估计"""
        observer = DisturbanceObserverCorrection(self.A, self.B, self.C)

        x = np.array([1.0, 0.5])
        u = np.array([0.5])

        d = observer.estimate_disturbance(x, u)
        assert len(d) == 2

    def test_correct_state_prediction(self):
        """测试状态预测修正"""
        observer = DisturbanceObserverCorrection(self.A, self.B, self.C)

        x = np.array([1.0, 0.5])
        u = np.array([0.5])

        X_corrected = observer.correct_state_prediction(x, u, Np=5)
        assert X_corrected.shape == (6, 2)

    def test_reset(self):
        """测试重置"""
        observer = DisturbanceObserverCorrection(self.A, self.B, self.C)

        # 执行一些估计
        observer.estimate_disturbance(np.array([1.0, 0.5]), np.array([0.5]))

        observer.reset()
        np.testing.assert_array_equal(observer._d_hat, np.zeros(2))


class TestFeedbackCorrectionManager:
    """反馈校正管理器测试"""

    def test_error_feedback_method(self):
        """测试误差反馈方法"""
        A = np.array([[0.9]])
        B = np.array([[1.0]])
        C = np.array([[1.0]])

        manager = FeedbackCorrection(
            method=CorrectionMethod.ERROR_FEEDBACK,
            n_states=1, n_inputs=1, n_outputs=1,
            A=A, B=B, C=C
        )

        result = manager.correct(
            y_measured=np.array([1.2]),
            y_predicted=np.array([1.0]),
            Y_predicted=np.array([[0.9], [0.8]])
        )

        assert result.shape == (2, 1)

    def test_disturbance_observer_method(self):
        """测试扰动观测器方法"""
        A = np.array([[0.9]])
        B = np.array([[1.0]])
        C = np.array([[1.0]])

        manager = FeedbackCorrection(
            method=CorrectionMethod.DISTURBANCE_OBSERVER,
            n_states=1, n_inputs=1, n_outputs=1,
            A=A, B=B, C=C
        )

        result = manager.correct(
            x=np.array([1.0]),
            u=np.array([0.5])
        )

        assert len(result) == 1

    def test_reset(self):
        """测试重置"""
        manager = FeedbackCorrection(
            method=CorrectionMethod.ERROR_FEEDBACK,
            n_states=1, n_inputs=1, n_outputs=1
        )

        manager.correct(
            y_measured=np.array([1.0]),
            y_predicted=np.array([0.9])
        )

        manager.reset()
        assert len(manager.get_corrector()._error_history) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
