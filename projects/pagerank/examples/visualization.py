"""Visualization example for PageRank algorithm."""

import sys
sys.path.insert(0, '/home/siok/project_copyninja/projects/pagerank')

from src.graph import WebGraph
from src.pagerank import PageRank
from src.visualizer import PageRankVisualizer

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend


def main():
    """Demonstrate PageRank visualization."""

    # Create a sample web graph
    print("Creating sample web graph...")
    edges = [
        ("Home", "About"),
        ("Home", "Products"),
        ("Home", "Contact"),
        ("About", "Home"),
        ("Products", "Home"),
        ("Products", "Product A"),
        ("Products", "Product B"),
        ("Product A", "Products"),
        ("Product B", "Products"),
        ("Contact", "Home"),
        ("Blog", "Home"),
        ("Blog", "Post 1"),
        ("Blog", "Post 2"),
        ("Post 1", "Blog"),
        ("Post 2", "Blog"),
        ("Post 1", "Products"),
    ]
    graph = WebGraph.from_edges(edges)

    # Compute PageRank
    print("Computing PageRank...")
    pr = PageRank(damping_factor=0.85)
    result = pr.compute(graph)

    print(f"Converged in {result.iterations} iterations")

    # Visualize ranked pages
    print("\nCreating ranked pages chart...")
    fig1 = PageRankVisualizer.plot_ranked_pages(
        result,
        top_n=10,
        title="Top Pages by PageRank Score"
    )
    fig1.savefig("/home/siok/project_copyninja/projects/pagerank/examples/ranked_pages.png",
                 dpi=150, bbox_inches='tight')
    print("Saved: ranked_pages.png")

    # Visualize graph structure
    print("\nCreating graph visualization...")
    fig2 = PageRankVisualizer.plot_graph(
        graph,
        result,
        title="Web Graph with PageRank Scores"
    )
    fig2.savefig("/home/siok/project_copyninja/projects/pagerank/examples/graph_visualization.png",
                 dpi=150, bbox_inches='tight')
    print("Saved: graph_visualization.png")

    # Visualize convergence
    print("\nCreating convergence plot...")
    # Collect scores at each iteration
    scores_history = []
    n = graph.num_pages
    transition = graph.build_transition_matrix()

    import numpy as np
    scores = np.ones(n) / n
    damping_vector = np.ones(n) * (1 - 0.85) / n

    for _ in range(20):
        scores_history.append(scores.copy())
        scores = damping_vector + 0.85 * (transition @ scores)
        scores = scores / scores.sum()

    fig3 = PageRankVisualizer.plot_convergence(
        scores_history,
        title="PageRank Score Convergence"
    )
    fig3.savefig("/home/siok/project_copyninja/projects/pagerank/examples/convergence.png",
                 dpi=150, bbox_inches='tight')
    print("Saved: convergence.png")

    # Compare damping factors
    print("\nCreating damping factor comparison...")
    fig4 = PageRankVisualizer.plot_damping_factor_comparison(
        graph,
        damping_factors=[0.5, 0.7, 0.85, 0.95]
    )
    fig4.savefig("/home/siok/project_copyninja/projects/pagerank/examples/damping_comparison.png",
                 dpi=150, bbox_inches='tight')
    print("Saved: damping_comparison.png")

    print("\nAll visualizations saved to examples/ directory!")
    print("Done!")


if __name__ == "__main__":
    main()
