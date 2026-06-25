"""
特征工程实现

实现常用的特征工程方法：
1. 特征缩放：标准化、归一化
2. 特征选择：基于方差、基于相关性
3. 交叉验证：K折交叉验证
"""

import numpy as np
from typing import List, Tuple, Optional


class StandardScaler:
    """
    标准化缩放器

    将特征缩放到均值为0，标准差为1的分布。

    公式: z = (x - μ) / σ

    Parameters
    ----------
    Attributes
    ----------
    mean : ndarray of shape (n_features,)
        每个特征的均值
    std : ndarray of shape (n_features,)
        每个特征的标准差
    """

    def __init__(self):
        self.mean: Optional[np.ndarray] = None
        self.std: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray) -> 'StandardScaler':
        """
        计算训练数据的均值和标准差

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            训练数据

        Returns
        -------
        self
        """
        X = np.array(X)
        self.mean = np.mean(X, axis=0)
        self.std = np.std(X, axis=0)
        # 避免除零
        self.std[self.std == 0] = 1.0
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        对数据进行标准化

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            待标准化的数据

        Returns
        -------
        ndarray of shape (n_samples, n_features)
            标准化后的数据
        """
        X = np.array(X)
        return (X - self.mean) / self.std

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """
        训练并转换数据

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            训练数据

        Returns
        -------
        ndarray of shape (n_samples, n_features)
            标准化后的数据
        """
        return self.fit(X).transform(X)

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """
        将标准化数据转换回原始尺度

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            标准化的数据

        Returns
        -------
        ndarray of shape (n_samples, n_features)
            原始尺度的数据
        """
        X = np.array(X)
        return X * self.std + self.mean


class MinMaxScaler:
    """
    归一化缩放器

    将特征缩放到[0, 1]区间。

    公式: x_scaled = (x - x_min) / (x_max - x_min)

    Parameters
    ----------
    feature_range : tuple, default=(0, 1)
        目标范围

    Attributes
    ----------
    min : ndarray of shape (n_features,)
        每个特征的最小值
    max : ndarray of shape (n_features,)
        每个特征的最大值
    """

    def __init__(self, feature_range: Tuple[float, float] = (0, 1)):
        self.feature_range = feature_range
        self.min: Optional[np.ndarray] = None
        self.max: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray) -> 'MinMaxScaler':
        """
        计算训练数据的最小值和最大值

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            训练数据

        Returns
        -------
        self
        """
        X = np.array(X)
        self.min = np.min(X, axis=0)
        self.max = np.max(X, axis=0)
        # 避免除零
        self.max[self.max == self.min] = self.min[self.max == self.min] + 1.0
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        对数据进行归一化

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            待归一化的数据

        Returns
        -------
        ndarray of shape (n_samples, n_features)
            归一化后的数据
        """
        X = np.array(X)
        # 缩放到[0, 1]
        X_scaled = (X - self.min) / (self.max - self.min)

        # 如果目标范围不是[0, 1]，进行线性变换
        if self.feature_range != (0, 1):
            min_val, max_val = self.feature_range
            X_scaled = X_scaled * (max_val - min_val) + min_val

        return X_scaled

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """
        训练并转换数据

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            训练数据

        Returns
        -------
        ndarray of shape (n_samples, n_features)
            归一化后的数据
        """
        return self.fit(X).transform(X)

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """
        将归一化数据转换回原始尺度

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            归一化的数据

        Returns
        -------
        ndarray of shape (n_samples, n_features)
            原始尺度的数据
        """
        X = np.array(X)

        # 如果目标范围不是[0, 1]，先还原到[0, 1]
        if self.feature_range != (0, 1):
            min_val, max_val = self.feature_range
            X = (X - min_val) / (max_val - min_val)

        return X * (self.max - self.min) + self.min


class VarianceThreshold:
    """
    方差阈值特征选择

    移除方差低于阈值的特征。方差为0的特征是常数特征，不包含信息。

    Parameters
    ----------
    threshold : float, default=0.0
        方差阈值

    Attributes
    ----------
    variances : ndarray of shape (n_features,)
        每个特征的方差
    support : ndarray of shape (n_features,)
        布尔数组，表示哪些特征被选中
    """

    def __init__(self, threshold: float = 0.0):
        self.threshold = threshold
        self.variances: Optional[np.ndarray] = None
        self.support: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray) -> 'VarianceThreshold':
        """
        计算每个特征的方差

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            训练数据

        Returns
        -------
        self
        """
        X = np.array(X)
        self.variances = np.var(X, axis=0)
        self.support = self.variances > self.threshold
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        选择方差大于阈值的特征

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            待转换的数据

        Returns
        -------
        ndarray of shape (n_samples, n_selected_features)
            选择后的数据
        """
        X = np.array(X)
        return X[:, self.support]

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """
        训练并转换数据

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            训练数据

        Returns
        -------
        ndarray of shape (n_samples, n_selected_features)
            选择后的数据
        """
        return self.fit(X).transform(X)

    def get_support(self) -> np.ndarray:
        """
        获取被选中的特征索引

        Returns
        -------
        ndarray of shape (n_selected_features,)
            被选中特征的索引
        """
        return np.where(self.support)[0]


class CorrelationThreshold:
    """
    相关性阈值特征选择

    移除与其他特征高度相关的特征，减少冗余。

    Parameters
    ----------
    threshold : float, default=0.95
        相关性阈值

    Attributes
    ----------
    correlation_matrix : ndarray of shape (n_features, n_features)
        相关性矩阵
    support : ndarray of shape (n_features,)
        布尔数组，表示哪些特征被选中
    """

    def __init__(self, threshold: float = 0.95):
        self.threshold = threshold
        self.correlation_matrix: Optional[np.ndarray] = None
        self.support: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray) -> 'CorrelationThreshold':
        """
        计算特征相关性并选择特征

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            训练数据

        Returns
        -------
        self
        """
        X = np.array(X)
        n_features = X.shape[1]

        # 计算相关性矩阵
        self.correlation_matrix = np.abs(np.corrcoef(X.T))

        # 选择特征
        self.support = np.ones(n_features, dtype=bool)

        for i in range(n_features):
            if not self.support[i]:
                continue
            for j in range(i + 1, n_features):
                if not self.support[j]:
                    continue
                # 如果相关性高于阈值，移除后面的特征
                if self.correlation_matrix[i, j] > self.threshold:
                    self.support[j] = False

        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        选择不相关的特征

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            待转换的数据

        Returns
        -------
        ndarray of shape (n_samples, n_selected_features)
            选择后的数据
        """
        X = np.array(X)
        return X[:, self.support]

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """
        训练并转换数据

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            训练数据

        Returns
        -------
        ndarray of shape (n_samples, n_selected_features)
            选择后的数据
        """
        return self.fit(X).transform(X)

    def get_support(self) -> np.ndarray:
        """
        获取被选中的特征索引

        Returns
        -------
        ndarray of shape (n_selected_features,)
            被选中特征的索引
        """
        return np.where(self.support)[0]


def cross_validate(
    model,
    X: np.ndarray,
    y: np.ndarray,
    cv: int = 5,
    scoring: str = 'accuracy'
) -> np.ndarray:
    """
    K折交叉验证

    将数据分成K折，轮流使用其中一折作为验证集，其余作为训练集。

    Parameters
    ----------
    model : object
        模型对象，需要有fit和predict方法
    X : ndarray of shape (n_samples, n_features)
        训练数据特征
    y : ndarray of shape (n_samples,)
        训练数据标签
    cv : int, default=5
        折数
    scoring : str, default='accuracy'
        评估指标

    Returns
    -------
    ndarray of shape (cv,)
        每折的评估分数
    """
    X = np.array(X)
    y = np.array(y)
    n_samples = len(X)

    # 创建索引并打乱
    indices = np.arange(n_samples)
    np.random.shuffle(indices)

    # 计算每折的大小
    fold_size = n_samples // cv
    scores = []

    for i in range(cv):
        # 划分验证集和训练集
        val_start = i * fold_size
        val_end = val_start + fold_size if i < cv - 1 else n_samples

        val_indices = indices[val_start:val_end]
        train_indices = np.concatenate([indices[:val_start], indices[val_end:]])

        X_train, X_val = X[train_indices], X[val_indices]
        y_train, y_val = y[train_indices], y[val_indices]

        # 训练模型
        from copy import deepcopy
        model_copy = deepcopy(model)
        model_copy.fit(X_train, y_train)

        # 评估
        y_pred = model_copy.predict(X_val)

        if scoring == 'accuracy':
            score = np.mean(y_pred == y_val)
        elif scoring == 'precision':
            from .metrics import precision_score
            score = precision_score(y_val, y_pred)
        elif scoring == 'recall':
            from .metrics import recall_score
            score = recall_score(y_val, y_pred)
        elif scoring == 'f1':
            from .metrics import f1_score
            score = f1_score(y_val, y_pred)
        else:
            raise ValueError(f"Unknown scoring: {scoring}")

        scores.append(score)

    return np.array(scores)


def train_test_split(
    X: np.ndarray,
    y: np.ndarray,
    test_size: float = 0.2,
    random_state: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    划分训练集和测试集

    Parameters
    ----------
    X : ndarray of shape (n_samples, n_features)
        特征数据
    y : ndarray of shape (n_samples,)
        标签数据
    test_size : float, default=0.2
        测试集比例
    random_state : int, optional
        随机种子

    Returns
    -------
    X_train : ndarray
        训练集特征
    X_test : ndarray
        测试集特征
    y_train : ndarray
        训练集标签
    y_test : ndarray
        测试集标签
    """
    X = np.array(X)
    y = np.array(y)
    n_samples = len(X)

    if random_state is not None:
        np.random.seed(random_state)

    # 创建索引并打乱
    indices = np.arange(n_samples)
    np.random.shuffle(indices)

    # 计算测试集大小
    test_count = int(n_samples * test_size)

    # 划分
    test_indices = indices[:test_count]
    train_indices = indices[test_count:]

    X_train, X_test = X[train_indices], X[test_indices]
    y_train, y_test = y[train_indices], y[test_indices]

    return X_train, X_test, y_train, y_test
