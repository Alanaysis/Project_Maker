"""
正则化逻辑回归实现

实现三种正则化策略：
1. L1正则化 (Lasso): 稀疏化特征，特征选择
2. L2正则化 (Ridge): 防止过拟合
3. Elastic Net: L1和L2的组合
"""

import numpy as np
from typing import Optional, Tuple


class LogisticRegressionL1:
    """
    L1正则化逻辑回归 (Lasso)

    L1正则化倾向于产生稀疏权重，可以用于特征选择。

    Parameters
    ----------
    learning_rate : float, default=0.01
        学习率
    n_iterations : int, default=1000
        迭代次数
    lambda_param : float, default=0.1
        L1正则化强度
    threshold : float, default=0.5
        分类阈值

    Attributes
    ----------
    weights : ndarray of shape (n_features,)
        模型权重
    bias : float
        偏置项
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        n_iterations: int = 1000,
        lambda_param: float = 0.1,
        threshold: float = 0.5
    ):
        self.learning_rate = learning_rate
        self.n_iterations = n_iterations
        self.lambda_param = lambda_param
        self.threshold = threshold
        self.weights: Optional[np.ndarray] = None
        self.bias: float = 0.0

    def _sigmoid(self, z: np.ndarray) -> np.ndarray:
        """Sigmoid激活函数"""
        z = np.clip(z, -500, 500)
        return 1 / (1 + np.exp(-z))

    def _compute_loss(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """
        计算带L1正则化的交叉熵损失

        公式: L = -1/m * Σ[y*log(p) + (1-y)*log(1-p)] + λ * Σ|w_i|
        """
        m = len(y_true)
        epsilon = 1e-15
        y_pred = np.clip(y_pred, epsilon, 1 - epsilon)

        # 交叉熵损失
        cross_entropy = -np.mean(
            y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred)
        )

        # L1正则化项
        l1_penalty = self.lambda_param * np.sum(np.abs(self.weights))

        return cross_entropy + l1_penalty

    def fit(self, X: np.ndarray, y: np.ndarray) -> 'LogisticRegressionL1':
        """
        训练L1正则化逻辑回归

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
        n_samples, n_features = X.shape

        # 初始化参数
        self.weights = np.zeros(n_features)
        self.bias = 0.0

        # 梯度下降训练
        for _ in range(self.n_iterations):
            # 前向传播
            z = np.dot(X, self.weights) + self.bias
            y_pred = self._sigmoid(z)

            # 计算梯度
            error = y_pred - y
            dw = (1 / n_samples) * np.dot(X.T, error)
            db = (1 / n_samples) * np.sum(error)

            # L1正则化梯度（次梯度）
            # L1的次梯度：sign(w)
            dw += self.lambda_param * np.sign(self.weights)

            # 更新参数
            self.weights -= self.learning_rate * dw
            self.bias -= self.learning_rate * db

        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """预测概率"""
        X = np.array(X)
        z = np.dot(X, self.weights) + self.bias
        return self._sigmoid(z)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测类别"""
        probas = self.predict_proba(X)
        return (probas >= self.threshold).astype(int)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """计算准确率"""
        y_pred = self.predict(X)
        return np.mean(y_pred == y)


class LogisticRegressionL2:
    """
    L2正则化逻辑回归 (Ridge)

    L2正则化通过惩罚大的权重来防止过拟合。

    Parameters
    ----------
    learning_rate : float, default=0.01
        学习率
    n_iterations : int, default=1000
        迭代次数
    lambda_param : float, default=0.1
        L2正则化强度
    threshold : float, default=0.5
        分类阈值

    Attributes
    ----------
    weights : ndarray of shape (n_features,)
        模型权重
    bias : float
        偏置项
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        n_iterations: int = 1000,
        lambda_param: float = 0.1,
        threshold: float = 0.5
    ):
        self.learning_rate = learning_rate
        self.n_iterations = n_iterations
        self.lambda_param = lambda_param
        self.threshold = threshold
        self.weights: Optional[np.ndarray] = None
        self.bias: float = 0.0

    def _sigmoid(self, z: np.ndarray) -> np.ndarray:
        """Sigmoid激活函数"""
        z = np.clip(z, -500, 500)
        return 1 / (1 + np.exp(-z))

    def _compute_loss(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """
        计算带L2正则化的交叉熵损失

        公式: L = -1/m * Σ[y*log(p) + (1-y)*log(1-p)] + λ/2 * Σw_i^2
        """
        m = len(y_true)
        epsilon = 1e-15
        y_pred = np.clip(y_pred, epsilon, 1 - epsilon)

        # 交叉熵损失
        cross_entropy = -np.mean(
            y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred)
        )

        # L2正则化项
        l2_penalty = (self.lambda_param / 2) * np.sum(self.weights ** 2)

        return cross_entropy + l2_penalty

    def fit(self, X: np.ndarray, y: np.ndarray) -> 'LogisticRegressionL2':
        """
        训练L2正则化逻辑回归

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
        n_samples, n_features = X.shape

        # 初始化参数
        self.weights = np.zeros(n_features)
        self.bias = 0.0

        # 梯度下降训练
        for _ in range(self.n_iterations):
            # 前向传播
            z = np.dot(X, self.weights) + self.bias
            y_pred = self._sigmoid(z)

            # 计算梯度
            error = y_pred - y
            dw = (1 / n_samples) * np.dot(X.T, error)
            db = (1 / n_samples) * np.sum(error)

            # L2正则化梯度
            dw += self.lambda_param * self.weights

            # 更新参数
            self.weights -= self.learning_rate * dw
            self.bias -= self.learning_rate * db

        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """预测概率"""
        X = np.array(X)
        z = np.dot(X, self.weights) + self.bias
        return self._sigmoid(z)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测类别"""
        probas = self.predict_proba(X)
        return (probas >= self.threshold).astype(int)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """计算准确率"""
        y_pred = self.predict(X)
        return np.mean(y_pred == y)


class ElasticNet:
    """
    Elastic Net正则化逻辑回归

    Elastic Net结合了L1和L2正则化，既有特征选择能力，又能防止过拟合。

    Parameters
    ----------
    learning_rate : float, default=0.01
        学习率
    n_iterations : int, default=1000
        迭代次数
    l1_ratio : float, default=0.5
        L1正则化比例（0到1之间）
    lambda_param : float, default=0.1
        正则化强度
    threshold : float, default=0.5
        分类阈值

    Attributes
    ----------
    weights : ndarray of shape (n_features,)
        模型权重
    bias : float
        偏置项
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        n_iterations: int = 1000,
        l1_ratio: float = 0.5,
        lambda_param: float = 0.1,
        threshold: float = 0.5
    ):
        self.learning_rate = learning_rate
        self.n_iterations = n_iterations
        self.l1_ratio = l1_ratio
        self.lambda_param = lambda_param
        self.threshold = threshold
        self.weights: Optional[np.ndarray] = None
        self.bias: float = 0.0

    def _sigmoid(self, z: np.ndarray) -> np.ndarray:
        """Sigmoid激活函数"""
        z = np.clip(z, -500, 500)
        return 1 / (1 + np.exp(-z))

    def _compute_loss(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """
        计算带Elastic Net正则化的交叉熵损失

        公式: L = -1/m * Σ[y*log(p) + (1-y)*log(1-p)]
                + λ * [l1_ratio * Σ|w_i| + (1-l1_ratio)/2 * Σw_i^2]
        """
        m = len(y_true)
        epsilon = 1e-15
        y_pred = np.clip(y_pred, epsilon, 1 - epsilon)

        # 交叉熵损失
        cross_entropy = -np.mean(
            y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred)
        )

        # Elastic Net正则化项
        l1_penalty = self.l1_ratio * np.sum(np.abs(self.weights))
        l2_penalty = (1 - self.l1_ratio) / 2 * np.sum(self.weights ** 2)
        elastic_penalty = self.lambda_param * (l1_penalty + l2_penalty)

        return cross_entropy + elastic_penalty

    def fit(self, X: np.ndarray, y: np.ndarray) -> 'ElasticNet':
        """
        训练Elastic Net正则化逻辑回归

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
        n_samples, n_features = X.shape

        # 初始化参数
        self.weights = np.zeros(n_features)
        self.bias = 0.0

        # 梯度下降训练
        for _ in range(self.n_iterations):
            # 前向传播
            z = np.dot(X, self.weights) + self.bias
            y_pred = self._sigmoid(z)

            # 计算梯度
            error = y_pred - y
            dw = (1 / n_samples) * np.dot(X.T, error)
            db = (1 / n_samples) * np.sum(error)

            # Elastic Net正则化梯度
            # L1部分（次梯度）
            dw += self.lambda_param * self.l1_ratio * np.sign(self.weights)
            # L2部分
            dw += self.lambda_param * (1 - self.l1_ratio) * self.weights

            # 更新参数
            self.weights -= self.learning_rate * dw
            self.bias -= self.learning_rate * db

        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """预测概率"""
        X = np.array(X)
        z = np.dot(X, self.weights) + self.bias
        return self._sigmoid(z)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测类别"""
        probas = self.predict_proba(X)
        return (probas >= self.threshold).astype(int)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """计算准确率"""
        y_pred = self.predict(X)
        return np.mean(y_pred == y)
