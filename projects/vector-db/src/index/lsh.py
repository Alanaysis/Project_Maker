"""Locality-Sensitive Hashing (LSH) index for approximate nearest neighbor search."""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

from .base import BaseIndex
from ..metrics import DistanceMetric, get_distance_fn


class LSHIndex(BaseIndex):
    """LSH index using random hyperplane hashing.

    Approximate nearest neighbor search that projects vectors onto
    random hyperplanes and hashes them into buckets. Vectors in the
    same bucket are likely to be near each other.

    Good for high-dimensional data with millions of vectors.
    """

    def __init__(self, dimension: int, metric: DistanceMetric = DistanceMetric.EUCLIDEAN,
                 num_tables: int = 10, num_hyperplanes: int = 16, seed: int = 42):
        """Initialize LSH index.

        Args:
            dimension: Vector dimension.
            metric: Distance metric to use.
            num_tables: Number of hash tables (more = better recall, more memory).
            num_hyperplanes: Number of hyperplanes per table (more = finer buckets).
            seed: Random seed for reproducibility.
        """
        super().__init__(dimension, metric)
        self.num_tables = num_tables
        self.num_hyperplanes = num_hyperplanes
        self._distance_fn, self._is_similarity = get_distance_fn(metric)

        # Generate random hyperplanes for each table
        rng = np.random.RandomState(seed)
        self._hyperplanes = [
            rng.randn(num_hyperplanes, dimension) for _ in range(num_tables)
        ]

        # Hash tables: list of dicts mapping hash_key -> list of vector ids
        self._hash_tables: List[Dict[int, List[str]]] = [
            defaultdict(list) for _ in range(num_tables)
        ]

        # Cache hash keys for each vector
        self._hash_keys: Dict[str, List[int]] = {}

    def _compute_hash(self, vector: np.ndarray, table_idx: int) -> int:
        """Compute hash key for a vector in a specific table.

        Args:
            vector: The vector to hash.
            table_idx: Index of the hash table.

        Returns:
            Integer hash key.
        """
        # Project vector onto hyperplanes
        projections = self._hyperplanes[table_idx] @ vector
        # Convert to binary hash: positive -> 1, negative -> 0
        bits = (projections > 0).astype(int)
        # Convert bit array to integer
        hash_key = 0
        for bit in bits:
            hash_key = (hash_key << 1) | int(bit)
        return hash_key

    def _on_add(self, id: str, vector: np.ndarray, metadata: Optional[Dict[str, Any]]) -> None:
        """Add vector to all hash tables."""
        hash_keys = []
        for table_idx in range(self.num_tables):
            hash_key = self._compute_hash(vector, table_idx)
            self._hash_tables[table_idx][hash_key].append(id)
            hash_keys.append(hash_key)
        self._hash_keys[id] = hash_keys

    def _on_remove(self, id: str) -> None:
        """Remove vector from all hash tables."""
        if id in self._hash_keys:
            for table_idx, hash_key in enumerate(self._hash_keys[id]):
                bucket = self._hash_tables[table_idx][hash_key]
                if id in bucket:
                    bucket.remove(id)
                if not bucket:
                    del self._hash_tables[table_idx][hash_key]
            del self._hash_keys[id]

    def _remove_from_index(self, id: str) -> None:
        """Remove from index structures before re-adding."""
        self._on_remove(id)

    def search(self, query: np.ndarray, k: int = 10,
               metadata_filter: Optional[Any] = None,
               max_candidates: int = 200) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for approximate k nearest neighbors.

        Looks up candidates from hash buckets and computes exact distances.

        Args:
            query: Query vector.
            k: Number of results to return.
            metadata_filter: Optional metadata filter.
            max_candidates: Maximum number of candidates to evaluate.

        Returns:
            List of (id, distance, metadata) tuples sorted by distance.
        """
        if query.shape[0] != self.dimension:
            raise ValueError(
                f"Query dimension {query.shape[0]} doesn't match index dimension {self.dimension}"
            )

        if not self._vectors:
            return []

        # Collect candidates from all hash tables
        candidates = set()
        for table_idx in range(self.num_tables):
            hash_key = self._compute_hash(query, table_idx)
            bucket = self._hash_tables[table_idx].get(hash_key, [])
            candidates.update(bucket)
            if len(candidates) >= max_candidates:
                break

        # If not enough candidates, fall back to all vectors
        if len(candidates) < k:
            candidates = set(self._vectors.keys())

        # Compute exact distances for candidates
        results = []
        for id in candidates:
            if id not in self._vectors:
                continue
            if metadata_filter is not None and not metadata_filter.match(self._metadata[id]):
                continue
            dist = self._distance_fn(query, self._vectors[id])
            results.append((id, dist, self._metadata[id].copy()))

        # Sort by distance
        if self._is_similarity:
            results.sort(key=lambda x: x[1], reverse=True)
        else:
            results.sort(key=lambda x: x[1])

        return results[:k]
