"""优化算法模块

实现梯度下降的各种变体：
- 批量梯度下降 (Batch Gradient Descent)
- 随机梯度下降 (Stochastic Gradient Descent)
- 小批量梯度下降 (Mini-Batch Gradient Descent)
- 学习率调度器
"""

import numpy as np
from typing import Tuple, Optional, List


class BatchGradientDescent:
    """批量梯度下降 (Batch Gradient Descent, BGD)

    每次使用全部训练数据计算梯度，然后更新参数。

    特点：
    - 梯度估计准确，收敛稳定
    - 每次迭代计算量大
    - 容易收敛到全局最优（凸问题）
    - 可能陷入局部最优（非凸问题）

    数学公式：
        dw = (2/n) * X.T @ (y_pred - y)
        db = (2/n) * sum(y_pred - y)
        w = w - lr * dw
        b = b - lr * db
    """

    def __init__(self, learning_rate: float = 0.01):
        """初始化批量梯度下降

        Args:
            learning_rate: 学习率
        """
        self.learning_rate = learning_rate

    def compute_gradients(
        self,
        X: np.ndarray,
        y: np.ndarray,
        y_pred: np.ndarray,
        weights: np.ndarray,
        bias: float,
    ) -> Tuple[np.ndarray, float]:
        """计算梯度

        Args:
            X: 特征矩阵，形状 (n_samples, n_features)
            y: 真实值，形状 (n_samples,)
            y_pred: 预测值，形状 (n_samples,)
            weights: 当前权重
            bias: 当前偏置

        Returns:
            (dw, db): 权重梯度和偏置梯度
        """
        n = len(y)
        error = y_pred - y

        dw = (2.0 / n) * (X.T @ error)
        db = (2.0 / n) * np.sum(error)

        return dw, db

    def update(
        self,
        weights: np.ndarray,
        bias: float,
        dw: np.ndarray,
        db: float,
    ) -> Tuple[np.ndarray, float]:
        """更新参数

        Args:
            weights: 当前权重
            bias: 当前偏置
            dw: 权重梯度
            db: 偏置梯度

        Returns:
            (new_weights, new_bias): 更新后的参数
        """
        new_weights = weights - self.learning_rate * dw
        new_bias = bias - self.learning_rate * db
        return new_weights, new_bias


class StochasticGradientDescent:
    """随机梯度下降 (Stochastic Gradient Descent, SGD)

    每次使用单个样本计算梯度并更新参数。

    特点：
    - 每次迭代计算量小
    - 更新频繁，收敛速度快（单次迭代）
    - 梯度噪声大，可能跳出局部最优
    - 损失曲线震荡

    数学公式（对单个样本 i）：
        dw = 2 * x_i * (y_pred_i - y_i)
        db = 2 * (y_pred_i - y_i)
        w = w - lr * dw
        b = b - lr * db
    """

    def __init__(self, learning_rate: float = 0.01):
        """初始化随机梯度下降

        Args:
            learning_rate: 学习率
        """
        self.learning_rate = learning_rate

    def compute_single_gradient(
        self,
        x_i: np.ndarray,
        y_i: float,
        y_pred_i: float,
    ) -> Tuple[np.ndarray, float]:
        """计算单个样本的梯度

        Args:
            x_i: 单个样本特征，形状 (n_features,)
            y_i: 单个样本真实值
            y_pred_i: 单个样本预测值

        Returns:
            (dw_i, db_i): 单样本权重梯度和偏置梯度
        """
        error = y_pred_i - y_i
        dw_i = 2.0 * x_i * error
        db_i = 2.0 * error

        return dw_i, db_i

    def update(
        self,
        weights: np.ndarray,
        bias: float,
        dw: np.ndarray,
        db: float,
    ) -> Tuple[np.ndarray, float]:
        """更新参数

        Args:
            weights: 当前权重
            bias: 当前偏置
            dw: 权重梯度
            db: 偏置梯度

        Returns:
            (new_weights, new_bias)
        """
        new_weights = weights - self.learning_rate * dw
        new_bias = bias - self.learning_rate * db
        return new_weights, new_bias


class MiniBatchGradientDescent:
    """小批量梯度下降 (Mini-Batch Gradient Descent)

    每次使用一小批样本计算梯度，平衡了 BGD 和 SGD 的优缺点。

    特点：
    - 计算效率高（利用向量化）
    - 梯度比 SGD 更稳定
    - 可以利用 GPU 并行计算
    - 最常用的训练方式

    数学公式（对 mini-batch B）：
        dw = (2/|B|) * X_B.T @ (y_pred_B - y_B)
        db = (2/|B|) * sum(y_pred_B - y_B)
        w = w - lr * dw
        b = b - lr * db
    """

    def __init__(self, learning_rate: float = 0.01, batch_size: int = 32):
        """初始化小批量梯度下降

        Args:
            learning_rate: 学习率
            batch_size: 批量大小
        """
        self.learning_rate = learning_rate
        self.batch_size = batch_size

    def get_batches(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> List[Tuple[np.ndarray, np.ndarray]]:
        """将数据划分为小批量

        Args:
            X: 特征矩阵，形状 (n_samples, n_features)
            y: 目标值，形状 (n_samples,)

        Returns:
            批量列表 [(X_batch, y_batch), ...]
        """
        n_samples = len(y)
        indices = np.random.permutation(n_samples)
        X_shuffled = X[indices]
        y_shuffled = y[indices]

        batches = []
        for start in range(0, n_samples, self.batch_size):
            end = min(start + self.batch_size, n_samples)
            X_batch = X_shuffled[start:end]
            y_batch = y_shuffled[start:end]
            batches.append((X_batch, y_batch))

        return batches

    def compute_batch_gradients(
        self,
        X_batch: np.ndarray,
        y_batch: np.ndarray,
        y_pred_batch: np.ndarray,
    ) -> Tuple[np.ndarray, float]:
        """计算小批量梯度

        Args:
            X_batch: 批量特征
            y_batch: 批量真实值
            y_pred_batch: 批量预测值

        Returns:
            (dw, db): 批量梯度
        """
        n = len(y_batch)
        error = y_pred_batch - y_batch

        dw = (2.0 / n) * (X_batch.T @ error)
        db = (2.0 / n) * np.sum(error)

        return dw, db

    def update(
        self,
        weights: np.ndarray,
        bias: float,
        dw: np.ndarray,
        db: float,
    ) -> Tuple[np.ndarray, float]:
        """更新参数

        Args:
            weights: 当前权重
            bias: 当前偏置
            dw: 权重梯度
            db: 偏置梯度

        Returns:
            (new_weights, new_bias)
        """
        new_weights = weights - self.learning_rate * dw
        new_bias = bias - self.learning_rate * db
        return new_weights, new_bias


class LearningRateScheduler:
    """学习率调度器

    在训练过程中动态调整学习率，帮助模型更好地收敛。

    支持的调度策略：
    - constant: 恒定学习率
    - step_decay: 阶梯衰减
    - exponential_decay: 指数衰减
    - cosine_annealing: 余弦退火
    """

    def __init__(
        self,
        initial_lr: float = 0.01,
        strategy: str = "constant",
        decay_rate: float = 0.5,
        decay_steps: int = 100,
        min_lr: float = 1e-6,
    ):
        """初始化学习率调度器

        Args:
            initial_lr: 初始学习率
            strategy: 调度策略，可选 'constant', 'step_decay',
                      'exponential_decay', 'cosine_annealing'
            decay_rate: 衰减率
            decay_steps: 衰减步数
            min_lr: 最小学习率
        """
        self.initial_lr = initial_lr
        self.strategy = strategy
        self.decay_rate = decay_rate
        self.decay_steps = decay_steps
        self.min_lr = min_lr

    def get_lr(self, step: int, total_steps: int = 1000) -> float:
        """获取当前步的学习率

        Args:
            step: 当前步数
            total_steps: 总步数（用于余弦退火）

        Returns:
            当前学习率
        """
        if self.strategy == "constant":
            return self.initial_lr

        elif self.strategy == "step_decay":
            # 阶梯衰减：每 decay_steps 步衰减一次
            n_decays = step // self.decay_steps
            lr = self.initial_lr * (self.decay_rate ** n_decays)
            return max(lr, self.min_lr)

        elif self.strategy == "exponential_decay":
            # 指数衰减：lr = lr0 * decay_rate^(step/decay_steps)
            lr = self.initial_lr * (self.decay_rate ** (step / self.decay_steps))
            return max(lr, self.min_lr)

        elif self.strategy == "cosine_annealing":
            # 余弦退火：lr = min_lr + 0.5*(lr0 - min_lr)*(1 + cos(pi*step/total_steps))
            lr = self.min_lr + 0.5 * (self.initial_lr - self.min_lr) * (
                1 + np.cos(np.pi * step / total_steps)
            )
            return max(lr, self.min_lr)

        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")

    def __repr__(self) -> str:
        return (
            f"LearningRateScheduler(initial_lr={self.initial_lr}, "
            f"strategy='{self.strategy}')"
        )
