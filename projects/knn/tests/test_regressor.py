"""
KNN 回归器测试用例
"""

import pytest
import numpy as np
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.knn_regressor import KNNRegressor


class TestKNNRegressor:
    """KNN 回归器测试类"""

    def test_initialization_default(self):
        """测试默认参数初始化"""
        reg = KNNRegressor()
        assert reg.k == 5
        assert reg.metric == 'euclidean'
        assert reg.weights == 'uniform'
        assert reg.X_train is None
        assert reg.y_train is None

    def test_initialization_custom(self):
        """测试自定义参数初始化"""
        reg = KNNRegressor(k=3, metric='manhattan', weights='distance')
        assert reg.k == 3
        assert reg.metric == 'manhattan'
        assert reg.weights == 'distance'

    def test_initialization_invalid_k(self):
        """测试无效 K 值初始化"""
        with pytest.raises(ValueError):
            KNNRegressor(k=0)

        with pytest.raises(ValueError):
            KNNRegressor(k=-1)

        with pytest.raises(ValueError):
            KNNRegressor(k=1.5)

    def test_initialization_invalid_metric(self):
        """测试无效距离度量初始化"""
        with pytest.raises(ValueError):
            KNNRegressor(metric='invalid')

    def test_initialization_invalid_weights(self):
        """测试无效权重策略初始化"""
        with pytest.raises(ValueError):
            KNNRegressor(weights='invalid')

    def test_fit_basic(self):
        """测试基本训练功能"""
        X_train = np.array([[1], [2], [3], [4], [5]])
        y_train = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        reg = KNNRegressor(k=3)
        result = reg.fit(X_train, y_train)

        assert result is reg
        np.testing.assert_array_equal(reg.X_train, X_train)
        np.testing.assert_array_equal(reg.y_train, y_train)

    def test_fit_validation(self):
        """测试训练时输入验证"""
        reg = KNNRegressor(k=2)

        # 一维 X
        with pytest.raises(ValueError):
            reg.fit(np.array([1, 2, 3]), np.array([1, 2, 3]))

        # 二维 y
        with pytest.raises(ValueError):
            reg.fit(np.array([[1], [2]]), np.array([[1], [2]]))

        # 样本数量不匹配
        with pytest.raises(ValueError):
            reg.fit(np.array([[1], [2]]), np.array([1, 2, 3]))

        # 空数据
        with pytest.raises(ValueError):
            reg.fit(np.array([]).reshape(0, 1), np.array([]))

        # K 值过大
        with pytest.raises(ValueError):
            reg.fit(np.array([[1]]), np.array([1.0]))

    def test_predict_basic(self):
        """测试基本预测功能"""
        X_train = np.array([[1], [2], [3], [4], [5]])
        y_train = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        reg = KNNRegressor(k=3, weights='uniform')
        reg.fit(X_train, y_train)

        X_test = np.array([[3.5]])
        predictions = reg.predict(X_test)

        assert len(predictions) == 1
        # K=3, 最近的 3 个是 index [2,3,1] 对应值 [3.0, 4.0, 2.0]，平均值 = 3.0
        assert abs(predictions[0] - 3.0) < 0.1

    def test_predict_single_sample(self):
        """测试单样本预测"""
        X_train = np.array([[1], [2], [3]])
        y_train = np.array([1.0, 2.0, 3.0])

        reg = KNNRegressor(k=2)
        reg.fit(X_train, y_train)

        # 一维输入
        X_test = np.array([2.0])
        predictions = reg.predict(X_test)

        assert len(predictions) == 1

    def test_predict_before_fit(self):
        """测试未训练时预测"""
        reg = KNNRegressor(k=3)

        with pytest.raises(RuntimeError):
            reg.predict(np.array([[1]]))

    def test_predict_feature_mismatch(self):
        """测试特征数量不匹配"""
        X_train = np.array([[1], [2]])
        y_train = np.array([1.0, 2.0])

        reg = KNNRegressor(k=1)
        reg.fit(X_train, y_train)

        with pytest.raises(ValueError):
            reg.predict(np.array([[1, 2]]))

    def test_predict_weighted(self):
        """测试距离加权预测"""
        X_train = np.array([[1], [2], [3], [4], [5]])
        y_train = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        reg = KNNRegressor(k=3, weights='distance')
        reg.fit(X_train, y_train)

        X_test = np.array([[3.5]])
        predictions = reg.predict(X_test)

        assert len(predictions) == 1
        # 距离加权应该更接近近距离的值
        assert 3.0 < predictions[0] < 4.0

    def test_predict_exact_match(self):
        """测试精确匹配"""
        X_train = np.array([[1], [2], [3]])
        y_train = np.array([10.0, 20.0, 30.0])

        reg = KNNRegressor(k=1)
        reg.fit(X_train, y_train)

        predictions = reg.predict(np.array([[2]]))
        assert abs(predictions[0] - 20.0) < 1e-10

    def test_score_basic(self):
        """测试 R² 评分"""
        X_train = np.array([[1], [2], [3], [4], [5]])
        y_train = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        reg = KNNRegressor(k=1)
        reg.fit(X_train, y_train)

        # 使用 k=1 时应该能完美预测训练数据
        X_test = np.array([[1], [2], [3], [4], [5]])
        y_test = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        score = reg.score(X_test, y_test)
        assert score > 0.9  # 应该接近 1

    def test_different_metrics(self):
        """测试不同距离度量"""
        X_train = np.array([[1], [2], [3]])
        y_train = np.array([1.0, 2.0, 3.0])

        for metric in ['euclidean', 'manhattan', 'cosine']:
            reg = KNNRegressor(k=2, metric=metric)
            reg.fit(X_train, y_train)

            predictions = reg.predict(np.array([[2.5]]))
            assert len(predictions) == 1

    def test_different_k_values(self):
        """测试不同 K 值"""
        X_train = np.array([[1], [2], [3], [4], [5]])
        y_train = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        for k in [1, 3, 5]:
            reg = KNNRegressor(k=k)
            reg.fit(X_train, y_train)

            predictions = reg.predict(np.array([[3]]))
            assert len(predictions) == 1

    def test_multidimensional(self):
        """测试多维特征"""
        X_train = np.array([[1, 2], [3, 4], [5, 6]])
        y_train = np.array([1.0, 2.0, 3.0])

        reg = KNNRegressor(k=2)
        reg.fit(X_train, y_train)

        predictions = reg.predict(np.array([[2, 3]]))
        assert len(predictions) == 1

    def test_get_params(self):
        """测试获取参数"""
        reg = KNNRegressor(k=3, metric='manhattan', weights='distance')
        params = reg.get_params()

        assert params == {'k': 3, 'metric': 'manhattan', 'weights': 'distance'}

    def test_set_params(self):
        """测试设置参数"""
        reg = KNNRegressor()
        reg.set_params(k=7, metric='manhattan', weights='distance')

        assert reg.k == 7
        assert reg.metric == 'manhattan'
        assert reg.weights == 'distance'

    def test_set_params_invalid(self):
        """测试设置无效参数"""
        reg = KNNRegressor()

        with pytest.raises(ValueError):
            reg.set_params(k=0)

        with pytest.raises(ValueError):
            reg.set_params(metric='invalid')

        with pytest.raises(ValueError):
            reg.set_params(weights='invalid')

        with pytest.raises(ValueError):
            reg.set_params(unknown_param=1)

    def test_repr(self):
        """测试字符串表示"""
        reg = KNNRegressor(k=3, metric='manhattan', weights='distance')
        repr_str = repr(reg)

        assert 'KNNRegressor' in repr_str
        assert 'k=3' in repr_str
        assert 'manhattan' in repr_str
        assert 'distance' in repr_str

    def test_chain_calling(self):
        """测试链式调用"""
        X_train = np.array([[1], [2]])
        y_train = np.array([1.0, 2.0])

        reg = KNNRegressor(k=1)
        result = reg.fit(X_train, y_train)

        assert result is reg


class TestKNNRegressorIntegration:
    """KNN 回归器集成测试"""

    def test_linear_function(self):
        """测试线性函数拟合"""
        np.random.seed(42)
        X = np.linspace(0, 10, 50).reshape(-1, 1)
        y = 2 * X.ravel() + 1 + np.random.randn(50) * 0.1

        reg = KNNRegressor(k=5, weights='distance')
        reg.fit(X, y)

        # 预测应该接近线性关系
        X_test = np.array([[5]])
        prediction = reg.predict(X_test)
        assert abs(prediction[0] - 11) < 1  # 2*5 + 1 = 11

    def test_sine_function(self):
        """测试正弦函数拟合"""
        np.random.seed(42)
        X = np.linspace(0, 2 * np.pi, 100).reshape(-1, 1)
        y = np.sin(X.ravel()) + np.random.randn(100) * 0.1

        reg = KNNRegressor(k=5, weights='distance')
        reg.fit(X, y)

        # 预测应该接近正弦值
        X_test = np.array([[np.pi / 2]])
        prediction = reg.predict(X_test)
        assert abs(prediction[0] - 1.0) < 0.3

    def test_constant_function(self):
        """测试常数函数"""
        X = np.array([[1], [2], [3], [4], [5]])
        y = np.array([5.0, 5.0, 5.0, 5.0, 5.0])

        reg = KNNRegressor(k=3)
        reg.fit(X, y)

        predictions = reg.predict(np.array([[3]]))
        assert abs(predictions[0] - 5.0) < 1e-10

    def test_weights_effect(self):
        """测试权重策略的效果"""
        X_train = np.array([[0], [1], [10]])
        y_train = np.array([0.0, 1.0, 100.0])

        # 等权平均
        reg_uniform = KNNRegressor(k=2, weights='uniform')
        reg_uniform.fit(X_train, y_train)
        pred_uniform = reg_uniform.predict(np.array([[0.5]]))

        # 距离加权
        reg_distance = KNNRegressor(k=2, weights='distance')
        reg_distance.fit(X_train, y_train)
        pred_distance = reg_distance.predict(np.array([[0.5]]))

        # 等权平均：(0 + 1) / 2 = 0.5
        # 距离加权：w1=1/0.5=2, w2=1/0.5=2 → (2*0 + 2*1) / (2+2) = 0.5
        # 两者相同，因为到 [0] 和 [1] 的距离相等
        assert abs(pred_uniform[0] - 0.5) < 0.1
        assert abs(pred_distance[0] - 0.5) < 0.1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
