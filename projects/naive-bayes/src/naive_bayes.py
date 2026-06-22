"""
朴素贝叶斯分类器基类

朴素贝叶斯分类器基于贝叶斯定理，假设特征之间条件独立。
贝叶斯定理: P(C|X) = P(X|C) * P(C) / P(X)

其中:
- P(C|X): 后验概率 (给定特征X，类别为C的概率)
- P(X|C): 似然 (类别C下观测到特征X的概率)
- P(C): 先验概率 (类别C的概率)
- P(X): 证据 (观测到特征X的概率)

条件独立假设: P(X1,X2,...,Xn|C) = P(X1|C) * P(X2|C) * ... * P(Xn|C)
"""

from abc import ABC, abstractmethod
from typing import Any
import math


class NaiveBayesClassifier(ABC):
    """朴素贝叶斯分类器抽象基类"""

    def __init__(self, alpha: float = 1.0) -> None:
        """
        初始化分类器

        Args:
            alpha: 平滑参数 (Laplace平滑)，避免零概率问题
        """
        self.alpha = alpha
        self.class_priors: dict[Any, float] = {}
        self.classes: list[Any] = []
        self.is_fitted: bool = False

    @abstractmethod
    def fit(self, X: list[list[float]], y: list[Any]) -> "NaiveBayesClassifier":
        """
        训练模型

        Args:
            X: 训练数据特征，形状为 (n_samples, n_features)
            y: 训练数据标签，形状为 (n_samples,)

        Returns:
            self
        """

    @abstractmethod
    def _calculate_likelihood(
        self, x: list[float], class_label: Any
    ) -> float:
        """
        计算似然 P(X|C)

        Args:
            x: 单个样本的特征
            class_label: 类别标签

        Returns:
            对数似然值
        """

    def predict(self, X: list[list[float]]) -> list[Any]:
        """
        预测类别

        Args:
            X: 待预测数据特征

        Returns:
            预测的类别标签列表
        """
        if not self.is_fitted:
            raise RuntimeError("模型尚未训练，请先调用 fit() 方法")

        predictions = []
        for x in X:
            best_class = None
            best_score = float("-inf")

            for class_label in self.classes:
                # 计算对数后验概率: log P(C|X) = log P(X|C) + log P(C) - log P(X)
                # 由于 log P(X) 对所有类别相同，可以忽略
                score = self._calculate_likelihood(x, class_label) + math.log(
                    self.class_priors[class_label]
                )

                if score > best_score:
                    best_score = score
                    best_class = class_label

            predictions.append(best_class)

        return predictions

    def predict_proba(self, X: list[list[float]]) -> list[dict[Any, float]]:
        """
        预测各类别的概率

        Args:
            X: 待预测数据特征

        Returns:
            每个样本的类别概率字典列表
        """
        if not self.is_fitted:
            raise RuntimeError("模型尚未训练，请先调用 fit() 方法")

        probabilities = []
        for x in X:
            scores = {}
            for class_label in self.classes:
                scores[class_label] = self._calculate_likelihood(
                    x, class_label
                ) + math.log(self.class_priors[class_label])

            # 使用 log-sum-exp 技巧转换为概率
            max_score = max(scores.values())
            exp_scores = {
                k: math.exp(v - max_score) for k, v in scores.items()
            }
            total = sum(exp_scores.values())
            proba = {k: v / total for k, v in exp_scores.items()}

            probabilities.append(proba)

        return probabilities

    def score(self, X: list[list[float]], y: list[Any]) -> float:
        """
        计算准确率

        Args:
            X: 测试数据特征
            y: 测试数据标签

        Returns:
            准确率 (0-1)
        """
        predictions = self.predict(X)
        correct = sum(1 for pred, true in zip(predictions, y) if pred == true)
        return correct / len(y)
