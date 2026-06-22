import numpy as np
import random

def train_test_split(X, y, test_size=0.2, random_state=None):
    """
    将数据集划分为训练集和测试集

    参数:
    X: 特征矩阵
    y: 标签向量
    test_size: 测试集比例 (默认0.2)
    random_state: 随机种子 (默认None)

    返回:
    X_train, X_test, y_train, y_test: 划分后的数据集
    """
    if random_state is not None:
        random.seed(random_state)
        np.random.seed(random_state)

    n_samples = len(X)
    n_test = int(n_samples * test_size)
    n_train = n_samples - n_test

    # 生成随机索引
    indices = list(range(n_samples))
    random.shuffle(indices)

    train_indices = indices[:n_train]
    test_indices = indices[n_train:]

    X_train = X[train_indices]
    X_test = X[test_indices]
    y_train = y[train_indices]
    y_test = y[test_indices]

    return X_train, X_test, y_train, y_test

def accuracy_score(y_true, y_pred):
    """
    计算准确率

    参数:
    y_true: 真实标签
    y_pred: 预测标签

    返回:
    accuracy: 准确率
    """
    if len(y_true) != len(y_pred):
        raise ValueError("真实标签和预测标签长度必须相同")

    correct = np.sum(y_true == y_pred)
    total = len(y_true)

    return correct / total

def normalize(X):
    """
    数据标准化 (Z-score)

    参数:
    X: 特征矩阵

    返回:
    X_normalized: 标准化后的特征矩阵
    """
    mean = np.mean(X, axis=0)
    std = np.std(X, axis=0)

    # 避免除以零
    std[std == 0] = 1

    return (X - mean) / std

def check_input(X, y):
    """
    检查输入数据的有效性

    参数:
    X: 特征矩阵
    y: 标签向量

    返回:
    无 (如果无效则抛出异常)
    """
    if not isinstance(X, np.ndarray):
        raise TypeError("X必须是numpy数组")

    if not isinstance(y, np.ndarray):
        raise TypeError("y必须是numpy数组")

    if X.ndim != 2:
        raise ValueError("X必须是二维数组")

    if y.ndim != 1:
        raise ValueError("y必须是一维数组")

    if X.shape[0] != y.shape[0]:
        raise ValueError("X和y的样本数量必须相同")