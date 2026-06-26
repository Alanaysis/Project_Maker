"""
PageRank 核心算法模块 - PageRank Core Algorithm Module

实现 PageRank 算法及其变体：
- 标准 PageRank (幂迭代法)
- 阻尼因子处理
- 收敛检测
- 个性化 PageRank
"""

import numpy as np
from scipy import sparse
from typing import Tuple, Optional, List, Dict
from .graph import Graph


def compute_pagerank(
    graph: Graph,
    damping: float = 0.85,
    max_iter: int = 100,
    tol: float = 1e-6,
    use_sparse: bool = True
) -> Tuple[np.ndarray, List[float], int]:
    """
    使用幂迭代法计算 PageRank

    PageRank 的核心迭代公式：
    PR = (1-d)/N * 1 + d * M^T * PR

    其中：
    - d: 阻尼因子 (damping factor)
    - M: 转移矩阵
    - N: 节点总数
    - 1: 全1向量

    幂迭代法：
    1. 初始化 PR = 1/N (均匀分布)
    2. 迭代: PR_new = (1-d)/N + d * M^T * PR_old
    3. 直到收敛 ||PR_new - PR_old|| < tol

    Parameters:
        graph: 图对象
        damping: 阻尼因子，默认 0.85。表示用户继续点击链接的概率
        max_iter: 最大迭代次数
        tol: 收敛容差
        use_sparse: 是否使用稀疏矩阵加速

    Returns:
        (pagerank_values, convergence_history, iterations_used)
        - pagerank_values: PageRank 分数数组
        - convergence_history: 每次迭代的 L1 变化量
        - iterations_used: 实际迭代次数
    """
    n = graph.num_nodes

    # 初始化 PageRank 向量 (均匀分布)
    pr = np.ones(n, dtype=np.float64) / n

    # 获取转移矩阵
    if use_sparse:
        M = graph.to_sparse_transition_matrix()
        # 使用稀疏矩阵运算
        M_T = M.T.tocsr()
    else:
        M = graph.to_transition_matrix()
        M_T = M.T.copy()

    # 处理悬垂节点 (dangling nodes)
    dangling_nodes = graph.get_dangling_nodes()

    # 初始化收敛历史
    convergence_history = []
    iterations_used = 0

    for i in range(max_iter):
        pr_old = pr.copy()

        if use_sparse:
            # 稀疏矩阵计算
            # 悬垂节点的贡献：均匀分配给所有节点
            dangling_contribution = pr[dangling_nodes].sum()

            # 主要转移 + 悬垂节点贡献
            pr = (1 - damping) / n + damping * (
                M_T.dot(pr) + dangling_contribution / n
            )
        else:
            # 稠密矩阵计算
            dangling_contribution = pr[dangling_nodes].sum()
            pr = (1 - damping) / n + damping * (
                M_T @ pr + dangling_contribution / n
            )

        # 归一化 (确保概率和为 1)
        pr_sum = pr.sum()
        if pr_sum > 0:
            pr = pr / pr_sum

        # 计算收敛指标 (L1 范数变化)
        change = np.linalg.norm(pr - pr_old, 1)
        convergence_history.append(change)

        iterations_used = i + 1

        # 检查收敛
        if change < tol:
            break

    return pr, convergence_history, iterations_used


def compute_pagerank_with_personalization(
    graph: Graph,
    personalization: Optional[np.ndarray] = None,
    damping: float = 0.85,
    max_iter: int = 100,
    tol: float = 1e-6,
    use_sparse: bool = True
) -> Tuple[np.ndarray, List[float], int]:
    """
    计算个性化 PageRank (Personalized PageRank)

    个性化 PageRank 允许用户指定"兴趣点"，
    返回从这些页面开始的随机游走的重要性分数。

    公式：
    PR_p = (1-d) * p + d * M^T * PR_p

    其中 p 是个人化向量 (personalization vector)，
    表示用户从每个页面开始游走的概率。

    Parameters:
        graph: 图对象
        personalization: 个人化向量，长度等于节点数。
                         如果为 None，则使用均匀分布。
        damping: 阻尼因子
        max_iter: 最大迭代次数
        tol: 收敛容差
        use_sparse: 是否使用稀疏矩阵

    Returns:
        (personalized_pagerank, convergence_history, iterations_used)
    """
    n = graph.num_nodes

    # 设置个人化向量
    if personalization is None:
        personalization = np.ones(n, dtype=np.float64) / n
    else:
        personalization = np.asarray(personalization, dtype=np.float64).copy()
        # 归一化
        p_sum = personalization.sum()
        if p_sum > 0:
            personalization = personalization / p_sum
        else:
            personalization = np.ones(n, dtype=np.float64) / n

    pr = personalization.copy()

    # 获取转移矩阵
    if use_sparse:
        M = graph.to_sparse_transition_matrix()
        M_T = M.T.tocsr()
    else:
        M = graph.to_transition_matrix()
        M_T = M.T.copy()

    dangling_nodes = graph.get_dangling_nodes()
    convergence_history = []
    iterations_used = 0

    for i in range(max_iter):
        pr_old = pr.copy()

        if use_sparse:
            dangling_contribution = pr[dangling_nodes].sum()
            pr = (1 - damping) * personalization + damping * (
                M_T.dot(pr) + dangling_contribution / n
            )
        else:
            dangling_contribution = pr[dangling_nodes].sum()
            pr = (1 - damping) * personalization + damping * (
                M_T @ pr + dangling_contribution / n
            )

        # 归一化
        pr_sum = pr.sum()
        if pr_sum > 0:
            pr = pr / pr_sum

        change = np.linalg.norm(pr - pr_old, 1)
        convergence_history.append(change)
        iterations_used = i + 1

        if change < tol:
            break

    return pr, convergence_history, iterations_used


def compute_pagerank_batch(
    graph: Graph,
    seeds: List[int],
    damping: float = 0.85,
    max_iter: int = 100,
    tol: float = 1e-6
) -> np.ndarray:
    """
    批量计算从多个种子节点开始的个性化 PageRank

    对于每个种子节点，计算从该节点开始的随机游走
    到达每个页面的概率。

    Parameters:
        graph: 图对象
        seeds: 种子节点列表
        damping: 阻尼因子
        max_iter: 最大迭代次数
        tol: 收敛容差

    Returns:
        形状为 (len(seeds), n) 的数组，每行是对应的 PageRank 向量
    """
    n = graph.num_nodes
    results = np.zeros((len(seeds), n), dtype=np.float64)

    for idx, seed in enumerate(seeds):
        personalization = np.zeros(n, dtype=np.float64)
        personalization[seed] = 1.0
        pr, _, _ = compute_pagerank_with_personalization(
            graph, personalization=personalization,
            damping=damping, max_iter=max_iter, tol=tol
        )
        results[idx] = pr

    return results


def get_top_pages(pagerank: np.ndarray, n: int = 10) -> np.ndarray:
    """
    获取 PageRank 最高的前 N 个页面

    Parameters:
        pagerank: PageRank 分数数组
        n: 返回的页面数量

    Returns:
        按 PageRank 降序排列的节点索引数组
    """
    return np.argsort(pagerank)[::-1][:n]


def normalize_pagerank(pagerank: np.ndarray) -> np.ndarray:
    """
    归一化 PageRank 分数，使其和为 1

    Parameters:
        pagerank: 原始 PageRank 分数

    Returns:
        归一化后的 PageRank 分数
    """
    total = pagerank.sum()
    if total > 0:
        return pagerank / total
    return pagerank.copy()


def expected_iterations(n: int, tolerance: float = 1e-6) -> int:
    """
    估算 PageRank 幂迭代的收敛迭代次数

    PageRank 的收敛速度与 (1-d) * lambda_2 有关，
    其中 lambda_2 是转移矩阵的第二大特征值。

    近似公式：
    k ≈ log(tolerance) / log(d * lambda_2)

    Parameters:
        n: 节点数量
        tolerance: 收敛容差

    Returns:
        估算的迭代次数
    """
    # 简化估计：假设 lambda_2 ≈ 1 - 1/n
    # 对于 d = 0.85
    d = 0.85
    lambda_2 = 1 - 1.0 / n
    convergence_rate = d * lambda_2

    if convergence_rate >= 1:
        return float('inf')

    return int(np.ceil(np.log(tolerance) / np.log(convergence_rate)))
