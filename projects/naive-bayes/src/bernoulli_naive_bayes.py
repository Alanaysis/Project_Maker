"""
伯努利朴素贝叶斯分类器

适用于二值型特征数据 (0或1)。
假设特征服从伯努利分布。

P(xi|C) = p * xi + (1-p) * (1-xi)

其中:
- p: 类别C下特征i为1的概率

与多项式朴素贝叶斯的区别:
- 伯努利模型考虑特征是否出现 (二值)
- 多项式模型考虑特征出现的次数 (计数)
"""

import math
from typing import Any

from .naive_bayes import NaiveBayesClassifier


class BernoulliNaiveBayes(NaiveBayesClassifier):
    """伯努利朴素贝叶斯分类器"""

    def __init__(self, alpha: float = 1.0) -> None:
        """
        初始化伯努利朴素贝叶斯分类器

        Args:
            alpha: Laplace平滑参数
        """
        super().__init__(alpha=alpha)
        self.feature_log_prob: dict[Any, list[tuple[float, float]]] = {}
        self.n_features: int = 0

    def fit(
        self, X: list[list[float]], y: list[Any]
    ) -> "BernoulliNaiveBayes":
        """
        训练伯努利朴素贝叶斯模型

        Args:
            X: 训练数据特征 (二值: 0或1)
            y: 训练数据标签

        Returns:
            self
        """
        if len(X) != len(y):
            raise ValueError("X 和 y 的样本数量必须相同")

        if len(X) == 0:
            raise ValueError("训练数据不能为空")

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
            n_class = len(class_samples)

            # 计算每个特征为1的计数
            feature_counts = [0.0] * self.n_features
            for sample in class_samples:
                for j in range(self.n_features):
                    feature_counts[j] += sample[j]

            # 应用Laplace平滑计算概率
            # P(xi=1|C) = (count + alpha) / (n_class + 2*alpha)
            self.feature_log_prob[cls] = []
            for j in range(self.n_features):
                p1 = (feature_counts[j] + self.alpha) / (
                    n_class + 2 * self.alpha
                )
                p0 = 1 - p1
                # 存储 (log P(xi=0|C), log P(xi=1|C))
                self.feature_log_prob[cls].append(
                    (math.log(p0), math.log(p1))
                )

        self.is_fitted = True
        return self

    def _calculate_likelihood(
        self, x: list[float], class_label: Any
    ) -> float:
        """
        计算伯努利分布下的对数似然

        log P(X|C) = sum_i log P(xi|C)

        Args:
            x: 单个样本的特征
            class_label: 类别标签

        Returns:
            对数似然值
        """
        log_likelihood = 0.0
        log_probs = self.feature_log_prob[class_label]

        for i in range(self.n_features):
            if x[i] == 1:
                log_likelihood += log_probs[i][1]  # log P(xi=1|C)
            else:
                log_likelihood += log_probs[i][0]  # log P(xi=0|C)

        return log_likelihood

    def get_params(self) -> dict[str, Any]:
        """获取模型参数"""
        return {
            "feature_log_prob": self.feature_log_prob,
            "class_priors": self.class_priors,
            "classes": self.classes,
            "n_features": self.n_features,
        }
