"""
决策树剪枝实现

剪枝是防止决策树过拟合的重要技术。

1. 预剪枝 (Pre-pruning):
   - 在构建树的过程中提前停止
   - 使用验证集评估分裂是否有效
   - 方法：设置最大深度、最小样本数、最小信息增益等

2. 后剪枝 (Post-pruning):
   - 先构建完整的树，然后自底向上剪枝
   - 代价复杂度剪枝 (Cost Complexity Pruning, CCP)
   - 使用交叉验证选择最优的剪枝参数 alpha

代价复杂度剪枝：
Cost(T) = R(T) + alpha * |T_leaf|
其中：
- R(T) 是树的训练误差
- alpha 是复杂度参数
- |T_leaf| 是叶节点数量
"""

import numpy as np
from collections import Counter
from .cart_classifier import CARTClassifier, CARTNode


class PrePruningTree(CARTClassifier):
    """
    预剪枝决策树

    在构建树的过程中使用验证集评估分裂是否有效。

    参数:
    ----------
    max_depth : int, optional (默认=None)
        树的最大深度
    min_samples_split : int (默认=2)
        节点分裂所需的最小样本数
    min_samples_leaf : int (默认=1)
        叶节点所需的最小样本数
    min_impurity_decrease : float (默认=0.0)
        分裂所需的最小不纯度减少
    validation_data : tuple (默认=None)
        验证数据 (X_val, y_val)

    属性:
    ----------
    root : CARTNode
        决策树的根节点
    """

    def __init__(self, max_depth=None, min_samples_split=2, min_samples_leaf=1,
                 min_impurity_decrease=0.0, validation_data=None):
        """
        初始化预剪枝决策树

        参数:
        max_depth: 最大深度
        min_samples_split: 最小分裂样本数
        min_samples_leaf: 最小叶节点样本数
        min_impurity_decrease: 最小不纯度减少
        validation_data: 验证数据 (X_val, y_val)
        """
        super().__init__(max_depth=max_depth, min_samples_split=min_samples_split,
                        min_samples_leaf=min_samples_leaf)
        self.min_impurity_decrease = min_impurity_decrease
        self.validation_data = validation_data

    def _build_tree(self, X, y, depth=0):
        """
        递归构建决策树（带预剪枝）

        参数:
        X: 特征矩阵
        y: 目标向量
        depth: 当前深度

        返回:
        node: 构建好的节点
        """
        n_samples, n_features = X.shape
        n_classes = len(np.unique(y))

        # 计算当前节点的基尼系数
        current_impurity = self._gini(y)

        # 停止条件
        if (self.max_depth is not None and depth >= self.max_depth) or \
           n_samples < self.min_samples_split or \
           n_classes == 1:
            return CARTNode(
                value=self._most_common_label(y),
                n_samples=n_samples,
                impurity=current_impurity
            )

        # 寻找最佳分裂
        best_feature, best_threshold, best_gain = self._find_best_split(X, y)

        if best_feature is None:
            return CARTNode(
                value=self._most_common_label(y),
                n_samples=n_samples,
                impurity=current_impurity
            )

        # 预剪枝条件1: 检查不纯度减少是否足够
        if best_gain < self.min_impurity_decrease:
            return CARTNode(
                value=self._most_common_label(y),
                n_samples=n_samples,
                impurity=current_impurity
            )

        # 预剪枝条件2: 使用验证集评估分裂是否有效
        if self.validation_data is not None:
            X_val, y_val = self.validation_data

            # 计算不分裂时的准确率
            majority_label = self._most_common_label(y)
            accuracy_no_split = np.mean(y_val == majority_label)

            # 计算分裂后的准确率
            left_indices = X[:, best_feature] <= best_threshold
            right_indices = ~left_indices

            left_label = self._most_common_label(y[left_indices])
            right_label = self._most_common_label(y[right_indices])

            left_mask = X_val[:, best_feature] <= best_threshold
            right_mask = ~left_mask

            predictions = np.empty(len(y_val), dtype=y_val.dtype)
            predictions[left_mask] = left_label
            predictions[right_mask] = right_label

            accuracy_with_split = np.mean(y_val == predictions)

            # 如果分裂后准确率没有提高，则不分裂
            if accuracy_with_split <= accuracy_no_split:
                return CARTNode(
                    value=self._most_common_label(y),
                    n_samples=n_samples,
                    impurity=current_impurity
                )

        # 根据最佳特征和阈值分裂数据集
        left_indices = X[:, best_feature] <= best_threshold
        right_indices = ~left_indices

        # 检查分裂后的样本数
        if np.sum(left_indices) < self.min_samples_leaf or \
           np.sum(right_indices) < self.min_samples_leaf:
            return CARTNode(
                value=self._most_common_label(y),
                n_samples=n_samples,
                impurity=current_impurity
            )

        # 记录特征重要性
        self.feature_importances_[best_feature] += best_gain * n_samples

        # 递归构建左右子树
        left_subtree = self._build_tree(X[left_indices], y[left_indices], depth + 1)
        right_subtree = self._build_tree(X[right_indices], y[right_indices], depth + 1)

        return CARTNode(
            feature_index=best_feature,
            threshold=best_threshold,
            left=left_subtree,
            right=right_subtree,
            n_samples=n_samples,
            impurity=current_impurity
        )


class PostPruningTree(CARTClassifier):
    """
    后剪枝决策树（代价复杂度剪枝）

    先构建完整的树，然后使用代价复杂度剪枝方法进行剪枝。

    参数:
    ----------
    max_depth : int, optional (默认=None)
        树的最大深度
    min_samples_split : int (默认=2)
        节点分裂所需的最小样本数
    min_samples_leaf : int (默认=1)
        叶节点所需的最小样本数
    ccp_alpha : float (默认=0.0)
        代价复杂度剪枝参数

    属性:
    ----------
    root : CARTNode
        决策树的根节点
    ccp_alphas : list
        有效的 alpha 值序列
    trees : list
        对应每个 alpha 的树

    示例:
    ----------
    >>> from pruning import PostPruningTree
    >>> import numpy as np
    >>> X_train = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
    >>> y_train = np.array([0, 0, 1, 1])
    >>> X_val = np.array([[0, 0], [1, 1]])
    >>> y_val = np.array([0, 1])
    >>> tree = PostPruningTree(ccp_alpha=0.1)
    >>> tree.fit(X_train, y_train)
    >>> tree.prune(X_val, y_val)
    """

    def __init__(self, max_depth=None, min_samples_split=2, min_samples_leaf=1,
                 ccp_alpha=0.0):
        """
        初始化后剪枝决策树

        参数:
        max_depth: 最大深度
        min_samples_split: 最小分裂样本数
        min_samples_leaf: 最小叶节点样本数
        ccp_alpha: 代价复杂度剪枝参数
        """
        super().__init__(max_depth=max_depth, min_samples_split=min_samples_split,
                        min_samples_leaf=min_samples_leaf)
        self.ccp_alpha = ccp_alpha
        self.ccp_alphas = []
        self.trees = []

    def fit(self, X, y):
        """
        训练决策树

        参数:
        X: 特征矩阵 (n_samples, n_features)
        y: 目标向量 (n_samples,)

        返回:
        self: 训练后的模型
        """
        # 先构建完整的树
        super().fit(X, y)

        # 如果设置了 ccp_alpha，进行剪枝
        if self.ccp_alpha > 0:
            self._prune_with_alpha(self.root, self.ccp_alpha)

        return self

    def _prune_with_alpha(self, node, alpha):
        """
        使用指定的 alpha 值剪枝

        参数:
        node: 当前节点
        alpha: 复杂度参数
        """
        if node.is_leaf():
            return

        # 递归剪枝子树
        if node.left is not None:
            self._prune_with_alpha(node.left, alpha)
        if node.right is not None:
            self._prune_with_alpha(node.right, alpha)

        # 检查是否应该剪枝
        if not node.left.is_leaf() or not node.right.is_leaf():
            return

        # 计算剪枝前后的代价
        # 剪枝前：两个叶节点的加权不纯度
        left_samples = node.left.n_samples
        right_samples = node.right.n_samples
        total_samples = left_samples + right_samples

        cost_before = (left_samples / total_samples) * node.left.impurity + \
                      (right_samples / total_samples) * node.right.impurity

        # 剪枝后：当前节点变为叶节点
        cost_after = node.impurity

        # 如果剪枝后代价增加不超过 alpha * 1，则剪枝
        if cost_after <= cost_before + alpha:
            # 剪枝：将当前节点变为叶节点
            node.value = self._most_common_label_from_node(node)
            node.left = None
            node.right = None
            node.feature_index = None
            node.threshold = None

    def _most_common_label_from_node(self, node):
        """
        从节点获取最常见的标签

        参数:
        node: 节点

        返回:
        label: 最常见的标签
        """
        # 递归收集所有叶节点的标签
        labels = []
        self._collect_labels(node, labels)
        counter = Counter(labels)
        return counter.most_common(1)[0][0]

    def _collect_labels(self, node, labels):
        """递归收集标签"""
        if node.is_leaf():
            # 使用 n_samples 来模拟多个相同的标签
            labels.extend([node.value] * node.n_samples)
            return

        if node.left is not None:
            self._collect_labels(node.left, labels)
        if node.right is not None:
            self._collect_labels(node.right, labels)

    def cost_complexity_pruning_path(self, X, y):
        """
        计算代价复杂度剪枝路径

        参数:
        X: 特征矩阵
        y: 目标向量

        返回:
        ccp_alphas: alpha 值序列
        impurities: 对应的不纯度
        """
        # 先构建完整的树
        self.fit(X, y)

        # 收集所有可能的 alpha 值
        ccp_alphas = []
        impurities = []
        self._collect_alphas(self.root, ccp_alphas, impurities)

        # 按 alpha 排序
        indices = np.argsort(ccp_alphas)
        ccp_alphas = np.array(ccp_alphas)[indices]
        impurities = np.array(impurities)[indices]

        self.ccp_alphas = ccp_alphas
        return ccp_alphas, impurities

    def _collect_alphas(self, node, alphas, impurities):
        """
        收集所有可能的 alpha 值

        参数:
        node: 当前节点
        alphas: alpha 值列表
        impurities: 不纯度列表
        """
        if node.is_leaf():
            return

        # 递归收集子树的 alpha 值
        if node.left is not None:
            self._collect_alphas(node.left, alphas, impurities)
        if node.right is not None:
            self._collect_alphas(node.right, alphas, impurities)

        # 计算当前节点的 alpha 值
        # alpha = (R(t) - R(T_t)) / (|T_t| - 1)
        # 其中 R(t) 是节点的误差，R(T_t) 是子树的误差，|T_t| 是子树的叶节点数
        if not node.is_leaf() and node.left is not None and node.right is not None:
            # 子树的叶节点数
            n_leaves = self._count_leaves(node)

            if n_leaves > 1:
                # 计算 alpha
                alpha = self._compute_alpha(node)
                alphas.append(alpha)
                impurities.append(node.impurity)

    def _count_leaves(self, node):
        """计算节点下的叶节点数"""
        if node.is_leaf():
            return 1
        count = 0
        if node.left is not None:
            count += self._count_leaves(node.left)
        if node.right is not None:
            count += self._count_leaves(node.right)
        return count

    def _compute_alpha(self, node):
        """
        计算节点的 alpha 值

        参数:
        node: 节点

        返回:
        alpha: 复杂度参数
        """
        # 子树的加权不纯度
        left_samples = node.left.n_samples if node.left else 0
        right_samples = node.right.n_samples if node.right else 0
        total_samples = left_samples + right_samples

        if total_samples == 0:
            return 0

        subtree_impurity = (left_samples / total_samples) * (node.left.impurity if node.left else 0) + \
                          (right_samples / total_samples) * (node.right.impurity if node.right else 0)

        # 叶节点数
        n_leaves = self._count_leaves(node)

        # alpha = (节点不纯度 - 子树不纯度) / (叶节点数 - 1)
        if n_leaves <= 1:
            return 0

        alpha = (node.impurity - subtree_impurity) / (n_leaves - 1)

        return max(0, alpha)

    def prune_with_cross_validation(self, X, y, cv=5):
        """
        使用交叉验证选择最优的 alpha 值

        参数:
        X: 特征矩阵
        y: 目标向量
        cv: 交叉验证折数

        返回:
        best_alpha: 最优的 alpha 值
        """
        from .utils import train_test_split

        # 计算剪枝路径
        ccp_alphas, _ = self.cost_complexity_pruning_path(X, y)

        if len(ccp_alphas) == 0:
            return 0

        best_alpha = 0
        best_score = -np.inf

        # 对每个 alpha 进行交叉验证
        for alpha in ccp_alphas:
            scores = []

            for i in range(cv):
                # 划分训练集和验证集
                X_train, X_val, y_train, y_val = train_test_split(
                    X, y, test_size=1/cv, random_state=i
                )

                # 训练模型
                tree = PostPruningTree(ccp_alpha=alpha)
                tree.fit(X_train, y_train)

                # 评估模型
                score = tree.score(X_val, y_val)
                scores.append(score)

            # 计算平均分数
            mean_score = np.mean(scores)

            if mean_score > best_score:
                best_score = mean_score
                best_alpha = alpha

        return best_alpha


class ReducedErrorPruning:
    """
    减少错误剪枝 (Reduced Error Pruning)

    使用验证集进行后剪枝。

    参数:
    ----------
    tree : 决策树
        要剪枝的决策树

    示例:
    ----------
    >>> from pruning import ReducedErrorPruning
    >>> import numpy as np
    >>> tree = CARTClassifier()
    >>> tree.fit(X_train, y_train)
    >>> pruner = ReducedErrorPruning(tree)
    >>> pruner.prune(X_val, y_val)
    """

    def __init__(self, tree):
        """
        初始化减少错误剪枝

        参数:
        tree: 决策树
        """
        self.tree = tree

    def prune(self, X_val, y_val):
        """
        使用验证集进行剪枝

        参数:
        X_val: 验证集特征
        y_val: 验证集标签

        返回:
        pruned_tree: 剪枝后的树
        """
        # 递归剪枝
        self._prune_node(self.tree.root, X_val, y_val)
        return self.tree

    def _prune_node(self, node, X_val, y_val):
        """
        递归剪枝节点

        参数:
        node: 当前节点
        X_val: 验证集特征
        y_val: 验证集标签
        """
        if node.is_leaf():
            return

        if len(X_val) == 0:
            return

        # 获取当前节点的样本
        left_mask = X_val[:, node.feature_index] <= node.threshold
        right_mask = ~left_mask

        # 递归剪枝左子树
        if np.sum(left_mask) > 0:
            self._prune_node(node.left, X_val[left_mask], y_val[left_mask])

        # 递归剪枝右子树
        if np.sum(right_mask) > 0:
            self._prune_node(node.right, X_val[right_mask], y_val[right_mask])

        # 检查是否应该剪枝
        # 计算剪枝前的准确率
        predictions_before = np.array([self._predict_single(x, node) for x in X_val])
        accuracy_before = np.mean(predictions_before == y_val)

        # 计算剪枝后的准确率（将当前节点变为叶节点）
        majority_label = Counter(y_val).most_common(1)[0][0]
        accuracy_after = np.mean(majority_label == y_val)

        # 如果剪枝后准确率不降低，则剪枝
        if accuracy_after >= accuracy_before:
            node.value = majority_label
            node.left = None
            node.right = None
            node.feature_index = None
            node.threshold = None

    def _predict_single(self, x, node):
        """预测单个样本"""
        if node.is_leaf():
            return node.value

        if x[node.feature_index] <= node.threshold:
            return self._predict_single(x, node.left)
        else:
            return self._predict_single(x, node.right)
