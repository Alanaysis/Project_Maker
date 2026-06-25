"""
ID3 决策树算法实现

ID3 (Iterative Dichotomiser 3) 是由 Ross Quinlan 提出的决策树算法。
它使用信息增益 (Information Gain) 作为特征选择的标准。

信息增益 = 父节点的熵 - 子节点的加权平均熵
Gain(D, A) = H(D) - Σ(|Dv|/|D|) * H(Dv)

其中：
- H(D) 是数据集 D 的熵
- A 是特征
- Dv 是特征 A 取值为 v 的子集
"""

import numpy as np
from collections import Counter


class ID3Node:
    """ID3 决策树节点"""

    def __init__(self, feature_index=None, children=None, value=None, feature_name=None):
        """
        初始化节点

        参数:
        feature_index: 分裂特征索引
        children: 子节点字典 {特征值: 子节点}
        value: 叶节点的预测值
        feature_name: 特征名称
        """
        self.feature_index = feature_index
        self.children = children or {}
        self.value = value
        self.feature_name = feature_name

    def is_leaf(self):
        """判断是否为叶节点"""
        return self.value is not None


class ID3DecisionTree:
    """
    ID3 决策树分类器

    使用信息增益作为特征选择标准，适用于离散特征的分类问题。

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
    root : ID3Node
        决策树的根节点
    n_features : int
        特征数量
    classes : array
        类别标签
    feature_importances_ : array
        特征重要性

    示例:
    ----------
    >>> from id3 import ID3DecisionTree
    >>> import numpy as np
    >>> X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
    >>> y = np.array([0, 0, 1, 1])
    >>> tree = ID3DecisionTree(max_depth=3)
    >>> tree.fit(X, y)
    >>> predictions = tree.predict(X)
    """

    def __init__(self, max_depth=None, min_samples_split=2, min_samples_leaf=1):
        """
        初始化 ID3 决策树

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
        self.classes = None
        self.feature_importances_ = None

    def fit(self, X, y):
        """
        训练 ID3 决策树模型

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
        self.classes = np.unique(y)

        # 初始化特征重要性
        self.feature_importances_ = np.zeros(self.n_features)

        # 递归构建决策树
        self.root = self._build_tree(X, y, depth=0, used_features=set())

        # 归一化特征重要性
        total = np.sum(self.feature_importances_)
        if total > 0:
            self.feature_importances_ /= total

        return self

    def _build_tree(self, X, y, depth=0, used_features=None):
        """
        递归构建决策树

        参数:
        X: 特征矩阵
        y: 目标向量
        depth: 当前深度
        used_features: 已使用的特征集合

        返回:
        node: 构建好的节点
        """
        if used_features is None:
            used_features = set()

        n_samples, n_features = X.shape
        n_classes = len(np.unique(y))

        # 停止条件
        if (self.max_depth is not None and depth >= self.max_depth) or \
           n_samples < self.min_samples_split or \
           n_classes == 1 or \
           len(used_features) == n_features:
            # 创建叶节点
            return ID3Node(value=self._most_common_label(y))

        # 寻找最佳分裂特征（基于信息增益）
        best_feature = self._find_best_feature(X, y, used_features)

        if best_feature is None:
            return ID3Node(value=self._most_common_label(y))

        # 记录特征重要性
        gain = self._information_gain(X, y, best_feature)
        self.feature_importances_[best_feature] += gain * n_samples

        # 根据最佳特征的取值分裂数据集
        feature_values = np.unique(X[:, best_feature])
        children = {}

        for value in feature_values:
            # 获取该特征值对应的样本
            indices = X[:, best_feature] == value
            X_subset = X[indices]
            y_subset = y[indices]

            # 检查样本数是否满足最小叶节点要求
            if len(y_subset) < self.min_samples_leaf:
                children[value] = ID3Node(value=self._most_common_label(y))
            else:
                # 递归构建子树
                children[value] = self._build_tree(
                    X_subset, y_subset, depth + 1,
                    used_features | {best_feature}
                )

        return ID3Node(feature_index=best_feature, children=children)

    def _find_best_feature(self, X, y, used_features):
        """
        寻找最佳分裂特征（基于信息增益）

        参数:
        X: 特征矩阵
        y: 目标向量
        used_features: 已使用的特征集合

        返回:
        best_feature: 最佳特征索引
        """
        n_samples, n_features = X.shape
        best_gain = -1
        best_feature = None

        # 计算当前节点的熵
        current_entropy = self._entropy(y)

        # 遍历所有未使用的特征
        for feature_index in range(n_features):
            if feature_index in used_features:
                continue

            # 计算信息增益
            gain = self._information_gain(X, y, feature_index)

            if gain > best_gain:
                best_gain = gain
                best_feature = feature_index

        return best_feature

    def _information_gain(self, X, y, feature_index):
        """
        计算信息增益

        参数:
        X: 特征矩阵
        y: 目标向量
        feature_index: 特征索引

        返回:
        gain: 信息增益
        """
        n_samples = len(y)

        # 计算父节点的熵
        parent_entropy = self._entropy(y)

        # 计算子节点的加权平均熵
        feature_values = np.unique(X[:, feature_index])
        child_entropy = 0

        for value in feature_values:
            indices = X[:, feature_index] == value
            y_subset = y[indices]
            weight = len(y_subset) / n_samples
            child_entropy += weight * self._entropy(y_subset)

        # 信息增益 = 父节点熵 - 子节点加权平均熵
        gain = parent_entropy - child_entropy

        return gain

    def _entropy(self, y):
        """
        计算熵

        参数:
        y: 目标向量

        返回:
        entropy: 熵值
        """
        # 计算每个类别的概率
        _, counts = np.unique(y, return_counts=True)
        probabilities = counts / len(y)

        # 计算熵: H(X) = -Σ p(x) * log2(p(x))
        entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))

        return entropy

    def _most_common_label(self, y):
        """
        获取最常见的标签

        参数:
        y: 目标向量

        返回:
        most_common: 最常见的标签
        """
        counter = Counter(y)
        most_common = counter.most_common(1)[0][0]
        return most_common

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

        # 对每个样本进行预测
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

        # 获取特征值
        feature_value = x[node.feature_index]

        # 如果特征值存在于子节点中，继续遍历
        if feature_value in node.children:
            return self._traverse_tree(x, node.children[feature_value])
        else:
            # 如果特征值不存在，返回最常见的类别
            return self._most_common_label(np.array([node.value for node in node.children.values() if node.is_leaf()]))

    def score(self, X, y):
        """
        计算准确率

        参数:
        X: 特征矩阵 (n_samples, n_features)
        y: 真实标签 (n_samples,)

        返回:
        accuracy: 准确率
        """
        predictions = self.predict(X)
        accuracy = np.sum(predictions == y) / len(y)
        return accuracy

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
            print(f"{indent}预测: {node.value}")
            return

        # 获取特征名称
        if feature_names and node.feature_index < len(feature_names):
            feature_name = feature_names[node.feature_index]
        else:
            feature_name = f"特征 {node.feature_index}"

        print(f"{indent}[{feature_name}]")

        for value, child in node.children.items():
            print(f"{indent}├── 值 = {value}:")
            self.print_tree(child, indent + "│   ", feature_names)
