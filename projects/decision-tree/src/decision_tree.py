import numpy as np
from collections import Counter

class TreeNode:
    """
    决策树节点类
    """

    def __init__(self, feature_index=None, threshold=None, left=None, right=None, value=None):
        """
        初始化节点

        参数:
        feature_index: 分裂特征索引
        threshold: 分裂阈值
        left: 左子树
        right: 右子树
        value: 叶节点的预测值
        """
        self.feature_index = feature_index
        self.threshold = threshold
        self.left = left
        self.right = right
        self.value = value

    def is_leaf_node(self):
        """
        判断是否为叶节点

        返回:
        是否为叶节点
        """
        return self.value is not None

class DecisionTreeClassifier:
    """
    决策树分类器
    """

    def __init__(self, max_depth=None, min_samples_split=2, min_samples_leaf=1, criterion='entropy'):
        """
        初始化决策树分类器

        参数:
        max_depth: 最大深度 (默认None，表示不限制)
        min_samples_split: 最小分裂样本数 (默认2)
        min_samples_leaf: 最小叶节点样本数 (默认1)
        criterion: 特征选择标准 ('entropy' 或 'gini')
        """
        self.root = None
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.criterion = criterion
        self.n_features = None
        self.n_classes = None
        self.classes = None

    def fit(self, X, y):
        """
        训练决策树模型

        参数:
        X: 特征矩阵 (n_samples, n_features)
        y: 目标向量 (n_samples,)

        返回:
        self: 训练后的模型
        """
        # 输入验证
        if X.ndim != 2:
            raise ValueError("X必须是二维数组")
        if y.ndim != 1:
            raise ValueError("y必须是一维数组")
        if X.shape[0] != y.shape[0]:
            raise ValueError("X和y的样本数量必须相同")

        self.n_features = X.shape[1]
        self.classes = np.unique(y)
        self.n_classes = len(self.classes)

        # 递归构建决策树
        self.root = self._build_tree(X, y, depth=0)

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
        n_classes = len(np.unique(y))

        # 停止条件
        if (self.max_depth is not None and depth >= self.max_depth) or \
           n_samples < self.min_samples_split or \
           n_classes == 1:
            # 创建叶节点
            return TreeNode(value=self._most_common_label(y))

        # 寻找最佳分裂特征
        best_feature, best_threshold = self._find_best_split(X, y)

        if best_feature is None:
            # 没有找到有效的分裂，创建叶节点
            return TreeNode(value=self._most_common_label(y))

        # 根据最佳特征和阈值分裂数据集
        left_indices = X[:, best_feature] <= best_threshold
        right_indices = ~left_indices

        # 检查分裂后的样本数是否满足最小叶节点要求
        if np.sum(left_indices) < self.min_samples_leaf or \
           np.sum(right_indices) < self.min_samples_leaf:
            return TreeNode(value=self._most_common_label(y))

        # 递归构建左右子树
        left_subtree = self._build_tree(X[left_indices], y[left_indices], depth + 1)
        right_subtree = self._build_tree(X[right_indices], y[right_indices], depth + 1)

        # 返回当前节点
        return TreeNode(feature_index=best_feature, threshold=best_threshold,
                       left=left_subtree, right=right_subtree)

    def _find_best_split(self, X, y):
        """
        寻找最佳分裂特征和阈值

        参数:
        X: 特征矩阵
        y: 目标向量

        返回:
        best_feature: 最佳特征索引
        best_threshold: 最佳分裂阈值
        """
        n_samples, n_features = X.shape
        best_gain = -1
        best_feature = None
        best_threshold = None

        # 计算当前节点的纯度
        if self.criterion == 'entropy':
            current_impurity = self._entropy(y)
        else:  # gini
            current_impurity = self._gini(y)

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

                # 计算分裂后的纯度
                if self.criterion == 'entropy':
                    left_impurity = self._entropy(y[left_indices])
                    right_impurity = self._entropy(y[right_indices])
                else:  # gini
                    left_impurity = self._gini(y[left_indices])
                    right_impurity = self._gini(y[right_indices])

                # 计算信息增益
                left_weight = np.sum(left_indices) / n_samples
                right_weight = np.sum(right_indices) / n_samples

                gain = current_impurity - (left_weight * left_impurity + right_weight * right_impurity)

                # 更新最佳分裂
                if gain > best_gain:
                    best_gain = gain
                    best_feature = feature_index
                    best_threshold = threshold

        return best_feature, best_threshold

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

        # 计算熵
        entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))

        return entropy

    def _gini(self, y):
        """
        计算基尼指数

        参数:
        y: 目标向量

        返回:
        gini: 基尼指数
        """
        # 计算每个类别的概率
        _, counts = np.unique(y, return_counts=True)
        probabilities = counts / len(y)

        # 计算基尼指数
        gini = 1 - np.sum(probabilities ** 2)

        return gini

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
            raise ValueError("模型尚未训练，请先调用fit方法")

        if X.ndim != 2:
            raise ValueError("X必须是二维数组")

        if X.shape[1] != self.n_features:
            raise ValueError(f"特征数量必须为{self.n_features}")

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
        if node.is_leaf_node():
            return node.value

        # 根据特征值选择子树
        if x[node.feature_index] <= node.threshold:
            return self._traverse_tree(x, node.left)
        else:
            return self._traverse_tree(x, node.right)

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
            'min_samples_leaf': self.min_samples_leaf,
            'criterion': self.criterion
        }

    def print_tree(self, node=None, indent=""):
        """
        打印决策树结构

        参数:
        node: 当前节点 (默认为根节点)
        indent: 缩进字符串
        """
        if node is None:
            node = self.root

        if node.is_leaf_node():
            print(f"{indent}预测: {node.value}")
            return

        print(f"{indent}特征 {node.feature_index} <= {node.threshold}?")
        print(f"{indent}├── 是:")
        self.print_tree(node.left, indent + "│   ")
        print(f"{indent}└── 否:")
        self.print_tree(node.right, indent + "    ")