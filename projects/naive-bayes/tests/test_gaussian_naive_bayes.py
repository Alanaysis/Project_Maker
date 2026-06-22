"""高斯朴素贝叶斯分类器测试"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import math
import pytest
from src.gaussian_naive_bayes import GaussianNaiveBayes


class TestGaussianNaiveBayes:
    """高斯朴素贝叶斯测试类"""

    def setup_method(self) -> None:
        """每个测试前初始化"""
        self.clf = GaussianNaiveBayes()

    def test_fit_basic(self) -> None:
        """测试基本训练功能"""
        X = [[1.0, 2.0], [2.0, 3.0], [3.0, 4.0], [10.0, 11.0], [11.0, 12.0]]
        y = [0, 0, 0, 1, 1]

        self.clf.fit(X, y)

        assert self.clf.is_fitted is True
        assert set(self.clf.classes) == {0, 1}
        assert 0 in self.clf.class_priors
        assert 1 in self.clf.class_priors

    def test_class_priors(self) -> None:
        """测试先验概率计算"""
        X = [[1.0], [2.0], [3.0], [4.0], [5.0], [6.0]]
        y = [0, 0, 0, 1, 1, 1]

        self.clf.fit(X, y)

        assert abs(self.clf.class_priors[0] - 0.5) < 1e-6
        assert abs(self.clf.class_priors[1] - 0.5) < 1e-6

    def test_class_priors_imbalanced(self) -> None:
        """测试不平衡数据的先验概率"""
        X = [[1.0], [2.0], [3.0], [4.0]]
        y = [0, 0, 0, 1]

        self.clf.fit(X, y)

        assert abs(self.clf.class_priors[0] - 0.75) < 1e-6
        assert abs(self.clf.class_priors[1] - 0.25) < 1e-6

    def test_means_calculation(self) -> None:
        """测试均值计算"""
        X = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]
        y = [0, 0, 1]

        self.clf.fit(X, y)

        # 类别0: 特征0均值=(1+3)/2=2.0, 特征1均值=(2+4)/2=3.0
        assert abs(self.clf.means[0][0] - 2.0) < 1e-6
        assert abs(self.clf.means[0][1] - 3.0) < 1e-6

        # 类别1: 特征0均值=5.0, 特征1均值=6.0
        assert abs(self.clf.means[1][0] - 5.0) < 1e-6
        assert abs(self.clf.means[1][1] - 6.0) < 1e-6

    def test_predict_basic(self) -> None:
        """测试基本预测功能"""
        X_train = [[1.0, 2.0], [2.0, 3.0], [3.0, 4.0],
                    [10.0, 11.0], [11.0, 12.0], [12.0, 13.0]]
        y_train = [0, 0, 0, 1, 1, 1]

        self.clf.fit(X_train, y_train)

        X_test = [[1.5, 2.5], [11.0, 12.0]]
        predictions = self.clf.predict(X_test)

        assert predictions[0] == 0
        assert predictions[1] == 1

    def test_predict_proba(self) -> None:
        """测试概率预测"""
        X_train = [[1.0, 2.0], [2.0, 3.0], [10.0, 11.0], [11.0, 12.0]]
        y_train = [0, 0, 1, 1]

        self.clf.fit(X_train, y_train)

        X_test = [[1.5, 2.5]]
        proba = self.clf.predict_proba(X_test)

        assert len(proba) == 1
        assert 0 in proba[0]
        assert 1 in proba[0]
        # 概率之和应为1
        assert abs(proba[0][0] + proba[0][1] - 1.0) < 1e-6
        # 类别0的概率应该更高
        assert proba[0][0] > proba[0][1]

    def test_score(self) -> None:
        """测试准确率计算"""
        X_train = [[1.0], [2.0], [3.0], [10.0], [11.0], [12.0]]
        y_train = [0, 0, 0, 1, 1, 1]

        self.clf.fit(X_train, y_train)

        X_test = [[1.5], [11.5]]
        y_test = [0, 1]

        score = self.clf.score(X_test, y_test)
        assert score == 1.0

    def test_predict_before_fit_raises(self) -> None:
        """测试训练前预测抛出异常"""
        with pytest.raises(RuntimeError, match="模型尚未训练"):
            self.clf.predict([[1.0]])

    def test_fit_empty_data_raises(self) -> None:
        """测试空数据训练抛出异常"""
        with pytest.raises(ValueError, match="训练数据不能为空"):
            self.clf.fit([], [])

    def test_fit_mismatched_lengths_raises(self) -> None:
        """测试数据长度不匹配抛出异常"""
        with pytest.raises(ValueError, match="样本数量必须相同"):
            self.clf.fit([[1.0], [2.0]], [0])

    def test_single_feature(self) -> None:
        """测试单特征数据"""
        X = [[1.0], [2.0], [3.0], [10.0], [11.0], [12.0]]
        y = [0, 0, 0, 1, 1, 1]

        self.clf.fit(X, y)
        predictions = self.clf.predict([[1.5], [11.5]])

        assert predictions == [0, 1]

    def test_multiple_classes(self) -> None:
        """测试多类别分类"""
        X = [[1.0], [2.0], [10.0], [11.0], [20.0], [21.0]]
        y = [0, 0, 1, 1, 2, 2]

        self.clf.fit(X, y)
        predictions = self.clf.predict([[1.5], [10.5], [20.5]])

        assert predictions == [0, 1, 2]

    def test_variance_smoothing(self) -> None:
        """测试方差平滑效果"""
        # 创建方差为0的数据
        X = [[1.0], [1.0], [1.0], [10.0], [10.0], [10.0]]
        y = [0, 0, 0, 1, 1, 1]

        self.clf = GaussianNaiveBayes(alpha=1e-9)
        self.clf.fit(X, y)

        # 方差不应该是0
        assert self.clf.variances[0][0] > 0
        assert self.clf.variances[1][0] > 0

    def test_get_params(self) -> None:
        """测试获取参数"""
        X = [[1.0, 2.0], [3.0, 4.0]]
        y = [0, 1]

        self.clf.fit(X, y)
        params = self.clf.get_params()

        assert "means" in params
        assert "variances" in params
        assert "class_priors" in params
        assert "classes" in params

    def test_iris_like_data(self) -> None:
        """测试类似鸢尾花数据集的场景"""
        # 模拟两类数据，特征明显分离
        X = (
            [[5.1, 3.5], [4.9, 3.0], [4.7, 3.2], [4.6, 3.1], [5.0, 3.6]]
            + [[7.0, 3.2], [6.4, 3.2], [6.9, 3.1], [5.5, 2.3], [6.5, 2.8]]
        )
        y = [0, 0, 0, 0, 0] + [1, 1, 1, 1, 1]

        self.clf.fit(X, y)

        # 预测应该正确
        assert self.clf.predict([[4.8, 3.0]]) == [0]
        assert self.clf.predict([[6.5, 3.0]]) == [1]
