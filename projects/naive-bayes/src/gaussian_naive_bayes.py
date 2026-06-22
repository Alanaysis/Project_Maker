"""
高斯朴素贝叶斯分类器

假设特征服从高斯分布 (正态分布):
P(xi|C) = (1 / sqrt(2*pi*sigma_c^2)) * exp(-(xi - mu_c)^2 / (2*sigma_c^2))

适用于连续型特征数据。
"""

import math
from typing import Any

from .naive_bayes import NaiveBayesClassifier


class GaussianNaiveBayes(NaiveBayesClassifier):
    """高斯朴素贝叶斯分类器"""

    def __init__(self, alpha: float = 1e-9) -> None:
        """
        初始化高斯朴素贝叶斯分类器

        Args:
            alpha: 方差平滑参数，防止方差为零
        """
        super().__init__(alpha=alpha)
        self.means: dict[Any, list[float]] = {}
        self.variances: dict[Any, list[float]] = {}

    def fit(self, X: list[list[float]], y: list[Any]) -> "GaussianNaiveBayes":
        """
        训练高斯朴素贝叶斯模型

        计算每个类别下每个特征的均值和方差。

        Args:
            X: 训练数据特征
            y: 训练数据标签

        Returns:
            self
        """
        if len(X) != len(y):
            raise ValueError("X 和 y 的样本数量必须相同")

        if len(X) == 0:
            raise ValueError("训练数据不能为空")

        n_samples = len(X)
        n_features = len(X[0])

        # 获取所有类别
        self.classes = list(set(y))

        # 计算先验概率 P(C)
        class_counts: dict[Any, int] = {}
        for label in y:
            class_counts[label] = class_counts.get(label, 0) + 1

        self.class_priors = {
            cls: count / n_samples for cls, count in class_counts.items()
        }

        # 按类别分组计算均值和方差
        for cls in self.classes:
            # 获取该类别的所有样本
            class_samples = [X[i] for i in range(n_samples) if y[i] == cls]
            n_class = len(class_samples)

            # 计算均值
            means = []
            for j in range(n_features):
                feature_sum = sum(sample[j] for sample in class_samples)
                means.append(feature_sum / n_class)

            # 计算方差
            variances = []
            for j in range(n_features):
                variance_sum = sum(
                    (sample[j] - means[j]) ** 2 for sample in class_samples
                )
                # 使用平滑参数防止方差为零
                variances.append(variance_sum / n_class + self.alpha)

            self.means[cls] = means
            self.variances[cls] = variances

        self.is_fitted = True
        return self

    def _calculate_likelihood(
        self, x: list[float], class_label: Any
    ) -> float:
        """
        计算高斯分布下的对数似然

        log P(X|C) = sum_i log P(xi|C)
        log P(xi|C) = -0.5 * log(2*pi*sigma^2) - (xi - mu)^2 / (2*sigma^2)

        Args:
            x: 单个样本的特征
            class_label: 类别标签

        Returns:
            对数似然值
        """
        log_likelihood = 0.0
        means = self.means[class_label]
        variances = self.variances[class_label]

        for i in range(len(x)):
            mean = means[i]
            variance = variances[i]

            # 高斯分布的对数概率密度
            log_likelihood += -0.5 * math.log(2 * math.pi * variance)
            log_likelihood -= (x[i] - mean) ** 2 / (2 * variance)

        return log_likelihood

    def get_params(self) -> dict[str, Any]:
        """获取模型参数"""
        return {
            "means": self.means,
            "variances": self.variances,
            "class_priors": self.class_priors,
            "classes": self.classes,
        }
