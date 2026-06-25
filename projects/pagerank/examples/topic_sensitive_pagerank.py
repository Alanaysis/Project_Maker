"""Example: Topic-Sensitive PageRank demonstration."""

import sys
sys.path.insert(0, '/home/siok/project_copyninja/projects/pagerank')

from src.graph import WebGraph
from src.pagerank import PageRank


def main():
    """Demonstrate Topic-Sensitive PageRank."""
    print("=" * 60)
    print("Topic-Sensitive PageRank Example")
    print("=" * 60)

    # Create a sample web graph with diverse content
    graph = WebGraph.from_edges([
        # News cluster
        ("CNN", "BBC"),
        ("BBC", "CNN"),
        ("CNN", "Reuters"),
        ("Reuters", "BBC"),

        # Tech cluster
        ("TechCrunch", "Wired"),
        ("Wired", "TechCrunch"),
        ("ArsTechnica", "TechCrunch"),
        ("TechCrunch", "ArsTechnica"),

        # Science cluster
        ("Nature", "Science"),
        ("Science", "Nature"),
        ("ScientificAmerican", "Nature"),

        # Cross-links
        ("CNN", "TechCrunch"),
        ("TechCrunch", "CNN"),
        ("BBC", "Nature"),
        ("Nature", "BBC"),
        ("Wired", "Science"),
    ])

    print("\nGraph structure:")
    print(graph)

    # Define topics with seed pages
    topics = {
        "News": ["CNN", "BBC", "Reuters"],
        "Technology": ["TechCrunch", "Wired", "ArsTechnica"],
        "Science": ["Nature", "Science", "ScientificAmerican"]
    }

    # Topic weights (how important each topic is)
    topic_weights = {
        "News": 0.4,
        "Technology": 0.35,
        "Science": 0.25
    }

    pr = PageRank(damping_factor=0.85)

    # Compute per-topic PageRank
    print("\n--- Per-Topic PageRank ---")
    topic_results = pr.compute_topic_sensitive(
        graph,
        topic_pages=topics,
        topic_weights=topic_weights
    )

    for topic, result in topic_results.items():
        print(f"\n  Topic: {topic}")
        for page, score in result.top_k(5):
            print(f"    {page:20s}: {score:.4f}")

    # Compute combined Topic-Sensitive PageRank
    print("\n--- Combined Topic-Sensitive PageRank ---")
    combined_result = pr.compute_topic_sensitive_combined(
        graph,
        topic_pages=topics,
        topic_weights=topic_weights
    )

    for page, score in combined_result.ranked_pages:
        print(f"  {page:20s}: {score:.4f}")

    # Compare with standard PageRank
    print("\n--- Comparison: Standard vs Topic-Sensitive ---")
    standard_result = pr.compute(graph)

    print(f"{'Page':20s} {'Standard':>10s} {'Topic-Sens':>10s} {'Diff':>10s}")
    print("-" * 55)

    for page in graph.page_names.values():
        std_score = standard_result.get_score(page) or 0
        topic_score = combined_result.get_score(page) or 0
        diff = topic_score - std_score
        print(f"{page:20s} {std_score:10.4f} {topic_score:10.4f} {diff:+10.4f}")

    # Demonstrate different topic weights
    print("\n--- Impact of Topic Weights ---")

    # News-heavy weighting
    news_heavy = {"News": 0.7, "Technology": 0.2, "Science": 0.1}
    news_result = pr.compute_topic_sensitive_combined(
        graph, topic_pages=topics, topic_weights=news_heavy
    )

    # Tech-heavy weighting
    tech_heavy = {"News": 0.1, "Technology": 0.7, "Science": 0.2}
    tech_result = pr.compute_topic_sensitive_combined(
        graph, topic_pages=topics, topic_weights=tech_heavy
    )

    print(f"\n{'Page':20s} {'News-Heavy':>12s} {'Tech-Heavy':>12s}")
    print("-" * 48)
    for page in graph.page_names.values():
        news_score = news_result.get_score(page) or 0
        tech_score = tech_result.get_score(page) or 0
        print(f"{page:20s} {news_score:12.4f} {tech_score:12.4f}")


if __name__ == "__main__":
    main()
