"""
模型选择模块

实现 K 值选择和交叉验证功能，用于 KNN 模型的超参数调优。
"""

import numpy as np
from typing import Optional, List, Tuple, Union, Callable


class KFold:
    """
    K 折交叉验证

    将数据集分成 K 份，轮流使用其中一份作为验证集，
    其余 K-1 份作为训练集。

    Attributes:
        n_splits: 折数
        shuffle: 是否打乱数据
        random_state: 随机种子

    Examples:
        >>> kfold = KFold(n_splits=5, shuffle=True, random_state=42)
        >>> for train_idx, val_idx in kfold.split(X):
        ...     X_train, X_val = X[train_idx], X[val_idx]
        ...     y_train, y_val = y[train_idx], y[val_idx]
    """

    def __init__(self, n_splits: int = 5, shuffle: bool = True,
                 random_state: Optional[int] = None):
        """
        初始化 K-Fold

        Args:
            n_splits: 折数 (默认: 5)
            shuffle: 是否打乱数据 (默认: True)
            random_state: 随机种子
        """
        if n_splits < 2:
            raise ValueError("n_splits must be at least 2")

        self.n_splits = n_splits
        self.shuffle = shuffle
        self.random_state = random_state

    def split(self, X: np.ndarray) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        生成训练/验证索引对

        Args:
            X: 数据矩阵 (n_samples, n_features)

        Returns:
            splits: [(train_indices, val_indices), ...] 列表
        """
        n_samples = X.shape[0] if X.ndim == 2 else len(X)

        if n_samples < self.n_splits:
            raise ValueError(
                f"n_samples={n_samples} is less than n_splits={self.n_splits}"
            )

        # 生成索引
        indices = np.arange(n_samples)

        if self.shuffle:
            rng = np.random.RandomState(self.random_state)
            rng.shuffle(indices)

        # 计算每折大小
        fold_size = n_samples // self.n_splits
        remainder = n_samples % self.n_splits

        splits = []
        start = 0

        for i in range(self.n_splits):
            # 前 remainder 折多一个样本
            current_fold_size = fold_size + (1 if i < remainder else 0)
            end = start + current_fold_size

            val_indices = indices[start:end]
            train_indices = np.concatenate([indices[:start], indices[end:]])

            splits.append((train_indices, val_indices))
            start = end

        return splits


class CrossValidator:
    """
    交叉验证器

    提供 KNN 模型的交叉验证功能，包括：
    - K 折交叉验证
    - 留一法交叉验证
    - K 值选择

    Examples:
        >>> from src.model_selection import CrossValidator
        >>> from src.knn_classifier import KNNClassifier
        >>>
        >>> cv = CrossValidator(n_folds=5)
        >>> results = cv.cross_val_score(KNNClassifier(k=5), X, y)
        >>> print(f"平均准确率: {results['mean_score']:.4f}")
    """

    def __init__(self, n_folds: int = 5, shuffle: bool = True,
                 random_state: Optional[int] = None):
        """
        初始化交叉验证器

        Args:
            n_folds: 折数
            shuffle: 是否打乱
            random_state: 随机种子
        """
        self.n_folds = n_folds
        self.shuffle = shuffle
        self.random_state = random_state

    def cross_val_score(self, estimator, X: np.ndarray, y: np.ndarray,
                        scoring: Optional[Callable] = None) -> dict:
        """
        交叉验证评分

        Args:
            estimator: KNN 分类器或回归器（需实现 fit/predict/score）
            X: 特征矩阵 (n_samples, n_features)
            y: 标签 (n_samples,)
            scoring: 评分函数（默认使用 estimator.score）

        Returns:
            results: 包含以下字段的字典
                - scores: 各折分数
                - mean_score: 平均分数
                - std_score: 分数标准差
                - train_scores: 各折训练分数
        """
        X = np.asarray(X, dtype=float)
        y = np.asarray(y)

        kfold = KFold(
            n_splits=self.n_folds,
            shuffle=self.shuffle,
            random_state=self.random_state
        )

        splits = kfold.split(X)

        val_scores = []
        train_scores = []

        for train_idx, val_idx in splits:
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]

            # 克隆 estimator
            clone = self._clone_estimator(estimator)
            clone.fit(X_train, y_train)

            # 验证分数
            if scoring is not None:
                val_score = scoring(y_val, clone.predict(X_val))
            else:
                val_score = clone.score(X_val, y_val)
            val_scores.append(val_score)

            # 训练分数
            if scoring is not None:
                train_score = scoring(y_train, clone.predict(X_train))
            else:
                train_score = clone.score(X_train, y_train)
            train_scores.append(train_score)

        return {
            'scores': np.array(val_scores),
            'mean_score': np.mean(val_scores),
            'std_score': np.std(val_scores),
            'train_scores': np.array(train_scores),
            'mean_train_score': np.mean(train_scores)
        }

    def _clone_estimator(self, estimator):
        """克隆 estimator（简单实现）"""
        params = estimator.get_params()
        return estimator.__class__(**params)

    def select_k(self, X: np.ndarray, y: np.ndarray,
                 k_range: Optional[List[int]] = None,
                 metric: str = 'euclidean',
                 task: str = 'classification',
                 weights: str = 'uniform') -> dict:
        """
        选择最优 K 值

        通过交叉验证找到最优的 K 值。

        Args:
            X: 特征矩阵
            y: 标签
            k_range: K 值候选列表（默认: [1, 3, 5, 7, 9, 11, 13, 15]）
            metric: 距离度量
            task: 任务类型 ('classification' 或 'regression')
            weights: 权重策略

        Returns:
            results: 包含以下字段的字典
                - best_k: 最优 K 值
                - best_score: 最优分数
                - k_scores: 各 K 值的平均分数
                - k_std: 各 K 值的分数标准差
                - all_results: 各 K 值的详细结果
        """
        if k_range is None:
            k_range = [1, 3, 5, 7, 9, 11, 13, 15]

        # 验证 K 值范围
        max_k = max(k_range)
        n_train = X.shape[0] - X.shape[0] // self.n_folds
        if max_k > n_train:
            raise ValueError(
                f"Max k ({max_k}) is larger than training set size "
                f"({n_train}) in each fold"
            )

        k_scores = {}
        k_std = {}
        all_results = {}

        for k in k_range:
            if task == 'classification':
                from .knn_classifier import KNNClassifier
                estimator = KNNClassifier(k=k, metric=metric)
            else:
                from .knn_regressor import KNNRegressor
                estimator = KNNRegressor(k=k, metric=metric, weights=weights)

            results = self.cross_val_score(estimator, X, y)
            k_scores[k] = results['mean_score']
            k_std[k] = results['std_score']
            all_results[k] = results

        # 找到最优 K
        best_k = max(k_scores, key=k_scores.get)

        return {
            'best_k': best_k,
            'best_score': k_scores[best_k],
            'k_scores': k_scores,
            'k_std': k_std,
            'all_results': all_results
        }


def train_test_split(X: np.ndarray, y: np.ndarray,
                     test_size: float = 0.2,
                     random_state: Optional[int] = None) -> Tuple:
    """
    划分训练集和测试集

    Args:
        X: 特征矩阵
        y: 标签
        test_size: 测试集比例 (默认: 0.2)
        random_state: 随机种子

    Returns:
        X_train, X_test, y_train, y_test
    """
    X = np.asarray(X, dtype=float)
    y = np.asarray(y)

    n_samples = X.shape[0]
    n_test = int(n_samples * test_size)

    if n_test == 0:
        n_test = 1
    if n_test >= n_samples:
        n_test = n_samples - 1

    # 生成随机索引
    rng = np.random.RandomState(random_state)
    indices = rng.permutation(n_samples)

    test_indices = indices[:n_test]
    train_indices = indices[n_test:]

    return X[train_indices], X[test_indices], y[train_indices], y[test_indices]


def accuracy_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    计算分类准确率

    Args:
        y_true: 真实标签
        y_pred: 预测标签

    Returns:
        accuracy: 准确率
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    return float(np.mean(y_true == y_pred))


def mean_squared_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    计算均方误差

    Args:
        y_true: 真实值
        y_pred: 预测值

    Returns:
        mse: 均方误差
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.mean((y_true - y_pred) ** 2))


def r2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    计算 R^2 决定系数

    Args:
        y_true: 真实值
        y_pred: 预测值

    Returns:
        r2: R^2 决定系数
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)

    if ss_tot == 0:
        return 0.0

    return float(1 - ss_res / ss_tot)
