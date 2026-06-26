"""
简单 PageRank 示例 - Simple PageRank Example

演示如何使用 PageRank 算法对小型网页图进行排序。
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.graph import create_web_graph, Graph
from src.pagerank import compute_pagerank, get_top_pages
from src.hits import compute_hits


def main():
    print("=" * 60)
    print("简单 PageRank 示例")
    print("Simple PageRank Example")
    print("=" * 60)

    # 创建示例网页图
    graph = create_web_graph()
    print(f"\n图信息 / Graph Info:")
    print(f"  {graph}")
    print(f"\n节点名称 / Node Names:")
    names = ['A', 'B', 'C', 'D', 'E', 'F']
    for i, name in enumerate(names):
        print(f"  {i}: {name}")

    # 打印图结构
    print(f"\n图结构 / Graph Structure:")
    for i in range(graph.num_nodes):
        neighbors = graph.get_neighbors(i, "out")
        neighbor_names = [names[n] for n in neighbors]
        print(f"  {names[i]} -> {', '.join(neighbor_names) if neighbor_names else '(none)'}")

    # 计算 PageRank
    print(f"\n计算 PageRank (damping=0.85)...")
    pr, history, iterations = compute_pagerank(graph, damping=0.85)
    print(f"  收敛迭代次数 / Iterations: {iterations}")
    print(f"  最终变化量 / Final change: {history[-1]:.2e}")

    # 显示结果
    print(f"\nPageRank 分数 / PageRank Scores:")
    print("-" * 40)
    print(f"  {'页面':<8} {'PageRank':<15} {'排名':<8}")
    print("-" * 40)

    sorted_indices = get_top_pages(pr, graph.num_nodes)
    for rank, idx in enumerate(sorted_indices, 1):
        print(f"  {names[idx]:<8} {pr[idx]:<15.6f} {rank:<8}")

    # 与 HITS 算法对比
    print(f"\n" + "=" * 60)
    print("与 HITS 算法对比 / Comparison with HITS Algorithm")
    print("=" * 60)

    authority, hub, hits_history, hits_iter = compute_hits(graph)
    print(f"\nHITS 结果:")
    print(f"  收敛迭代次数 / Iterations: {hits_iter}")
    print(f"\n  {'页面':<8} {'Authority':<15} {'Hub':<15}")
    print("-" * 40)
    for i in range(graph.num_nodes):
        print(f"  {names[i]:<8} {authority[i]:<15.6f} {hub[i]:<15.6f}")

    # 收敛历史
    print(f"\n" + "=" * 60)
    print("收敛历史 / Convergence History")
    print("=" * 60)
    print(f"  {'迭代':<10} {'变化量':<20}")
    print("-" * 30)
    for i, change in enumerate(history[:10]):
        print(f"  {i+1:<10} {change:<20.6e}")
    if len(history) > 10:
        print(f"  ... ({len(history) - 10} more iterations)")


if __name__ == "__main__":
    main()
