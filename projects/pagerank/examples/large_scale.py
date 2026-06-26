"""
大规模图模拟 - Large-Scale Graph Simulation

演示在大规模图上运行 PageRank 的性能。
比较稠密矩阵和稀疏矩阵的性能差异。
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.graph import create_random_graph, create_scale_free_graph, Graph
from src.pagerank import compute_pagerank, expected_iterations
from src.sparse_utils import analyze_memory_usage, format_memory_size


def benchmark_pagerank(graph: Graph, label: str):
    """
    基准测试 PageRank 计算

    比较稠密矩阵和稀疏矩阵的：
    - 内存使用
    - 计算时间
    """
    print(f"\n{'=' * 50}")
    print(f"测试 / Test: {label}")
    print(f"{'=' * 50}")
    print(f"  节点数 / Nodes: {graph.num_nodes}")
    print(f"  边数 / Edges: {graph.edge_count}")
    print(f"  密度 / Density: {graph.get_density():.6f}")

    # 内存分析
    memory = analyze_memory_usage(graph.adj_matrix, graph.adj_list)
    print(f"\n  内存使用 / Memory Usage:")
    print(f"    稠密矩阵 / Dense:    {format_memory_size(memory['dense_bytes'])}")
    print(f"    稀疏矩阵 / Sparse:   {format_memory_size(memory['sparse_bytes'])}")
    print(f"    邻接表 / Adj List:  {format_memory_size(memory['list_bytes'])}")
    print(f"    压缩比 / Compression: {memory['compression_ratio']:.1f}x")

    # 估算收敛迭代次数
    expected = expected_iterations(graph.num_nodes)
    print(f"\n  估算收敛迭代 / Expected iterations: ~{expected}")

    # 稠密矩阵计时
    t0 = time.time()
    pr_dense, hist_dense, iter_dense = compute_pagerank(
        graph, damping=0.85, use_sparse=False
    )
    t_dense = time.time() - t0

    # 稀疏矩阵计时
    t0 = time.time()
    pr_sparse, hist_sparse, iter_sparse = compute_pagerank(
        graph, damping=0.85, use_sparse=True
    )
    t_sparse = time.time() - t0

    # 结果对比
    print(f"\n  计算结果对比 / Results Comparison:")
    print(f"    稠密矩阵时间 / Dense time:    {t_dense:.4f}s")
    print(f"    稀疏矩阵时间 / Sparse time:   {t_sparse:.4f}s")
    if t_sparse > 0:
        print(f"    加速比 / Speedup:             {t_dense / t_sparse:.2f}x")

    # 验证结果一致性
    diff = abs(pr_dense - pr_sparse).max()
    print(f"    结果差异 / Max difference:    {diff:.2e}")

    # Top 10 页面
    top_indices = pr_sparse.argsort()[::-1][:10]
    print(f"\n  Top 10 页面 / Top 10 Pages:")
    for rank, idx in enumerate(top_indices, 1):
        print(f"    {rank:>2}. Node {idx:>5}: {pr_sparse[idx]:.8f}")


def main():
    print("=" * 60)
    print("大规模图 PageRank 模拟")
    print("Large-Scale Graph PageRank Simulation")
    print("=" * 60)

    # 测试不同规模的图
    sizes = [100, 500, 1000]

    for n in sizes:
        # 随机图
        random_graph = create_random_graph(n, n * 3, seed=42)
        benchmark_pagerank(random_graph, f"随机图 / Random Graph (n={n}, m={random_graph.edge_count})")

    # 无标度图
    print(f"\n{'=' * 60}")
    print("无标度图测试 / Scale-Free Graph Test")
    print("=" * 60)

    sf_graph = create_scale_free_graph(500, m_per_node=3, seed=42)
    benchmark_pagerank(sf_graph, f"无标度图 / Scale-Free (n={sf_graph.num_nodes})")

    # 大规模图
    print(f"\n{'=' * 60}")
    print("大规模图测试 / Large-Scale Graph Test")
    print("=" * 60)

    large_graph = create_random_graph(5000, 30000, seed=42)
    benchmark_pagerank(large_graph, f"大规模随机图 / Large Random Graph (n={large_graph.num_nodes})")

    print(f"\n{'=' * 60}")
    print("测试完成 / Benchmark Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
