"""伯努利朴素贝叶斯分类器测试"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from src.bernoulli_naive_bayes import BernoulliNaiveBayes


class TestBernoulliNaiveBayes:
    """伯努利朴素贝叶斯测试类"""

    def setup_method(self) -> None:
        """每个测试前初始化"""
        self.clf = BernoulliNaiveBayes()

    def test_fit_basic(self) -> None:
        """测试基本训练功能"""
        X = [[1, 0, 1], [1, 1, 0], [0, 1, 0], [0, 0, 1]]
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

    def test_predict_binary_features(self) -> None:
        """测试二值特征预测"""
        # 特征: [是否包含word_a, 是否包含word_b]
        # 类别0: 包含word_a
        # 类别1: 包含word_b
        X_train = [
            [1, 0],
            [1, 0],
            [1, 1],
            [0, 1],
            [0, 1],
            [0, 1],
        ]
        y_train = [0, 0, 0, 1, 1, 1]

        self.clf.fit(X_train, y_train)

        assert self.clf.predict([[1, 0]]) == [0]
        assert self.clf.predict([[0, 1]]) == [1]

    def test_predict_proba(self) -> None:
        """测试概率预测"""
        X = [[1, 0], [0, 1]]
        y = [0, 1]

        self.clf.fit(X, y)

        proba = self.clf.predict_proba([[1, 0]])

        assert len(proba) == 1
        assert 0 in proba[0]
        assert 1 in proba[0]
        assert abs(proba[0][0] + proba[0][1] - 1.0) < 1e-6

    def test_score(self) -> None:
        """测试准确率计算"""
        X_train = [[1, 0], [1, 0], [0, 1], [0, 1]]
        y_train = [0, 0, 1, 1]

        self.clf.fit(X_train, y_train)

        assert self.clf.score([[1, 0], [0, 1]], [0, 1]) == 1.0

    def test_predict_before_fit_raises(self) -> None:
        """测试训练前预测抛出异常"""
        with pytest.raises(RuntimeError, match="模型尚未训练"):
            self.clf.predict([[1, 0]])

    def test_laplace_smoothing(self) -> None:
        """测试Laplace平滑效果"""
        X = [[1, 0], [0, 1]]
        y = [0, 1]

        self.clf.fit(X, y)

        # 验证概率经过平滑
        params = self.clf.get_params()
        for cls in params["classes"]:
            for log_p0, log_p1 in params["feature_log_prob"][cls]:
                assert log_p0 > float("-inf")
                assert log_p1 > float("-inf")

    def test_multiple_classes(self) -> None:
        """测试多类别分类"""
        X = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        y = [0, 1, 2]

        self.clf.fit(X, y)

        assert self.clf.predict([[1, 0, 0]]) == [0]
        assert self.clf.predict([[0, 1, 0]]) == [1]
        assert self.clf.predict([[0, 0, 1]]) == [2]

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

    def test_email_spam_detection(self) -> None:
        """测试邮件垃圾检测场景"""
        # 特征: [包含free, 包含win, 包含meeting, 包含report]
        # 类别0: 正常邮件
        # 类别1: 垃圾邮件
        X_train = [
            [0, 0, 1, 1],  # 正常
            [0, 0, 1, 0],  # 正常
            [0, 1, 1, 1],  # 正常
            [1, 1, 0, 0],  # 垃圾
            [1, 1, 0, 0],  # 垃圾
            [1, 0, 0, 0],  # 垃圾
        ]
        y_train = [0, 0, 0, 1, 1, 1]

        self.clf.fit(X_train, y_train)

        # 正常邮件
        assert self.clf.predict([[0, 0, 1, 1]]) == [0]
        # 垃圾邮件
        assert self.clf.predict([[1, 1, 0, 0]]) == [1]
