"""Helper utilities for vector database."""

import numpy as np
from typing import List, Optional


def random_vectors(n: int, dimension: int, seed: int = 42) -> np.ndarray:
    """Generate random unit vectors.

    Args:
        n: Number of vectors.
        dimension: Vector dimension.
        seed: Random seed.

    Returns:
        2D numpy array of shape (n, dimension).
    """
    rng = np.random.RandomState(seed)
    vectors = rng.randn(n, dimension).astype(np.float32)
    # Normalize to unit vectors
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1
    vectors = vectors / norms
    return vectors


def normalize_vectors(vectors: np.ndarray) -> np.ndarray:
    """Normalize vectors to unit length.

    Args:
        vectors: 2D numpy array of shape (n, dimension).

    Returns:
        Normalized vectors.
    """
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1
    return vectors / norms


def cosine_distance_metric() -> str:
    """Return the metric name for cosine distance."""
    return "cosine"


def generate_cluster_data(n_clusters: int, points_per_cluster: int, dimension: int,
                          cluster_std: float = 0.1, seed: int = 42) -> np.ndarray:
    """Generate clustered data for testing.

    Args:
        n_clusters: Number of clusters.
        points_per_cluster: Points per cluster.
        dimension: Vector dimension.
        cluster_std: Standard deviation within clusters.
        seed: Random seed.

    Returns:
        2D numpy array of shape (n_clusters * points_per_cluster, dimension).
    """
    rng = np.random.RandomState(seed)
    cluster_centers = rng.randn(n_clusters, dimension).astype(np.float32)

    all_points = []
    for center in cluster_centers:
        points = center + rng.randn(points_per_cluster, dimension).astype(np.float32) * cluster_std
        all_points.append(points)

    return np.vstack(all_points)


def recall_at_k(retrieved: List[str], relevant: List[str], k: int) -> float:
    """Compute recall@k metric.

    Args:
        retrieved: List of retrieved IDs.
        relevant: List of relevant IDs.
        k: Number of top results to consider.

    Returns:
        Recall@k value in [0, 1].
    """
    if not relevant:
        return 0.0
    retrieved_at_k = set(retrieved[:k])
    relevant_set = set(relevant)
    return len(retrieved_at_k & relevant_set) / len(relevant_set)
