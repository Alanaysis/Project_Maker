"""线性回归模型模块

从零实现线性回归，支持梯度下降优化。
"""

import numpy as np
from typing import List, Optional, Tuple
from .losses import MSELoss


class LinearRegression:
    """线性回归模型

    使用梯度下降优化的线性回归实现。

    数学公式：
        y_pred = X @ weights + bias
        Loss = (1/n) * Σ(y_pred - y_true)²

    Attributes:
        learning_rate: 学习率
        n_iterations: 迭代次数
        weights: 权重参数
        bias: 偏置参数
        losses: 损失历史
        weight_history: 权重更新历史
        bias_history: 偏置更新历史
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        n_iterations: int = 1000,
        verbose: bool = False,
    ):
        """初始化线性回归模型

        Args:
            learning_rate: 学习率，控制参数更新步长
            n_iterations: 迭代次数
            verbose: 是否打印训练过程
        """
        self.learning_rate = learning_rate
        self.n_iterations = n_iterations
        self.verbose = verbose

        # 模型参数
        self.weights: Optional[np.ndarray] = None
        self.bias: float = 0.0

        # 训练历史
        self.losses: List[float] = []
        self.weight_history: List[np.ndarray] = []
        self.bias_history: List[float] = []

    def fit(self, X: np.ndarray, y: np.ndarray) -> "LinearRegression":
        """训练模型

        Args:
            X: 特征矩阵，形状 (n_samples, n_features)
            y: 目标值，形状 (n_samples,)

        Returns:
            self: 训练后的模型

        Raises:
            ValueError: 当输入数据维度不匹配时
        """
        X = np.asarray(X)
        y = np.asarray(y).flatten()

        # 验证输入
        if X.shape[0] != y.shape[0]:
            raise ValueError(
                f"X and y must have same number of samples: {X.shape[0]} vs {y.shape[0]}"
            )

        # 确保 X 是 2D
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        n_samples, n_features = X.shape

        # 初始化参数
        self.weights = np.zeros(n_features)
        self.bias = 0.0

        # 清空历史
        self.losses = []
        self.weight_history = []
        self.bias_history = []

        # 训练循环
        for i in range(self.n_iterations):
            # 前向传播
            y_pred = self._forward(X)

            # 计算损失
            loss = MSELoss.compute(y, y_pred)
            self.losses.append(loss)

            # 记录参数历史
            self.weight_history.append(self.weights.copy())
            self.bias_history.append(self.bias)

            # 反向传播：计算梯度
            dw, db = self._compute_gradients(X, y, y_pred)

            # 更新参数
            self._update_parameters(dw, db)

            # 打印训练过程
            if self.verbose and (i + 1) % 100 == 0:
                print(f"Iteration {i + 1}/{self.n_iterations}, Loss: {loss:.6f}")

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测

        Args:
            X: 特征矩阵，形状 (n_samples, n_features)

        Returns:
            预测值，形状 (n_samples,)

        Raises:
            RuntimeError: 当模型未训练时
        """
        if self.weights is None:
            raise RuntimeError("Model must be fitted before prediction")

        X = np.asarray(X)

        # 确保 X 是 2D
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        return self._forward(X)

    def _forward(self, X: np.ndarray) -> np.ndarray:
        """前向传播

        计算 y_pred = X @ weights + bias

        Args:
            X: 特征矩阵

        Returns:
            预测值
        """
        return X @ self.weights + self.bias

    def _compute_gradients(
        self, X: np.ndarray, y: np.ndarray, y_pred: np.ndarray
    ) -> Tuple[np.ndarray, float]:
        """计算梯度

        ∂Loss/∂w = (2/n) * X.T @ (y_pred - y_true)
        ∂Loss/∂b = (2/n) * Σ(y_pred - y_true)

        Args:
            X: 特征矩阵
            y: 真实值
            y_pred: 预测值

        Returns:
            (dw, db): 权重梯度和偏置梯度
        """
        n = len(y)
        error = y_pred - y

        dw = (2.0 / n) * (X.T @ error)
        db = (2.0 / n) * np.sum(error)

        return dw, db

    def _update_parameters(self, dw: np.ndarray, db: float) -> None:
        """更新参数

        w = w - learning_rate * dw
        b = b - learning_rate * db

        Args:
            dw: 权重梯度
            db: 偏置梯度
        """
        self.weights -= self.learning_rate * dw
        self.bias -= self.learning_rate * db

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """计算 R² 分数

        R² = 1 - SS_res / SS_tot

        Args:
            X: 特征矩阵
            y: 真实值

        Returns:
            R² 分数
        """
        y_pred = self.predict(X)
        y = np.asarray(y).flatten()

        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)

        return 1 - (ss_res / ss_tot)

    def get_params(self) -> dict:
        """获取模型参数

        Returns:
            参数字典
        """
        return {
            "learning_rate": self.learning_rate,
            "n_iterations": self.n_iterations,
            "weights": self.weights.tolist() if self.weights is not None else None,
            "bias": self.bias,
        }

    def __repr__(self) -> str:
        return (
            f"LinearRegression(learning_rate={self.learning_rate}, "
            f"n_iterations={self.n_iterations})"
        )
