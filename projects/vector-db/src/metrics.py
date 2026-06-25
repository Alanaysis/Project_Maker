"""Distance metrics for vector similarity computation."""

import numpy as np
from enum import Enum
from typing import Union


class DistanceMetric(Enum):
    """Supported distance metrics."""
    EUCLIDEAN = "euclidean"
    COSINE = "cosine"
    INNER_PRODUCT = "inner_product"


def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Compute Euclidean distance between two vectors.

    Args:
        a: First vector.
        b: Second vector.

    Returns:
        Euclidean distance (lower is more similar).
    """
    return float(np.linalg.norm(a - b))


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors.

    Args:
        a: First vector.
        b: Second vector.

    Returns:
        Cosine similarity in [-1, 1] (higher is more similar).
    """
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def inner_product(a: np.ndarray, b: np.ndarray) -> float:
    """Compute inner product (dot product) between two vectors.

    Args:
        a: First vector.
        b: Second vector.

    Returns:
        Inner product (higher is more similar).
    """
    return float(np.dot(a, b))


# Metric registry: maps metric to (distance_function, is_similarity)
# is_similarity=True means higher value = more similar
METRIC_REGISTRY = {
    DistanceMetric.EUCLIDEAN: (euclidean_distance, False),
    DistanceMetric.COSINE: (cosine_similarity, True),
    DistanceMetric.INNER_PRODUCT: (inner_product, True),
}


def get_distance_fn(metric: DistanceMetric):
    """Get distance function for a metric.

    Args:
        metric: The distance metric.

    Returns:
        Tuple of (distance_function, is_similarity).
    """
    if metric not in METRIC_REGISTRY:
        raise ValueError(f"Unsupported metric: {metric}")
    return METRIC_REGISTRY[metric]


def compute_distance(a: np.ndarray, b: np.ndarray, metric: DistanceMetric) -> float:
    """Compute distance/similarity between two vectors.

    Args:
        a: First vector.
        b: Second vector.
        metric: The distance metric to use.

    Returns:
        Distance or similarity score.
    """
    fn, _ = get_distance_fn(metric)
    return fn(a, b)
