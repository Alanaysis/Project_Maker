"""Vector similarity metrics module.

Provides distance and similarity functions for vector comparison:
- Euclidean distance
- Cosine similarity
- Dot product similarity
"""

import numpy as np


def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Compute Euclidean distance between two vectors.

    Euclidean distance is the straight-line distance between two points
    in Euclidean space. It is the most common distance metric.

    Formula: sqrt(sum((a_i - b_i)^2))

    Args:
        a: First vector (1D numpy array)
        b: Second vector (1D numpy array)

    Returns:
        Euclidean distance as a float

    Raises:
        ValueError: If vectors have different dimensions
    """
    if a.shape != b.shape:
        raise ValueError(
            f"Vector dimension mismatch: {a.shape} vs {b.shape}"
        )
    return float(np.sqrt(np.sum((a - b) ** 2)))


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors.

    Cosine similarity measures the cosine of the angle between two vectors.
    Values range from -1 (opposite) to 1 (identical direction), with 0
    meaning orthogonal (no similarity).

    Formula: (a . b) / (||a|| * ||b||)

    Args:
        a: First vector (1D numpy array)
        b: Second vector (1D numpy array)

    Returns:
        Cosine similarity as a float in [-1, 1]

    Raises:
        ValueError: If vectors have different dimensions
        ZeroDivisionError: If either vector has zero norm
    """
    if a.shape != b.shape:
        raise ValueError(
            f"Vector dimension mismatch: {a.shape} vs {b.shape}"
        )
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        raise ZeroDivisionError("Zero norm vector cannot compute cosine similarity")
    return float(np.dot(a, b) / (norm_a * norm_b))


def dot_product(a: np.ndarray, b: np.ndarray) -> float:
    """Compute dot product (inner product) of two vectors.

    The dot product equals the product of magnitudes and cosine of the angle.
    It is useful when vectors are already normalized or when magnitude matters.

    Formula: sum(a_i * b_i)

    Args:
        a: First vector (1D numpy array)
        b: Second vector (1D numpy array)

    Returns:
        Dot product as a float

    Raises:
        ValueError: If vectors have different dimensions
    """
    if a.shape != b.shape:
        raise ValueError(
            f"Vector dimension mismatch: {a.shape} vs {b.shape}"
        )
    return float(np.dot(a, b))


def l2_normalize(v: np.ndarray) -> np.ndarray:
    """Normalize a vector to unit length using L2 norm.

    This is useful for cosine similarity computation since:
        cosine_similarity(a, b) = dot_product(normalize(a), normalize(b))

    Args:
        v: Input vector (1D numpy array)

    Returns:
        Normalized vector with unit L2 norm

    Raises:
        ValueError: If input is not 1D
        ZeroDivisionError: If vector has zero norm
    """
    if v.ndim != 1:
        raise ValueError("Input must be a 1D vector")
    norm = np.linalg.norm(v)
    if norm == 0:
        raise ZeroDivisionError("Cannot normalize zero vector")
    return v / norm


def batch_cosine_similarity(
    query: np.ndarray,
    database: np.ndarray,
) -> np.ndarray:
    """Compute cosine similarity between one query and many database vectors.

    This is an optimized batch version for searching against a full database.

    Args:
        query: Query vector (1D array)
        database: Database vectors (2D array, shape [n, dim])

    Returns:
        Array of cosine similarities of shape [n]
    """
    norms_db = np.linalg.norm(database, axis=1)
    norms_db[norms_db == 0] = 1e-10  # avoid division by zero
    norms_q = np.linalg.norm(query)
    if norms_q == 0:
        return np.zeros(len(database))
    return (database @ query) / (norms_db * norms_q)


def batch_euclidean_distances(
    query: np.ndarray,
    database: np.ndarray,
) -> np.ndarray:
    """Compute Euclidean distances between one query and many database vectors.

    Uses the expansion: ||a - b||^2 = ||a||^2 + ||b||^2 - 2*a.b

    Args:
        query: Query vector (1D array)
        database: Database vectors (2D array, shape [n, dim])

    Returns:
        Array of Euclidean distances of shape [n]
    """
    query_norm_sq = np.dot(query, query)
    db_norm_sq = np.sum(database ** 2, axis=1)
    cross = database @ query
    # Squared distances, clamp to avoid negative values from floating point
    sq_dists = np.maximum(query_norm_sq + db_norm_sq - 2 * cross, 0.0)
    return np.sqrt(sq_dists)
