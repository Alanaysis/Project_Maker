"""Example: Recommendation system using PageRank."""

import sys
sys.path.insert(0, '/home/siok/project_copyninja/projects/pagerank')

from src.applications import RecommendationSystem


def main():
    """Demonstrate recommendation system using PageRank."""
    print("=" * 60)
    print("Recommendation System using PageRank")
    print("=" * 60)

    # Initialize recommendation system
    rec_system = RecommendationSystem(damping_factor=0.85)

    # Add user-item interactions (ratings)
    interactions = [
        # User 1 likes tech and sci-fi
        ("user1", "tech_book1", 5.0),
        ("user1", "tech_book2", 4.0),
        ("user1", "scifi_movie1", 5.0),
        ("user1", "scifi_movie2", 4.0),

        # User 2 likes tech and comedy
        ("user2", "tech_book1", 4.0),
        ("user2", "tech_book3", 5.0),
        ("user2", "comedy_movie1", 5.0),
        ("user2", "comedy_movie2", 4.0),

        # User 3 likes sci-fi and comedy
        ("user3", "scifi_movie1", 4.0),
        ("user3", "scifi_movie3", 5.0),
        ("user3", "comedy_movie1", 4.0),
        ("user3", "comedy_movie3", 5.0),

        # User 4 likes everything
        ("user4", "tech_book1", 3.0),
        ("user4", "scifi_movie1", 4.0),
        ("user4", "comedy_movie1", 5.0),
        ("user4", "drama_movie1", 4.0),

        # User 5 likes drama
        ("user5", "drama_movie1", 5.0),
        ("user5", "drama_movie2", 5.0),
        ("user5", "drama_movie3", 4.0),
    ]

    for user, item, rating in interactions:
        rec_system.add_interaction(user, item, rating)

    # Add item similarities
    item_similarities = [
        ("tech_book1", "tech_book2"),
        ("tech_book1", "tech_book3"),
        ("tech_book2", "tech_book3"),
        ("scifi_movie1", "scifi_movie2"),
        ("scifi_movie1", "scifi_movie3"),
        ("comedy_movie1", "comedy_movie2"),
        ("comedy_movie1", "comedy_movie3"),
        ("drama_movie1", "drama_movie2"),
        ("drama_movie1", "drama_movie3"),
    ]

    for item1, item2 in item_similarities:
        rec_system.add_similar_items(item1, item2)

    # Add user similarities
    user_similarities = [
        ("user1", "user2"),  # Both like tech
        ("user2", "user3"),  # Both like comedy
        ("user3", "user4"),  # Overlapping interests
    ]

    for user1, user2 in user_similarities:
        rec_system.add_user_similarity(user1, user2)

    # Generate recommendations for User 1
    print("\n--- Recommendations for User 1 ---")
    print("(User 1 likes: tech books, sci-fi movies)")

    recommendations = rec_system.recommend("user1", num_recommendations=5)

    for i, (item, score) in enumerate(recommendations, 1):
        print(f"  {i:2d}. {item:20s}: {score:.4f}")

    # Generate recommendations for User 5
    print("\n--- Recommendations for User 5 ---")
    print("(User 5 likes: drama movies)")

    recommendations = rec_system.recommend("user5", num_recommendations=5)

    for i, (item, score) in enumerate(recommendations, 1):
        print(f"  {i:2d}. {item:20s}: {score:.4f}")

    # Find similar items to tech_book1
    print("\n--- Items Similar to tech_book1 ---")

    similar_items = rec_system.recommend_similar("tech_book1", num_recommendations=5)

    for i, (item, score) in enumerate(similar_items, 1):
        print(f"  {i:2d}. {item:20s}: {score:.4f}")

    # Topic-based recommendations
    print("\n--- Topic-Based Recommendations for User 1 ---")

    topics = {
        "Tech": ["tech_book1", "tech_book2", "tech_book3"],
        "Sci-Fi": ["scifi_movie1", "scifi_movie2", "scifi_movie3"],
        "Comedy": ["comedy_movie1", "comedy_movie2", "comedy_movie3"],
    }

    topic_recs = rec_system.recommend_by_topic(
        "user1",
        topic_items=topics,
        num_recommendations=3
    )

    for topic, recs in topic_recs.items():
        print(f"\n  Topic: {topic}")
        for i, (item, score) in enumerate(recs, 1):
            print(f"    {i:2d}. {item:20s}: {score:.4f}")

    # Show how PageRank captures transitive preferences
    print("\n--- Transitive Preference Discovery ---")
    print("User 1 likes tech -> User 2 likes tech -> User 2 likes comedy")
    print("Therefore, User 1 might like comedy items:")

    comedy_recs = rec_system.recommend("user1", num_recommendations=10)
    comedy_items = [item for item, _ in comedy_recs if "comedy" in item]

    for item in comedy_items:
        score = next(s for i, s in comedy_recs if i == item)
        print(f"  - {item}: {score:.4f}")


if __name__ == "__main__":
    main()
