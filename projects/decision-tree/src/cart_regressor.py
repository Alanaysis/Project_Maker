"""
CART 回归决策树算法实现

CART 回归版本使用方差减少 (Variance Reduction) 作为特征选择的标准。

方差减少 = 父节点方差 - 子节点的加权平均方差

CART 回归的特点：
- 二叉树结构
- 叶节点输出为连续值（均值）
- 使用方差减少作为分裂标准
- 支持后剪枝

方差计算：
Var(D) = (1/|D|) * Σ(yi - y_mean)^2
"""

import numpy as np


class CARTRegressorNode:
    """CART 回归树节点"""

    def __init__(self, feature_index=None, threshold=None, left=None, right=None,
                 value=None, n_samples=None, variance=None):
        """
        初始化节点

        参数:
        feature_index: 分裂特征索引
        threshold: 分裂阈值
        left: 左子树 (<= threshold)
        right: 右子树 (> threshold)
        value: 叶节点的预测值（均值）
        n_samples: 节点中的样本数
        variance: 节点的方差
        """
        self.feature_index = feature_index
        self.threshold = threshold
        self.left = left
        self.right = right
        self.value = value
        self.n_samples = n_samples
        self.variance = variance

    def is_leaf(self):
        """判断是否为叶节点"""
        return self.value is not None


class CARTRegressor:
    """
    CART 回归决策树

    使用方差减少作为特征选择标准，生成二叉树结构。

    参数:
    ----------
    max_depth : int, optional (默认=None)
        树的最大深度，None 表示不限制
    min_samples_split : int (默认=2)
        节点分裂所需的最小样本数
    min_samples_leaf : int (默认=1)
        叶节点所需的最小样本数

    属性:
    ----------
    root : CARTRegressorNode
        决策树的根节点
    n_features : int
        特征数量
    feature_importances_ : array
        特征重要性

    示例:
    ----------
    >>> from cart_regressor import CARTRegressor
    >>> import numpy as np
    >>> X = np.array([[1], [2], [3], [4], [5]])
    >>> y = np.array([1.5, 2.5, 3.5, 4.5, 5.5])
    >>> tree = CARTRegressor(max_depth=3)
    >>> tree.fit(X, y)
    >>> predictions = tree.predict(X)
    """

    def __init__(self, max_depth=None, min_samples_split=2, min_samples_leaf=1):
        """
        初始化 CART 回归决策树

        参数:
        max_depth: 最大深度 (默认None，表示不限制)
        min_samples_split: 最小分裂样本数 (默认2)
        min_samples_leaf: 最小叶节点样本数 (默认1)
        """
        self.root = None
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.n_features = None
        self.feature_importances_ = None

    def fit(self, X, y):
        """
        训练 CART 回归决策树

        参数:
        X: 特征矩阵 (n_samples, n_features)
        y: 目标向量 (n_samples,)

        返回:
        self: 训练后的模型
        """
        # 输入验证
        if X.ndim != 2:
            raise ValueError("X 必须是二维数组")
        if y.ndim != 1:
            raise ValueError("y 必须是一维数组")
        if X.shape[0] != y.shape[0]:
            raise ValueError("X 和 y 的样本数量必须相同")

        self.n_features = X.shape[1]

        # 初始化特征重要性
        self.feature_importances_ = np.zeros(self.n_features)

        # 递归构建决策树
        self.root = self._build_tree(X, y, depth=0)

        # 归一化特征重要性
        total = np.sum(self.feature_importances_)
        if total > 0:
            self.feature_importances_ /= total

        return self

    def _build_tree(self, X, y, depth=0):
        """
        递归构建决策树

        参数:
        X: 特征矩阵
        y: 目标向量
        depth: 当前深度

        返回:
        node: 构建好的节点
        """
        n_samples, n_features = X.shape

        # 计算当前节点的方差
        current_variance = self._variance(y)

        # 停止条件
        if (self.max_depth is not None and depth >= self.max_depth) or \
           n_samples < self.min_samples_split or \
           current_variance == 0:
            return CARTRegressorNode(
                value=np.mean(y),
                n_samples=n_samples,
                variance=current_variance
            )

        # 寻找最佳分裂
        best_feature, best_threshold, best_gain = self._find_best_split(X, y)

        if best_feature is None:
            return CARTRegressorNode(
                value=np.mean(y),
                n_samples=n_samples,
                variance=current_variance
            )

        # 记录特征重要性
        self.feature_importances_[best_feature] += best_gain * n_samples

        # 根据最佳特征和阈值分裂数据集
        left_indices = X[:, best_feature] <= best_threshold
        right_indices = ~left_indices

        # 检查分裂后的样本数
        if np.sum(left_indices) < self.min_samples_leaf or \
           np.sum(right_indices) < self.min_samples_leaf:
            return CARTRegressorNode(
                value=np.mean(y),
                n_samples=n_samples,
                variance=current_variance
            )

        # 递归构建左右子树
        left_subtree = self._build_tree(X[left_indices], y[left_indices], depth + 1)
        right_subtree = self._build_tree(X[right_indices], y[right_indices], depth + 1)

        return CARTRegressorNode(
            feature_index=best_feature,
            threshold=best_threshold,
            left=left_subtree,
            right=right_subtree,
            n_samples=n_samples,
            variance=current_variance
        )

    def _find_best_split(self, X, y):
        """
        寻找最佳分裂特征和阈值

        参数:
        X: 特征矩阵
        y: 目标向量

        返回:
        best_feature: 最佳特征索引
        best_threshold: 最佳分裂阈值
        best_gain: 最佳方差减少
        """
        n_samples, n_features = X.shape
        best_gain = -1
        best_feature = None
        best_threshold = None

        # 当前节点的方差
        current_variance = self._variance(y)

        # 遍历所有特征
        for feature_index in range(n_features):
            # 获取该特征的所有唯一值
            thresholds = np.unique(X[:, feature_index])

            # 遍历所有可能的阈值
            for threshold in thresholds:
                # 根据阈值分裂数据集
                left_indices = X[:, feature_index] <= threshold
                right_indices = ~left_indices

                # 跳过无效的分裂
                if np.sum(left_indices) == 0 or np.sum(right_indices) == 0:
                    continue

                # 计算分裂后的方差
                left_variance = self._variance(y[left_indices])
                right_variance = self._variance(y[right_indices])

                # 计算加权方差
                left_weight = np.sum(left_indices) / n_samples
                right_weight = np.sum(right_indices) / n_samples

                weighted_variance = left_weight * left_variance + right_weight * right_variance

                # 计算方差减少
                gain = current_variance - weighted_variance

                # 更新最佳分裂
                if gain > best_gain:
                    best_gain = gain
                    best_feature = feature_index
                    best_threshold = threshold

        return best_feature, best_threshold, best_gain

    def _variance(self, y):
        """
        计算方差

        参数:
        y: 目标向量

        返回:
        variance: 方差
        """
        if len(y) == 0:
            return 0
        return np.var(y)

    def _mse(self, y):
        """
        计算均方误差

        参数:
        y: 目标向量

        返回:
        mse: 均方误差
        """
        if len(y) == 0:
            return 0
        mean = np.mean(y)
        return np.mean((y - mean) ** 2)

    def predict(self, X):
        """
        预测新数据

        参数:
        X: 特征矩阵 (n_samples, n_features)

        返回:
        predictions: 预测结果 (n_samples,)
        """
        if self.root is None:
            raise ValueError("模型尚未训练，请先调用 fit 方法")

        if X.ndim != 2:
            raise ValueError("X 必须是二维数组")

        if X.shape[1] != self.n_features:
            raise ValueError(f"特征数量必须为 {self.n_features}")

        predictions = np.array([self._traverse_tree(x, self.root) for x in X])
        return predictions

    def _traverse_tree(self, x, node):
        """
        遍历树进行预测

        参数:
        x: 单个样本
        node: 当前节点

        返回:
        prediction: 预测结果
        """
        # 如果是叶节点，返回预测值
        if node.is_leaf():
            return node.value

        # 根据特征值选择子树
        if x[node.feature_index] <= node.threshold:
            return self._traverse_tree(x, node.left)
        else:
            return self._traverse_tree(x, node.right)

    def score(self, X, y):
        """
        计算 R² 分数

        参数:
        X: 特征矩阵 (n_samples, n_features)
        y: 真实标签 (n_samples,)

        返回:
        r2: R² 分数
        """
        predictions = self.predict(X)
        ss_res = np.sum((y - predictions) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)

        if ss_tot == 0:
            return 0

        return 1 - (ss_res / ss_tot)

    def mse(self, X, y):
        """
        计算均方误差

        参数:
        X: 特征矩阵 (n_samples, n_features)
        y: 真实标签 (n_samples,)

        返回:
        mse: 均方误差
        """
        predictions = self.predict(X)
        return np.mean((y - predictions) ** 2)

    def rmse(self, X, y):
        """
        计算均方根误差

        参数:
        X: 特征矩阵 (n_samples, n_features)
        y: 真实标签 (n_samples,)

        返回:
        rmse: 均方根误差
        """
        return np.sqrt(self.mse(X, y))

    def mae(self, X, y):
        """
        计算平均绝对误差

        参数:
        X: 特征矩阵 (n_samples, n_features)
        y: 真实标签 (n_samples,)

        返回:
        mae: 平均绝对误差
        """
        predictions = self.predict(X)
        return np.mean(np.abs(y - predictions))

    def get_params(self):
        """
        获取模型参数

        返回:
        params: 参数字典
        """
        return {
            'max_depth': self.max_depth,
            'min_samples_split': self.min_samples_split,
            'min_samples_leaf': self.min_samples_leaf
        }

    def get_depth(self):
        """
        获取树的深度

        返回:
        depth: 树的深度
        """
        return self._get_depth(self.root)

    def _get_depth(self, node):
        """递归获取节点深度"""
        if node.is_leaf():
            return 0
        return 1 + max(self._get_depth(node.left), self._get_depth(node.right))

    def get_n_leaves(self):
        """
        获取叶节点数量

        返回:
        n_leaves: 叶节点数量
        """
        return self._get_n_leaves(self.root)

    def _get_n_leaves(self, node):
        """递归获取叶节点数量"""
        if node.is_leaf():
            return 1
        return self._get_n_leaves(node.left) + self._get_n_leaves(node.right)

    def print_tree(self, node=None, indent="", feature_names=None):
        """
        打印决策树结构

        参数:
        node: 当前节点 (默认为根节点)
        indent: 缩进字符串
        feature_names: 特征名称列表
        """
        if node is None:
            node = self.root

        if node.is_leaf():
            print(f"{indent}预测: {node.value:.4f} (样本数: {node.n_samples})")
            return

        if feature_names and node.feature_index < len(feature_names):
            feature_name = feature_names[node.feature_index]
        else:
            feature_name = f"特征 {node.feature_index}"

        print(f"{indent}[{feature_name} <= {node.threshold:.4f}] (样本数: {node.n_samples})")
        print(f"{indent}├── 是:")
        self.print_tree(node.left, indent + "│   ", feature_names)
        print(f"{indent}└── 否:")
        self.print_tree(node.right, indent + "    ", feature_names)
