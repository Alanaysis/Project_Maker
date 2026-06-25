"""
优化算法实现

实现三种梯度下降变体：
1. 批量梯度下降 (Batch Gradient Descent)
2. 随机梯度下降 (Stochastic Gradient Descent)
3. 小批量梯度下降 (Mini-batch Gradient Descent)
4. 学习率调度
"""

import numpy as np
from typing import Optional, List


class BaseOptimizer:
    """
    优化器基类

    Parameters
    ----------
    learning_rate : float, default=0.01
        学习率
    n_iterations : int, default=1000
        迭代次数
    threshold : float, default=0.5
        分类阈值

    Attributes
    ----------
    weights : ndarray of shape (n_features,)
        模型权重
    bias : float
        偏置项
    losses : list
        损失记录
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        n_iterations: int = 1000,
        threshold: float = 0.5
    ):
        self.learning_rate = learning_rate
        self.n_iterations = n_iterations
        self.threshold = threshold
        self.weights: Optional[np.ndarray] = None
        self.bias: float = 0.0
        self.losses: List[float] = []

    def _sigmoid(self, z: np.ndarray) -> np.ndarray:
        """Sigmoid激活函数"""
        z = np.clip(z, -500, 500)
        return 1 / (1 + np.exp(-z))

    def _compute_loss(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """计算交叉熵损失"""
        epsilon = 1e-15
        y_pred = np.clip(y_pred, epsilon, 1 - epsilon)
        return -np.mean(
            y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred)
        )

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


class BatchGradientDescent(BaseOptimizer):
    """
    批量梯度下降 (Batch Gradient Descent)

    每次迭代使用所有训练样本计算梯度。

    优点：
    - 收敛稳定
    - 梯度方向准确

    缺点：
    - 计算开销大
    - 内存消耗高
    - 不适合大规模数据

    Parameters
    ----------
    learning_rate : float, default=0.01
        学习率
    n_iterations : int, default=1000
        迭代次数
    threshold : float, default=0.5
        分类阈值
    """

    def fit(self, X: np.ndarray, y: np.ndarray) -> 'BatchGradientDescent':
        """
        使用批量梯度下降训练模型

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
        self.losses = []

        # 梯度下降训练
        for _ in range(self.n_iterations):
            # 前向传播
            z = np.dot(X, self.weights) + self.bias
            y_pred = self._sigmoid(z)

            # 计算损失
            loss = self._compute_loss(y, y_pred)
            self.losses.append(loss)

            # 计算梯度（使用所有样本）
            error = y_pred - y
            dw = (1 / n_samples) * np.dot(X.T, error)
            db = (1 / n_samples) * np.sum(error)

            # 更新参数
            self.weights -= self.learning_rate * dw
            self.bias -= self.learning_rate * db

        return self


class StochasticGradientDescent(BaseOptimizer):
    """
    随机梯度下降 (Stochastic Gradient Descent)

    每次迭代只使用一个随机样本计算梯度。

    优点：
    - 计算速度快
    - 能跳出局部最优
    - 适合在线学习

    缺点：
    - 收敛不稳定
    - 梯度方向有噪声

    Parameters
    ----------
    learning_rate : float, default=0.01
        学习率
    n_iterations : int, default=1000
        迭代次数
    threshold : float, default=0.5
        分类阈值
    learning_rate_schedule : str, default='constant'
        学习率调度策略：'constant', 'decay', 'inverse'
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        n_iterations: int = 1000,
        threshold: float = 0.5,
        learning_rate_schedule: str = 'constant'
    ):
        super().__init__(learning_rate, n_iterations, threshold)
        self.learning_rate_schedule = learning_rate_schedule

    def _get_learning_rate(self, t: int) -> float:
        """
        获取当前学习率

        Parameters
        ----------
        t : int
            当前迭代次数

        Returns
        -------
        float
            当前学习率
        """
        if self.learning_rate_schedule == 'constant':
            return self.learning_rate
        elif self.learning_rate_schedule == 'decay':
            # 指数衰减
            return self.learning_rate * np.exp(-0.01 * t)
        elif self.learning_rate_schedule == 'inverse':
            # 反比例衰减
            return self.learning_rate / (1 + 0.01 * t)
        else:
            raise ValueError(f"Unknown schedule: {self.learning_rate_schedule}")

    def fit(self, X: np.ndarray, y: np.ndarray) -> 'StochasticGradientDescent':
        """
        使用随机梯度下降训练模型

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
        self.losses = []

        # 梯度下降训练
        for t in range(self.n_iterations):
            # 随机打乱数据
            indices = np.random.permutation(n_samples)
            X_shuffled = X[indices]
            y_shuffled = y[indices]

            # 获取当前学习率
            lr = self._get_learning_rate(t)

            # 遍历每个样本
            for i in range(n_samples):
                # 取一个样本
                xi = X_shuffled[i:i + 1]
                yi = y_shuffled[i:i + 1]

                # 前向传播
                z = np.dot(xi, self.weights) + self.bias
                y_pred = self._sigmoid(z)

                # 计算梯度
                error = y_pred - yi
                dw = xi.T * error
                db = error

                # 更新参数
                self.weights -= lr * dw.flatten()
                self.bias -= lr * db[0]

            # 计算整个数据集的损失
            z = np.dot(X, self.weights) + self.bias
            y_pred = self._sigmoid(z)
            loss = self._compute_loss(y, y_pred)
            self.losses.append(loss)

        return self


class MiniBatchGradientDescent(BaseOptimizer):
    """
    小批量梯度下降 (Mini-batch Gradient Descent)

    每次迭代使用一小批样本计算梯度，是BGD和SGD的折中。

    优点：
    - 计算效率高
    - 收敛相对稳定
    - 适合大规模数据

    缺点：
    - 需要选择批量大小
    - 可能需要学习率调整

    Parameters
    ----------
    learning_rate : float, default=0.01
        学习率
    n_iterations : int, default=1000
        迭代次数
    batch_size : int, default=32
        批量大小
    threshold : float, default=0.5
        分类阈值
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        n_iterations: int = 1000,
        batch_size: int = 32,
        threshold: float = 0.5
    ):
        super().__init__(learning_rate, n_iterations, threshold)
        self.batch_size = batch_size

    def fit(self, X: np.ndarray, y: np.ndarray) -> 'MiniBatchGradientDescent':
        """
        使用小批量梯度下降训练模型

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
        self.losses = []

        # 梯度下降训练
        for _ in range(self.n_iterations):
            # 随机打乱数据
            indices = np.random.permutation(n_samples)
            X_shuffled = X[indices]
            y_shuffled = y[indices]

            # 分批处理
            for start in range(0, n_samples, self.batch_size):
                end = min(start + self.batch_size, n_samples)
                X_batch = X_shuffled[start:end]
                y_batch = y_shuffled[start:end]
                batch_len = end - start

                # 前向传播
                z = np.dot(X_batch, self.weights) + self.bias
                y_pred = self._sigmoid(z)

                # 计算梯度
                error = y_pred - y_batch
                dw = (1 / batch_len) * np.dot(X_batch.T, error)
                db = (1 / batch_len) * np.sum(error)

                # 更新参数
                self.weights -= self.learning_rate * dw
                self.bias -= self.learning_rate * db

            # 计算整个数据集的损失
            z = np.dot(X, self.weights) + self.bias
            y_pred = self._sigmoid(z)
            loss = self._compute_loss(y, y_pred)
            self.losses.append(loss)

        return self


class LearningRateScheduler:
    """
    学习率调度器

    提供多种学习率调度策略。

    Parameters
    ----------
    initial_lr : float
        初始学习率
    schedule : str, default='constant'
        调度策略：'constant', 'step_decay', 'exponential_decay', 'cosine_annealing'
    step_size : int, default=100
        步长衰减的步长
    gamma : float, default=0.1
        衰减因子
    """

    def __init__(
        self,
        initial_lr: float = 0.01,
        schedule: str = 'constant',
        step_size: int = 100,
        gamma: float = 0.1
    ):
        self.initial_lr = initial_lr
        self.schedule = schedule
        self.step_size = step_size
        self.gamma = gamma

    def get_lr(self, epoch: int) -> float:
        """
        获取指定epoch的学习率

        Parameters
        ----------
        epoch : int
            当前epoch

        Returns
        -------
        float
            当前学习率
        """
        if self.schedule == 'constant':
            return self.initial_lr
        elif self.schedule == 'step_decay':
            # 步长衰减
            return self.initial_lr * (self.gamma ** (epoch // self.step_size))
        elif self.schedule == 'exponential_decay':
            # 指数衰减
            return self.initial_lr * np.exp(-self.gamma * epoch)
        elif self.schedule == 'cosine_annealing':
            # 余弦退火
            return self.initial_lr * 0.5 * (1 + np.cos(np.pi * epoch / self.step_size))
        else:
            raise ValueError(f"Unknown schedule: {self.schedule}")


class MomentumOptimizer(BaseOptimizer):
    """
    动量优化器

    使用动量加速梯度下降，有助于跳出局部最优。

    Parameters
    ----------
    learning_rate : float, default=0.01
        学习率
    n_iterations : int, default=1000
        迭代次数
    momentum : float, default=0.9
        动量因子
    threshold : float, default=0.5
        分类阈值

    Attributes
    ----------
    velocity_w : ndarray
        权重的动量
    velocity_b : float
        偏置的动量
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        n_iterations: int = 1000,
        momentum: float = 0.9,
        threshold: float = 0.5
    ):
        super().__init__(learning_rate, n_iterations, threshold)
        self.momentum = momentum
        self.velocity_w: Optional[np.ndarray] = None
        self.velocity_b: float = 0.0

    def fit(self, X: np.ndarray, y: np.ndarray) -> 'MomentumOptimizer':
        """
        使用动量梯度下降训练模型

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
        self.velocity_w = np.zeros(n_features)
        self.velocity_b = 0.0
        self.losses = []

        # 梯度下降训练
        for _ in range(self.n_iterations):
            # 前向传播
            z = np.dot(X, self.weights) + self.bias
            y_pred = self._sigmoid(z)

            # 计算损失
            loss = self._compute_loss(y, y_pred)
            self.losses.append(loss)

            # 计算梯度
            error = y_pred - y
            dw = (1 / n_samples) * np.dot(X.T, error)
            db = (1 / n_samples) * np.sum(error)

            # 更新动量
            self.velocity_w = self.momentum * self.velocity_w - self.learning_rate * dw
            self.velocity_b = self.momentum * self.velocity_b - self.learning_rate * db

            # 更新参数
            self.weights += self.velocity_w
            self.bias += self.velocity_b

        return self


class AdamOptimizer(BaseOptimizer):
    """
    Adam优化器

    结合了动量和自适应学习率的优点。

    Parameters
    ----------
    learning_rate : float, default=0.001
        学习率
    n_iterations : int, default=1000
        迭代次数
    beta1 : float, default=0.9
        一阶矩估计的指数衰减率
    beta2 : float, default=0.999
        二阶矩估计的指数衰减率
    epsilon : float, default=1e-8
        数值稳定性常数
    threshold : float, default=0.5
        分类阈值

    Attributes
    ----------
    m_w, v_w : ndarray
        权重的一阶矩和二阶矩
    m_b, v_b : float
        偏置的一阶矩和二阶矩
    """

    def __init__(
        self,
        learning_rate: float = 0.001,
        n_iterations: int = 1000,
        beta1: float = 0.9,
        beta2: float = 0.999,
        epsilon: float = 1e-8,
        threshold: float = 0.5
    ):
        super().__init__(learning_rate, n_iterations, threshold)
        self.beta1 = beta1
        self.beta2 = beta2
        self.epsilon = epsilon
        self.m_w: Optional[np.ndarray] = None
        self.v_w: Optional[np.ndarray] = None
        self.m_b: float = 0.0
        self.v_b: float = 0.0

    def fit(self, X: np.ndarray, y: np.ndarray) -> 'AdamOptimizer':
        """
        使用Adam优化器训练模型

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
        self.m_w = np.zeros(n_features)
        self.v_w = np.zeros(n_features)
        self.m_b = 0.0
        self.v_b = 0.0
        self.losses = []

        # 梯度下降训练
        for t in range(1, self.n_iterations + 1):
            # 前向传播
            z = np.dot(X, self.weights) + self.bias
            y_pred = self._sigmoid(z)

            # 计算损失
            loss = self._compute_loss(y, y_pred)
            self.losses.append(loss)

            # 计算梯度
            error = y_pred - y
            dw = (1 / n_samples) * np.dot(X.T, error)
            db = (1 / n_samples) * np.sum(error)

            # 更新一阶矩
            self.m_w = self.beta1 * self.m_w + (1 - self.beta1) * dw
            self.m_b = self.beta1 * self.m_b + (1 - self.beta1) * db

            # 更新二阶矩
            self.v_w = self.beta2 * self.v_w + (1 - self.beta2) * dw ** 2
            self.v_b = self.beta2 * self.v_b + (1 - self.beta2) * db ** 2

            # 偏差修正
            m_w_hat = self.m_w / (1 - self.beta1 ** t)
            m_b_hat = self.m_b / (1 - self.beta1 ** t)
            v_w_hat = self.v_w / (1 - self.beta2 ** t)
            v_b_hat = self.v_b / (1 - self.beta2 ** t)

            # 更新参数
            self.weights -= self.learning_rate * m_w_hat / (np.sqrt(v_w_hat) + self.epsilon)
            self.bias -= self.learning_rate * m_b_hat / (np.sqrt(v_b_hat) + self.epsilon)

        return self
