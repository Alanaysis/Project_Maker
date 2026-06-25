"""
KD-Tree 加速结构

实现 KD-Tree 数据结构，用于加速 KNN 最近邻搜索。
KD-Tree 是一种空间划分树，在低维空间中能显著降低搜索复杂度。
"""

import numpy as np
import heapq
from typing import Optional, List, Tuple


class KDNode:
    """
    KD-Tree 节点

    Attributes:
        point: 节点存储的数据点
        label: 数据点的标签（分类）或目标值（回归）
        index: 数据点在原始数据中的索引
        left: 左子树
        right: 右子树
        axis: 分割维度
        depth: 节点深度
    """

    def __init__(self, point: np.ndarray, label, index: int = 0,
                 axis: int = 0, depth: int = 0):
        self.point = point
        self.label = label
        self.index = index
        self.left: Optional['KDNode'] = None
        self.right: Optional['KDNode'] = None
        self.axis = axis
        self.depth = depth

    def __repr__(self) -> str:
        return f"KDNode(point={self.point}, axis={self.axis})"


class KDTree:
    """
    KD-Tree 数据结构

    KD-Tree (K-Dimensional Tree) 是一种空间划分树，用于高效地
    组织 K 维空间中的点。在低维空间（d < 20）中，KD-Tree 能将
    最近邻搜索的复杂度从 O(n) 降低到 O(log n)。

    建树过程：
    1. 选择方差最大的维度作为分割维度
    2. 取中位数作为分割点
    3. 递归构建左右子树

    搜索过程：
    1. 从根节点开始，沿树向下搜索到叶节点
    2. 回溯时检查兄弟子树是否可能包含更近的点
    3. 维护 K 个最近邻的优先队列

    Attributes:
        root: 树根节点
        n_features: 特征维度
        metric: 距离度量方式

    Examples:
        >>> import numpy as np
        >>> from src.kd_tree import KDTree
        >>>
        >>> X = np.array([[2, 3], [5, 4], [9, 6], [4, 7], [8, 1], [7, 2]])
        >>> y = np.array([0, 0, 1, 0, 1, 1])
        >>>
        >>> tree = KDTree(metric='euclidean')
        >>> tree.build(X, y)
        >>> indices, distances = tree.query(np.array([3, 4]), k=3)
    """

    def __init__(self, metric: str = 'euclidean'):
        """
        初始化 KD-Tree

        Args:
            metric: 距离度量方式，目前支持 'euclidean' 和 'manhattan'
        """
        if metric not in ['euclidean', 'manhattan']:
            raise ValueError(
                f"KD-Tree supports 'euclidean' and 'manhattan' metrics, "
                f"got '{metric}'"
            )
        self.metric = metric
        self.root: Optional[KDNode] = None
        self.n_features: int = 0

    def build(self, X: np.ndarray, y: np.ndarray) -> 'KDTree':
        """
        构建 KD-Tree

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

        self.n_features = X.shape[1]

        # 递归建树
        indices = np.arange(X.shape[0])
        self.root = self._build_recursive(X, y, indices, depth=0)

        return self

    def _build_recursive(self, X: np.ndarray, y: np.ndarray,
                         indices: np.ndarray, depth: int) -> Optional[KDNode]:
        """
        递归构建 KD-Tree

        Args:
            X: 数据点矩阵
            y: 标签数组
            indices: 当前子集的索引
            depth: 当前深度

        Returns:
            KD-Tree 节点
        """
        if len(indices) == 0:
            return None

        # 选择分割维度（循环选择）
        axis = depth % self.n_features

        # 按分割维度排序
        sorted_idx = indices[np.argsort(X[indices, axis])]

        # 选择中位数作为分割点
        median_idx = len(sorted_idx) // 2

        # 创建节点
        node = KDNode(
            point=X[sorted_idx[median_idx]].copy(),
            label=y[sorted_idx[median_idx]],
            index=int(sorted_idx[median_idx]),
            axis=axis,
            depth=depth
        )

        # 递归构建左右子树
        node.left = self._build_recursive(
            X, y, sorted_idx[:median_idx], depth + 1
        )
        node.right = self._build_recursive(
            X, y, sorted_idx[median_idx + 1:], depth + 1
        )

        return node

    def query(self, point: np.ndarray, k: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        """
        查询 K 个最近邻

        Args:
            point: 查询点 (n_features,)
            k: 近邻数量

        Returns:
            indices: 近邻在原始数据中的索引
            distances: 近邻距离数组

        Raises:
            RuntimeError: 树未构建
        """
        if self.root is None:
            raise RuntimeError("KD-Tree must be built before querying")

        point = np.asarray(point, dtype=float)

        if point.ndim > 1:
            point = point.flatten()

        if point.shape[0] != self.n_features:
            raise ValueError(
                f"Query point must have {self.n_features} features, "
                f"got {point.shape[0]}"
            )

        # 使用最大堆维护 K 个最近邻
        # heapq 是最小堆，所以存储 (-distance, counter, index)
        # counter 用于打破相同距离的平局
        self._heap = []
        self._counter = 0
        self._k = k
        self._query_point = point

        self._search_recursive(self.root)

        # 提取结果（堆中存储的是 (-distance, counter, index)）
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

    def _search_recursive(self, node: Optional[KDNode]):
        """
        递归搜索最近邻

        使用最大堆维护 K 个最近邻。
        堆中存储 (-distance, counter, index)，这样堆顶是距离最大的元素。
        """
        if node is None:
            return

        # 计算当前节点与查询点的距离
        dist = self._distance(self._query_point, node.point)

        # 添加到堆
        if len(self._heap) < self._k:
            heapq.heappush(self._heap, (-dist, self._counter, node.index))
            self._counter += 1
        elif dist < -self._heap[0][0]:
            # 当前距离比堆中最大距离小，替换堆顶
            heapq.heapreplace(self._heap, (-dist, self._counter, node.index))
            self._counter += 1

        # 计算查询点到分割超平面的距离
        plane_dist = abs(self._query_point[node.axis] - node.point[node.axis])

        # 确定搜索顺序
        if self._query_point[node.axis] < node.point[node.axis]:
            first, second = node.left, node.right
        else:
            first, second = node.right, node.left

        # 先搜索近侧子树
        self._search_recursive(first)

        # 如果近侧不够 K 个，或者到分割平面的距离小于当前最远近邻
        max_dist = -self._heap[0][0] if len(self._heap) >= self._k else float('inf')
        if len(self._heap) < self._k or plane_dist < max_dist:
            self._search_recursive(second)

    def _distance(self, x1: np.ndarray, x2: np.ndarray) -> float:
        """
        计算两点之间的距离

        Args:
            x1: 第一个点
            x2: 第二个点

        Returns:
            距离值
        """
        if self.metric == 'euclidean':
            return float(np.sqrt(np.sum((x1 - x2) ** 2)))
        else:  # manhattan
            return float(np.sum(np.abs(x1 - x2)))

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
            raise RuntimeError("KD-Tree must be built before querying")

        point = np.asarray(point, dtype=float).flatten()

        neighbors = []
        self._radius_search_recursive(self.root, point, radius, neighbors)

        if len(neighbors) == 0:
            return np.array([], dtype=int), np.array([], dtype=float)

        neighbors.sort(key=lambda x: x[0])
        indices = np.array([n[1] for n in neighbors])
        distances = np.array([n[0] for n in neighbors])

        return indices, distances

    def _radius_search_recursive(self, node: Optional[KDNode],
                                 point: np.ndarray, radius: float,
                                 neighbors: List[Tuple[float, int]]):
        """递归进行半径搜索"""
        if node is None:
            return

        dist = self._distance(point, node.point)
        if dist <= radius:
            neighbors.append((dist, node.index))

        plane_dist = abs(point[node.axis] - node.point[node.axis])

        if point[node.axis] < node.point[node.axis]:
            first, second = node.left, node.right
        else:
            first, second = node.right, node.left

        self._radius_search_recursive(first, point, radius, neighbors)

        if plane_dist <= radius:
            self._radius_search_recursive(second, point, radius, neighbors)

    def get_depth(self) -> int:
        """获取树的深度"""
        return self._get_depth_recursive(self.root)

    def _get_depth_recursive(self, node: Optional[KDNode]) -> int:
        """递归计算树深度"""
        if node is None:
            return 0
        left_depth = self._get_depth_recursive(node.left)
        right_depth = self._get_depth_recursive(node.right)
        return 1 + max(left_depth, right_depth)

    def get_size(self) -> int:
        """获取树中节点数量"""
        return self._get_size_recursive(self.root)

    def _get_size_recursive(self, node: Optional[KDNode]) -> int:
        """递归计算节点数量"""
        if node is None:
            return 0
        return (1 + self._get_size_recursive(node.left) +
                self._get_size_recursive(node.right))
