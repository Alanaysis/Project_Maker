"""损失函数模块

实现常用的回归损失函数，用于评估模型预测值与真实值的差异。
包含 MSE、RMSE、MAE 等经典损失函数。
"""

import numpy as np
from typing import Union


class MSELoss:
    """均方误差损失函数 (Mean Squared Error)

    MSE = (1/n) * Σ(y_pred - y_true)²

    特点：
    - 数学性质好，处处可导
    - 对大误差惩罚更重（平方效应）
    - 有唯一最优解
    - 对异常值敏感
    """

    @staticmethod
    def compute(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """计算 MSE 损失

        Args:
            y_true: 真实值，形状 (n_samples,)
            y_pred: 预测值，形状 (n_samples,)

        Returns:
            MSE 损失值（标量）

        Raises:
            ValueError: 当输入维度不匹配时
        """
        y_true = np.asarray(y_true).flatten()
        y_pred = np.asarray(y_pred).flatten()

        if y_true.shape != y_pred.shape:
            raise ValueError(
                f"Shape mismatch: y_true {y_true.shape} vs y_pred {y_pred.shape}"
            )

        return float(np.mean((y_true - y_pred) ** 2))

    @staticmethod
    def gradient(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """计算 MSE 损失对 y_pred 的梯度

        ∂MSE/∂y_pred = (2/n) * (y_pred - y_true)

        Args:
            y_true: 真实值
            y_pred: 预测值

        Returns:
            梯度值，形状 (n_samples,)
        """
        y_true = np.asarray(y_true).flatten()
        y_pred = np.asarray(y_pred).flatten()

        if y_true.shape != y_pred.shape:
            raise ValueError(
                f"Shape mismatch: y_true {y_true.shape} vs y_pred {y_pred.shape}"
            )

        n = len(y_true)
        return (2.0 / n) * (y_pred - y_true)


class RMSELoss:
    """均方根误差损失函数 (Root Mean Squared Error)

    RMSE = sqrt(MSE) = sqrt((1/n) * Σ(y_pred - y_true)²)

    特点：
    - 与目标值量纲相同，解释性好
    - 对大误差惩罚重
    """

    @staticmethod
    def compute(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """计算 RMSE 损失

        Args:
            y_true: 真实值
            y_pred: 预测值

        Returns:
            RMSE 损失值
        """
        return float(np.sqrt(MSELoss.compute(y_true, y_pred)))

    @staticmethod
    def gradient(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """计算 RMSE 对 y_pred 的梯度

        ∂RMSE/∂y_pred = (y_pred - y_true) / (n * RMSE)

        Args:
            y_true: 真实值
            y_pred: 预测值

        Returns:
            梯度值
        """
        y_true = np.asarray(y_true).flatten()
        y_pred = np.asarray(y_pred).flatten()
        n = len(y_true)
        rmse = RMSELoss.compute(y_true, y_pred)

        # 避免除以零
        if rmse < 1e-10:
            return np.zeros_like(y_pred)

        return (y_pred - y_true) / (n * rmse)


class MAELoss:
    """平均绝对误差损失函数 (Mean Absolute Error)

    MAE = (1/n) * Σ|y_pred - y_true|

    特点：
    - 对异常值鲁棒
    - 解释直观（与目标值同量纲）
    - 在零点不可导（使用 subgradient）
    """

    @staticmethod
    def compute(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """计算 MAE 损失

        Args:
            y_true: 真实值
            y_pred: 预测值

        Returns:
            MAE 损失值
        """
        y_true = np.asarray(y_true).flatten()
        y_pred = np.asarray(y_pred).flatten()

        return float(np.mean(np.abs(y_true - y_pred)))

    @staticmethod
    def gradient(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """计算 MAE 对 y_pred 的梯度（subgradient）

        ∂MAE/∂y_pred = sign(y_pred - y_true) / n

        Args:
            y_true: 真实值
            y_pred: 预测值

        Returns:
            梯度值
        """
        y_true = np.asarray(y_true).flatten()
        y_pred = np.asarray(y_pred).flatten()

        n = len(y_true)
        return np.sign(y_pred - y_true) / n
