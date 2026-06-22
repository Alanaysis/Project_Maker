"""损失函数模块

实现常用的损失函数，用于评估模型预测值与真实值的差异。
"""

import numpy as np
from typing import Union


class MSELoss:
    """均方误差损失函数

    MSE = (1/n) * Σ(y_pred - y_true)²

    用于回归问题，惩罚较大的误差。
    """

    @staticmethod
    def compute(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """计算 MSE 损失

        Args:
            y_true: 真实值，形状 (n_samples,)
            y_pred: 预测值，形状 (n_samples,)

        Returns:
            MSE 损失值

        Raises:
            ValueError: 当输入维度不匹配时
        """
        y_true = np.asarray(y_true).flatten()
        y_pred = np.asarray(y_pred).flatten()

        if y_true.shape != y_pred.shape:
            raise ValueError(
                f"Shape mismatch: y_true {y_true.shape} vs y_pred {y_pred.shape}"
            )

        return np.mean((y_true - y_pred) ** 2)

    @staticmethod
    def gradient(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """计算 MSE 损失的梯度

        ∂MSE/∂y_pred = (2/n) * (y_pred - y_true)

        Args:
            y_true: 真实值，形状 (n_samples,)
            y_pred: 预测值，形状 (n_samples,)

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


class MAELoss:
    """平均绝对误差损失函数

    MAE = (1/n) * Σ|y_pred - y_true|

    对异常值更鲁棒，但梯度在零点不可导。
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

        return np.mean(np.abs(y_true - y_pred))

    @staticmethod
    def gradient(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """计算 MAE 损失的梯度

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
