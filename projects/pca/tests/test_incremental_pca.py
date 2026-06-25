"""增量 PCA 测试"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.incremental_pca import IncrementalPCA
from src.pca import PCA


@pytest.fixture
def sample_data():
    """生成测试数据"""
    np.random.seed(42)
    X = np.random.randn(200, 10)
    return X


class TestIncrementalPCA:
    """增量 PCA 测试类"""

    def test_basic_fit_transform(self, sample_data):
        """测试基本拟合和转换"""
        ipca = IncrementalPCA(n_components=3, batch_size=50)
        X_transformed = ipca.fit_transform(sample_data)

        assert X_transformed.shape == (200, 3)
        assert ipca.components_.shape == (3, 10)

    def test_consistency_with_pca(self, sample_data):
        """测试与标准 PCA 结果的一致性"""
        # 标准 PCA
        pca = PCA(n_components=3)
        X_pca = pca.fit_transform(sample_data)

        # 增量 PCA（一次性处理）
        ipca = IncrementalPCA(n_components=3, batch_size=200)
        X_ipca = ipca.fit_transform(sample_data)

        # 结果应该非常接近（可能符号不同）
        for i in range(3):
            corr = abs(np.corrcoef(X_pca[:, i], X_ipca[:, i])[0, 1])
            assert corr > 0.95, f"主成分 {i} 相关系数过低: {corr}"

    def test_partial_fit(self, sample_data):
        """测试增量更新"""
        ipca = IncrementalPCA(n_components=3)

        # 分批处理
        batch_size = 50
        for i in range(0, len(sample_data), batch_size):
            batch = sample_data[i:i + batch_size]
            ipca.partial_fit(batch)

        X_transformed = ipca.transform(sample_data)
        assert X_transformed.shape == (200, 3)
        assert ipca.n_samples_seen_ == 200

    def test_different_batch_sizes(self, sample_data):
        """测试不同批次大小"""
        results = []
        for batch_size in [25, 50, 100]:
            ipca = IncrementalPCA(n_components=3, batch_size=batch_size)
            X_transformed = ipca.fit_transform(sample_data)
            results.append(X_transformed)

        # 不同批次大小应该产生相似结果
        for i in range(1, len(results)):
            for j in range(3):
                corr = abs(np.corrcoef(results[0][:, j], results[i][:, j])[0, 1])
                assert corr > 0.9, f"批次大小不一致: corr={corr}"

    def test_inverse_transform(self, sample_data):
        """测试逆转换"""
        ipca = IncrementalPCA(n_components=5, batch_size=50)
        X_transformed = ipca.fit_transform(sample_data)
        X_reconstructed = ipca.inverse_transform(X_transformed)

        assert X_reconstructed.shape == sample_data.shape

    def test_explained_variance(self, sample_data):
        """测试解释方差"""
        ipca = IncrementalPCA(n_components=5, batch_size=50)
        ipca.fit(sample_data)

        assert ipca.explained_variance_ is not None
        assert ipca.explained_variance_ratio_ is not None
        assert len(ipca.explained_variance_) == 5
        assert all(ipca.explained_variance_ >= 0)

    def test_auto_n_components(self, sample_data):
        """测试自动确定主成分数量"""
        ipca = IncrementalPCA(batch_size=50)
        ipca.fit(sample_data)

        # 应该保留所有成分
        assert ipca.n_components == min(sample_data.shape)

    def test_repr(self, sample_data):
        """测试字符串表示"""
        ipca = IncrementalPCA(n_components=3, batch_size=50)
        assert "IncrementalPCA" in repr(ipca)
        assert "3" in repr(ipca)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
