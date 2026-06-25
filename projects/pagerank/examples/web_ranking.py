"""Example: Web page ranking application."""

import sys
sys.path.insert(0, '/home/siok/project_copyninja/projects/pagerank')

from src.applications import WebRankingSystem, WebPage


def main():
    """Demonstrate web page ranking using PageRank."""
    print("=" * 60)
    print("Web Ranking Application")
    print("=" * 60)

    # Create web pages
    pages = [
        WebPage(
            url="homepage.com",
            title="Homepage",
            content="Welcome to our website",
            links=["about.com", "blog.com", "products.com"],
            category="main"
        ),
        WebPage(
            url="blog.com",
            title="Blog",
            content="Latest articles and news",
            links=["homepage.com", "article1.com", "article2.com"],
            category="content"
        ),
        WebPage(
            url="products.com",
            title="Products",
            content="Our product catalog",
            links=["homepage.com", "product1.com", "product2.com"],
            category="commerce"
        ),
        WebPage(
            url="about.com",
            title="About Us",
            content="Company information",
            links=["homepage.com", "team.com"],
            category="info"
        ),
        WebPage(
            url="article1.com",
            title="Article 1",
            content="First article content",
            links=["blog.com", "article2.com", "homepage.com"],
            category="content"
        ),
        WebPage(
            url="article2.com",
            title="Article 2",
            content="Second article content",
            links=["blog.com", "homepage.com"],
            category="content"
        ),
        WebPage(
            url="product1.com",
            title="Product 1",
            content="First product description",
            links=["products.com", "homepage.com"],
            category="commerce"
        ),
        WebPage(
            url="product2.com",
            title="Product 2",
            content="Second product description",
            links=["products.com", "homepage.com"],
            category="commerce"
        ),
        WebPage(
            url="team.com",
            title="Our Team",
            content="Meet the team",
            links=["about.com", "homepage.com"],
            category="info"
        ),
    ]

    # Initialize ranking system
    ranking_system = WebRankingSystem(damping_factor=0.85)
    ranking_system.add_pages(pages)

    # Standard PageRank ranking
    print("\n--- Standard PageRank Ranking ---")
    standard_result = ranking_system.compute_ranking()

    for i, (page, score) in enumerate(standard_result.top_k(10), 1):
        print(f"  {i:2d}. {page:20s}: {score:.4f}")

    # Personalized ranking for content reader
    print("\n--- Personalized Ranking (Content Reader) ---")
    content_result = ranking_system.compute_personalized_ranking(
        preferred_categories=["content"]
    )

    for i, (page, score) in enumerate(content_result.top_k(10), 1):
        print(f"  {i:2d}. {page:20s}: {score:.4f}")

    # Personalized ranking for shopper
    print("\n--- Personalized Ranking (Shopper) ---")
    shopper_result = ranking_system.compute_personalized_ranking(
        preferred_categories=["commerce"]
    )

    for i, (page, score) in enumerate(shopper_result.top_k(10), 1):
        print(f"  {i:2d}. {page:20s}: {score:.4f}")

    # Topic-sensitive ranking
    print("\n--- Topic-Sensitive Ranking ---")
    topics = {
        "Content": ["blog.com", "article1.com", "article2.com"],
        "Commerce": ["products.com", "product1.com", "product2.com"],
        "Info": ["about.com", "team.com"]
    }

    topic_results = ranking_system.compute_topic_ranking(topics)

    for topic, result in topic_results.items():
        print(f"\n  Topic: {topic}")
        for i, (page, score) in enumerate(result.top_k(5), 1):
            print(f"    {i:2d}. {page:20s}: {score:.4f}")

    # Show ranking differences
    print("\n--- Ranking Differences ---")
    print(f"{'Page':20s} {'Standard':>10s} {'Content':>10s} {'Shopper':>10s}")
    print("-" * 55)

    for page in ["blog.com", "products.com", "homepage.com", "article1.com"]:
        std = standard_result.get_score(page) or 0
        content = content_result.get_score(page) or 0
        shopper = shopper_result.get_score(page) or 0
        print(f"{page:20s} {std:10.4f} {content:10.4f} {shopper:10.4f}")


if __name__ == "__main__":
    main()
