"""
Ball Tree 加速结构

实现 Ball Tree 数据结构，用于加速 KNN 最近邻搜索。
Ball Tree 使用超球体划分空间，在高维数据中表现优于 KD-Tree。
"""

import numpy as np
import heapq
from typing import Optional, List, Tuple


class BallNode:
    """
    Ball Tree 节点

    Attributes:
        center: 超球体中心
        radius: 超球体半径
        label: 叶节点标签（仅叶节点有效）
        point: 叶节点数据点（仅叶节点有效）
        left: 左子树
        right: 右子树
        indices: 叶节点包含的数据索引
        is_leaf: 是否为叶节点
    """

    def __init__(self, center: np.ndarray, radius: float):
        self.center = center
        self.radius = radius
        self.label = None
        self.point: Optional[np.ndarray] = None
        self.left: Optional['BallNode'] = None
        self.right: Optional['BallNode'] = None
        self.indices: Optional[np.ndarray] = None
        self.is_leaf = False

    def __repr__(self) -> str:
        return f"BallNode(center={self.center}, radius={self.radius:.4f})"


class BallTree:
    """
    Ball Tree 数据结构

    Ball Tree 使用超球体（ball）来划分空间。每个节点代表一个
    包含其所有子节点数据点的超球体。

    优势：
    - 在高维数据中比 KD-Tree 表现更好
    - 支持任意距离度量
    - 对数据分布没有特殊要求

    建树过程：
    1. 计算数据点的质心和半径
    2. 选择两个最远的点作为分裂种子
    3. 将数据点分配到最近的种子
    4. 递归构建左右子树

    Attributes:
        root: 树根节点
        metric: 距离度量方式
        leaf_size: 叶节点最大容量

    Examples:
        >>> import numpy as np
        >>> from src.ball_tree import BallTree
        >>>
        >>> X = np.array([[2, 3], [5, 4], [9, 6], [4, 7], [8, 1], [7, 2]])
        >>> y = np.array([0, 0, 1, 0, 1, 1])
        >>>
        >>> tree = BallTree(metric='euclidean', leaf_size=2)
        >>> tree.build(X, y)
        >>> indices, distances = tree.query(np.array([[3, 4]]), k=3)
    """

    def __init__(self, metric: str = 'euclidean', leaf_size: int = 10):
        """
        初始化 Ball Tree

        Args:
            metric: 距离度量方式 ('euclidean', 'manhattan', 'cosine')
            leaf_size: 叶节点最大容量
        """
        valid_metrics = ['euclidean', 'manhattan', 'cosine']
        if metric not in valid_metrics:
            raise ValueError(
                f"Unsupported metric: {metric}. "
                f"Supported metrics: {valid_metrics}"
            )

        self.metric = metric
        self.leaf_size = max(1, leaf_size)
        self.root: Optional[BallNode] = None
        self.X_train: Optional[np.ndarray] = None
        self.y_train: Optional[np.ndarray] = None
        self.n_features: int = 0

    def build(self, X: np.ndarray, y: np.ndarray) -> 'BallTree':
        """
        构建 Ball Tree

        Args:
            X: 数据点矩阵 (n_samples, n_features)
            y: 标签数组 (n_samples,)

        Returns:
            self: 返回自身

        Raises:
            ValueError: 输入数据格式不正确
        """
        X = np.asarray(X, dtype=float)
        y = np.asarray(y)

        if X.ndim != 2:
            raise ValueError("X must be a 2D array")

        if X.shape[0] != y.shape[0]:
            raise ValueError("X and y must have the same number of samples")

        if X.shape[0] == 0:
            raise ValueError("Data cannot be empty")

        self.X_train = X.copy()
        self.y_train = y.copy()
        self.n_features = X.shape[1]

        # 递归建树
        indices = np.arange(X.shape[0])
        self.root = self._build_recursive(indices)

        return self

    def _build_recursive(self, indices: np.ndarray) -> BallNode:
        """
        递归构建 Ball Tree

        Args:
            indices: 当前子集的数据索引

        Returns:
            Ball Tree 节点
        """
        X_subset = self.X_train[indices]

        # 计算质心和半径
        center = np.mean(X_subset, axis=0)
        distances_to_center = self._batch_distances(X_subset, center)
        radius = np.max(distances_to_center) if len(distances_to_center) > 0 else 0

        node = BallNode(center=center, radius=radius)

        # 如果数据量小于叶节点大小，创建叶节点
        if len(indices) <= self.leaf_size:
            node.is_leaf = True
            node.indices = indices.copy()
            return node

        # 选择分裂种子：选择两个最远的点
        seed1, seed2 = self._select_seeds(X_subset)

        # 将数据点分配到最近的种子
        dist_to_seed1 = self._batch_distances(X_subset, X_subset[seed1])
        dist_to_seed2 = self._batch_distances(X_subset, X_subset[seed2])

        left_mask = dist_to_seed1 <= dist_to_seed2
        right_mask = ~left_mask

        # 确保两个子集都不为空
        if np.sum(left_mask) == 0:
            left_mask[0] = True
            right_mask[0] = False
        elif np.sum(right_mask) == 0:
            right_mask[-1] = True
            left_mask[-1] = False

        left_indices = indices[left_mask]
        right_indices = indices[right_mask]

        # 递归构建子树
        node.left = self._build_recursive(left_indices)
        node.right = self._build_recursive(right_indices)

        return node

    def _select_seeds(self, X: np.ndarray) -> Tuple[int, int]:
        """
        选择分裂种子（两个最远的点）

        使用两遍扫描的贪心算法：
        1. 选择离质心最远的点作为第一个种子
        2. 选择离第一个种子最远的点作为第二个种子

        Args:
            X: 数据点矩阵

        Returns:
            (seed1_idx, seed2_idx): 两个种子的索引
        """
        center = np.mean(X, axis=0)

        # 第一遍：找离质心最远的点
        dists_to_center = self._batch_distances(X, center)
        seed1 = np.argmax(dists_to_center)

        # 第二遍：找离第一个种子最远的点
        dists_to_seed1 = self._batch_distances(X, X[seed1])
        seed2 = np.argmax(dists_to_seed1)

        # 确保两个种子不同
        if seed1 == seed2:
            seed2 = (seed1 + 1) % len(X)

        return int(seed1), int(seed2)

    def _batch_distances(self, X: np.ndarray, point: np.ndarray) -> np.ndarray:
        """
        批量计算点到指定点的距离

        Args:
            X: 数据点矩阵 (n_samples, n_features)
            point: 目标点 (n_features,)

        Returns:
            distances: 距离数组 (n_samples,)
        """
        if self.metric == 'euclidean':
            return np.sqrt(np.sum((X - point) ** 2, axis=1))
        elif self.metric == 'manhattan':
            return np.sum(np.abs(X - point), axis=1)
        elif self.metric == 'cosine':
            # 余弦距离 = 1 - 余弦相似度
            dot_products = np.dot(X, point)
            norms_X = np.linalg.norm(X, axis=1)
            norm_point = np.linalg.norm(point)

            # 处理零向量
            denom = norms_X * norm_point
            denom = np.where(denom == 0, 1, denom)
            similarities = dot_products / denom
            return 1 - similarities
        else:
            raise ValueError(f"Unsupported metric: {self.metric}")

    def query(self, point: np.ndarray, k: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        """
        查询 K 个最近邻

        Args:
            point: 查询点 (n_features,)
            k: 近邻数量

        Returns:
            indices: 近邻在训练数据中的索引
            distances: 近邻距离数组

        Raises:
            RuntimeError: 树未构建
        """
        if self.root is None:
            raise RuntimeError("Ball Tree must be built before querying")

        point = np.asarray(point, dtype=float).flatten()

        if point.shape[0] != self.n_features:
            raise ValueError(
                f"Query point must have {self.n_features} features, "
                f"got {point.shape[0]}"
            )

        # 使用最大堆维护 K 个最近邻
        # heapq 是最小堆，所以存储 (-distance, counter, index)
        self._heap = []
        self._counter = 0
        self._k = k
        self._query_point = point

        self._search_recursive(self.root)

        # 提取结果
        neighbors = []
        while self._heap:
            neg_dist, _, idx = heapq.heappop(self._heap)
            neighbors.append((-neg_dist, idx))

        # 按距离排序
        neighbors.sort(key=lambda x: x[0])

        k_actual = min(k, len(neighbors))
        indices = np.array([n[1] for n in neighbors[:k_actual]])
        distances = np.array([n[0] for n in neighbors[:k_actual]])

        return indices, distances

    def _search_recursive(self, node: Optional[BallNode]):
        """
        递归搜索最近邻

        使用最大堆维护 K 个最近邻。
        """
        if node is None:
            return

        # 计算查询点到球心的距离
        dist_to_center = self._distance(self._query_point, node.center)

        # 剪枝：如果球体中不可能有更近的点，跳过
        max_dist = -self._heap[0][0] if len(self._heap) >= self._k else float('inf')

        if dist_to_center - node.radius > max_dist:
            return

        if node.is_leaf:
            # 叶节点：检查所有数据点
            for idx in node.indices:
                dist = self._distance(self._query_point, self.X_train[idx])

                if len(self._heap) < self._k:
                    heapq.heappush(self._heap, (-dist, self._counter, idx))
                    self._counter += 1
                elif dist < -self._heap[0][0]:
                    heapq.heapreplace(self._heap, (-dist, self._counter, idx))
                    self._counter += 1
        else:
            # 内部节点：先搜索更近的子树
            dist_left = self._distance(self._query_point, node.left.center) if node.left else float('inf')
            dist_right = self._distance(self._query_point, node.right.center) if node.right else float('inf')

            if dist_left <= dist_right:
                first, second = node.left, node.right
            else:
                first, second = node.right, node.left

            self._search_recursive(first)

            max_dist = -self._heap[0][0] if len(self._heap) >= self._k else float('inf')
            dist_to_second = dist_right if first is node.left else dist_left
            if len(self._heap) < self._k or dist_to_second - (second.radius if second else 0) <= max_dist:
                self._search_recursive(second)

    def _distance(self, x1: np.ndarray, x2: np.ndarray) -> float:
        """计算两点之间的距离"""
        if self.metric == 'euclidean':
            return float(np.sqrt(np.sum((x1 - x2) ** 2)))
        elif self.metric == 'manhattan':
            return float(np.sum(np.abs(x1 - x2)))
        elif self.metric == 'cosine':
            dot = np.dot(x1, x2)
            norm1 = np.linalg.norm(x1)
            norm2 = np.linalg.norm(x2)
            if norm1 == 0 or norm2 == 0:
                return 1.0
            return float(1 - dot / (norm1 * norm2))
        else:
            raise ValueError(f"Unsupported metric: {self.metric}")

    def query_radius(self, point: np.ndarray,
                     radius: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        查询指定半径内的所有点

        Args:
            point: 查询点
            radius: 搜索半径

        Returns:
            indices: 点索引数组
            distances: 距离数组
        """
        if self.root is None:
            raise RuntimeError("Ball Tree must be built before querying")

        point = np.asarray(point, dtype=float).flatten()
        neighbors = []
        self._radius_search_recursive(self.root, point, radius, neighbors)

        if len(neighbors) == 0:
            return np.array([], dtype=int), np.array([], dtype=float)

        neighbors.sort(key=lambda x: x[0])
        indices = np.array([n[1] for n in neighbors])
        distances = np.array([n[0] for n in neighbors])

        return indices, distances

    def _radius_search_recursive(self, node: BallNode, point: np.ndarray,
                                 radius: float,
                                 neighbors: List[Tuple[float, int]]):
        """递归进行半径搜索"""
        if node is None:
            return

        dist_to_center = self._distance(point, node.center)

        # 剪枝：球体完全在半径外
        if dist_to_center - node.radius > radius:
            return

        if node.is_leaf:
            for idx in node.indices:
                dist = self._distance(point, self.X_train[idx])
                if dist <= radius:
                    neighbors.append((dist, idx))
        else:
            self._radius_search_recursive(node.left, point, radius, neighbors)
            self._radius_search_recursive(node.right, point, radius, neighbors)

    def get_depth(self) -> int:
        """获取树的深度"""
        return self._get_depth_recursive(self.root)

    def _get_depth_recursive(self, node: Optional[BallNode]) -> int:
        if node is None:
            return 0
        return 1 + max(
            self._get_depth_recursive(node.left),
            self._get_depth_recursive(node.right)
        )

    def get_size(self) -> int:
        """获取树中节点数量"""
        return self._get_size_recursive(self.root)

    def _get_size_recursive(self, node: Optional[BallNode]) -> int:
        if node is None:
            return 0
        return (1 + self._get_size_recursive(node.left) +
                self._get_size_recursive(node.right))
