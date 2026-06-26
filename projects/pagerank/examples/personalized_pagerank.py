"""
个性化 PageRank 示例 - Personalized PageRank Demo

演示个性化 PageRank 的概念：
- 不同用户有不同的"兴趣点"
- 从不同种子节点开始的随机游走会给出不同的排名
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.graph import create_web_graph
from src.pagerank import (
    compute_pagerank,
    compute_pagerank_with_personalization,
    get_top_pages
)


def main():
    print("=" * 60)
    print("个性化 PageRank 示例")
    print("Personalized PageRank Demo")
    print("=" * 60)

    # 创建示例图
    graph = create_web_graph()
    names = ['A', 'B', 'C', 'D', 'E', 'F']

    print(f"\n图结构:")
    for i in range(graph.num_nodes):
        neighbors = graph.get_neighbors(i, "out")
        neighbor_names = [names[n] for n in neighbors]
        print(f"  {names[i]} -> {', '.join(neighbor_names) if neighbor_names else '(none)'}")

    # 1. 标准 PageRank (均匀个人化)
    print(f"\n{'=' * 60}")
    print("1. 标准 PageRank (均匀个人化)")
    print("   Standard PageRank (uniform personalization)")
    print("=" * 60)

    pr_standard, _, _ = compute_pagerank(graph)
    print(f"\n  排名 / Ranking:")
    sorted_idx = get_top_pages(pr_standard, graph.num_nodes)
    for rank, idx in enumerate(sorted_idx, 1):
        print(f"    {rank:>2}. {names[idx]:<5} = {pr_standard[idx]:.6f}")

    # 2. 个性化 PageRank - 从节点 A 开始
    print(f"\n{'=' * 60}")
    print("2. 个性化 PageRank - 从 A 开始")
    print("   Personalized PageRank - starting from A")
    print("=" * 60)

    personalization_a = [0.0] * graph.num_nodes
    personalization_a[0] = 1.0  # 100% 从 A 开始
    pr_a, _, _ = compute_pagerank_with_personalization(
        graph, personalization=personalization_a
    )
    print(f"\n  排名 / Ranking:")
    sorted_idx = get_top_pages(pr_a, graph.num_nodes)
    for rank, idx in enumerate(sorted_idx, 1):
        print(f"    {rank:>2}. {names[idx]:<5} = {pr_a[idx]:.6f}")

    # 3. 个性化 PageRank - 从节点 E 开始
    print(f"\n{'=' * 60}")
    print("3. 个性化 PageRank - 从 E 开始")
    print("   Personalized PageRank - starting from E")
    print("=" * 60)

    personalization_e = [0.0] * graph.num_nodes
    personalization_e[4] = 1.0  # 100% 从 E 开始
    pr_e, _, _ = compute_pagerank_with_personalization(
        graph, personalization=personalization_e
    )
    print(f"\n  排名 / Ranking:")
    sorted_idx = get_top_pages(pr_e, graph.num_nodes)
    for rank, idx in enumerate(sorted_idx, 1):
        print(f"    {rank:>2}. {names[idx]:<5} = {pr_e[idx]:.6f}")

    # 4. 混合个人化
    print(f"\n{'=' * 60}")
    print("4. 混合个人化 - A(60%) + E(40%)")
    print("   Mixed personalization - A(60%) + E(40%)")
    print("=" * 60)

    personalization_mix = [0.0] * graph.num_nodes
    personalization_mix[0] = 0.6  # 60% 从 A 开始
    personalization_mix[4] = 0.4  # 40% 从 E 开始
    pr_mix, _, _ = compute_pagerank_with_personalization(
        graph, personalization=personalization_mix
    )
    print(f"\n  排名 / Ranking:")
    sorted_idx = get_top_pages(pr_mix, graph.num_nodes)
    for rank, idx in enumerate(sorted_idx, 1):
        print(f"    {rank:>2}. {names[idx]:<5} = {pr_mix[idx]:.6f}")

    # 5. 阻尼因子影响
    print(f"\n{'=' * 60}")
    print("5. 阻尼因子影响 / Damping Factor Impact")
    print("=" * 60)

    damping_values = [0.5, 0.7, 0.85, 0.95, 1.0]
    print(f"\n  {'阻尼因子':<12} {'Top1':<6} {'Top2':<6} {'Top3':<6} {'Top4':<6}")
    print(f"  {'-' * 40}")

    for d in damping_values:
        pr, _, _ = compute_pagerank(graph, damping=d)
        top = get_top_pages(pr, 4)
        top_names = [names[i] for i in top]
        print(f"  {d:<12.2f} {top_names[0]:<6} {top_names[1]:<6} {top_names[2]:<6} {top_names[3]:<6}")


if __name__ == "__main__":
    main()
