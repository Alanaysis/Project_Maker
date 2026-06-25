"""Example: Social network analysis using PageRank."""

import sys
sys.path.insert(0, '/home/siok/project_copyninja/projects/pagerank')

from src.applications import SocialNetworkAnalyzer, SocialUser


def main():
    """Demonstrate social network analysis using PageRank."""
    print("=" * 60)
    print("Social Network Analysis")
    print("=" * 60)

    # Create users
    users = [
        SocialUser(
            user_id="alice",
            name="Alice",
            interests=["technology", "science"],
            followers=["bob", "charlie", "dave"],
            following=["bob", "eve"]
        ),
        SocialUser(
            user_id="bob",
            name="Bob",
            interests=["technology", "gaming"],
            followers=["alice", "charlie"],
            following=["alice", "charlie", "frank"]
        ),
        SocialUser(
            user_id="charlie",
            name="Charlie",
            interests=["science", "music"],
            followers=["alice", "bob", "dave", "eve"],
            following=["alice", "bob"]
        ),
        SocialUser(
            user_id="dave",
            name="Dave",
            interests=["gaming", "music"],
            followers=["eve", "frank"],
            following=["alice", "charlie", "eve"]
        ),
        SocialUser(
            user_id="eve",
            name="Eve",
            interests=["music", "art"],
            followers=["alice", "dave", "frank"],
            following=["charlie", "dave"]
        ),
        SocialUser(
            user_id="frank",
            name="Frank",
            interests=["technology", "art"],
            followers=["bob"],
            following=["bob", "dave", "eve"]
        ),
    ]

    # Initialize analyzer
    analyzer = SocialNetworkAnalyzer(damping_factor=0.85)
    analyzer.add_users(users)

    # Compute influence ranking
    print("\n--- Influence Ranking (Standard PageRank) ---")
    influence_result = analyzer.compute_influence_ranking()

    for i, (user, score) in enumerate(influence_result.top_k(10), 1):
        print(f"  {i:2d}. {user:15s}: {score:.4f}")

    # Personalized influence (from Alice's perspective)
    print("\n--- Personalized Influence (Alice's Network) ---")
    alice_result = analyzer.compute_personalized_influence(["alice"])

    for i, (user, score) in enumerate(alice_result.top_k(10), 1):
        print(f"  {i:2d}. {user:15s}: {score:.4f}")

    # Topic-specific influence
    print("\n--- Topic-Specific Influence ---")
    topic_users = {
        "Technology": ["alice", "bob", "frank"],
        "Science": ["alice", "charlie"],
        "Music": ["charlie", "dave", "eve"],
        "Gaming": ["bob", "dave"]
    }

    topic_results = analyzer.compute_topic_influence(topic_users)

    for topic, result in topic_results.items():
        print(f"\n  Topic: {topic}")
        for i, (user, score) in enumerate(result.top_k(5), 1):
            print(f"    {i:2d}. {user:15s}: {score:.4f}")

    # Get recommendations for Dave
    print("\n--- Recommendations for Dave ---")
    recommendations = analyzer.get_recommendations("dave", max_recommendations=5)

    for i, (user, score) in enumerate(recommendations, 1):
        print(f"  {i:2d}. {user:15s}: {score:.4f}")

    # Community detection
    print("\n--- Community Detection ---")
    communities = analyzer.detect_communities(num_communities=3)

    for comm_id, members in communities.items():
        print(f"  Community {comm_id}: {', '.join(members)}")

    # Compare rankings
    print("\n--- Ranking Comparison ---")
    print(f"{'User':15s} {'Influence':>10s} {'From Alice':>10s}")
    print("-" * 40)

    for user in ["alice", "bob", "charlie", "dave", "eve", "frank"]:
        inf = influence_result.get_score(user) or 0
        alice = alice_result.get_score(user) or 0
        print(f"{user:15s} {inf:10.4f} {alice:10.4f}")


if __name__ == "__main__":
    main()
