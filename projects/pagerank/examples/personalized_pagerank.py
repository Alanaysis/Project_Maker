"""Example: Personalized PageRank demonstration."""

import sys
sys.path.insert(0, '/home/siok/project_copyninja/projects/pagerank')

from src.graph import WebGraph
from src.pagerank import PageRank


def main():
    """Demonstrate Personalized PageRank."""
    print("=" * 60)
    print("Personalized PageRank Example")
    print("=" * 60)

    # Create a sample web graph
    graph = WebGraph.from_edges([
        ("News", "Sports"),
        ("News", "Tech"),
        ("News", "Entertainment"),
        ("Sports", "News"),
        ("Tech", "News"),
        ("Tech", "Science"),
        ("Science", "Tech"),
        ("Entertainment", "News"),
        ("Entertainment", "Sports"),
        ("Blog", "Tech"),
        ("Blog", "Science"),
        ("Blog", "News"),
    ])

    print("\nGraph structure:")
    print(graph)

    # Standard PageRank
    pr = PageRank(damping_factor=0.85)
    standard_result = pr.compute(graph)

    print("\n--- Standard PageRank ---")
    for page, score in standard_result.ranked_pages:
        print(f"  {page:15s}: {score:.4f}")

    # Personalized PageRank: User interested in Technology
    print("\n--- Personalized PageRank (Tech enthusiast) ---")
    tech_personalization = {
        "Tech": 0.5,
        "Science": 0.3,
        "Blog": 0.2
    }

    tech_result = pr.compute_personalized(
        graph,
        personalization_vector=tech_personalization
    )

    for page, score in tech_result.ranked_pages:
        print(f"  {page:15s}: {score:.4f}")

    # Personalized PageRank: User interested in Sports
    print("\n--- Personalized PageRank (Sports fan) ---")
    sports_personalization = {
        "Sports": 0.6,
        "Entertainment": 0.3,
        "News": 0.1
    }

    sports_result = pr.compute_personalized(
        graph,
        personalization_vector=sports_personalization
    )

    for page, score in sports_result.ranked_pages:
        print(f"  {page:15s}: {score:.4f}")

    # Compare rankings
    print("\n--- Ranking Comparison ---")
    print(f"{'Page':15s} {'Standard':>10s} {'Tech Fan':>10s} {'Sports Fan':>10s}")
    print("-" * 50)

    for page in graph.page_names.values():
        std_score = standard_result.get_score(page) or 0
        tech_score = tech_result.get_score(page) or 0
        sports_score = sports_result.get_score(page) or 0
        print(f"{page:15s} {std_score:10.4f} {tech_score:10.4f} {sports_score:10.4f}")


if __name__ == "__main__":
    main()
