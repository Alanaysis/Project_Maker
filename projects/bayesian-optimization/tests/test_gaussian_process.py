"""
高斯过程回归测试
"""

import numpy as np
import pytest
from src.gaussian_process import GaussianProcess
from src.kernels import RBF, Matern, WhiteNoise


class TestGaussianProcess:
    """高斯过程测试类"""

    def setup_method(self):
        """测试前准备"""
        np.random.seed(42)

        # 生成测试数据
        self.X_train = np.random.uniform(-5, 5, (20, 1))
        self.y_train = np.sin(self.X_train).ravel() + 0.1 * np.random.randn(20)

        self.X_test = np.random.uniform(-5, 5, (10, 1))

    def test_initialization(self):
        """测试初始化"""
        gp = GaussianProcess()
        assert gp.kernel is not None
        assert gp.noise_variance == 1e-6

    def test_fit(self):
        """测试拟合"""
        gp = GaussianProcess(kernel=RBF(length_scale=1.0))
        gp.fit(self.X_train, self.y_train)

        assert gp.X_train is not None
        assert gp.y_train is not None
        assert gp.alpha is not None
        assert gp.L is not None

    def test_predict_shape(self):
        """测试预测形状"""
        gp = GaussianProcess()
        gp.fit(self.X_train, self.y_train)

        y_mean, y_std = gp.predict(self.X_test, return_std=True)

        assert y_mean.shape == (len(self.X_test),)
        assert y_std.shape == (len(self.X_test),)

    def test_predict_without_fit(self):
        """测试未拟合时预测"""
        gp = GaussianProcess()

        with pytest.raises(RuntimeError):
            gp.predict(self.X_test)

    def test_predict_variance(self):
        """测试预测方差非负"""
        gp = GaussianProcess()
        gp.fit(self.X_train, self.y_train)

        _, y_std = gp.predict(self.X_test, return_std=True)

        assert np.all(y_std >= 0)

    def test_sample_shape(self):
        """测试采样形状"""
        gp = GaussianProcess()
        gp.fit(self.X_train, self.y_train)

        n_samples = 5
        samples = gp.sample(self.X_test, n_samples=n_samples)

        assert samples.shape == (len(self.X_test), n_samples)

    def test_rbf_kernel(self):
        """测试 RBF 核"""
        kernel = RBF(length_scale=1.0, signal_variance=1.0)
        K = kernel(self.X_train, self.X_train)

        assert K.shape == (len(self.X_train), len(self.X_train))
        assert np.allclose(K, K.T)  # 对称性
        assert np.all(np.diag(K) > 0)  # 正定性

    def test_matern_kernel(self):
        """测试 Matérn 核"""
        kernel = Matern(length_scale=1.0, signal_variance=1.0, nu=2.5)
        K = kernel(self.X_train, self.X_train)

        assert K.shape == (len(self.X_train), len(self.X_train))
        assert np.allclose(K, K.T)

    def test_white_noise_kernel(self):
        """测试白噪声核"""
        kernel = WhiteNoise(noise_variance=1.0)
        K = kernel(self.X_train, self.X_train)

        assert K.shape == (len(self.X_train), len(self.X_train))
        assert np.allclose(K, np.eye(len(self.X_train)))

    def test_different_kernels(self):
        """测试不同核函数"""
        kernels = [
            RBF(length_scale=1.0),
            RBF(length_scale=2.0),
            Matern(length_scale=1.0, nu=1.5),
            Matern(length_scale=1.0, nu=2.5),
        ]

        for kernel in kernels:
            gp = GaussianProcess(kernel=kernel)
            gp.fit(self.X_train, self.y_train)

            y_mean, y_std = gp.predict(self.X_test, return_std=True)

            assert y_mean.shape == (len(self.X_test),)
            assert y_std.shape == (len(self.X_test),)

    def test_log_marginal_likelihood(self):
        """测试边际似然计算"""
        gp = GaussianProcess(kernel=RBF(length_scale=1.0))
        gp.fit(self.X_train, self.y_train)

        assert gp.log_marginal_likelihood is not None
        assert np.isfinite(gp.log_marginal_likelihood)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
