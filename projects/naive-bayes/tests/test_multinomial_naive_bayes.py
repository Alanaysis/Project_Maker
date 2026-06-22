"""多项式朴素贝叶斯分类器测试"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from src.multinomial_naive_bayes import MultinomialNaiveBayes


class TestMultinomialNaiveBayes:
    """多项式朴素贝叶斯测试类"""

    def setup_method(self) -> None:
        """每个测试前初始化"""
        self.clf = MultinomialNaiveBayes()

    def test_fit_basic(self) -> None:
        """测试基本训练功能"""
        # 简单的词频数据
        X = [[2, 1, 0], [1, 2, 0], [0, 0, 3], [0, 1, 2]]
        y = [0, 0, 1, 1]

        self.clf.fit(X, y)

        assert self.clf.is_fitted is True
        assert set(self.clf.classes) == {0, 1}

    def test_class_priors(self) -> None:
        """测试先验概率计算"""
        X = [[1, 0], [1, 0], [0, 1], [0, 1]]
        y = [0, 0, 1, 1]

        self.clf.fit(X, y)

        assert abs(self.clf.class_priors[0] - 0.5) < 1e-6
        assert abs(self.clf.class_priors[1] - 0.5) < 1e-6

    def test_predict_text_classification(self) -> None:
        """测试文本分类场景"""
        # 模拟文本分类: [good, bad, great]
        # 类别0: 正面评论 (good, great 多)
        # 类别1: 负面评论 (bad 多)
        X_train = [
            [3, 0, 2],  # 正面
            [2, 0, 3],  # 正面
            [4, 1, 3],  # 正面
            [0, 3, 0],  # 负面
            [1, 4, 0],  # 负面
            [0, 3, 1],  # 负面
        ]
        y_train = [0, 0, 0, 1, 1, 1]

        self.clf.fit(X_train, y_train)

        # 正面评论
        assert self.clf.predict([[3, 0, 2]]) == [0]
        # 负面评论
        assert self.clf.predict([[0, 4, 0]]) == [1]

    def test_predict_proba(self) -> None:
        """测试概率预测"""
        X = [[2, 0], [3, 0], [0, 2], [0, 3]]
        y = [0, 0, 1, 1]

        self.clf.fit(X, y)

        proba = self.clf.predict_proba([[2, 0]])

        assert len(proba) == 1
        assert 0 in proba[0]
        assert 1 in proba[0]
        assert abs(proba[0][0] + proba[0][1] - 1.0) < 1e-6

    def test_score(self) -> None:
        """测试准确率计算"""
        X_train = [[3, 0], [2, 0], [0, 3], [0, 2]]
        y_train = [0, 0, 1, 1]

        self.clf.fit(X_train, y_train)

        X_test = [[3, 0], [0, 3]]
        y_test = [0, 1]

        assert self.clf.score(X_test, y_test) == 1.0

    def test_negative_features_raises(self) -> None:
        """测试负特征值抛出异常"""
        X = [[-1, 0], [0, 1]]
        y = [0, 1]

        with pytest.raises(ValueError, match="特征值非负"):
            self.clf.fit(X, y)

    def test_predict_before_fit_raises(self) -> None:
        """测试训练前预测抛出异常"""
        with pytest.raises(RuntimeError, match="模型尚未训练"):
            self.clf.predict([[1, 0]])

    def test_laplace_smoothing(self) -> None:
        """测试Laplace平滑效果"""
        X = [[1, 0], [0, 1]]
        y = [0, 1]

        self.clf.fit(X, y)

        # 即使某个特征在某类别中未出现，概率也不应该是0
        params = self.clf.get_params()
        for cls in params["classes"]:
            for log_prob in params["feature_log_prob"][cls]:
                assert log_prob > float("-inf")

    def test_multiple_classes(self) -> None:
        """测试多类别分类"""
        X = [[3, 0, 0], [0, 3, 0], [0, 0, 3]]
        y = [0, 1, 2]

        self.clf.fit(X, y)

        assert self.clf.predict([[3, 0, 0]]) == [0]
        assert self.clf.predict([[0, 3, 0]]) == [1]
        assert self.clf.predict([[0, 0, 3]]) == [2]

    def test_fit_empty_data_raises(self) -> None:
        """测试空数据训练抛出异常"""
        with pytest.raises(ValueError, match="训练数据不能为空"):
            self.clf.fit([], [])

    def test_get_params(self) -> None:
        """测试获取参数"""
        X = [[1, 0], [0, 1]]
        y = [0, 1]

        self.clf.fit(X, y)
        params = self.clf.get_params()

        assert "feature_log_prob" in params
        assert "class_priors" in params
        assert "classes" in params
        assert "n_features" in params
