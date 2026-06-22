"""PCA 主类测试"""

import numpy as np
import pytest

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.pca import PCA


class TestPCAFit:
    """测试 PCA 拟合过程。"""

    def test_basic_fit(self):
        """测试基本拟合功能。"""
        np.random.seed(42)
        X = np.random.randn(100, 5)

        pca = PCA(n_components=2)
        pca.fit(X)

        assert pca._is_fitted
        assert pca.n_components_ == 2
        assert pca.n_features_ == 5
        assert pca.n_samples_ == 100

    def test_components_shape(self):
        """测试主成分矩阵形状。"""
        np.random.seed(42)
        X = np.random.randn(50, 4)

        pca = PCA(n_components=2)
        pca.fit(X)

        assert pca.components_.shape == (2, 4)

    def test_explained_variance(self):
        """测试解释方差。"""
        np.random.seed(42)
        X = np.random.randn(100, 3)

        pca = PCA(n_components=3)
        pca.fit(X)

        # 特征值应为正数
        assert np.all(pca.explained_variance_ >= 0)

        # 解释方差比例之和应为1
        np.testing.assert_almost_equal(np.sum(pca.explained_variance_ratio_), 1.0)

    def test_explained_variance_ratio_by_threshold(self):
        """测试按阈值选择主成分数量。"""
        np.random.seed(42)
        X = np.random.randn(100, 5)

        pca = PCA(n_components=0.95)
        pca.fit(X)

        # 累积解释方差应 >= 0.95
        assert np.sum(pca.explained_variance_ratio_) >= 0.95

    def test_reproducibility(self):
        """测试可重复性（相同数据应得到相同结果）。"""
        np.random.seed(42)
        X = np.random.randn(50, 3)

        pca1 = PCA(n_components=2)
        pca2 = PCA(n_components=2)

        result1 = pca1.fit_transform(X)
        result2 = pca2.fit_transform(X)

        # 由于特征向量可能有符号差异，检查绝对值
        np.testing.assert_array_almost_equal(
            np.abs(result1), np.abs(result2), decimal=10
        )


class TestPCATransform:
    """测试 PCA 变换功能。"""

    def test_fit_transform(self):
        """测试 fit_transform 组合。"""
        np.random.seed(42)
        X = np.random.randn(100, 5)

        pca = PCA(n_components=2)
        X_reduced = pca.fit_transform(X)

        assert X_reduced.shape == (100, 2)

    def test_transform_new_data(self):
        """测试对新数据的变换。"""
        np.random.seed(42)
        X_train = np.random.randn(100, 5)
        X_test = np.random.randn(20, 5)

        pca = PCA(n_components=2)
        pca.fit(X_train)
        X_test_reduced = pca.transform(X_test)

        assert X_test_reduced.shape == (20, 2)

    def test_transform_before_fit_raises(self):
        """测试在拟合前调用 transform 应抛出异常。"""
        pca = PCA(n_components=2)
        X = np.random.randn(10, 3)

        with pytest.raises(RuntimeError, match="尚未拟合"):
            pca.transform(X)

    def test_transform_wrong_features(self):
        """测试特征数不匹配应抛出异常。"""
        np.random.seed(42)
        X_train = np.random.randn(50, 4)
        X_test = np.random.randn(10, 3)  # 不同的特征数

        pca = PCA(n_components=2)
        pca.fit(X_train)

        with pytest.raises(ValueError, match="特征数"):
            pca.transform(X_test)


class TestPCAInverseTransform:
    """测试 PCA 逆变换功能。"""

    def test_inverse_transform(self):
        """测试逆变换。"""
        np.random.seed(42)
        X = np.random.randn(50, 5)

        pca = PCA(n_components=2)
        X_reduced = pca.fit_transform(X)
        X_reconstructed = pca.inverse_transform(X_reduced)

        assert X_reconstructed.shape == X.shape

    def test_reconstruction_quality(self):
        """测试全维度 PCA 的重建质量（应无损）。"""
        np.random.seed(42)
        X = np.random.randn(50, 3)

        # 保留所有成分
        pca = PCA(n_components=3)
        X_reduced = pca.fit_transform(X)
        X_reconstructed = pca.inverse_transform(X_reduced)

        # 全维度重建应接近原始数据
        np.testing.assert_array_almost_equal(X, X_reconstructed, decimal=10)

    def test_reconstruction_error(self):
        """测试重建误差计算。"""
        np.random.seed(42)
        X = np.random.randn(100, 5)

        # 全维度应无误差
        pca_full = PCA(n_components=5)
        pca_full.fit(X)
        error_full = pca_full.reconstruction_error(X)
        assert error_full < 1e-10

        # 降维应有误差
        pca_reduced = PCA(n_components=2)
        pca_reduced.fit(X)
        error_reduced = pca_reduced.reconstruction_error(X)
        assert error_reduced > 0


class TestPCADimensionReduction:
    """测试 PCA 降维效果。"""

    def test_correlated_data(self):
        """测试对相关数据的降维效果。"""
        np.random.seed(42)

        # 创建高度相关的数据
        n = 200
        x = np.random.randn(n)
        X = np.column_stack([
            x,
            x + np.random.randn(n) * 0.1,  # 高度相关
            np.random.randn(n),              # 独立
        ])

        pca = PCA(n_components=2)
        X_reduced = pca.fit_transform(X)

        # 第一个主成分应解释大部分方差
        assert pca.explained_variance_ratio_[0] > 0.5

    def test_dimension_preserves_structure(self):
        """测试降维保留数据结构。"""
        np.random.seed(42)

        # 创建有明显聚类结构的数据
        cluster1 = np.random.randn(50, 5) + np.array([5, 0, 0, 0, 0])
        cluster2 = np.random.randn(50, 5) + np.array([-5, 0, 0, 0, 0])
        X = np.vstack([cluster1, cluster2])

        pca = PCA(n_components=2)
        X_reduced = pca.fit_transform(X)

        # 聚类在降维后应仍可分离
        cluster1_reduced = X_reduced[:50]
        cluster2_reduced = X_reduced[50:]

        center1 = np.mean(cluster1_reduced, axis=0)
        center2 = np.mean(cluster2_reduced, axis=0)

        # 两个聚类中心的距离应较大
        distance = np.linalg.norm(center1 - center2)
        assert distance > 1.0


class TestPCAEdgeCases:
    """测试边界情况。"""

    def test_invalid_n_components_int(self):
        """测试无效的整数 n_components。"""
        X = np.random.randn(10, 3)

        pca = PCA(n_components=0)
        with pytest.raises(ValueError, match=">= 1"):
            pca.fit(X)

    def test_invalid_n_components_float(self):
        """测试无效的浮点数 n_components。"""
        X = np.random.randn(10, 3)

        pca = PCA(n_components=1.5)
        with pytest.raises(ValueError, match="0, 1"):
            pca.fit(X)

    def test_n_components_exceeds_features(self):
        """测试 n_components 超过特征数。"""
        X = np.random.randn(10, 3)

        pca = PCA(n_components=5)
        with pytest.raises(ValueError, match="不能大于特征数"):
            pca.fit(X)

    def test_1d_input_raises(self):
        """测试1D输入应抛出异常。"""
        X = np.array([1, 2, 3], dtype=np.float64)
        pca = PCA(n_components=1)

        with pytest.raises(ValueError, match="2D"):
            pca.fit(X)

    def test_repr_not_fitted(self):
        """测试未拟合时的字符串表示。"""
        pca = PCA(n_components=2)
        repr_str = repr(pca)
        assert "not fitted" in repr_str

    def test_repr_fitted(self):
        """测试拟合后的字符串表示。"""
        np.random.seed(42)
        X = np.random.randn(50, 3)
        pca = PCA(n_components=2)
        pca.fit(X)

        repr_str = repr(pca)
        assert "n_components=2" in repr_str
        assert "not fitted" not in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
