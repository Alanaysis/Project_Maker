"""
分类评估指标

实现常用的二分类评估指标：
- 准确率 (Accuracy)
- 精确率 (Precision)
- 召回率 (Recall)
- F1分数
- 混淆矩阵
"""

import numpy as np
from typing import Tuple


def confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[int, int, int, int]:
    """
    计算混淆矩阵

    混淆矩阵结构：
                    预测
                 0    1
    实际  0  [ TN | FP ]
          1  [ FN | TP ]

    Parameters
    ----------
    y_true : ndarray
        真实标签
    y_pred : ndarray
        预测标签

    Returns
    -------
    tn : int
        True Negative - 真负例数
    fp : int
        False Positive - 假正例数（误报）
    fn : int
        False Negative - 假负例数（漏报）
    tp : int
        True Positive - 真正例数
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    tp = np.sum((y_true == 1) & (y_pred == 1))
    tn = np.sum((y_true == 0) & (y_pred == 0))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))

    return tn, fp, fn, tp


def accuracy_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    准确率：正确预测的比例

    公式: Accuracy = (TP + TN) / (TP + TN + FP + FN)

    Parameters
    ----------
    y_true : ndarray
        真实标签
    y_pred : ndarray
        预测标签

    Returns
    -------
    float
        准确率
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    return np.mean(y_true == y_pred)


def precision_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    精确率：预测为正的样本中实际为正的比例

    公式: Precision = TP / (TP + FP)

    含义：在所有预测为正类的样本中，有多少真的是正类

    Parameters
    ----------
    y_true : ndarray
        真实标签
    y_pred : ndarray
        预测标签

    Returns
    -------
    float
        精确率
    """
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred)
    if tp + fp == 0:
        return 0.0
    return tp / (tp + fp)


def recall_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    召回率：实际为正的样本中被正确预测的比例

    公式: Recall = TP / (TP + FN)

    含义：在所有实际为正类的样本中，有多少被正确识别出来

    Parameters
    ----------
    y_true : ndarray
        真实标签
    y_pred : ndarray
        预测标签

    Returns
    -------
    float
        召回率
    """
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred)
    if tp + fn == 0:
        return 0.0
    return tp / (tp + fn)


def f1_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    F1分数：精确率和召回率的调和平均数

    公式: F1 = 2 * (Precision * Recall) / (Precision + Recall)

    含义：综合考虑精确率和召回率的平衡指标

    Parameters
    ----------
    y_true : ndarray
        真实标签
    y_pred : ndarray
        预测标签

    Returns
    -------
    float
        F1分数
    """
    p = precision_score(y_true, y_pred)
    r = recall_score(y_true, y_pred)
    if p + r == 0:
        return 0.0
    return 2 * (p * r) / (p + r)


def classification_report(y_true: np.ndarray, y_pred: np.ndarray) -> str:
    """
    生成分类报告

    Parameters
    ----------
    y_true : ndarray
        真实标签
    y_pred : ndarray
        预测标签

    Returns
    -------
    str
        格式化的分类报告
    """
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred)
    rec = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred)

    report = f"""
分类评估报告
{'='*40}
准确率 (Accuracy):  {acc:.4f}
精确率 (Precision): {prec:.4f}
召回率 (Recall):    {rec:.4f}
F1分数 (F1 Score):  {f1:.4f}

混淆矩阵:
{'='*40}
              预测为0  预测为1
  实际为0      {tn:4d}    {fp:4d}
  实际为1      {fn:4d}    {tp:4d}
"""
    return report
