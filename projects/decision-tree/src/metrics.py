import numpy as np

def confusion_matrix(y_true, y_pred):
    """
    计算混淆矩阵

    参数:
    y_true: 真实标签
    y_pred: 预测标签

    返回:
    matrix: 混淆矩阵
    """
    classes = np.unique(np.concatenate([y_true, y_pred]))
    n_classes = len(classes)

    # 创建类别到索引的映射
    class_to_idx = {cls: idx for idx, cls in enumerate(classes)}

    matrix = np.zeros((n_classes, n_classes), dtype=int)

    for true, pred in zip(y_true, y_pred):
        matrix[class_to_idx[true]][class_to_idx[pred]] += 1

    return matrix

def precision_score(y_true, y_pred, average='macro'):
    """
    计算精确率

    参数:
    y_true: 真实标签
    y_pred: 预测标签
    average: 平均方式 ('macro', 'micro', 'weighted')

    返回:
    precision: 精确率
    """
    classes = np.unique(np.concatenate([y_true, y_pred]))
    n_classes = len(classes)

    if n_classes == 2:
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

def recall_score(y_true, y_pred, average='macro'):
    """
    计算召回率

    参数:
    y_true: 真实标签
    y_pred: 预测标签
    average: 平均方式 ('macro', 'micro', 'weighted')

    返回:
    recall: 召回率
    """
    classes = np.unique(np.concatenate([y_true, y_pred]))
    n_classes = len(classes)

    if n_classes == 2:
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
    计算F1分数

    参数:
    y_true: 真实标签
    y_pred: 预测标签
    average: 平均方式 ('macro', 'micro', 'weighted')

    返回:
    f1: F1分数
    """
    precision = precision_score(y_true, y_pred, average)
    recall = recall_score(y_true, y_pred, average)

    if precision + recall == 0:
        return 0.0

    return 2 * (precision * recall) / (precision + recall)