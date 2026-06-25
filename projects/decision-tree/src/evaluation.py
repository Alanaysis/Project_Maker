"""
模型评估模块

提供分类和回归模型的评估指标。

分类指标：
- 准确率 (Accuracy)
- 精确率 (Precision)
- 召回率 (Recall)
- F1 分数

回归指标：
- 均方误差 (MSE)
- 均方根误差 (RMSE)
- 平均绝对误差 (MAE)
- R² 分数
"""

import numpy as np


def accuracy(y_true, y_pred):
    """
    计算准确率

    参数:
    ----------
    y_true : numpy.ndarray
        真实标签
    y_pred : numpy.ndarray
        预测标签

    返回:
    ----------
    accuracy : float
        准确率
    """
    if len(y_true) != len(y_pred):
        raise ValueError("真实标签和预测标签长度必须相同")

    return np.sum(y_true == y_pred) / len(y_true)


def precision(y_true, y_pred, average='macro'):
    """
    计算精确率

    参数:
    ----------
    y_true : numpy.ndarray
        真实标签
    y_pred : numpy.ndarray
        预测标签
    average : str (默认='macro')
        平均方式 ('macro', 'micro', 'weighted')

    返回:
    ----------
    precision : float
        精确率
    """
    classes = np.unique(np.concatenate([y_true, y_pred]))

    if len(classes) == 2:
        # 二分类问题
        tp = np.sum((y_true == 1) & (y_pred == 1))
        fp = np.sum((y_true == 0) & (y_pred == 1))

        if tp + fp == 0:
            return 0.0
        return tp / (tp + fp)
    else:
        # 多分类问题
        precisions = []
        for cls in classes:
            tp = np.sum((y_true == cls) & (y_pred == cls))
            fp = np.sum((y_true != cls) & (y_pred == cls))

            if tp + fp == 0:
                precisions.append(0.0)
            else:
                precisions.append(tp / (tp + fp))

        if average == 'macro':
            return np.mean(precisions)
        elif average == 'micro':
            total_tp = np.sum(y_true == y_pred)
            total_fp = np.sum(y_pred != y_true)
            return total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
        elif average == 'weighted':
            weights = [np.sum(y_true == cls) for cls in classes]
            return np.average(precisions, weights=weights)
        else:
            return precisions


def recall(y_true, y_pred, average='macro'):
    """
    计算召回率

    参数:
    ----------
    y_true : numpy.ndarray
        真实标签
    y_pred : numpy.ndarray
        预测标签
    average : str (默认='macro')
        平均方式 ('macro', 'micro', 'weighted')

    返回:
    ----------
    recall : float
        召回率
    """
    classes = np.unique(np.concatenate([y_true, y_pred]))

    if len(classes) == 2:
        # 二分类问题
        tp = np.sum((y_true == 1) & (y_pred == 1))
        fn = np.sum((y_true == 1) & (y_pred == 0))

        if tp + fn == 0:
            return 0.0
        return tp / (tp + fn)
    else:
        # 多分类问题
        recalls = []
        for cls in classes:
            tp = np.sum((y_true == cls) & (y_pred == cls))
            fn = np.sum((y_true == cls) & (y_pred != cls))

            if tp + fn == 0:
                recalls.append(0.0)
            else:
                recalls.append(tp / (tp + fn))

        if average == 'macro':
            return np.mean(recalls)
        elif average == 'micro':
            total_tp = np.sum(y_true == y_pred)
            total_fn = np.sum(y_true != y_pred)
            return total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
        elif average == 'weighted':
            weights = [np.sum(y_true == cls) for cls in classes]
            return np.average(recalls, weights=weights)
        else:
            return recalls


def f1_score(y_true, y_pred, average='macro'):
    """
    计算 F1 分数

    参数:
    ----------
    y_true : numpy.ndarray
        真实标签
    y_pred : numpy.ndarray
        预测标签
    average : str (默认='macro')
        平均方式 ('macro', 'micro', 'weighted')

    返回:
    ----------
    f1 : float
        F1 分数
    """
    p = precision(y_true, y_pred, average)
    r = recall(y_true, y_pred, average)

    if p + r == 0:
        return 0.0

    return 2 * (p * r) / (p + r)


def confusion_matrix(y_true, y_pred):
    """
    计算混淆矩阵

    参数:
    ----------
    y_true : numpy.ndarray
        真实标签
    y_pred : numpy.ndarray
        预测标签

    返回:
    ----------
    matrix : numpy.ndarray
        混淆矩阵
    """
    classes = np.unique(np.concatenate([y_true, y_pred]))
    n_classes = len(classes)
    class_to_idx = {cls: idx for idx, cls in enumerate(classes)}

    matrix = np.zeros((n_classes, n_classes), dtype=int)

    for true, pred in zip(y_true, y_pred):
        matrix[class_to_idx[true]][class_to_idx[pred]] += 1

    return matrix


def mean_squared_error(y_true, y_pred):
    """
    计算均方误差 (MSE)

    参数:
    ----------
    y_true : numpy.ndarray
        真实值
    y_pred : numpy.ndarray
        预测值

    返回:
    ----------
    mse : float
        均方误差
    """
    if len(y_true) != len(y_pred):
        raise ValueError("真实值和预测值长度必须相同")

    return np.mean((y_true - y_pred) ** 2)


def root_mean_squared_error(y_true, y_pred):
    """
    计算均方根误差 (RMSE)

    参数:
    ----------
    y_true : numpy.ndarray
        真实值
    y_pred : numpy.ndarray
        预测值

    返回:
    ----------
    rmse : float
        均方根误差
    """
    return np.sqrt(mean_squared_error(y_true, y_pred))


def mean_absolute_error(y_true, y_pred):
    """
    计算平均绝对误差 (MAE)

    参数:
    ----------
    y_true : numpy.ndarray
        真实值
    y_pred : numpy.ndarray
        预测值

    返回:
    ----------
    mae : float
        平均绝对误差
    """
    if len(y_true) != len(y_pred):
        raise ValueError("真实值和预测值长度必须相同")

    return np.mean(np.abs(y_true - y_pred))


def r2_score(y_true, y_pred):
    """
    计算 R² 分数

    R² = 1 - SS_res / SS_tot
    其中：
    - SS_res = Σ(y_true - y_pred)²
    - SS_tot = Σ(y_true - y_mean)²

    参数:
    ----------
    y_true : numpy.ndarray
        真实值
    y_pred : numpy.ndarray
        预测值

    返回:
    ----------
    r2 : float
        R² 分数
    """
    if len(y_true) != len(y_pred):
        raise ValueError("真实值和预测值长度必须相同")

    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)

    if ss_tot == 0:
        return 0.0

    return 1 - (ss_res / ss_tot)


def adjusted_r2_score(y_true, y_pred, n_features):
    """
    计算调整后的 R² 分数

    调整 R² = 1 - (1 - R²) * (n - 1) / (n - p - 1)
    其中：
    - n 是样本数
    - p 是特征数

    参数:
    ----------
    y_true : numpy.ndarray
        真实值
    y_pred : numpy.ndarray
        预测值
    n_features : int
        特征数量

    返回:
    ----------
    adjusted_r2 : float
        调整后的 R² 分数
    """
    r2 = r2_score(y_true, y_pred)
    n = len(y_true)

    if n <= n_features + 1:
        return 0.0

    return 1 - (1 - r2) * (n - 1) / (n - n_features - 1)


def explained_variance_score(y_true, y_pred):
    """
    计算解释方差分数

    解释方差 = 1 - Var(y_true - y_pred) / Var(y_true)

    参数:
    ----------
    y_true : numpy.ndarray
        真实值
    y_pred : numpy.ndarray
        预测值

    返回:
    ----------
    evs : float
        解释方差分数
    """
    if len(y_true) != len(y_pred):
        raise ValueError("真实值和预测值长度必须相同")

    var_residual = np.var(y_true - y_pred)
    var_true = np.var(y_true)

    if var_true == 0:
        return 0.0

    return 1 - var_residual / var_true
