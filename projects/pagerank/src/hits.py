"""
HITS 算法模块 - HITS Algorithm Module

实现 HITS (Hyperlink-Induced Topic Search) 算法：
- Hub 值：页面指向高质量页面的程度
- Authority 值：页面被高质量页面引用的程度

HITS 与 PageRank 的区别：
- PageRank：全局重要性，考虑整个互联网
- HITS：局部重要性，针对特定查询的子图

算法：
1. 初始化所有 Hub 和 Authority 值为 1
2. 迭代更新：
   - Authority = M^T * Hub
   - Hub = M * Authority
3. 每次迭代后归一化
4. 直到收敛
"""

import numpy as np
from scipy import sparse
from typing import Tuple, Optional, List
from .graph import Graph


def compute_hits(
    graph: Graph,
    max_iter: int = 100,
    tol: float = 1e-6
) -> Tuple[np.ndarray, np.ndarray, List[float], int]:
    """
    计算 HITS 算法的 Hub 和 Authority 值

    HITS 算法步骤：
    1. 初始化：所有节点的 hub 和 authority 值为 1
    2. Authority 更新：a_i = sum(h_j) for all j linking to i
       即：a = M^T * h
    3. Hub 更新：h_i = sum(a_j) for all i linking to j
       即：h = M * a
    4. 归一化：a = a / ||a||, h = h / ||h||
    5. 重复直到收敛

    Parameters:
        graph: 图对象
        max_iter: 最大迭代次数
        tol: 收敛容差

    Returns:
        (authority, hub, convergence_history, iterations_used)
        - authority: Authority 分数数组
        - hub: Hub 分数数组
        - convergence_history: 每次迭代的 Authority 变化量
        - iterations_used: 实际迭代次数
    """
    n = graph.num_nodes

    # 初始化
    authority = np.ones(n, dtype=np.float64)
    hub = np.ones(n, dtype=np.float64)

    # 获取邻接矩阵 (邻接矩阵，不是转移矩阵)
    adj_matrix = graph.adj_matrix.copy()

    convergence_history = []
    iterations_used = 0

    for i in range(max_iter):
        authority_old = authority.copy()

        # Authority 更新：a = M^T * h
        # 页面 i 的 authority 等于所有指向它的页面的 hub 值之和
        authority = adj_matrix.T @ hub

        # Hub 更新：h = M * a
        # 页面 i 的 hub 等于它指向的所有页面的 authority 值之和
        hub = adj_matrix @ authority

        # 归一化
        auth_norm = np.linalg.norm(authority)
        hub_norm = np.linalg.norm(hub)

        if auth_norm > 0:
            authority = authority / auth_norm
        if hub_norm > 0:
            hub = hub / hub_norm

        # 收敛检查
        change = np.linalg.norm(authority - authority_old, 2)
        convergence_history.append(change)
        iterations_used = i + 1

        if change < tol:
            break

    return authority, hub, convergence_history, iterations_used


def compute_hits_for_subgraph(
    graph: Graph,
    seed_nodes: List[int],
    max_iter: int = 100,
    tol: float = 1e-6
) -> Tuple[np.ndarray, np.ndarray, List[int]]:
    """
    计算子图上的 HITS 值

    从种子节点出发，扩展相关的子图，
    在子图上运行 HITS 算法。

    Parameters:
        graph: 完整的图对象
        seed_nodes: 种子节点列表
        max_iter: 最大迭代次数
        tol: 收敛容差

    Returns:
        (authority, hub, subgraph_nodes)
        - authority: 完整图上的 Authority 值 (子图外为 0)
        - hub: 完整图上的 Hub 值 (子图外为 0)
        - subgraph_nodes: 子图中的节点列表
    """
    # BFS 扩展子图
    visited = set(seed_nodes)
    queue = list(seed_nodes)

    while queue:
        node = queue.pop(0)
        # 添加入链和出链邻居
        for neighbor in graph.get_neighbors(node, "out"):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
        for neighbor in graph.get_neighbors(node, "in"):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    subgraph_nodes = sorted(visited)

    # 创建子图
    node_to_idx = {node: i for i, node in enumerate(subgraph_nodes)}
    subgraph = Graph(len(subgraph_nodes))

    for node in subgraph_nodes:
        for neighbor in graph.get_neighbors(node, "out"):
            if neighbor in node_to_idx:
                subgraph.add_edge(node_to_idx[node], node_to_idx[neighbor])

    # 在子图上运行 HITS
    authority_sub, hub_sub, _, _ = compute_hits(subgraph, max_iter, tol)

    # 映射回完整图
    authority = np.zeros(graph.num_nodes)
    hub = np.zeros(graph.num_nodes)

    for node, idx in node_to_idx.items():
        authority[node] = authority_sub[idx]
        hub[node] = hub_sub[idx]

    return authority, hub, subgraph_nodes
