"""
KNN 测试用例

测试距离度量和 KNN 分类器的功能。
"""

import pytest
import numpy as np
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.distance_metrics import DistanceMetrics
from src.knn_classifier import KNNClassifier


class TestDistanceMetrics:
    """距离度量测试类"""

    def test_euclidean_distance_same_point(self):
        """测试相同点的欧氏距离"""
        assert DistanceMetrics.euclidean([0, 0], [0, 0]) == 0.0
        assert DistanceMetrics.euclidean([1, 2, 3], [1, 2, 3]) == 0.0

    def test_euclidean_distance_unit(self):
        """测试单位距离的欧氏距离"""
        assert DistanceMetrics.euclidean([0, 0], [1, 0]) == 1.0
        assert DistanceMetrics.euclidean([0, 0], [0, 1]) == 1.0

    def test_euclidean_distance_2d(self):
        """测试二维欧氏距离"""
        # 3-4-5 直角三角形
        assert abs(DistanceMetrics.euclidean([0, 0], [3, 4]) - 5.0) < 1e-10

    def test_euclidean_distance_3d(self):
        """测试三维欧氏距离"""
        x1 = np.array([1, 2, 3])
        x2 = np.array([4, 5, 6])
        expected = np.sqrt(27)
        assert abs(DistanceMetrics.euclidean(x1, x2) - expected) < 1e-10

    def test_euclidean_distance_symmetry(self):
        """测试欧氏距离的对称性"""
        x1 = [1, 2, 3]
        x2 = [4, 5, 6]
        assert DistanceMetrics.euclidean(x1, x2) == DistanceMetrics.euclidean(x2, x1)

    def test_manhattan_distance_same_point(self):
        """测试相同点的曼哈顿距离"""
        assert DistanceMetrics.manhattan([0, 0], [0, 0]) == 0
        assert DistanceMetrics.manhattan([1, 2, 3], [1, 2, 3]) == 0

    def test_manhattan_distance_unit(self):
        """测试单位距离的曼哈顿距离"""
        assert DistanceMetrics.manhattan([0, 0], [1, 0]) == 1
        assert DistanceMetrics.manhattan([0, 0], [0, 1]) == 1

    def test_manhattan_distance_grid(self):
        """测试网格路径的曼哈顿距离"""
        assert DistanceMetrics.manhattan([0, 0], [3, 4]) == 7

    def test_manhattan_distance_3d(self):
        """测试三维曼哈顿距离"""
        x1 = np.array([1, 2, 3])
        x2 = np.array([4, 5, 6])
        assert DistanceMetrics.manhattan(x1, x2) == 9

    def test_minkowski_distance_p1(self):
        """测试闵可夫斯基距离 p=1（曼哈顿距离）"""
        x1 = np.array([0, 0])
        x2 = np.array([3, 4])
        assert DistanceMetrics.minkowski(x1, x2, p=1) == 7

    def test_minkowski_distance_p2(self):
        """测试闵可夫斯基距离 p=2（欧氏距离）"""
        x1 = np.array([0, 0])
        x2 = np.array([3, 4])
        assert abs(DistanceMetrics.minkowski(x1, x2, p=2) - 5.0) < 1e-10

    def test_minkowski_distance_pinf(self):
        """测试闵可夫斯基距离 p=inf（切比雪夫距离）"""
        x1 = np.array([0, 0])
        x2 = np.array([3, 4])
        assert abs(DistanceMetrics.minkowski(x1, x2, p=float('inf')) - 4.0) < 1e-10

    def test_cosine_similarity_same_direction(self):
        """测试相同方向的余弦相似度"""
        assert abs(DistanceMetrics.cosine([1, 0], [1, 0]) - 1.0) < 1e-10
        assert abs(DistanceMetrics.cosine([1, 1], [2, 2]) - 1.0) < 1e-10

    def test_cosine_similarity_orthogonal(self):
        """测试正交向量的余弦相似度"""
        assert abs(DistanceMetrics.cosine([1, 0], [0, 1]) - 0.0) < 1e-10

    def test_cosine_similarity_opposite(self):
        """测试相反方向的余弦相似度"""
        assert abs(DistanceMetrics.cosine([1, 0], [-1, 0]) - (-1.0)) < 1e-10

    def test_cosine_similarity_zero_vector(self):
        """测试零向量的余弦相似度"""
        assert DistanceMetrics.cosine([0, 0], [1, 1]) == 0.0
        assert DistanceMetrics.cosine([1, 1], [0, 0]) == 0.0

    def test_cosine_distance(self):
        """测试余弦距离"""
        # 相同方向
        assert abs(DistanceMetrics.cosine_distance([1, 0], [1, 0]) - 0.0) < 1e-10

        # 正交
        assert abs(DistanceMetrics.cosine_distance([1, 0], [0, 1]) - 1.0) < 1e-10

        # 相反方向
        assert abs(DistanceMetrics.cosine_distance([1, 0], [-1, 0]) - 2.0) < 1e-10

    def test_get_metric_valid(self):
        """测试获取有效距离函数"""
        for metric_name in ['euclidean', 'manhattan', 'minkowski', 'cosine']:
            metric_func = DistanceMetrics.get_metric(metric_name)
            assert callable(metric_func)

    def test_get_metric_invalid(self):
        """测试获取无效距离函数"""
        with pytest.raises(ValueError):
            DistanceMetrics.get_metric('invalid_metric')

    def test_compute_distance(self):
        """测试统一距离计算接口"""
        x1 = [0, 0]
        x2 = [3, 4]

        # 测试各种距离度量
        assert abs(DistanceMetrics.compute_distance(x1, x2, 'euclidean') - 5.0) < 1e-10
        assert DistanceMetrics.compute_distance(x1, x2, 'manhattan') == 7
        assert abs(DistanceMetrics.compute_distance(x1, x2, 'minkowski', p=2) - 5.0) < 1e-10

    def test_input_shape_mismatch(self):
        """测试输入维度不匹配"""
        with pytest.raises(ValueError):
            DistanceMetrics.euclidean([1, 2], [1, 2, 3])

        with pytest.raises(ValueError):
            DistanceMetrics.manhattan([1, 2], [1, 2, 3])


class TestKNNClassifier:
    """KNN 分类器测试类"""

    def test_initialization_default(self):
        """测试默认参数初始化"""
        knn = KNNClassifier()
        assert knn.k == 3
        assert knn.metric == 'euclidean'
        assert knn.X_train is None
        assert knn.y_train is None

    def test_initialization_custom(self):
        """测试自定义参数初始化"""
        knn = KNNClassifier(k=5, metric='manhattan')
        assert knn.k == 5
        assert knn.metric == 'manhattan'

    def test_initialization_invalid_k(self):
        """测试无效 K 值初始化"""
        with pytest.raises(ValueError):
            KNNClassifier(k=0)

        with pytest.raises(ValueError):
            KNNClassifier(k=-1)

        with pytest.raises(ValueError):
            KNNClassifier(k=1.5)

    def test_initialization_invalid_metric(self):
        """测试无效距离度量初始化"""
        with pytest.raises(ValueError):
            KNNClassifier(metric='invalid')

    def test_fit_basic(self):
        """测试基本训练功能"""
        X_train = np.array([[1, 2], [3, 4], [5, 6]])
        y_train = np.array([0, 1, 0])

        knn = KNNClassifier(k=2)
        result = knn.fit(X_train, y_train)

        # 验证返回自身
        assert result is knn

        # 验证训练数据已存储
        np.testing.assert_array_equal(knn.X_train, X_train)
        np.testing.assert_array_equal(knn.y_train, y_train)
        np.testing.assert_array_equal(knn.classes_, np.array([0, 1]))

    def test_fit_validation_x_dimension(self):
        """测试训练时 X 维度验证"""
        X_train = np.array([1, 2, 3])  # 一维数组
        y_train = np.array([0, 1, 0])

        knn = KNNClassifier(k=2)
        with pytest.raises(ValueError):
            knn.fit(X_train, y_train)

    def test_fit_validation_y_dimension(self):
        """测试训练时 y 维度验证"""
        X_train = np.array([[1, 2], [3, 4], [5, 6]])
        y_train = np.array([[0, 1, 0]])  # 二维数组

        knn = KNNClassifier(k=2)
        with pytest.raises(ValueError):
            knn.fit(X_train, y_train)

    def test_fit_validation_sample_mismatch(self):
        """测试训练时样本数量不匹配"""
        X_train = np.array([[1, 2], [3, 4]])
        y_train = np.array([0, 1, 0])  # 样本数量不匹配

        knn = KNNClassifier(k=2)
        with pytest.raises(ValueError):
            knn.fit(X_train, y_train)

    def test_fit_validation_empty_data(self):
        """测试空数据训练"""
        X_train = np.array([]).reshape(0, 2)
        y_train = np.array([])

        knn = KNNClassifier(k=1)
        with pytest.raises(ValueError):
            knn.fit(X_train, y_train)

    def test_fit_validation_k_too_large(self):
        """测试 K 值过大"""
        X_train = np.array([[1, 2]])
        y_train = np.array([0])

        knn = KNNClassifier(k=2)
        with pytest.raises(ValueError):
            knn.fit(X_train, y_train)

    def test_predict_basic(self):
        """测试基本预测功能"""
        X_train = np.array([
            [1, 2], [1, 3], [2, 2],  # 类别 0
            [5, 5], [5, 6], [6, 5]   # 类别 1
        ])
        y_train = np.array([0, 0, 0, 1, 1, 1])

        knn = KNNClassifier(k=3)
        knn.fit(X_train, y_train)

        X_test = np.array([[2, 3], [4, 4]])
        predictions = knn.predict(X_test)

        assert len(predictions) == 2
        assert predictions[0] == 0  # 应该属于类别 0
        assert predictions[1] == 1  # 应该属于类别 1

    def test_predict_single_sample(self):
        """测试单样本预测"""
        X_train = np.array([[1, 2], [3, 4], [5, 6]])
        y_train = np.array([0, 1, 0])

        knn = KNNClassifier(k=2)
        knn.fit(X_train, y_train)

        # 一维输入
        X_test = np.array([2, 3])
        predictions = knn.predict(X_test)

        assert len(predictions) == 1

    def test_predict_before_fit(self):
        """测试未训练时预测"""
        knn = KNNClassifier(k=3)

        with pytest.raises(RuntimeError):
            knn.predict(np.array([[1, 2]]))

    def test_predict_feature_mismatch(self):
        """测试特征数量不匹配"""
        X_train = np.array([[1, 2], [3, 4]])
        y_train = np.array([0, 1])

        knn = KNNClassifier(k=1)
        knn.fit(X_train, y_train)

        with pytest.raises(ValueError):
            knn.predict(np.array([[1, 2, 3]]))  # 特征数量不匹配

    def test_predict_proba_basic(self):
        """测试概率预测"""
        X_train = np.array([[1, 2], [3, 4], [5, 6]])
        y_train = np.array([0, 1, 0])

        knn = KNNClassifier(k=2)
        knn.fit(X_train, y_train)

        X_test = np.array([[2, 3]])
        proba = knn.predict_proba(X_test)

        # 验证概率形状
        assert proba.shape == (1, 2)

        # 验证概率和为 1
        assert abs(np.sum(proba) - 1.0) < 1e-10

    def test_predict_proba_before_fit(self):
        """测试未训练时概率预测"""
        knn = KNNClassifier(k=3)

        with pytest.raises(RuntimeError):
            knn.predict_proba(np.array([[1, 2]]))

    def test_score_basic(self):
        """测试准确率计算"""
        X_train = np.array([
            [1, 2], [1, 3], [2, 2],  # 类别 0
            [5, 5], [5, 6], [6, 5]   # 类别 1
        ])
        y_train = np.array([0, 0, 0, 1, 1, 1])

        knn = KNNClassifier(k=3)
        knn.fit(X_train, y_train)

        X_test = np.array([[2, 3], [4, 4]])
        y_test = np.array([0, 1])

        accuracy = knn.score(X_test, y_test)
        assert accuracy == 1.0  # 完全正确

    def test_different_metrics(self):
        """测试不同距离度量"""
        X_train = np.array([[1, 2], [3, 4], [5, 6]])
        y_train = np.array([0, 1, 0])

        metrics = ['euclidean', 'manhattan', 'minkowski', 'cosine']

        for metric in metrics:
            knn = KNNClassifier(k=2, metric=metric)
            knn.fit(X_train, y_train)

            predictions = knn.predict(np.array([[2, 3]]))
            assert len(predictions) == 1

    def test_different_k_values(self):
        """测试不同 K 值"""
        X_train = np.array([
            [1, 2], [1, 3], [2, 2], [2, 3],  # 类别 0
            [5, 5], [5, 6], [6, 5], [6, 6]   # 类别 1
        ])
        y_train = np.array([0, 0, 0, 0, 1, 1, 1, 1])

        for k in [1, 3, 5, 7]:
            knn = KNNClassifier(k=k)
            knn.fit(X_train, y_train)

            predictions = knn.predict(np.array([[3, 4]]))
            assert len(predictions) == 1

    def test_multiclass(self):
        """测试多分类"""
        X_train = np.array([
            [1, 2], [1, 3], [2, 2],  # 类别 0
            [5, 5], [5, 6], [6, 5],  # 类别 1
            [3, 8], [4, 8], [3, 9]   # 类别 2
        ])
        y_train = np.array([0, 0, 0, 1, 1, 1, 2, 2, 2])

        knn = KNNClassifier(k=3)
        knn.fit(X_train, y_train)

        X_test = np.array([[1, 2], [5, 5], [3, 8]])
        predictions = knn.predict(X_test)

        assert len(predictions) == 3
        assert predictions[0] == 0
        assert predictions[1] == 1
        assert predictions[2] == 2

    def test_get_params(self):
        """测试获取参数"""
        knn = KNNClassifier(k=5, metric='manhattan')
        params = knn.get_params()

        assert params == {'k': 5, 'metric': 'manhattan', 'weights': 'uniform'}

    def test_set_params(self):
        """测试设置参数"""
        knn = KNNClassifier(k=3, metric='euclidean')
        knn.set_params(k=5, metric='manhattan')

        assert knn.k == 5
        assert knn.metric == 'manhattan'

    def test_set_params_invalid_k(self):
        """测试设置无效 K 值"""
        knn = KNNClassifier()

        with pytest.raises(ValueError):
            knn.set_params(k=0)

        with pytest.raises(ValueError):
            knn.set_params(k=-1)

    def test_set_params_invalid_metric(self):
        """测试设置无效距离度量"""
        knn = KNNClassifier()

        with pytest.raises(ValueError):
            knn.set_params(metric='invalid')

    def test_set_params_unknown(self):
        """测试设置未知参数"""
        knn = KNNClassifier()

        with pytest.raises(ValueError):
            knn.set_params(unknown_param=1)

    def test_repr(self):
        """测试字符串表示"""
        knn = KNNClassifier(k=5, metric='manhattan')
        assert repr(knn) == "KNNClassifier(k=5, metric='manhattan', weights='uniform')"

    def test_chain_calling(self):
        """测试链式调用"""
        X_train = np.array([[1, 2], [3, 4]])
        y_train = np.array([0, 1])

        knn = KNNClassifier(k=1)
        result = knn.fit(X_train, y_train)

        assert result is knn


class TestKNNIntegration:
    """KNN 集成测试类"""

    def test_iris_like_dataset(self):
        """测试类似鸢尾花数据集"""
        # 创建简单的三分类数据集
        np.random.seed(42)

        # 类别 0
        X0 = np.random.randn(20, 2) + np.array([0, 0])
        y0 = np.zeros(20, dtype=int)

        # 类别 1
        X1 = np.random.randn(20, 2) + np.array([5, 5])
        y1 = np.ones(20, dtype=int)

        # 类别 2
        X2 = np.random.randn(20, 2) + np.array([10, 0])
        y2 = np.full(20, 2, dtype=int)

        # 合并数据
        X_train = np.vstack([X0, X1, X2])
        y_train = np.concatenate([y0, y1, y2])

        # 训练模型
        knn = KNNClassifier(k=5, metric='euclidean')
        knn.fit(X_train, y_train)

        # 测试预测
        X_test = np.array([[1, 1], [6, 6], [11, 1]])
        predictions = knn.predict(X_test)

        assert len(predictions) == 3
        assert predictions[0] == 0
        assert predictions[1] == 1
        assert predictions[2] == 2

    def test_xor_like_dataset(self):
        """测试 XOR 类型数据集"""
        X_train = np.array([
            [0, 0], [0, 1], [1, 0], [1, 1]
        ])
        y_train = np.array([0, 1, 1, 0])

        knn = KNNClassifier(k=1)
        knn.fit(X_train, y_train)

        # 测试训练样本
        predictions = knn.predict(X_train)
        np.testing.assert_array_equal(predictions, y_train)

    def test_large_dataset_performance(self):
        """测试大规模数据集性能"""
        # 生成大数据集
        n_samples = 1000
        n_features = 10
        np.random.seed(42)

        X_train = np.random.randn(n_samples, n_features)
        y_train = np.random.randint(0, 3, n_samples)

        knn = KNNClassifier(k=5)
        knn.fit(X_train, y_train)

        # 测试预测
        X_test = np.random.randn(10, n_features)
        predictions = knn.predict(X_test)

        assert len(predictions) == 10

    def test_high_dimensional_data(self):
        """测试高维数据"""
        n_samples = 100
        n_features = 50
        np.random.seed(42)

        X_train = np.random.randn(n_samples, n_features)
        y_train = np.random.randint(0, 2, n_samples)

        knn = KNNClassifier(k=3, metric='euclidean')
        knn.fit(X_train, y_train)

        X_test = np.random.randn(5, n_features)
        predictions = knn.predict(X_test)

        assert len(predictions) == 5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])