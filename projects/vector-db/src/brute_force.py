"""Brute-force KNN search module.

Implements exhaustive nearest neighbor search that compares the query
against every vector in the database. This is the ground-truth baseline
for evaluating ANN algorithms.

Time complexity: O(n * d) per query
Space complexity: O(n * d)
"""

import numpy as np
from .metrics import (
    euclidean_distance,
    cosine_similarity,
    dot_product,
    batch_euclidean_distances,
    batch_cosine_similarity,
)


class BruteForceKNN:
    """Exhaustive nearest neighbor search.

    Stores all vectors in memory and computes distances to every vector
    at query time. Simple but exact — serves as the gold standard for
    comparison with approximate methods.

    Attributes:
        vectors: Stored vectors array of shape [n, dim]
        ids: Vector identifiers
        dim: Vector dimensionality
        metric: Distance metric name ('euclidean', 'cosine', 'dot')
    """

    def __init__(self, metric: str = "euclidean"):
        """Initialize brute-force KNN searcher.

        Args:
            metric: Distance metric to use.
                    'euclidean' for Euclidean distance
                    'cosine' for cosine similarity (higher is closer)
                    'dot' for dot product (higher is closer)
        """
        self.vectors: np.ndarray = np.empty((0, 0))
        self.ids: list = []
        self.dim: int = 0
        self.metric: str = metric

    def build(self, vectors: np.ndarray, ids: list = None) -> None:
        """Build the index by storing all vectors.

        Args:
            vectors: Array of vectors of shape [n, dim]
            ids: Optional list of identifiers for each vector
        """
        self.vectors = np.array(vectors, dtype=np.float64)
        self.dim = self.vectors.shape[1]
        self.ids = ids or list(range(len(vectors)))

    def search(
        self,
        query: np.ndarray,
        k: int = 10,
    ) -> tuple:
        """Search for the k nearest neighbors of the query vector.

        Compares the query against every vector in the database and
        returns the k closest results sorted by distance.

        Args:
            query: Query vector of shape [dim]
            k: Number of nearest neighbors to return

        Returns:
            Tuple of (distances, ids, indices) where:
                distances: Array of k distances
                ids: Array of k corresponding vector ids
                indices: Array of k corresponding indices in the database
        """
        if len(self.vectors) == 0:
            return np.array([]), np.array([]), np.array([])

        query = np.asarray(query, dtype=np.float64)
        if query.shape[0] != self.dim:
            raise ValueError(
                f"Query dimension {query.shape[0]} != index dimension {self.dim}"
            )

        k = min(k, len(self.vectors)) if len(self.vectors) > 0 else 0

        if self.metric == "euclidean":
            dists = batch_euclidean_distances(query, self.vectors)
            # Lower distance = more similar
            sorted_idx = np.argsort(dists)[:k]
            dists = dists[sorted_idx]
        elif self.metric == "cosine":
            sim = batch_cosine_similarity(query, self.vectors)
            # Higher similarity = more similar, negate for argsort
            sorted_idx = np.argsort(-sim)[:k]
            dists = 1.0 - sim[sorted_idx]
        elif self.metric == "dot":
            sim = self.vectors @ query
            sorted_idx = np.argsort(-sim)[:k]
            dists = sim[sorted_idx]
        else:
            raise ValueError(f"Unknown metric: {self.metric}")

        return dists, np.array([self.ids[i] for i in sorted_idx]), sorted_idx

    def add(self, vector: np.ndarray, vid: int) -> None:
        """Add a single vector to the index.

        Args:
            vector: Vector to add of shape [dim]
            vid: Identifier for the vector
        """
        vec = np.array(vector, dtype=np.float64).reshape(1, -1)
        self.vectors = np.vstack([self.vectors, vec])
        self.ids.append(vid)
        self.dim = self.vectors.shape[1]

    def __len__(self) -> int:
        return len(self.vectors)
