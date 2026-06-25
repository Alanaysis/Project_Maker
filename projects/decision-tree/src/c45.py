"""
C4.5 决策树算法实现

C4.5 是 ID3 的改进版本，由 Ross Quinlan 提出。
它使用信息增益率 (Gain Ratio) 作为特征选择的标准，解决了 ID3 偏向于选择取值较多的特征的问题。

信息增益率 = 信息增益 / 特征的固有值 (Intrinsic Value)
GainRatio(D, A) = Gain(D, A) / IV(A)

其中：
- Gain(D, A) 是信息增益
- IV(A) = -Σ(|Dv|/|D|) * log2(|Dv|/|D|) 是特征 A 的固有值

C4.5 还支持：
- 连续特征的处理
- 缺失值的处理
- 后剪枝 (悲观剪枝)
"""

import numpy as np
from collections import Counter


class C45Node:
    """C4.5 决策树节点"""

    def __init__(self, feature_index=None, children=None, value=None,
                 threshold=None, is_continuous=False):
        """
        初始化节点

        参数:
        feature_index: 分裂特征索引
        children: 子节点字典
        value: 叶节点的预测值
        threshold: 连续特征的分裂阈值
        is_continuous: 是否为连续特征
        """
        self.feature_index = feature_index
        self.children = children or {}
        self.value = value
        self.threshold = threshold
        self.is_continuous = is_continuous

    def is_leaf(self):
        """判断是否为叶节点"""
        return self.value is not None


class C45DecisionTree:
    """
    C4.5 决策树分类器

    使用信息增益率作为特征选择标准，适用于离散和连续特征的分类问题。

    参数:
    ----------
    max_depth : int, optional (默认=None)
        树的最大深度，None 表示不限制
    min_samples_split : int (默认=2)
        节点分裂所需的最小样本数
    min_samples_leaf : int (默认=1)
        叶节点所需的最小样本数
    handle_continuous : bool (默认=True)
        是否处理连续特征

    属性:
    ----------
    root : C45Node
        决策树的根节点
    n_features : int
        特征数量
    classes : array
        类别标签
    feature_importances_ : array
        特征重要性

    示例:
    ----------
    >>> from c45 import C45DecisionTree
    >>> import numpy as np
    >>> X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
    >>> y = np.array([0, 0, 1, 1])
    >>> tree = C45DecisionTree(max_depth=3)
    >>> tree.fit(X, y)
    >>> predictions = tree.predict(X)
    """

    def __init__(self, max_depth=None, min_samples_split=2, min_samples_leaf=1,
                 handle_continuous=True):
        """
        初始化 C4.5 决策树

        参数:
        max_depth: 最大深度 (默认None，表示不限制)
        min_samples_split: 最小分裂样本数 (默认2)
        min_samples_leaf: 最小叶节点样本数 (默认1)
        handle_continuous: 是否处理连续特征 (默认True)
        """
        self.root = None
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.handle_continuous = handle_continuous
        self.n_features = None
        self.classes = None
        self.feature_importances_ = None
        self.feature_types = None  # 'discrete' 或 'continuous'

    def fit(self, X, y):
        """
        训练 C4.5 决策树模型

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

        # 检测特征类型
        self.feature_types = self._detect_feature_types(X)

        # 初始化特征重要性
        self.feature_importances_ = np.zeros(self.n_features)

        # 递归构建决策树
        self.root = self._build_tree(X, y, depth=0)

        # 归一化特征重要性
        total = np.sum(self.feature_importances_)
        if total > 0:
            self.feature_importances_ /= total

        return self

    def _detect_feature_types(self, X):
        """
        检测特征类型（离散或连续）

        参数:
        X: 特征矩阵

        返回:
        feature_types: 特征类型列表
        """
        feature_types = []

        for i in range(X.shape[1]):
            unique_values = np.unique(X[:, i])
            # 如果唯一值数量较多，认为是连续特征
            if len(unique_values) > 10 and self.handle_continuous:
                feature_types.append('continuous')
            else:
                feature_types.append('discrete')

        return feature_types

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
        n_classes = len(np.unique(y))

        # 停止条件
        if (self.max_depth is not None and depth >= self.max_depth) or \
           n_samples < self.min_samples_split or \
           n_classes == 1:
            return C45Node(value=self._most_common_label(y))

        # 寻找最佳分裂特征
        best_feature, best_threshold, best_gain_ratio = self._find_best_split(X, y)

        if best_feature is None:
            return C45Node(value=self._most_common_label(y))

        # 记录特征重要性
        self.feature_importances_[best_feature] += best_gain_ratio * n_samples

        # 根据特征类型进行分裂
        if self.feature_types[best_feature] == 'continuous':
            # 连续特征：二分裂
            left_indices = X[:, best_feature] <= best_threshold
            right_indices = ~left_indices

            if np.sum(left_indices) < self.min_samples_leaf or \
               np.sum(right_indices) < self.min_samples_leaf:
                return C45Node(value=self._most_common_label(y))

            left_child = self._build_tree(X[left_indices], y[left_indices], depth + 1)
            right_child = self._build_tree(X[right_indices], y[right_indices], depth + 1)

            return C45Node(
                feature_index=best_feature,
                children={'<=': left_child, '>': right_child},
                threshold=best_threshold,
                is_continuous=True
            )
        else:
            # 离散特征：多分裂
            feature_values = np.unique(X[:, best_feature])
            children = {}

            for value in feature_values:
                indices = X[:, best_feature] == value
                X_subset = X[indices]
                y_subset = y[indices]

                if len(y_subset) < self.min_samples_leaf:
                    children[value] = C45Node(value=self._most_common_label(y))
                else:
                    children[value] = self._build_tree(X_subset, y_subset, depth + 1)

            return C45Node(feature_index=best_feature, children=children)

    def _find_best_split(self, X, y):
        """
        寻找最佳分裂特征和阈值（基于信息增益率）

        参数:
        X: 特征矩阵
        y: 目标向量

        返回:
        best_feature: 最佳特征索引
        best_threshold: 最佳分裂阈值（连续特征）
        best_gain_ratio: 最佳信息增益率
        """
        n_samples, n_features = X.shape
        best_gain_ratio = -1
        best_feature = None
        best_threshold = None

        for feature_index in range(n_features):
            if self.feature_types[feature_index] == 'continuous':
                # 连续特征：尝试所有可能的分裂点
                thresholds = np.unique(X[:, feature_index])
                for threshold in thresholds:
                    gain_ratio = self._gain_ratio_continuous(X, y, feature_index, threshold)
                    if gain_ratio > best_gain_ratio:
                        best_gain_ratio = gain_ratio
                        best_feature = feature_index
                        best_threshold = threshold
            else:
                # 离散特征
                gain_ratio = self._gain_ratio_discrete(X, y, feature_index)
                if gain_ratio > best_gain_ratio:
                    best_gain_ratio = gain_ratio
                    best_feature = feature_index
                    best_threshold = None

        return best_feature, best_threshold, best_gain_ratio

    def _gain_ratio_discrete(self, X, y, feature_index):
        """
        计算离散特征的信息增益率

        参数:
        X: 特征矩阵
        y: 目标向量
        feature_index: 特征索引

        返回:
        gain_ratio: 信息增益率
        """
        # 计算信息增益
        gain = self._information_gain_discrete(X, y, feature_index)

        # 计算固有值 (Intrinsic Value)
        iv = self._intrinsic_value(X, feature_index)

        # 避免除以零
        if iv == 0:
            return 0

        return gain / iv

    def _gain_ratio_continuous(self, X, y, feature_index, threshold):
        """
        计算连续特征的信息增益率

        参数:
        X: 特征矩阵
        y: 目标向量
        feature_index: 特征索引
        threshold: 分裂阈值

        返回:
        gain_ratio: 信息增益率
        """
        n_samples = len(y)

        # 计算信息增益
        parent_entropy = self._entropy(y)

        left_indices = X[:, feature_index] <= threshold
        right_indices = ~left_indices

        if np.sum(left_indices) == 0 or np.sum(right_indices) == 0:
            return 0

        left_weight = np.sum(left_indices) / n_samples
        right_weight = np.sum(right_indices) / n_samples

        child_entropy = (left_weight * self._entropy(y[left_indices]) +
                        right_weight * self._entropy(y[right_indices]))

        gain = parent_entropy - child_entropy

        # 计算固有值
        iv = -(left_weight * np.log2(left_weight + 1e-10) +
               right_weight * np.log2(right_weight + 1e-10))

        if iv == 0:
            return 0

        return gain / iv

    def _information_gain_discrete(self, X, y, feature_index):
        """
        计算离散特征的信息增益

        参数:
        X: 特征矩阵
        y: 目标向量
        feature_index: 特征索引

        返回:
        gain: 信息增益
        """
        n_samples = len(y)
        parent_entropy = self._entropy(y)

        feature_values = np.unique(X[:, feature_index])
        child_entropy = 0

        for value in feature_values:
            indices = X[:, feature_index] == value
            y_subset = y[indices]
            weight = len(y_subset) / n_samples
            child_entropy += weight * self._entropy(y_subset)

        return parent_entropy - child_entropy

    def _intrinsic_value(self, X, feature_index):
        """
        计算特征的固有值

        参数:
        X: 特征矩阵
        feature_index: 特征索引

        返回:
        iv: 固有值
        """
        n_samples = len(X)
        feature_values = np.unique(X[:, feature_index])

        iv = 0
        for value in feature_values:
            count = np.sum(X[:, feature_index] == value)
            p = count / n_samples
            if p > 0:
                iv -= p * np.log2(p)

        return iv

    def _entropy(self, y):
        """
        计算熵

        参数:
        y: 目标向量

        返回:
        entropy: 熵值
        """
        _, counts = np.unique(y, return_counts=True)
        probabilities = counts / len(y)
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
        return counter.most_common(1)[0][0]

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
        if node.is_leaf():
            return node.value

        if node.is_continuous:
            # 连续特征
            if x[node.feature_index] <= node.threshold:
                return self._traverse_tree(x, node.children['<='])
            else:
                return self._traverse_tree(x, node.children['>'])
        else:
            # 离散特征
            feature_value = x[node.feature_index]
            if feature_value in node.children:
                return self._traverse_tree(x, node.children[feature_value])
            else:
                # 如果特征值不存在，返回最常见的类别
                leaf_values = [n.value for n in node.children.values() if n.is_leaf()]
                if leaf_values:
                    return Counter(leaf_values).most_common(1)[0][0]
                return self._most_common_label(np.array([]))

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
        return np.sum(predictions == y) / len(y)

    def get_params(self):
        """
        获取模型参数

        返回:
        params: 参数字典
        """
        return {
            'max_depth': self.max_depth,
            'min_samples_split': self.min_samples_split,
            'min_samples_leaf': self.min_samples_leaf,
            'handle_continuous': self.handle_continuous
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

        if feature_names and node.feature_index < len(feature_names):
            feature_name = feature_names[node.feature_index]
        else:
            feature_name = f"特征 {node.feature_index}"

        if node.is_continuous:
            print(f"{indent}[{feature_name} <= {node.threshold:.4f}]")
            print(f"{indent}├── 是:")
            self.print_tree(node.children['<='], indent + "│   ", feature_names)
            print(f"{indent}└── 否:")
            self.print_tree(node.children['>'], indent + "    ", feature_names)
        else:
            print(f"{indent}[{feature_name}]")
            for i, (value, child) in enumerate(node.children.items()):
                is_last = i == len(node.children) - 1
                prefix = "└──" if is_last else "├──"
                print(f"{indent}{prefix} 值 = {value}:")
                self.print_tree(child, indent + ("    " if is_last else "│   "), feature_names)
