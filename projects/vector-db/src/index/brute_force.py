"""Brute-force (exact) nearest neighbor search."""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple

from .base import BaseIndex
from ..metrics import DistanceMetric, get_distance_fn


class BruteForceIndex(BaseIndex):
    """Brute-force index for exact nearest neighbor search.

    Computes distances to all vectors for every query.
    Guarantees correct results but O(n) per query.
    """

    def __init__(self, dimension: int, metric: DistanceMetric = DistanceMetric.EUCLIDEAN):
        """Initialize brute-force index.

        Args:
            dimension: Vector dimension.
            metric: Distance metric to use.
        """
        super().__init__(dimension, metric)
        self._distance_fn, self._is_similarity = get_distance_fn(metric)

    def search(self, query: np.ndarray, k: int = 10,
               metadata_filter: Optional[Any] = None) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for k nearest neighbors by computing all distances.

        Args:
            query: Query vector.
            k: Number of results to return.
            metadata_filter: Optional metadata filter.

        Returns:
            List of (id, distance, metadata) tuples sorted by distance.
        """
        if query.shape[0] != self.dimension:
            raise ValueError(
                f"Query dimension {query.shape[0]} doesn't match index dimension {self.dimension}"
            )

        if not self._vectors:
            return []

        # Compute distances for all vectors
        results = []
        for id, vector in self._vectors.items():
            # Apply metadata filter
            if metadata_filter is not None and not metadata_filter.match(self._metadata[id]):
                continue

            dist = self._distance_fn(query, vector)
            results.append((id, dist, self._metadata[id].copy()))

        # Sort by distance
        if self._is_similarity:
            results.sort(key=lambda x: x[1], reverse=True)  # Higher similarity first
        else:
            results.sort(key=lambda x: x[1])  # Lower distance first

        return results[:k]
