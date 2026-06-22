"""Basic usage example for PageRank algorithm."""

import sys
sys.path.insert(0, '/home/siok/project_copyninja/projects/pagerank')

from src.graph import WebGraph
from src.pagerank import PageRank
from src.visualizer import PageRankVisualizer


def main():
    """Demonstrate basic PageRank usage."""

    # Create a web graph
    print("Creating web graph...")
    graph = WebGraph()

    # Add links between pages
    graph.add_link("Google", "Gmail")
    graph.add_link("Google", "Maps")
    graph.add_link("Google", "YouTube")

    graph.add_link("Gmail", "Google")
    graph.add_link("Maps", "Google")

    graph.add_link("YouTube", "Google")
    graph.add_link("YouTube", "Netflix")

    graph.add_link("Netflix", "YouTube")
    graph.add_link("Netflix", "Amazon")

    graph.add_link("Amazon", "Netflix")
    graph.add_link("Amazon", "Google")

    print(f"Graph: {graph}")
    print(f"Pages: {list(graph.page_names.values())}")

    # Compute PageRank
    print("\nComputing PageRank (damping_factor=0.85)...")
    pr = PageRank(damping_factor=0.85)
    result = pr.compute(graph, max_iterations=100, tolerance=1e-6)

    print(f"Converged: {result.converged}")
    print(f"Iterations: {result.iterations}")
    print(f"Final difference: {result.final_diff:.2e}")

    # Display results
    print("\nPageRank Results:")
    print("-" * 40)
    for page, score in result.ranked_pages:
        print(f"{page:15} {score:.6f}")

    # Compare different damping factors
    print("\n\nComparing damping factors...")
    print("-" * 60)
    print(f"{'Page':15} {'d=0.5':>10} {'d=0.85':>10} {'d=0.95':>10}")
    print("-" * 60)

    for d in [0.5, 0.85, 0.95]:
        pr_d = PageRank(damping_factor=d)
        result_d = pr_d.compute(graph)

        if d == 0.5:
            scores_05 = {page: score for page, score in result_d.ranked_pages}
        elif d == 0.85:
            scores_085 = {page: score for page, score in result_d.ranked_pages}
        else:
            scores_095 = {page: score for page, score in result_d.ranked_pages}

    for page in graph.page_names.values():
        print(f"{page:15} {scores_05[page]:10.6f} {scores_085[page]:10.6f} {scores_095[page]:10.6f}")

    # Demonstrate different computation methods
    print("\n\nComparing computation methods...")
    print("-" * 40)

    result_iterative = pr.compute(graph)
    result_power = pr.compute_power_iteration(graph)
    result_algebraic = pr.compute_algebraic(graph)

    print("Method          Top Page    Score")
    print("-" * 40)
    print(f"Iterative       {result_iterative.ranked_pages[0][0]:10} {result_iterative.ranked_pages[0][1]:.6f}")
    print(f"Power Iter      {result_power.ranked_pages[0][0]:10} {result_power.ranked_pages[0][1]:.6f}")
    print(f"Algebraic       {result_algebraic.ranked_pages[0][0]:10} {result_algebraic.ranked_pages[0][1]:.6f}")

    print("\nDone!")


if __name__ == "__main__":
    main()
