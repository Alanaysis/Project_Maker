"""
多项式朴素贝叶斯分类器

适用于离散型特征数据，特别是文本分类中的词频特征。
假设特征服从多项式分布。

P(xi|C) = (Nxi + alpha) / (Nc + alpha * n_features)

其中:
- Nxi: 类别C中特征i出现的次数
- Nc: 类别C中所有特征出现的总次数
- alpha: Laplace平滑参数
- n_features: 特征数量
"""

import math
from typing import Any

from .naive_bayes import NaiveBayesClassifier


class MultinomialNaiveBayes(NaiveBayesClassifier):
    """多项式朴素贝叶斯分类器"""

    def __init__(self, alpha: float = 1.0) -> None:
        """
        初始化多项式朴素贝叶斯分类器

        Args:
            alpha: Laplace平滑参数
        """
        super().__init__(alpha=alpha)
        self.feature_log_prob: dict[Any, list[float]] = {}
        self.n_features: int = 0

    def fit(
        self, X: list[list[float]], y: list[Any]
    ) -> "MultinomialNaiveBayes":
        """
        训练多项式朴素贝叶斯模型

        Args:
            X: 训练数据特征 (非负值)
            y: 训练数据标签

        Returns:
            self
        """
        if len(X) != len(y):
            raise ValueError("X 和 y 的样本数量必须相同")

        if len(X) == 0:
            raise ValueError("训练数据不能为空")

        # 检查特征值非负
        for sample in X:
            for val in sample:
                if val < 0:
                    raise ValueError("多项式朴素贝叶斯要求特征值非负")

        n_samples = len(X)
        self.n_features = len(X[0])

        # 获取所有类别
        self.classes = list(set(y))

        # 计算先验概率 P(C)
        class_counts: dict[Any, int] = {}
        for label in y:
            class_counts[label] = class_counts.get(label, 0) + 1

        self.class_priors = {
            cls: count / n_samples for cls, count in class_counts.items()
        }

        # 计算每个类别下每个特征的对数概率
        for cls in self.classes:
            # 获取该类别的所有样本
            class_indices = [i for i in range(n_samples) if y[i] == cls]
            class_samples = [X[i] for i in class_indices]

            # 计算每个特征的计数
            feature_counts = [0.0] * self.n_features
            for sample in class_samples:
                for j in range(self.n_features):
                    feature_counts[j] += sample[j]

            # 计算总计数
            total_count = sum(feature_counts)

            # 应用Laplace平滑计算对数概率
            self.feature_log_prob[cls] = [
                math.log((feature_counts[j] + self.alpha))
                - math.log(total_count + self.alpha * self.n_features)
                for j in range(self.n_features)
            ]

        self.is_fitted = True
        return self

    def _calculate_likelihood(
        self, x: list[float], class_label: Any
    ) -> float:
        """
        计算多项式分布下的对数似然

        log P(X|C) = sum_i xi * log P(xi|C)

        Args:
            x: 单个样本的特征
            class_label: 类别标签

        Returns:
            对数似然值
        """
        log_likelihood = 0.0
        log_probs = self.feature_log_prob[class_label]

        for i in range(self.n_features):
            log_likelihood += x[i] * log_probs[i]

        return log_likelihood

    def get_params(self) -> dict[str, Any]:
        """获取模型参数"""
        return {
            "feature_log_prob": self.feature_log_prob,
            "class_priors": self.class_priors,
            "classes": self.classes,
            "n_features": self.n_features,
        }
