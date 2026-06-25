"""特征工程模块

实现常用的特征工程技术：
- 特征缩放（标准化、归一化）
- 多项式特征
- 特征选择
- 交叉验证
"""

import numpy as np
from typing import Tuple, List, Optional


class StandardScaler:
    """标准化缩放器 (Z-Score Normalization)

    将特征缩放到均值为 0、标准差为 1 的分布。

    公式：x_scaled = (x - mean) / std

    适用场景：
    - 特征量纲不同
    - 使用基于距离的算法
    - 梯度下降收敛更快
    """

    def __init__(self):
        self.mean_: Optional[np.ndarray] = None
        self.std_: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray) -> "StandardScaler":
        """计算均值和标准差

        Args:
            X: 特征矩阵，形状 (n_samples, n_features)

        Returns:
            self
        """
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        self.mean_ = np.mean(X, axis=0)
        self.std_ = np.std(X, axis=0)
        # 避免除以零
        self.std_[self.std_ < 1e-10] = 1.0
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """应用标准化

        Args:
            X: 特征矩阵

        Returns:
            标准化后的特征矩阵
        """
        if self.mean_ is None:
            raise RuntimeError("Must call fit before transform")
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        return (X - self.mean_) / self.std_

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """拟合并转换

        Args:
            X: 特征矩阵

        Returns:
            标准化后的特征矩阵
        """
        return self.fit(X).transform(X)

    def inverse_transform(self, X_scaled: np.ndarray) -> np.ndarray:
        """逆转换，将标准化数据恢复为原始数据

        Args:
            X_scaled: 标准化后的特征矩阵

        Returns:
            原始尺度的特征矩阵
        """
        if self.mean_ is None:
            raise RuntimeError("Must call fit before inverse_transform")
        X_scaled = np.asarray(X_scaled, dtype=float)
        if X_scaled.ndim == 1:
            X_scaled = X_scaled.reshape(-1, 1)
        return X_scaled * self.std_ + self.mean_


class MinMaxScaler:
    """归一化缩放器 (Min-Max Normalization)

    将特征缩放到 [0, 1] 范围。

    公式：x_scaled = (x - min) / (max - min)

    适用场景：
    - 需要特征在固定范围内
    - 神经网络输入
    - 图像像素值归一化
    """

    def __init__(self, feature_range: Tuple[float, float] = (0.0, 1.0)):
        self.feature_range = feature_range
        self.min_: Optional[np.ndarray] = None
        self.max_: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray) -> "MinMaxScaler":
        """计算最小值和最大值

        Args:
            X: 特征矩阵

        Returns:
            self
        """
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        self.min_ = np.min(X, axis=0)
        self.max_ = np.max(X, axis=0)
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """应用归一化

        Args:
            X: 特征矩阵

        Returns:
            归一化后的特征矩阵
        """
        if self.min_ is None:
            raise RuntimeError("Must call fit before transform")
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        range_ = self.max_ - self.min_
        range_[range_ < 1e-10] = 1.0  # 避免除以零

        X_scaled = (X - self.min_) / range_

        # 缩放到指定范围
        low, high = self.feature_range
        X_scaled = X_scaled * (high - low) + low

        return X_scaled

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """拟合并转换"""
        return self.fit(X).transform(X)

    def inverse_transform(self, X_scaled: np.ndarray) -> np.ndarray:
        """逆转换"""
        if self.min_ is None:
            raise RuntimeError("Must call fit before inverse_transform")
        X_scaled = np.asarray(X_scaled, dtype=float)
        if X_scaled.ndim == 1:
            X_scaled = X_scaled.reshape(-1, 1)

        low, high = self.feature_range
        range_ = self.max_ - self.min_
        range_[range_ < 1e-10] = 1.0

        X_original = ((X_scaled - low) / (high - low)) * range_ + self.min_
        return X_original


class PolynomialFeatures:
    """多项式特征生成器

    将原始特征扩展为多项式特征，用于拟合非线性关系。

    例如，对于特征 [x1, x2]，degree=2 时生成：
    [1, x1, x2, x1², x1*x2, x2²]

    适用场景：
    - 数据存在非线性关系
    - 使用线性模型拟合非线性数据
    """

    def __init__(self, degree: int = 2, include_bias: bool = False):
        """初始化多项式特征生成器

        Args:
            degree: 多项式阶数
            include_bias: 是否包含常数项（全 1 列）
        """
        self.degree = degree
        self.include_bias = include_bias

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """生成多项式特征

        Args:
            X: 原始特征矩阵，形状 (n_samples, n_features)

        Returns:
            多项式特征矩阵
        """
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        n_samples, n_features = X.shape
        features = []

        if self.include_bias:
            features.append(np.ones((n_samples, 1)))

        # 添加原始特征
        features.append(X)

        # 添加高阶特征
        for d in range(2, self.degree + 1):
            # 对每个特征取 d 次幂
            for i in range(n_features):
                features.append((X[:, i] ** d).reshape(-1, 1))

            # 交叉项
            if n_features > 1 and d == 2:
                for i in range(n_features):
                    for j in range(i + 1, n_features):
                        cross = (X[:, i] * X[:, j]).reshape(-1, 1)
                        features.append(cross)

        return np.hstack(features)

    def get_feature_names(self, n_features: int) -> List[str]:
        """获取生成的特征名称

        Args:
            n_features: 原始特征数量

        Returns:
            特征名称列表
        """
        names = []
        if self.include_bias:
            names.append("1")

        for i in range(n_features):
            names.append(f"x{i}")

        for d in range(2, self.degree + 1):
            for i in range(n_features):
                names.append(f"x{i}^{d}")

            if n_features > 1 and d == 2:
                for i in range(n_features):
                    for j in range(i + 1, n_features):
                        names.append(f"x{i}*x{j}")

        return names


class FeatureSelector:
    """特征选择器

    基于方差或相关性进行特征选择。

    方法：
    - variance_threshold: 移除低方差特征
    - correlation: 选择与目标相关性高的特征
    """

    @staticmethod
    def variance_threshold(
        X: np.ndarray, threshold: float = 0.0
    ) -> Tuple[np.ndarray, np.ndarray]:
        """基于方差的特征选择

        移除方差低于阈值的特征（方差低 = 信息量少）。

        Args:
            X: 特征矩阵
            threshold: 方差阈值

        Returns:
            (X_selected, selected_indices): 选中的特征和索引
        """
        X = np.asarray(X, dtype=float)
        variances = np.var(X, axis=0)
        mask = variances > threshold
        indices = np.where(mask)[0]
        return X[:, mask], indices

    @staticmethod
    def correlation_selection(
        X: np.ndarray,
        y: np.ndarray,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """基于相关性的特征选择

        选择与目标变量相关性最高的特征。

        Args:
            X: 特征矩阵
            y: 目标变量
            top_k: 选择前 k 个特征
            threshold: 相关性阈值

        Returns:
            (X_selected, selected_indices)
        """
        X = np.asarray(X, dtype=float)
        y = np.asarray(y).flatten()
        n_features = X.shape[1]

        # 计算每个特征与目标的相关系数
        correlations = np.zeros(n_features)
        for i in range(n_features):
            correlations[i] = np.abs(np.corrcoef(X[:, i], y)[0, 1])

        # 处理 NaN（常数特征）
        correlations = np.nan_to_num(correlations, nan=0.0)

        if threshold is not None:
            mask = correlations > threshold
            indices = np.where(mask)[0]
        elif top_k is not None:
            indices = np.argsort(correlations)[::-1][:top_k]
        else:
            indices = np.arange(n_features)

        return X[:, indices], indices

    @staticmethod
    def rfe_ranking(
        X: np.ndarray,
        y: np.ndarray,
        n_features_to_select: int = 1,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """递归特征消除 (简化版)

        通过迭代移除最不重要的特征来进行特征选择。
        使用权重绝对值作为重要性度量。

        Args:
            X: 特征矩阵
            y: 目标变量
            n_features_to_select: 要选择的特征数量

        Returns:
            (ranking, selected_indices): 排名和选中特征索引
        """
        X = np.asarray(X, dtype=float)
        y = np.asarray(y).flatten()

        n_features = X.shape[1]
        ranking = np.zeros(n_features, dtype=int)
        current_features = list(range(n_features))
        current_rank = n_features

        while len(current_features) > n_features_to_select:
            # 使用正规方程拟合
            X_curr = X[:, current_features]
            try:
                weights = np.linalg.lstsq(X_curr, y, rcond=None)[0]
            except np.linalg.LinAlgError:
                break

            # 找到最不重要的特征（权重绝对值最小）
            importance = np.abs(weights)
            min_idx = np.argmin(importance)
            eliminated = current_features[min_idx]

            # 记录排名
            ranking[eliminated] = current_rank
            current_rank -= 1

            # 移除该特征
            current_features.pop(min_idx)

        # 剩余特征排名为 1
        for idx in current_features:
            ranking[idx] = 1

        return ranking, np.array(current_features)


def cross_validation(
    X: np.ndarray,
    y: np.ndarray,
    model_class: type,
    model_params: dict,
    n_folds: int = 5,
    metric: str = "mse",
) -> dict:
    """K 折交叉验证

    将数据分成 K 份，轮流用 K-1 份训练、1 份验证，
    评估模型的泛化能力。

    Args:
        X: 特征矩阵
        y: 目标变量
        model_class: 模型类
        model_params: 模型参数
        n_folds: 折数
        metric: 评估指标，可选 'mse', 'rmse', 'mae', 'r2'

    Returns:
        包含各折分数和统计信息的字典
    """
    X = np.asarray(X, dtype=float)
    y = np.asarray(y).flatten()
    n_samples = len(y)

    # 打乱数据
    indices = np.random.permutation(n_samples)
    fold_size = n_samples // n_folds

    scores = []

    for fold in range(n_folds):
        # 划分验证集和训练集
        val_start = fold * fold_size
        val_end = val_start + fold_size if fold < n_folds - 1 else n_samples

        val_indices = indices[val_start:val_end]
        train_indices = np.concatenate([indices[:val_start], indices[val_end:]])

        X_train, X_val = X[train_indices], X[val_indices]
        y_train, y_val = y[train_indices], y[val_indices]

        # 训练模型
        model = model_class(**model_params)
        model.fit(X_train, y_train)

        # 预测
        y_pred = model.predict(X_val)

        # 计算指标
        if metric == "mse":
            score = mean_squared_error(y_val, y_pred)
        elif metric == "rmse":
            score = root_mean_squared_error(y_val, y_pred)
        elif metric == "mae":
            score = mean_absolute_error(y_val, y_pred)
        elif metric == "r2":
            score = r2_score(y_val, y_pred)
        else:
            raise ValueError(f"Unknown metric: {metric}")

        scores.append(score)

    scores = np.array(scores)

    return {
        "scores": scores,
        "mean": float(np.mean(scores)),
        "std": float(np.std(scores)),
        "min": float(np.min(scores)),
        "max": float(np.max(scores)),
    }


# 导入评估函数用于交叉验证
from .evaluation import mean_squared_error, root_mean_squared_error
from .evaluation import mean_absolute_error, r2_score
