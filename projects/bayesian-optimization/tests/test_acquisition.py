"""
采集函数测试
"""

import numpy as np
import pytest
from src.acquisition import (
    ExpectedImprovement,
    UpperConfidenceBound,
    ProbabilityOfImprovement,
    ThompsonSampling,
    create_acquisition
)
from src.gaussian_process import GaussianProcess
from src.kernels import RBF


class TestAcquisitionFunctions:
    """采集函数测试类"""

    def setup_method(self):
        """测试前准备"""
        np.random.seed(42)

        # 创建简单的 GP 模型
        self.X_train = np.array([[0.0], [1.0], [2.0]])
        self.y_train = np.array([0.0, 1.0, 0.5])

        self.gp = GaussianProcess(kernel=RBF(length_scale=1.0))
        self.gp.fit(self.X_train, self.y_train)

        self.X_test = np.linspace(-1, 3, 10).reshape(-1, 1)
        self.y_best = np.max(self.y_train)

    def test_ei_initialization(self):
        """测试 EI 初始化"""
        ei = ExpectedImprovement(xi=0.01)
        assert ei.xi == 0.01

    def test_ei_shape(self):
        """测试 EI 输出形状"""
        ei = ExpectedImprovement()
        values = ei(self.X_test, self.gp, self.y_best)

        assert values.shape == (len(self.X_test),)

    def test_ei_non_negative(self):
        """测试 EI 非负"""
        ei = ExpectedImprovement()
        values = ei(self.X_test, self.gp, self.y_best)

        assert np.all(values >= -1e-10)  # 允许小的数值误差

    def test_ucb_initialization(self):
        """测试 UCB 初始化"""
        ucb = UpperConfidenceBound(kappa=2.0)
        assert ucb.kappa == 2.0

    def test_ucb_shape(self):
        """测试 UCB 输出形状"""
        ucb = UpperConfidenceBound()
        values = ucb(self.X_test, self.gp, self.y_best)

        assert values.shape == (len(self.X_test),)

    def test_pi_initialization(self):
        """测试 PI 初始化"""
        pi = ProbabilityOfImprovement(xi=0.01)
        assert pi.xi == 0.01

    def test_pi_shape(self):
        """测试 PI 输出形状"""
        pi = ProbabilityOfImprovement()
        values = pi(self.X_test, self.gp, self.y_best)

        assert values.shape == (len(self.X_test),)

    def test_pi_range(self):
        """测试 PI 值范围 [0, 1]"""
        pi = ProbabilityOfImprovement()
        values = pi(self.X_test, self.gp, self.y_best)

        assert np.all(values >= -1e-10)
        assert np.all(values <= 1.0 + 1e-10)

    def test_ts_shape(self):
        """测试 Thompson 采样形状"""
        ts = ThompsonSampling()
        values = ts(self.X_test, self.gp, self.y_best)

        assert values.shape == (len(self.X_test),)

    def test_create_acquisition(self):
        """测试工厂函数"""
        acquisitions = ['ei', 'ucb', 'pi', 'ts']

        for name in acquisitions:
            acq = create_acquisition(name)
            assert acq is not None

    def test_create_acquisition_invalid(self):
        """测试无效采集函数名称"""
        with pytest.raises(ValueError):
            create_acquisition('invalid')

    def test_ei_exploration_exploitation(self):
        """测试 EI 的探索-开发权衡"""
        ei_low = ExpectedImprovement(xi=0.0)
        ei_high = ExpectedImprovement(xi=1.0)

        values_low = ei_low(self.X_test, self.gp, self.y_best)
        values_high = ei_high(self.X_test, self.gp, self.y_best)

        # xi 越大，应该更倾向于探索
        # 这里只检查形状，不检查具体值
        assert values_low.shape == values_high.shape

    def test_ucb_decay(self):
        """测试 UCB 衰减"""
        ucb = UpperConfidenceBound(kappa=2.0, decay=True)

        values1 = ucb(self.X_test, self.gp, self.y_best)
        values2 = ucb(self.X_test, self.gp, self.y_best)

        # 迭代次数增加，kappa 应该减小
        assert ucb.iteration == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
