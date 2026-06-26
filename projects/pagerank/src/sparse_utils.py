"""
稀疏矩阵优化工具 - Sparse Matrix Utilities

提供稀疏矩阵相关的辅助功能：
- 稀疏矩阵格式转换
- 内存使用分析
- 稀疏运算性能对比
"""

import numpy as np
from scipy import sparse
from typing import Tuple


def analyze_memory_usage(adj_matrix: np.ndarray, adj_list: dict) -> dict:
    """
    分析邻接矩阵和邻接表的内存使用

    Parameters:
        adj_matrix: 稠密邻接矩阵
        adj_list: 邻接表

    Returns:
        内存使用分析字典
    """
    dense_bytes = adj_matrix.nbytes

    # 估算邻接表内存
    list_bytes = 0
    for node, neighbors in adj_list.items():
        list_bytes += 8  # dict entry overhead
        list_bytes += len(neighbors) * 8  # neighbor indices

    # 估算 CSR 稀疏矩阵内存
    rows, cols, data = [], [], []
    for node, neighbors in adj_list.items():
        for neighbor in neighbors:
            rows.append(node)
            cols.append(neighbor)
            data.append(1.0)

    if rows:
        csr = sparse.csr_matrix((data, (rows, cols)),
                                  shape=adj_matrix.shape)
        sparse_bytes = csr.data.nbytes + csr.indices.nbytes + csr.indptr.nbytes
    else:
        sparse_bytes = 0

    density = np.count_nonzero(adj_matrix) / adj_matrix.size

    return {
        'dense_bytes': dense_bytes,
        'sparse_bytes': sparse_bytes,
        'list_bytes': list_bytes,
        'density': density,
        'compression_ratio': dense_bytes / max(sparse_bytes, 1),
    }


def dense_to_csr(adj_matrix: np.ndarray) -> sparse.csr_matrix:
    """
    将稠密邻接矩阵转换为 CSR 格式

    Parameters:
        adj_matrix: 稠密邻接矩阵

    Returns:
        CSR 格式的稀疏矩阵
    """
    return sparse.csr_matrix(adj_matrix)


def csr_to_dense(csr_matrix: sparse.csr_matrix) -> np.ndarray:
    """
    将 CSR 格式转换回稠密矩阵

    Parameters:
        csr_matrix: CSR 格式的稀疏矩阵

    Returns:
        稠密 numpy 数组
    """
    return csr_matrix.toarray()


def compute_sparsity(adj_matrix: np.ndarray) -> float:
    """
    计算矩阵的稀疏度 (零元素比例)

    Parameters:
        adj_matrix: 矩阵

    Returns:
        稀疏度 (0 到 1 之间，越接近 1 越稀疏)
    """
    total = adj_matrix.size
    zeros = np.count_nonzero(adj_matrix == 0)
    return zeros / total


def format_memory_size(bytes_count: int) -> str:
    """
    格式化内存大小为人类可读的字符串

    Parameters:
        bytes_count: 字节数

    Returns:
        格式化后的字符串
    """
    if bytes_count < 1024:
        return f"{bytes_count} B"
    elif bytes_count < 1024 ** 2:
        return f"{bytes_count / 1024:.2f} KB"
    elif bytes_count < 1024 ** 3:
        return f"{bytes_count / (1024 ** 2):.2f} MB"
    else:
        return f"{bytes_count / (1024 ** 3):.2f} GB"
