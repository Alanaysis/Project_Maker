"""线性回归模型模块

从零实现多种线性回归模型：
- LinearRegression: 基础线性回归（梯度下降 + 正规方程）
- RidgeRegression: L2 正则化线性回归
- LassoRegression: L1 正则化线性回归
- ElasticNet: L1+L2 混合正则化线性回归
"""

import numpy as np
from typing import List, Optional, Tuple, Literal
from .losses import MSELoss


class LinearRegression:
    """线性回归模型

    支持两种求解方法：
    1. 梯度下降法 (gradient_descent): 迭代优化，适合大规模数据
    2. 正规方程法 (normal_equation): 直接求解，适合小规模数据

    数学公式：
        y_pred = X @ weights + bias
        Loss = (1/n) * Σ(y_pred - y_true)²

    梯度下降更新规则：
        dw = (2/n) * X.T @ (y_pred - y)
        db = (2/n) * sum(y_pred - y)
        w = w - lr * dw
        b = b - lr * db

    正规方程：
        w = (X.T @ X)^(-1) @ X.T @ y
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        n_iterations: int = 1000,
        method: Literal["gradient_descent", "normal_equation"] = "gradient_descent",
        verbose: bool = False,
    ):
        """初始化线性回归模型

        Args:
            learning_rate: 学习率，控制参数更新步长
            n_iterations: 迭代次数
            method: 求解方法，'gradient_descent' 或 'normal_equation'
            verbose: 是否打印训练过程
        """
        self.learning_rate = learning_rate
        self.n_iterations = n_iterations
        self.method = method
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
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float).flatten()

        # 验证输入
        if X.shape[0] != y.shape[0]:
            raise ValueError(
                f"X and y must have same number of samples: {X.shape[0]} vs {y.shape[0]}"
            )

        # 确保 X 是 2D
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        if self.method == "normal_equation":
            self._fit_normal_equation(X, y)
        else:
            self._fit_gradient_descent(X, y)

        return self

    def _fit_gradient_descent(self, X: np.ndarray, y: np.ndarray) -> None:
        """使用梯度下降训练模型

        Args:
            X: 特征矩阵
            y: 目标值
        """
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

    def _fit_normal_equation(self, X: np.ndarray, y: np.ndarray) -> None:
        """使用正规方程求解

        正规方程：w = (X.T @ X)^(-1) @ X.T @ y

        优点：
        - 无需选择学习率
        - 无需迭代
        - 有闭式解

        缺点：
        - 计算复杂度 O(n³)，n 为特征数
        - 需要 X.T @ X 可逆
        - 不适合大规模数据

        Args:
            X: 特征矩阵
            y: 目标值
        """
        # 清空历史
        self.losses = []
        self.weight_history = []
        self.bias_history = []

        # 在 X 前添加一列 1 来包含偏置
        X_b = np.c_[np.ones((X.shape[0], 1)), X]

        try:
            # 使用正规方程求解
            # theta = (X^T X)^(-1) X^T y
            theta = np.linalg.pinv(X_b.T @ X_b) @ X_b.T @ y

            self.bias = theta[0]
            self.weights = theta[1:]

            # 计算最终损失
            y_pred = self._forward(X)
            loss = MSELoss.compute(y, y_pred)
            self.losses.append(loss)

        except np.linalg.LinAlgError:
            # 如果矩阵不可逆，回退到梯度下降
            print("Warning: Normal equation failed, falling back to gradient descent")
            self._fit_gradient_descent(X, y)

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

        X = np.asarray(X, dtype=float)

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
            "method": self.method,
            "weights": self.weights.tolist() if self.weights is not None else None,
            "bias": self.bias,
        }

    def __repr__(self) -> str:
        return (
            f"LinearRegression(learning_rate={self.learning_rate}, "
            f"n_iterations={self.n_iterations}, method='{self.method}')"
        )


class RidgeRegression:
    """岭回归 (Ridge Regression) - L2 正则化

    在损失函数中添加 L2 正则项，防止过拟合。

    损失函数：
        Loss = (1/n) * Σ(y_pred - y_true)² + α * Σ(w²)

    其中 α 是正则化强度参数。

    特点：
    - 权重趋向于小值，但不会为零
    - 所有特征都被保留
    - 适合多重共线性数据
    - 有闭式解：w = (X.T @ X + α*I)^(-1) @ X.T @ y

    数学推导（梯度）：
        ∂Loss/∂w = (2/n) * X.T @ (y_pred - y) + 2α * w
        ∂Loss/∂b = (2/n) * Σ(y_pred - y)
    """

    def __init__(
        self,
        alpha: float = 1.0,
        learning_rate: float = 0.01,
        n_iterations: int = 1000,
        method: Literal["gradient_descent", "normal_equation"] = "gradient_descent",
        verbose: bool = False,
    ):
        """初始化岭回归

        Args:
            alpha: L2 正则化强度
            learning_rate: 学习率
            n_iterations: 迭代次数
            method: 求解方法
            verbose: 是否打印训练过程
        """
        self.alpha = alpha
        self.learning_rate = learning_rate
        self.n_iterations = n_iterations
        self.method = method
        self.verbose = verbose

        self.weights: Optional[np.ndarray] = None
        self.bias: float = 0.0
        self.losses: List[float] = []

    def fit(self, X: np.ndarray, y: np.ndarray) -> "RidgeRegression":
        """训练模型

        Args:
            X: 特征矩阵
            y: 目标值

        Returns:
            self
        """
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float).flatten()

        if X.ndim == 1:
            X = X.reshape(-1, 1)

        if self.method == "normal_equation":
            self._fit_normal_equation(X, y)
        else:
            self._fit_gradient_descent(X, y)

        return self

    def _fit_gradient_descent(self, X: np.ndarray, y: np.ndarray) -> None:
        """使用梯度下降训练

        Args:
            X: 特征矩阵
            y: 目标值
        """
        n_samples, n_features = X.shape

        self.weights = np.zeros(n_features)
        self.bias = 0.0
        self.losses = []

        for i in range(self.n_iterations):
            # 前向传播
            y_pred = X @ self.weights + self.bias

            # 计算损失（含正则项）
            mse_loss = MSELoss.compute(y, y_pred)
            l2_penalty = self.alpha * np.sum(self.weights ** 2)
            total_loss = mse_loss + l2_penalty
            self.losses.append(total_loss)

            # 计算梯度（含正则项梯度）
            error = y_pred - y
            dw = (2.0 / n_samples) * (X.T @ error) + 2 * self.alpha * self.weights
            db = (2.0 / n_samples) * np.sum(error)

            # 更新参数
            self.weights -= self.learning_rate * dw
            self.bias -= self.learning_rate * db

            if self.verbose and (i + 1) % 100 == 0:
                print(f"Iteration {i + 1}/{self.n_iterations}, Loss: {total_loss:.6f}")

    def _fit_normal_equation(self, X: np.ndarray, y: np.ndarray) -> None:
        """使用正规方程求解

        w = (X.T @ X + α * I)^(-1) @ X.T @ y

        Args:
            X: 特征矩阵
            y: 目标值
        """
        self.losses = []

        n_features = X.shape[1]

        # 正规方程（带 L2 正则化）
        I = np.eye(n_features)
        try:
            self.weights = np.linalg.pinv(X.T @ X + self.alpha * I) @ X.T @ y
            self.bias = np.mean(y - X @ self.weights)

            # 计算损失
            y_pred = X @ self.weights + self.bias
            mse_loss = MSELoss.compute(y, y_pred)
            l2_penalty = self.alpha * np.sum(self.weights ** 2)
            self.losses.append(mse_loss + l2_penalty)

        except np.linalg.LinAlgError:
            print("Warning: Normal equation failed, falling back to gradient descent")
            self._fit_gradient_descent(X, y)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测

        Args:
            X: 特征矩阵

        Returns:
            预测值
        """
        if self.weights is None:
            raise RuntimeError("Model must be fitted before prediction")
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        return X @ self.weights + self.bias

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """计算 R² 分数"""
        y_pred = self.predict(X)
        y = np.asarray(y).flatten()
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return 1 - (ss_res / ss_tot)

    def get_params(self) -> dict:
        """获取模型参数"""
        return {
            "alpha": self.alpha,
            "learning_rate": self.learning_rate,
            "n_iterations": self.n_iterations,
            "method": self.method,
            "weights": self.weights.tolist() if self.weights is not None else None,
            "bias": self.bias,
        }

    def __repr__(self) -> str:
        return (
            f"RidgeRegression(alpha={self.alpha}, learning_rate={self.learning_rate}, "
            f"n_iterations={self.n_iterations})"
        )


class LassoRegression:
    """Lasso 回归 (Lasso Regression) - L1 正则化

    在损失函数中添加 L1 正则项，实现特征选择（稀疏解）。

    损失函数：
        Loss = (1/n) * Σ(y_pred - y_true)² + α * Σ|w|

    特点：
    - 可以将不重要的特征权重压缩到零（稀疏性）
    - 自动进行特征选择
    - 适合高维数据
    - 没有闭式解（L1 不可导），使用坐标下降法

    由于 L1 在零点不可导，使用次梯度（subgradient）：
        ∂|w|/∂w = sign(w)  (w != 0)
        ∂|w|/∂w ∈ [-1, 1]  (w = 0)
    """

    def __init__(
        self,
        alpha: float = 1.0,
        learning_rate: float = 0.01,
        n_iterations: int = 1000,
        verbose: bool = False,
    ):
        """初始化 Lasso 回归

        Args:
            alpha: L1 正则化强度
            learning_rate: 学习率
            n_iterations: 迭代次数
            verbose: 是否打印训练过程
        """
        self.alpha = alpha
        self.learning_rate = learning_rate
        self.n_iterations = n_iterations
        self.verbose = verbose

        self.weights: Optional[np.ndarray] = None
        self.bias: float = 0.0
        self.losses: List[float] = []

    def fit(self, X: np.ndarray, y: np.ndarray) -> "LassoRegression":
        """训练模型

        使用次梯度下降法优化（因为 L1 在零点不可导）。

        Args:
            X: 特征矩阵
            y: 目标值

        Returns:
            self
        """
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float).flatten()

        if X.ndim == 1:
            X = X.reshape(-1, 1)

        n_samples, n_features = X.shape

        # 初始化参数
        self.weights = np.zeros(n_features)
        self.bias = 0.0
        self.losses = []

        for i in range(self.n_iterations):
            # 前向传播
            y_pred = X @ self.weights + self.bias

            # 计算损失（含 L1 正则项）
            mse_loss = MSELoss.compute(y, y_pred)
            l1_penalty = self.alpha * np.sum(np.abs(self.weights))
            total_loss = mse_loss + l1_penalty
            self.losses.append(total_loss)

            # 计算梯度（使用次梯度）
            error = y_pred - y
            dw = (2.0 / n_samples) * (X.T @ error) + self.alpha * np.sign(self.weights)
            db = (2.0 / n_samples) * np.sum(error)

            # 更新参数
            self.weights -= self.learning_rate * dw
            self.bias -= self.learning_rate * db

            if self.verbose and (i + 1) % 100 == 0:
                print(f"Iteration {i + 1}/{self.n_iterations}, Loss: {total_loss:.6f}")

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测"""
        if self.weights is None:
            raise RuntimeError("Model must be fitted before prediction")
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        return X @ self.weights + self.bias

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """计算 R² 分数"""
        y_pred = self.predict(X)
        y = np.asarray(y).flatten()
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return 1 - (ss_res / ss_tot)

    def get_params(self) -> dict:
        """获取模型参数"""
        return {
            "alpha": self.alpha,
            "learning_rate": self.learning_rate,
            "n_iterations": self.n_iterations,
            "weights": self.weights.tolist() if self.weights is not None else None,
            "bias": self.bias,
            "n_nonzero_weights": int(np.sum(np.abs(self.weights) > 1e-10))
            if self.weights is not None
            else 0,
        }

    def __repr__(self) -> str:
        return (
            f"LassoRegression(alpha={self.alpha}, learning_rate={self.learning_rate}, "
            f"n_iterations={self.n_iterations})"
        )


class ElasticNet:
    """弹性网络回归 (Elastic Net Regression) - L1+L2 混合正则化

    结合 L1 和 L2 正则化的优点。

    损失函数：
        Loss = (1/n) * Σ(y_pred - y_true)²
             + α * l1_ratio * Σ|w|
             + α * (1 - l1_ratio) * 0.5 * Σ(w²)

    特点：
    - 结合 Lasso 和 Ridge 的优点
    - l1_ratio=1 时退化为 Lasso
    - l1_ratio=0 时退化为 Ridge
    - 适合特征之间有相关性的数据
    """

    def __init__(
        self,
        alpha: float = 1.0,
        l1_ratio: float = 0.5,
        learning_rate: float = 0.01,
        n_iterations: int = 1000,
        verbose: bool = False,
    ):
        """初始化 Elastic Net

        Args:
            alpha: 总正则化强度
            l1_ratio: L1 正则化占比 [0, 1]
            learning_rate: 学习率
            n_iterations: 迭代次数
            verbose: 是否打印训练过程
        """
        self.alpha = alpha
        self.l1_ratio = l1_ratio
        self.learning_rate = learning_rate
        self.n_iterations = n_iterations
        self.verbose = verbose

        self.weights: Optional[np.ndarray] = None
        self.bias: float = 0.0
        self.losses: List[float] = []

    def fit(self, X: np.ndarray, y: np.ndarray) -> "ElasticNet":
        """训练模型

        Args:
            X: 特征矩阵
            y: 目标值

        Returns:
            self
        """
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float).flatten()

        if X.ndim == 1:
            X = X.reshape(-1, 1)

        n_samples, n_features = X.shape

        # 初始化参数
        self.weights = np.zeros(n_features)
        self.bias = 0.0
        self.losses = []

        for i in range(self.n_iterations):
            # 前向传播
            y_pred = X @ self.weights + self.bias

            # 计算损失
            mse_loss = MSELoss.compute(y, y_pred)
            l1_penalty = self.alpha * self.l1_ratio * np.sum(np.abs(self.weights))
            l2_penalty = (
                self.alpha * (1 - self.l1_ratio) * 0.5 * np.sum(self.weights ** 2)
            )
            total_loss = mse_loss + l1_penalty + l2_penalty
            self.losses.append(total_loss)

            # 计算梯度
            error = y_pred - y
            dw = (
                (2.0 / n_samples) * (X.T @ error)
                + self.alpha * self.l1_ratio * np.sign(self.weights)
                + self.alpha * (1 - self.l1_ratio) * self.weights
            )
            db = (2.0 / n_samples) * np.sum(error)

            # 更新参数
            self.weights -= self.learning_rate * dw
            self.bias -= self.learning_rate * db

            if self.verbose and (i + 1) % 100 == 0:
                print(f"Iteration {i + 1}/{self.n_iterations}, Loss: {total_loss:.6f}")

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测"""
        if self.weights is None:
            raise RuntimeError("Model must be fitted before prediction")
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        return X @ self.weights + self.bias

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """计算 R² 分数"""
        y_pred = self.predict(X)
        y = np.asarray(y).flatten()
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return 1 - (ss_res / ss_tot)

    def get_params(self) -> dict:
        """获取模型参数"""
        return {
            "alpha": self.alpha,
            "l1_ratio": self.l1_ratio,
            "learning_rate": self.learning_rate,
            "n_iterations": self.n_iterations,
            "weights": self.weights.tolist() if self.weights is not None else None,
            "bias": self.bias,
            "n_nonzero_weights": int(np.sum(np.abs(self.weights) > 1e-10))
            if self.weights is not None
            else 0,
        }

    def __repr__(self) -> str:
        return (
            f"ElasticNet(alpha={self.alpha}, l1_ratio={self.l1_ratio}, "
            f"learning_rate={self.learning_rate}, n_iterations={self.n_iterations})"
        )
