"""
图表示模块 - Graph Representation Module

提供 PageRank 算法所需的图数据结构：
- 邻接矩阵 (Adjacency Matrix): 稠密表示，适合小规模图
- 邻接表 (Adjacency List): 稀疏表示，适合大规模图
- 转移矩阵 (Transition Matrix): PageRank 计算专用

PageRank 需要将有向图转换为概率转移矩阵，
表示从一页跳转到另一页的概率。
"""

import numpy as np
from scipy import sparse
from typing import List, Tuple, Dict, Optional


class Graph:
    """
    有向图 - Directed Graph

    用两种方式存储图结构：
    1. 邻接矩阵 (稠密) - 便于理解和小规模计算
    2. 邻接表 (稀疏) - 便于大规模计算

    对于 PageRank，我们需要将图转换为转移矩阵：
    - 如果页面 j 有 L 条出链，则每条链的转移概率为 1/L
    - 悬垂节点 (无出链) 需要特殊处理
    """

    def __init__(self, num_nodes: int):
        """
        初始化图

        Parameters:
            num_nodes: 节点数量 (网页数量)
        """
        self.num_nodes = num_nodes
        self.adj_matrix = np.zeros((num_nodes, num_nodes), dtype=np.float64)
        self.adj_list: Dict[int, List[int]] = {i: [] for i in range(num_nodes)}
        self.edge_count = 0

    def add_edge(self, from_node: int, to_node: int):
        """
        添加有向边 from_node -> to_node

        Parameters:
            from_node: 源节点索引
            to_node: 目标节点索引
        """
        if from_node < 0 or from_node >= self.num_nodes:
            raise ValueError(f"from_node {from_node} out of range [0, {self.num_nodes})")
        if to_node < 0 or to_node >= self.num_nodes:
            raise ValueError(f"to_node {to_node} out of range [0, {self.num_nodes})")

        # 如果边已存在，不重复添加
        if self.adj_matrix[from_node, to_node] == 0:
            self.adj_matrix[from_node, to_node] = 1.0
            self.adj_list[from_node].append(to_node)
            self.edge_count += 1

    def remove_edge(self, from_node: int, to_node: int):
        """移除一条边"""
        if self.adj_matrix[from_node, to_node] == 1.0:
            self.adj_matrix[from_node, to_node] = 0.0
            if to_node in self.adj_list[from_node]:
                self.adj_list[from_node].remove(to_node)
            self.edge_count -= 1

    def get_out_degree(self, node: int) -> int:
        """获取节点的出度 (外链数量)"""
        return len(self.adj_list[node])

    def get_in_degree(self, node: int) -> int:
        """获取节点的入度 (入链数量)"""
        return int(np.sum(self.adj_matrix[:, node]))

    def get_neighbors(self, node: int, direction: str = "out") -> List[int]:
        """
        获取邻居节点

        Parameters:
            node: 节点索引
            direction: 'out' 或 'in'

        Returns:
            邻居节点列表
        """
        if direction == "out":
            return self.adj_list[node]
        elif direction == "in":
            return [i for i in range(self.num_nodes) if self.adj_matrix[i, node] == 1.0]
        else:
            raise ValueError(f"Unknown direction: {direction}")

    def to_transition_matrix(self) -> np.ndarray:
        """
        将图转换为转移矩阵 (Transition Matrix)

        PageRank 的转移矩阵 M 满足：
        - M[i,j] = 1/L(j) 如果 j 指向 i (即从 j 可以跳转到 i)
        - M[i,j] = 0 如果 j 不指向 i
        - 对于悬垂节点 (L(j)=0)，M[:,j] = 1/N (均匀分布)

        Returns:
            转移矩阵，形状为 (N, N)
        """
        M = np.zeros((self.num_nodes, self.num_nodes), dtype=np.float64)

        for j in range(self.num_nodes):
            out_degree = len(self.adj_list[j])
            if out_degree > 0:
                # 正常节点：按出链均匀分布 PageRank
                for i in self.adj_list[j]:
                    M[i, j] = 1.0 / out_degree
            else:
                # 悬垂节点：PageRank 均匀分配给所有节点
                M[:, j] = 1.0 / self.num_nodes

        return M

    def to_sparse_transition_matrix(self) -> sparse.csr_matrix:
        """
        将图转换为稀疏转移矩阵

        使用 CSR (Compressed Sparse Row) 格式存储，
        节省内存并加速矩阵运算。

        Returns:
            稀疏转移矩阵
        """
        rows, cols, data = [], [], []

        for j in range(self.num_nodes):
            out_degree = len(self.adj_list[j])
            if out_degree > 0:
                for i in self.adj_list[j]:
                    rows.append(i)
                    cols.append(j)
                    data.append(1.0 / out_degree)
            else:
                # 悬垂节点：均匀分布
                for i in range(self.num_nodes):
                    rows.append(i)
                    cols.append(j)
                    data.append(1.0 / self.num_nodes)

        return sparse.csr_matrix((data, (rows, cols)),
                                  shape=(self.num_nodes, self.num_nodes))

    def to_adjacency_list(self) -> Dict[int, List[int]]:
        """
        返回邻接表的深拷贝

        Returns:
            {节点: [邻居节点列表]}
        """
        return {k: list(v) for k, v in self.adj_list.items()}

    def get_dangling_nodes(self) -> List[int]:
        """
        获取所有悬垂节点 (没有出链的节点)

        Returns:
            悬垂节点列表
        """
        return [i for i in range(self.num_nodes) if len(self.adj_list[i]) == 0]

    def get_density(self) -> float:
        """获取图的边密度"""
        max_edges = self.num_nodes * (self.num_nodes - 1)
        if max_edges == 0:
            return 0.0
        return self.edge_count / max_edges

    def __repr__(self):
        return (f"Graph(num_nodes={self.num_nodes}, edges={self.edge_count}, "
                f"density={self.get_density():.4f})")


def create_web_graph() -> Graph:
    """
    创建一个示例网页图

    模拟一个小型网站，包含 6 个页面：
    A -> B, C
    B -> C, D
    C -> A
    D -> C, E
    E -> A, D
    F -> E

    这个图包含一个悬垂节点 (无出链的节点) 用于演示处理。

    Returns:
        包含示例网页链接的 Graph 对象
    """
    graph = Graph(6)

    # 定义链接结构
    edges = [
        (0, 1), (0, 2),  # A -> B, C
        (1, 2), (1, 3),  # B -> C, D
        (2, 0),          # C -> A
        (3, 2), (3, 4),  # D -> C, E
        (4, 0), (4, 3),  # E -> A, D
        (5, 4),          # F -> E
    ]

    for from_node, to_node in edges:
        graph.add_edge(from_node, to_node)

    return graph


def create_random_graph(n: int, m: int, seed: Optional[int] = None) -> Graph:
    """
    创建随机有向图

    使用 Erdős–Rényi 模型生成随机图：
    - n: 节点数
    - m: 边数
    - 每个节点至少有 1 条出链 (避免悬垂节点)

    Parameters:
        n: 节点数量
        m: 边数量
        seed: 随机种子

    Returns:
        随机有向图
    """
    if seed is not None:
        np.random.seed(seed)

    graph = Graph(n)

    # 确保每个节点至少有一条出链
    for i in range(n):
        j = np.random.randint(0, n)
        if j != i:
            graph.add_edge(i, j)

    # 添加额外边
    edges_added = n
    attempts = 0
    while edges_added < m and attempts < m * 10:
        i = np.random.randint(0, n)
        j = np.random.randint(0, n)
        if i != j:
            graph.add_edge(i, j)
            edges_added += 1
        attempts += 1

    return graph


def create_scale_free_graph(n: int, m_per_node: int = 2, seed: Optional[int] = None) -> Graph:
    """
    创建无标度图 (Scale-Free Graph)

    使用优先连接 (preferential attachment) 模型：
    新节点更倾向于链接到已有高入度的节点。

    这更真实地模拟了互联网的链接结构。

    Parameters:
        n: 节点数量
        m_per_node: 每个新节点添加的边数
        seed: 随机种子

    Returns:
        无标度有向图
    """
    if seed is not None:
        np.random.seed(seed)

    graph = Graph(n)

    # 先创建一个小的完整图作为种子
    for i in range(min(m_per_node + 1, n)):
        for j in range(i + 1, min(i + m_per_node + 1, n)):
            graph.add_edge(i, j)

    # 逐步添加节点，使用优先连接
    for new_node in range(m_per_node + 1, n):
        # 计算选择概率 (与入度成正比)
        in_degrees = np.array([graph.get_in_degree(i) for i in range(new_node)])
        total = in_degrees.sum()
        if total == 0:
            in_degrees = np.ones(new_node) / new_node
        else:
            in_degrees = in_degrees / total

        # 选择 m_per_node 个目标节点
        targets = np.random.choice(new_node, size=min(m_per_node, new_node),
                                   replace=False, p=in_degrees)
        for target in targets:
            graph.add_edge(new_node, int(target))

    return graph
