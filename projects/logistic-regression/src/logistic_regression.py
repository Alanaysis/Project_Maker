"""
逻辑回归模型实现

核心概念：
1. Sigmoid函数：将线性输出映射到(0,1)概率空间
2. 交叉熵损失：衡量预测概率与真实标签的差异
3. 梯度下降：通过计算损失函数的梯度更新权重
"""

import numpy as np
from typing import Optional, Tuple


class LogisticRegression:
    """
    逻辑回归分类器

    Parameters
    ----------
    learning_rate : float, default=0.01
        学习率，控制梯度下降的步长
    n_iterations : int, default=1000
        迭代次数
    regularization : float, default=0.0
        L2正则化强度（lambda）
    threshold : float, default=0.5
        分类决策阈值
    verbose : bool, default=False
        是否打印训练过程

    Attributes
    ----------
    weights : ndarray of shape (n_features,)
        模型权重
    bias : float
        偏置项
    losses : list
        每次迭代的损失值记录
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        n_iterations: int = 1000,
        regularization: float = 0.0,
        threshold: float = 0.5,
        verbose: bool = False
    ):
        self.learning_rate = learning_rate
        self.n_iterations = n_iterations
        self.regularization = regularization
        self.threshold = threshold
        self.verbose = verbose

        # 模型参数
        self.weights: Optional[np.ndarray] = None
        self.bias: float = 0.0
        self.losses: list = []

    def _sigmoid(self, z: np.ndarray) -> np.ndarray:
        """
        Sigmoid激活函数

        公式: σ(z) = 1 / (1 + e^(-z))

        将任意实数映射到(0,1)区间，输出可解释为概率。

        Parameters
        ----------
        z : ndarray
            线性输出 z = w^T * x + b

        Returns
        -------
        ndarray
            Sigmoid激活值
        """
        # 数值稳定性处理：避免溢出
        z = np.clip(z, -500, 500)
        return 1 / (1 + np.exp(-z))

    def _compute_loss(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """
        计算交叉熵损失（Binary Cross-Entropy Loss）

        公式: L = -1/m * Σ[y*log(p) + (1-y)*log(1-p)]

        其中:
        - m: 样本数量
        - y: 真实标签 (0或1)
        - p: 预测概率

        Parameters
        ----------
        y_true : ndarray of shape (n_samples,)
            真实标签
        y_pred : ndarray of shape (n_samples,)
            预测概率

        Returns
        -------
        float
            交叉熵损失值
        """
        m = len(y_true)
        # 数值稳定性：避免log(0)
        epsilon = 1e-15
        y_pred = np.clip(y_pred, epsilon, 1 - epsilon)

        # 交叉熵损失
        cross_entropy = -np.mean(
            y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred)
        )

        # L2正则化项（可选）
        if self.regularization > 0:
            l2_penalty = (self.regularization / (2 * m)) * np.sum(self.weights ** 2)
            return cross_entropy + l2_penalty

        return cross_entropy

    def _compute_gradients(
        self,
        X: np.ndarray,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> Tuple[np.ndarray, float]:
        """
        计算损失函数关于权重和偏置的梯度

        推导过程：
        ∂L/∂w = 1/m * X^T * (p - y)
        ∂L/∂b = 1/m * Σ(p - y)

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            输入特征矩阵
        y_true : ndarray of shape (n_samples,)
            真实标签
        y_pred : ndarray of shape (n_samples,)
            预测概率

        Returns
        -------
        dw : ndarray of shape (n_features,)
            权重梯度
        db : float
            偏置梯度
        """
        m = len(y_true)
        error = y_pred - y_true

        # 权重梯度
        dw = (1 / m) * np.dot(X.T, error)

        # L2正则化梯度
        if self.regularization > 0:
            dw += (self.regularization / m) * self.weights

        # 偏置梯度
        db = (1 / m) * np.sum(error)

        return dw, db

    def fit(self, X: np.ndarray, y: np.ndarray) -> 'LogisticRegression':
        """
        训练逻辑回归模型

        使用梯度下降优化算法：
        1. 初始化权重和偏置
        2. 前向传播：计算预测概率
        3. 计算损失
        4. 反向传播：计算梯度
        5. 更新参数
        6. 重复直到收敛

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            训练数据特征
        y : ndarray of shape (n_samples,)
            训练数据标签 (0或1)

        Returns
        -------
        self
            训练后的模型实例
        """
        X = np.array(X)
        y = np.array(y)

        n_samples, n_features = X.shape

        # 初始化参数
        self.weights = np.zeros(n_features)
        self.bias = 0.0
        self.losses = []

        # 梯度下降训练
        for i in range(self.n_iterations):
            # 前向传播：计算预测概率
            z = np.dot(X, self.weights) + self.bias
            y_pred = self._sigmoid(z)

            # 计算损失
            loss = self._compute_loss(y, y_pred)
            self.losses.append(loss)

            # 反向传播：计算梯度
            dw, db = self._compute_gradients(X, y, y_pred)

            # 更新参数
            self.weights -= self.learning_rate * dw
            self.bias -= self.learning_rate * db

            # 打印训练过程
            if self.verbose and (i + 1) % 100 == 0:
                print(f"迭代 {i + 1}/{self.n_iterations}, 损失: {loss:.6f}")

        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        预测样本属于正类的概率

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            待预测的特征数据

        Returns
        -------
        ndarray of shape (n_samples,)
            属于正类的概率
        """
        X = np.array(X)
        z = np.dot(X, self.weights) + self.bias
        return self._sigmoid(z)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        预测样本类别

        根据阈值将概率转换为类别标签：
        - 概率 >= 阈值 → 1 (正类)
        - 概率 < 阈值 → 0 (负类)

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            待预测的特征数据

        Returns
        -------
        ndarray of shape (n_samples,)
            预测的类别标签 (0或1)
        """
        probabilities = self.predict_proba(X)
        return (probabilities >= self.threshold).astype(int)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        计算模型准确率

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            测试数据特征
        y : ndarray of shape (n_samples,)
            测试数据真实标签

        Returns
        -------
        float
            准确率 (正确预测的比例)
        """
        y_pred = self.predict(X)
        return np.mean(y_pred == y)

    def get_params(self) -> dict:
        """获取模型参数"""
        return {
            'weights': self.weights.tolist() if self.weights is not None else None,
            'bias': self.bias,
            'learning_rate': self.learning_rate,
            'n_iterations': self.n_iterations,
            'regularization': self.regularization,
            'threshold': self.threshold
        }

    def __repr__(self) -> str:
        return (
            f"LogisticRegression(learning_rate={self.learning_rate}, "
            f"n_iterations={self.n_iterations}, "
            f"regularization={self.regularization})"
        )
