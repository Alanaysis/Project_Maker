"""模型评估模块

实现回归模型的常用评估指标：
- MSE (均方误差)
- RMSE (均方根误差)
- MAE (平均绝对误差)
- R² (决定系数)
"""

import numpy as np


def mean_squared_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """计算均方误差 (Mean Squared Error)

    MSE = (1/n) * Σ(y_pred - y_true)²

    特点：
    - 对大误差惩罚更重（平方效应）
    - 量纲是目标值量纲的平方
    - 范围 [0, +∞)，越小越好

    Args:
        y_true: 真实值
        y_pred: 预测值

    Returns:
        MSE 值
    """
    y_true = np.asarray(y_true).flatten()
    y_pred = np.asarray(y_pred).flatten()
    return float(np.mean((y_true - y_pred) ** 2))


def root_mean_squared_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """计算均方根误差 (Root Mean Squared Error)

    RMSE = sqrt(MSE) = sqrt((1/n) * Σ(y_pred - y_true)²)

    特点：
    - 与目标值量纲相同，解释性好
    - 对大误差惩罚重
    - 范围 [0, +∞)，越小越好

    Args:
        y_true: 真实值
        y_pred: 预测值

    Returns:
        RMSE 值
    """
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def mean_absolute_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """计算平均绝对误差 (Mean Absolute Error)

    MAE = (1/n) * Σ|y_pred - y_true|

    特点：
    - 对异常值鲁棒
    - 与目标值量纲相同
    - 范围 [0, +∞)，越小越好

    Args:
        y_true: 真实值
        y_pred: 预测值

    Returns:
        MAE 值
    """
    y_true = np.asarray(y_true).flatten()
    y_pred = np.asarray(y_pred).flatten()
    return float(np.mean(np.abs(y_true - y_pred)))


def r2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """计算 R² 分数 (决定系数, Coefficient of Determination)

    R² = 1 - SS_res / SS_tot

    其中：
    - SS_res = Σ(y_true - y_pred)²  (残差平方和)
    - SS_tot = Σ(y_true - mean(y_true))²  (总平方和)

    解读：
    - R² = 1: 完美拟合
    - R² = 0: 与均值预测一样好
    - R² < 0: 比均值预测还差
    - 范围 (-∞, 1]，越大越好

    Args:
        y_true: 真实值
        y_pred: 预测值

    Returns:
        R² 分数
    """
    y_true = np.asarray(y_true).flatten()
    y_pred = np.asarray(y_pred).flatten()

    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)

    # 避免除以零（所有真实值相同时）
    if ss_tot < 1e-10:
        return 1.0 if ss_res < 1e-10 else 0.0

    return float(1 - (ss_res / ss_tot))
