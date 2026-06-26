"""
收敛可视化 - Convergence Visualization

可视化 PageRank 算法的收敛过程和结果。
使用 matplotlib 绘制：
- 收敛曲线
- PageRank 分数柱状图
- 图结构可视化
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.graph import create_web_graph, create_random_graph
from src.pagerank import compute_pagerank, compute_pagerank_with_personalization
from src.hits import compute_hits

try:
    import matplotlib
    matplotlib.use('Agg')  # 非交互式后端
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("警告: matplotlib 未安装，跳过可视化")


def plot_convergence(history, output_path="convergence.png"):
    """
    绘制收敛曲线

    Parameters:
        history: 收敛历史 (每次迭代的 L1 变化量)
        output_path: 输出文件路径
    """
    if not MATPLOTLIB_AVAILABLE:
        return

    fig, ax = plt.subplots(1, 1, figsize=(10, 6))

    iterations = np.arange(1, len(history) + 1)
    ax.plot(iterations, history, 'b-', linewidth=1.5, marker='o', markersize=3)

    # 标记收敛点
    tol = 1e-6
    converged_idx = np.where(np.array(history) < tol)[0]
    if len(converged_idx) > 0:
        first_converged = converged_idx[0] + 1
        ax.axvline(x=first_converged, color='r', linestyle='--', alpha=0.7,
                   label=f'Converged at iteration {first_converged}')
        ax.axhline(y=tol, color='g', linestyle='--', alpha=0.7,
                   label=f'Tolerance = {tol}')

    ax.set_xlabel('Iteration', fontsize=12)
    ax.set_ylabel('L1 Change', fontsize=12)
    ax.set_title('PageRank Convergence', fontsize=14)
    ax.set_yscale('log')
    ax.grid(True, alpha=0.3)
    ax.legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  收敛曲线已保存 / Convergence plot saved: {output_path}")


def plot_pagerank_scores(graph, pagerank_values, output_path="pagerank_scores.png"):
    """
    绘制 PageRank 分数柱状图

    Parameters:
        graph: 图对象
        pagerank_values: PageRank 分数
        output_path: 输出文件路径
    """
    if not MATPLOTLIB_AVAILABLE:
        return

    names = [f'Node {i}' for i in range(graph.num_nodes)]
    sorted_indices = np.argsort(pagerank_values)[::-1]

    fig, ax = plt.subplots(1, 1, figsize=(10, 6))

    colors = plt.cm.viridis(np.linspace(0.2, 0.8, graph.num_nodes))
    bars = ax.bar(range(graph.num_nodes), pagerank_values[sorted_indices], color=colors)

    # 标记 Top 3
    for i in range(min(3, graph.num_nodes)):
        bars[i].set_color('red')
        bars[i].set_alpha(0.8)

    ax.set_xlabel('Node (sorted by PageRank)', fontsize=12)
    ax.set_ylabel('PageRank Score', fontsize=12)
    ax.set_title('PageRank Scores (sorted)', fontsize=14)
    ax.set_xticks(range(graph.num_nodes))
    ax.set_xticklabels([names[i] for i in sorted_indices], rotation=45, ha='right')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  PageRank 分数图已保存 / Scores plot saved: {output_path}")


def plot_comparison(graph, output_path="comparison.png"):
    """
    对比 PageRank 和 HITS 的结果

    Parameters:
        graph: 图对象
        output_path: 输出文件路径
    """
    if not MATPLOTLIB_AVAILABLE:
        return

    # 计算 PageRank 和 HITS
    pr, _, _ = compute_pagerank(graph)
    authority, hub, _, _ = compute_hits(graph)

    names = [f'Node {i}' for i in range(graph.num_nodes)]

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # PageRank
    sorted_pr = np.argsort(pr)[::-1]
    axes[0].bar(range(graph.num_nodes), pr[sorted_pr], color='steelblue')
    axes[0].set_xlabel('Node')
    axes[0].set_ylabel('Score')
    axes[0].set_title('PageRank')
    axes[0].set_xticks([])

    # Authority
    sorted_auth = np.argsort(authority)[::-1]
    axes[1].bar(range(graph.num_nodes), authority[sorted_auth], color='coral')
    axes[1].set_xlabel('Node')
    axes[1].set_ylabel('Score')
    axes[1].set_title('Authority (HITS)')
    axes[1].set_xticks([])

    # Hub
    sorted_hub = np.argsort(hub)[::-1]
    axes[2].bar(range(graph.num_nodes), hub[sorted_hub], color='mediumpurple')
    axes[2].set_xlabel('Node')
    axes[2].set_ylabel('Score')
    axes[2].set_title('Hub (HITS)')
    axes[2].set_xticks([])

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  对比图已保存 / Comparison plot saved: {output_path}")


def plot_personalized_comparison(graph, output_path="personalized_comparison.png"):
    """
    对比不同个人化向量的结果

    Parameters:
        graph: 图对象
        output_path: 输出文件路径
    """
    if not MATPLOTLIB_AVAILABLE:
        return

    names = [f'Node {i}' for i in range(graph.num_nodes)]

    # 计算不同个人化向量
    pr_standard, _, _ = compute_pagerank(graph)

    personalizations = {
        'From Node 0': [1.0] + [0.0] * (graph.num_nodes - 1),
        'From Node 4': [0.0] * 4 + [1.0, 0.0],
        'From Node 0+4': [0.5] + [0.0] * 3 + [0.5, 0.0],
    }

    fig, axes = plt.subplots(1, len(personalizations) + 1, figsize=(5 * (len(personalizations) + 1), 5))

    # Standard
    sorted_pr = np.argsort(pr_standard)[::-1]
    axes[0].bar(range(graph.num_nodes), pr_standard[sorted_pr], color='gray', alpha=0.7)
    axes[0].set_title('Standard PR')
    axes[0].set_xticks([])
    axes[0].set_ylabel('Score')

    for idx, (label, personalization) in enumerate(personalizations.items()):
        pr, _, _ = compute_pagerank_with_personalization(graph, personalization=personalization)
        sorted_p = np.argsort(pr)[::-1]
        axes[idx + 1].bar(range(graph.num_nodes), pr[sorted_p], color='steelblue', alpha=0.7)
        axes[idx + 1].set_title(label)
        axes[idx + 1].set_xticks([])

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  个性化对比图已保存 / Personalized comparison saved: {output_path}")


def main():
    print("=" * 60)
    print("收敛可视化示例")
    print("Convergence Visualization Demo")
    print("=" * 60)

    if not MATPLOTLIB_AVAILABLE:
        print("\nmatplotlib 未安装，跳过可视化。")
        print("安装: pip install matplotlib")
        return

    # 创建示例图
    graph = create_web_graph()
    print(f"\n图信息: {graph}")

    # 1. 计算 PageRank
    pr, history, iterations = compute_pagerank(graph)
    print(f"\nPageRank 结果:")
    names = ['A', 'B', 'C', 'D', 'E', 'F']
    for i in range(graph.num_nodes):
        print(f"  {names[i]}: {pr[i]:.6f}")

    # 2. 绘制收敛曲线
    print("\n绘制收敛曲线...")
    plot_convergence(history)

    # 3. 绘制 PageRank 分数
    print("绘制 PageRank 分数...")
    plot_pagerank_scores(graph, pr)

    # 4. 对比 PageRank 和 HITS
    print("绘制对比图...")
    plot_comparison(graph)

    # 5. 个性化 PageRank 对比
    print("绘制个性化 PageRank 对比图...")
    plot_personalized_comparison(graph)

    print("\n" + "=" * 60)
    print("可视化完成 / Visualization Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
