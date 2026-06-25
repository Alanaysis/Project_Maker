"""核 PCA 测试"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.kernel_pca import KernelPCA


@pytest.fixture
def sample_data():
    """生成测试数据"""
    np.random.seed(42)
    # 创建非线性可分的数据
    n = 100
    t = np.linspace(0, 2 * np.pi, n)
    X = np.column_stack([
        np.cos(t) + 0.1 * np.random.randn(n),
        np.sin(t) + 0.1 * np.random.randn(n),
        0.5 * np.cos(2 * t) + 0.1 * np.random.randn(n),
    ])
    return X


class TestKernelPCA:
    """核 PCA 测试类"""

    def test_basic_fit_transform(self, sample_data):
        """测试基本拟合和转换"""
        kpca = KernelPCA(n_components=2, kernel='rbf')
        X_transformed = kpca.fit_transform(sample_data)

        assert X_transformed.shape == (100, 2)
        assert kpca.lambdas_ is not None
        assert kpca.alphas_ is not None

    def test_rbf_kernel(self, sample_data):
        """测试 RBF 核"""
        kpca = KernelPCA(n_components=2, kernel='rbf', gamma=1.0)
        X_transformed = kpca.fit_transform(sample_data)

        assert X_transformed.shape == (100, 2)
        assert kpca.gamma_ == 1.0

    def test_poly_kernel(self, sample_data):
        """测试多项式核"""
        kpca = KernelPCA(n_components=2, kernel='poly', degree=3)
        X_transformed = kpca.fit_transform(sample_data)

        assert X_transformed.shape == (100, 2)

    def test_linear_kernel(self, sample_data):
        """测试线性核（应接近标准 PCA）"""
        kpca = KernelPCA(n_components=2, kernel='linear')
        X_transformed = kpca.fit_transform(sample_data)

        assert X_transformed.shape == (100, 2)

    def test_sigmoid_kernel(self, sample_data):
        """测试 sigmoid 核"""
        kpca = KernelPCA(n_components=2, kernel='sigmoid')
        X_transformed = kpca.fit_transform(sample_data)

        assert X_transformed.shape == (100, 2)

    def test_transform_new_data(self, sample_data):
        """测试转换新数据"""
        kpca = KernelPCA(n_components=2, kernel='rbf')
        kpca.fit(sample_data)

        X_new = sample_data[:10]
        X_transformed = kpca.transform(X_new)

        assert X_transformed.shape == (10, 2)

    def test_n_components(self, sample_data):
        """测试不同主成分数量"""
        for n in [1, 2, 3]:
            kpca = KernelPCA(n_components=n, kernel='rbf')
            X_transformed = kpca.fit_transform(sample_data)
            assert X_transformed.shape == (100, n)

    def test_auto_gamma(self, sample_data):
        """测试自动 gamma 设置"""
        kpca = KernelPCA(n_components=2, kernel='rbf')
        kpca.fit(sample_data)

        # gamma 应该是 1/n_features
        expected_gamma = 1.0 / sample_data.shape[1]
        assert abs(kpca.gamma_ - expected_gamma) < 1e-10

    def test_repr(self, sample_data):
        """测试字符串表示"""
        kpca = KernelPCA(n_components=2, kernel='rbf', gamma=0.5)
        assert "KernelPCA" in repr(kpca)
        assert "rbf" in repr(kpca)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
