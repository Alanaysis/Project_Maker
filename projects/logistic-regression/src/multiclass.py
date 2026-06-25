"""
多分类逻辑回归实现

实现三种多分类策略：
1. One-vs-Rest (OvR): 为每个类别训练一个二分类器
2. One-vs-One (OvO): 为每对类别训练一个二分类器
3. Softmax回归: 直接处理多分类问题
"""

import numpy as np
from typing import List, Optional
from .logistic_regression import LogisticRegression


class OneVsRestClassifier:
    """
    One-vs-Rest (OvR) 多分类策略

    为每个类别训练一个二分类器，该分类器将该类别视为正类，
    其余所有类别视为负类。预测时选择概率最高的类别。

    Parameters
    ----------
    learning_rate : float, default=0.01
        学习率
    n_iterations : int, default=1000
        迭代次数
    regularization : float, default=0.0
        L2正则化强度

    Attributes
    ----------
    classifiers : list
        每个类别的二分类器
    classes : ndarray
        所有类别标签
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        n_iterations: int = 1000,
        regularization: float = 0.0
    ):
        self.learning_rate = learning_rate
        self.n_iterations = n_iterations
        self.regularization = regularization
        self.classifiers: List[LogisticRegression] = []
        self.classes: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> 'OneVsRestClassifier':
        """
        训练One-vs-Rest分类器

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            训练数据特征
        y : ndarray of shape (n_samples,)
            训练数据标签

        Returns
        -------
        self
            训练后的分类器
        """
        self.classes = np.unique(y)
        self.classifiers = []

        for cls in self.classes:
            # 创建二分类标签：当前类别为1，其余为0
            binary_y = (y == cls).astype(int)

            # 训练二分类器
            clf = LogisticRegression(
                learning_rate=self.learning_rate,
                n_iterations=self.n_iterations,
                regularization=self.regularization
            )
            clf.fit(X, binary_y)
            self.classifiers.append(clf)

        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        预测每个类别的概率

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            待预测的特征数据

        Returns
        -------
        ndarray of shape (n_samples, n_classes)
            每个类别的概率
        """
        probas = np.zeros((len(X), len(self.classes)))

        for i, clf in enumerate(self.classifiers):
            probas[:, i] = clf.predict_proba(X)

        # 归一化概率
        proba_sum = probas.sum(axis=1, keepdims=True)
        probas = probas / proba_sum

        return probas

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        预测类别

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            待预测的特征数据

        Returns
        -------
        ndarray of shape (n_samples,)
            预测的类别标签
        """
        probas = self.predict_proba(X)
        indices = np.argmax(probas, axis=1)
        return self.classes[indices]


class OneVsOneClassifier:
    """
    One-vs-One (OvO) 多分类策略

    为每对类别训练一个二分类器。预测时使用投票机制，
    选择得票最多的类别。

    Parameters
    ----------
    learning_rate : float, default=0.01
        学习率
    n_iterations : int, default=1000
        迭代次数
    regularization : float, default=0.0
        L2正则化强度

    Attributes
    ----------
    classifiers : dict
        每对类别的二分类器
    classes : ndarray
        所有类别标签
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        n_iterations: int = 1000,
        regularization: float = 0.0
    ):
        self.learning_rate = learning_rate
        self.n_iterations = n_iterations
        self.regularization = regularization
        self.classifiers = {}
        self.classes: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> 'OneVsOneClassifier':
        """
        训练One-vs-One分类器

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            训练数据特征
        y : ndarray of shape (n_samples,)
            训练数据标签

        Returns
        -------
        self
            训练后的分类器
        """
        self.classes = np.unique(y)
        self.classifiers = {}

        # 为每对类别训练一个分类器
        for i, cls1 in enumerate(self.classes):
            for cls2 in self.classes[i + 1:]:
                # 选择属于这两个类别的样本
                mask = (y == cls1) | (y == cls2)
                X_pair = X[mask]
                y_pair = y[mask]

                # 将标签转换为0和1
                binary_y = (y_pair == cls1).astype(int)

                # 训练二分类器
                clf = LogisticRegression(
                    learning_rate=self.learning_rate,
                    n_iterations=self.n_iterations,
                    regularization=self.regularization
                )
                clf.fit(X_pair, binary_y)

                # 存储分类器
                self.classifiers[(cls1, cls2)] = clf

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        预测类别

        使用投票机制，选择得票最多的类别。

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            待预测的特征数据

        Returns
        -------
        ndarray of shape (n_samples,)
            预测的类别标签
        """
        n_samples = len(X)
        votes = np.zeros((n_samples, len(self.classes)))

        for (cls1, cls2), clf in self.classifiers.items():
            predictions = clf.predict(X)

            # 获取类别索引
            idx1 = np.where(self.classes == cls1)[0][0]
            idx2 = np.where(self.classes == cls2)[0][0]

            # 投票
            for i in range(n_samples):
                if predictions[i] == 1:
                    votes[i, idx1] += 1
                else:
                    votes[i, idx2] += 1

        # 选择得票最多的类别
        indices = np.argmax(votes, axis=1)
        return self.classes[indices]


class SoftmaxRegression:
    """
    Softmax回归（多项逻辑回归）

    直接处理多分类问题，使用softmax函数将线性输出转换为概率分布。

    Parameters
    ----------
    learning_rate : float, default=0.01
        学习率
    n_iterations : int, default=1000
        迭代次数
    regularization : float, default=0.0
        L2正则化强度

    Attributes
    ----------
    weights : ndarray of shape (n_classes, n_features)
        权重矩阵
    bias : ndarray of shape (n_classes,)
        偏置向量
    classes : ndarray
        所有类别标签
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        n_iterations: int = 1000,
        regularization: float = 0.0
    ):
        self.learning_rate = learning_rate
        self.n_iterations = n_iterations
        self.regularization = regularization
        self.weights: Optional[np.ndarray] = None
        self.bias: Optional[np.ndarray] = None
        self.classes: Optional[np.ndarray] = None

    def _softmax(self, z: np.ndarray) -> np.ndarray:
        """
        Softmax函数

        公式: softmax(z_i) = e^(z_i) / Σ e^(z_j)

        Parameters
        ----------
        z : ndarray of shape (n_samples, n_classes)
            线性输出

        Returns
        -------
        ndarray of shape (n_samples, n_classes)
            概率分布
        """
        # 数值稳定性处理
        z_max = np.max(z, axis=1, keepdims=True)
        exp_z = np.exp(z - z_max)
        return exp_z / np.sum(exp_z, axis=1, keepdims=True)

    def _compute_loss(self, y_onehot: np.ndarray, y_pred: np.ndarray) -> float:
        """
        计算交叉熵损失

        Parameters
        ----------
        y_onehot : ndarray of shape (n_samples, n_classes)
            one-hot编码的真实标签
        y_pred : ndarray of shape (n_samples, n_classes)
            预测概率

        Returns
        -------
        float
            交叉熵损失
        """
        m = len(y_onehot)
        epsilon = 1e-15
        y_pred = np.clip(y_pred, epsilon, 1 - epsilon)

        # 交叉熵损失
        loss = -np.sum(y_onehot * np.log(y_pred)) / m

        # L2正则化
        if self.regularization > 0:
            l2_penalty = (self.regularization / (2 * m)) * np.sum(self.weights ** 2)
            loss += l2_penalty

        return loss

    def fit(self, X: np.ndarray, y: np.ndarray) -> 'SoftmaxRegression':
        """
        训练Softmax回归

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            训练数据特征
        y : ndarray of shape (n_samples,)
            训练数据标签

        Returns
        -------
        self
            训练后的模型
        """
        X = np.array(X)
        y = np.array(y)

        self.classes = np.unique(y)
        n_classes = len(self.classes)
        n_samples, n_features = X.shape

        # 初始化参数
        self.weights = np.zeros((n_classes, n_features))
        self.bias = np.zeros(n_classes)

        # 创建one-hot编码
        y_onehot = np.zeros((n_samples, n_classes))
        for i, cls in enumerate(self.classes):
            y_onehot[:, i] = (y == cls).astype(int)

        # 梯度下降训练
        for _ in range(self.n_iterations):
            # 前向传播
            z = np.dot(X, self.weights.T) + self.bias
            y_pred = self._softmax(z)

            # 计算梯度
            error = y_pred - y_onehot
            dw = np.dot(error.T, X) / n_samples
            db = np.mean(error, axis=0)

            # L2正则化梯度
            if self.regularization > 0:
                dw += (self.regularization / n_samples) * self.weights

            # 更新参数
            self.weights -= self.learning_rate * dw
            self.bias -= self.learning_rate * db

        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        预测每个类别的概率

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            待预测的特征数据

        Returns
        -------
        ndarray of shape (n_samples, n_classes)
            每个类别的概率
        """
        X = np.array(X)
        z = np.dot(X, self.weights.T) + self.bias
        return self._softmax(z)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        预测类别

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            待预测的特征数据

        Returns
        -------
        ndarray of shape (n_samples,)
            预测的类别标签
        """
        probas = self.predict_proba(X)
        indices = np.argmax(probas, axis=1)
        return self.classes[indices]

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        计算准确率

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            测试数据特征
        y : ndarray of shape (n_samples,)
            测试数据真实标签

        Returns
        -------
        float
            准确率
        """
        y_pred = self.predict(X)
        return np.mean(y_pred == y)
