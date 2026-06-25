"""
模型评估指标模块

提供分类和回归任务的常用评估指标，仅依赖 NumPy 实现。
"""

import numpy as np


def accuracy_score(y_true, y_pred):
    """
    计算分类准确率（Accuracy）。

    准确率 = 正确预测的样本数 / 总样本数

    参数:
        y_true: array-like, 真实标签
        y_pred: array-like, 预测标签

    返回:
        float, 准确率，取值范围 [0, 1]
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    if y_true.shape[0] != y_pred.shape[0]:
        raise ValueError("y_true 和 y_pred 的样本数必须一致")
    return np.sum(y_true == y_pred) / y_true.shape[0]


def _binary_confusion_counts(y_true, y_pred, positive_label=1):
    """
    计算二分类的 TP、FP、FN、TN。

    参数:
        y_true: array-like, 真实标签
        y_pred: array-like, 预测标签
        positive_label: 正类标签，默认为 1

    返回:
        tuple, (tp, fp, fn, tn)
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    tp = np.sum((y_pred == positive_label) & (y_true == positive_label))
    fp = np.sum((y_pred == positive_label) & (y_true != positive_label))
    fn = np.sum((y_pred != positive_label) & (y_true == positive_label))
    tn = np.sum((y_pred != positive_label) & (y_true != positive_label))
    return tp, fp, fn, tn


def precision_score(y_true, y_pred, average='binary'):
    """
    计算精确率（Precision）。

    粆确率 = TP / (TP + FP)，即预测为正类的样本中真正为正类的比例。

    参数:
        y_true: array-like, 真实标签
        y_pred: array-like, 预测标签
        average: str, 多分类平均方式
            - 'binary': 二分类模式，将正类（默认为1）视为正类
            - 'micro': 微平均，汇总所有类的 TP、FP 后计算
            - 'macro': 宏平均，先计算每个类的精确率再取平均

    返回:
        float, 精确率
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if average == 'binary':
        tp, fp, fn, tn = _binary_confusion_counts(y_true, y_pred)
        if tp + fp == 0:
            return 0.0
        return tp / (tp + fp)

    classes = np.unique(np.concatenate([y_true, y_pred]))

    if average == 'micro':
        total_tp = 0
        total_fp = 0
        for c in classes:
            tp, fp, fn, tn = _binary_confusion_counts(y_true, y_pred, positive_label=c)
            total_tp += tp
            total_fp += fp
        if total_tp + total_fp == 0:
            return 0.0
        return total_tp / (total_tp + total_fp)

    if average == 'macro':
        precisions = []
        for c in classes:
            tp, fp, fn, tn = _binary_confusion_counts(y_true, y_pred, positive_label=c)
            if tp + fp == 0:
                precisions.append(0.0)
            else:
                precisions.append(tp / (tp + fp))
        return np.mean(precisions)

    raise ValueError(f"不支持的 average 参数: '{average}'，可选 'binary', 'micro', 'macro'")


def recall_score(y_true, y_pred, average='binary'):
    """
    计算召回率（Recall）。

    召回率 = TP / (TP + FN)，即真正为正类的样本中被正确预测的比例。

    参数:
        y_true: array-like, 真实标签
        y_pred: array-like, 预测标签
        average: str, 多分类平均方式
            - 'binary': 二分类模式，将正类（默认为1）视为正类
            - 'micro': 微平均，汇总所有类的 TP、FN 后计算
            - 'macro': 宏平均，先计算每个类的召回率再取平均

    返回:
        float, 召回率
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if average == 'binary':
        tp, fp, fn, tn = _binary_confusion_counts(y_true, y_pred)
        if tp + fn == 0:
            return 0.0
        return tp / (tp + fn)

    classes = np.unique(np.concatenate([y_true, y_pred]))

    if average == 'micro':
        total_tp = 0
        total_fn = 0
        for c in classes:
            tp, fp, fn, tn = _binary_confusion_counts(y_true, y_pred, positive_label=c)
            total_tp += tp
            total_fn += fn
        if total_tp + total_fn == 0:
            return 0.0
        return total_tp / (total_tp + total_fn)

    if average == 'macro':
        recalls = []
        for c in classes:
            tp, fp, fn, tn = _binary_confusion_counts(y_true, y_pred, positive_label=c)
            if tp + fn == 0:
                recalls.append(0.0)
            else:
                recalls.append(tp / (tp + fn))
        return np.mean(recalls)

    raise ValueError(f"不支持的 average 参数: '{average}'，可选 'binary', 'micro', 'macro'")


def f1_score(y_true, y_pred, average='binary'):
    """
    计算 F1 分数。

    F1 = 2 * (Precision * Recall) / (Precision + Recall)，是精确率和召回率的调和平均。

    参数:
        y_true: array-like, 真实标签
        y_pred: array-like, 预测标签
        average: str, 多分类平均方式
            - 'binary': 二分类模式
            - 'micro': 微平均（等价于准确率）
            - 'macro': 宏平均，先计算每个类的 F1 再取平均

    返回:
        float, F1 分数
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if average == 'binary':
        p = precision_score(y_true, y_pred, average='binary')
        r = recall_score(y_true, y_pred, average='binary')
        if p + r == 0:
            return 0.0
        return 2 * p * r / (p + r)

    classes = np.unique(np.concatenate([y_true, y_pred]))

    if average == 'micro':
        p = precision_score(y_true, y_pred, average='micro')
        r = recall_score(y_true, y_pred, average='micro')
        if p + r == 0:
            return 0.0
        return 2 * p * r / (p + r)

    if average == 'macro':
        f1s = []
        for c in classes:
            p = precision_score(y_true, y_pred, average='binary') if len(classes) == 2 else 0
            tp, fp, fn, tn = _binary_confusion_counts(y_true, y_pred, positive_label=c)
            p_c = tp / (tp + fp) if tp + fp > 0 else 0.0
            r_c = tp / (tp + fn) if tp + fn > 0 else 0.0
            if p_c + r_c == 0:
                f1s.append(0.0)
            else:
                f1s.append(2 * p_c * r_c / (p_c + r_c))
        return np.mean(f1s)

    raise ValueError(f"不支持的 average 参数: '{average}'，可选 'binary', 'micro', 'macro'")


def confusion_matrix(y_true, y_pred):
    """
    计算混淆矩阵。

    混淆矩阵的行表示真实标签，列表示预测标签。
    矩阵元素 C[i][j] 表示真实类别为 i 且被预测为 j 的样本数。
    支持任意数量的类别。

    参数:
        y_true: array-like, 真实标签
        y_pred: array-like, 预测标签

    返回:
        np.ndarray, 形状为 (n_classes, n_classes) 的混淆矩阵
        标签按升序排列对应矩阵的行列索引
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    if y_true.shape[0] != y_pred.shape[0]:
        raise ValueError("y_true 和 y_pred 的样本数必须一致")

    classes = np.unique(np.concatenate([y_true, y_pred]))
    n_classes = len(classes)
    class_to_idx = {c: i for i, c in enumerate(classes)}

    matrix = np.zeros((n_classes, n_classes), dtype=np.int64)
    for true, pred in zip(y_true, y_pred):
        matrix[class_to_idx[true], class_to_idx[pred]] += 1

    return matrix


def mean_squared_error(y_true, y_pred):
    """
    计算均方误差（MSE）。

    MSE = (1/n) * Σ(y_true - y_pred)^2

    参数:
        y_true: array-like, 真实值
        y_pred: array-like, 预测值

    返回:
        float, 均方误差
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)
    if y_true.shape[0] != y_pred.shape[0]:
        raise ValueError("y_true 和 y_pred 的样本数必须一致")
    return np.mean((y_true - y_pred) ** 2)


def r2_score(y_true, y_pred):
    """
    计算决定系数（R-squared）。

    R^2 = 1 - SS_res / SS_tot
    其中 SS_res = Σ(y_true - y_pred)^2，SS_tot = Σ(y_true - mean(y_true))^2

    R^2 越接近 1 表示模型拟合越好；等于 0 表示模型等价于预测均值；
    小于 0 表示模型比简单预测均值还差。

    参数:
        y_true: array-like, 真实值
        y_pred: array-like, 预测值

    返回:
        float, R^2 分数
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)
    if y_true.shape[0] != y_pred.shape[0]:
        raise ValueError("y_true 和 y_pred 的样本数必须一致")

    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return 0.0
    return 1 - ss_res / ss_tot


def mean_absolute_error(y_true, y_pred):
    """
    计算平均绝对误差（MAE）。

    MAE = (1/n) * Σ|y_true - y_pred|

    参数:
        y_true: array-like, 真实值
        y_pred: array-like, 预测值

    返回:
        float, 平均绝对误差
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)
    if y_true.shape[0] != y_pred.shape[0]:
        raise ValueError("y_true 和 y_pred 的样本数必须一致")
    return np.mean(np.abs(y_true - y_pred))
