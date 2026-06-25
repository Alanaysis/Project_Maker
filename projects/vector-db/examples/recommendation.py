"""Example: Recommendation System using Vector Database.

Simulates a movie recommendation system where users and movies
are represented as vectors in the same embedding space. The system
recommends movies by finding items similar to what a user likes.
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.vector_db import VectorDB
from src.metrics import DistanceMetric
from src.filter import MetadataFilter, FilterOperator


def generate_movie_data(n_movies: int = 100, dimension: int = 32):
    """Generate simulated movie embeddings and metadata.

    Args:
        n_movies: Number of movies.
        dimension: Embedding dimension.

    Returns:
        Tuple of (movie_ids, embeddings, metadata_list).
    """
    rng = np.random.RandomState(42)

    genres = ["Action", "Comedy", "Drama", "Sci-Fi", "Horror", "Romance", "Animation"]
    # Genre centroids in embedding space (each genre has a characteristic direction)
    genre_dim = len(genres)
    genre_vectors = rng.randn(genre_dim, dimension).astype(np.float32)
    # Normalize
    for i in range(genre_dim):
        genre_vectors[i] /= np.linalg.norm(genre_vectors[i])

    movie_ids = []
    embeddings = []
    metadata_list = []

    for i in range(n_movies):
        # Assign primary and secondary genres
        primary_genre = rng.choice(genres)
        secondary_genre = rng.choice([g for g in genres if g != primary_genre])

        # Create embedding as weighted combination of genre vectors
        primary_idx = genres.index(primary_genre)
        secondary_idx = genres.index(secondary_genre)

        embedding = (
            genre_vectors[primary_idx] * 0.7 +
            genre_vectors[secondary_idx] * 0.2 +
            rng.randn(dimension).astype(np.float32) * 0.1
        )
        embedding /= np.linalg.norm(embedding)

        movie_id = f"movie_{i:03d}"
        metadata = {
            "title": f"Movie {i}",
            "primary_genre": primary_genre,
            "secondary_genre": secondary_genre,
            "year": int(rng.choice(range(1990, 2025))),
            "rating": float(round(rng.uniform(3.0, 9.5), 1)),
            "popularity": float(rng.randint(100, 10000)),
        }

        movie_ids.append(movie_id)
        embeddings.append(embedding)
        metadata_list.append(metadata)

    return movie_ids, np.array(embeddings), metadata_list


def generate_user_profiles(n_users: int = 20, dimension: int = 32, seed: int = 123):
    """Generate simulated user preference vectors.

    Args:
        n_users: Number of users.
        dimension: Embedding dimension.
        seed: Random seed.

    Returns:
        List of (user_id, preference_vector, metadata).
    """
    rng = np.random.RandomState(seed)

    genres = ["Action", "Comedy", "Drama", "Sci-Fi", "Horror", "Romance", "Animation"]
    genre_dim = len(genres)
    genre_vectors = rng.randn(genre_dim, dimension).astype(np.float32)
    for i in range(genre_dim):
        genre_vectors[i] /= np.linalg.norm(genre_vectors[i])

    users = []
    for i in range(n_users):
        # Each user likes 1-2 genres
        liked_genres = rng.choice(genres, size=rng.randint(1, 3), replace=False)

        pref = np.zeros(dimension, dtype=np.float32)
        for g in liked_genres:
            idx = genres.index(g)
            pref += genre_vectors[idx]
        pref += rng.randn(dimension).astype(np.float32) * 0.15
        pref /= np.linalg.norm(pref)

        user_id = f"user_{i:03d}"
        metadata = {
            "username": f"User{i}",
            "preferred_genres": ", ".join(liked_genres),
        }
        users.append((user_id, pref, metadata))

    return users


def recommend_for_user(user_pref: np.ndarray, db: VectorDB, k: int = 5,
                       min_rating: float = 7.0) -> list:
    """Get movie recommendations for a user.

    Args:
        user_pref: User's preference vector.
        db: Movie vector database.
        k: Number of recommendations.
        min_rating: Minimum movie rating.

    Returns:
        List of recommended movies.
    """
    # Filter for high-rated movies
    rating_filter = MetadataFilter()
    rating_filter.add_condition("rating", FilterOperator.GTE, min_rating)

    results = db.search(user_pref, k=k, metadata_filter=rating_filter)
    return results


def main():
    print("=" * 60)
    print("Movie Recommendation System Demo")
    print("=" * 60)

    dimension = 32

    # Generate movie data
    n_movies = 200
    movie_ids, movie_embeddings, movie_metadata = generate_movie_data(n_movies, dimension)

    # Build movie database
    print(f"\nBuilding movie database with {n_movies} movies...")
    movie_db = VectorDB(
        dimension=dimension,
        index_type="hnsw",
        metric="cosine",
        max_connections=16,
        ef_construction=100,
    )
    movie_db.insert_batch(movie_ids, movie_embeddings, movie_metadata)
    print(f"Indexed {movie_db.size} movies")

    # Generate users
    users = generate_user_profiles(n_users=5, dimension=dimension)

    # Get recommendations for each user
    for user_id, user_pref, user_meta in users:
        print(f"\n{'='*50}")
        print(f"Recommendations for {user_meta['username']}")
        print(f"Preferred genres: {user_meta['preferred_genres']}")
        print(f"{'='*50}")

        # Top 5 high-rated movies
        results = recommend_for_user(user_pref, movie_db, k=5, min_rating=7.0)
        for i, r in enumerate(results):
            m = r["metadata"]
            print(f"  {i+1}. {m['title']} ({m['year']})")
            print(f"     Genre: {m['primary_genre']}/{m['secondary_genre']}, "
                  f"Rating: {m['rating']}, Similarity: {1-r['distance']:.3f}")

        # Filter by specific genre
        print(f"\n  Sci-Fi recommendations only:")
        genre_filter = MetadataFilter()
        genre_filter.add_condition("primary_genre", FilterOperator.EQ, "Sci-Fi")
        genre_filter.add_condition("rating", FilterOperator.GTE, 6.0)

        results = movie_db.search(user_pref, k=3, metadata_filter=genre_filter)
        for i, r in enumerate(results):
            m = r["metadata"]
            print(f"    {i+1}. {m['title']} - Rating: {m['rating']}")

    # Similar movies lookup
    print(f"\n{'='*50}")
    print("Similar Movies Lookup")
    print(f"{'='*50}")

    target = "movie_000"
    target_result = movie_db.get(target)
    if target_result:
        similar = movie_db.search_by_id(target, k=6)
        print(f"\nMovies similar to {target_result['metadata']['title']} "
              f"({target_result['metadata']['primary_genre']}):")
        for i, r in enumerate(similar[:5]):
            m = r["metadata"]
            print(f"  {i+1}. {m['title']} "
                  f"({m['primary_genre']}, rating: {m['rating']})")

    print("\nDone!")


if __name__ == "__main__":
    main()
