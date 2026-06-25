"""Main VectorDB class - unified interface for vector database operations."""

import numpy as np
import json
import os
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from .metrics import DistanceMetric
from .index import BruteForceIndex, LSHIndex, HNSWIndex
from .filter import MetadataFilter, FilterOperator


class IndexType(Enum):
    """Supported index types."""
    BRUTE_FORCE = "brute_force"
    LSH = "lsh"
    HNSW = "hnsw"


class VectorDB:
    """A lightweight vector database with multiple indexing strategies.

    Supports brute-force, LSH, and HNSW indexing with metadata filtering.
    """

    def __init__(self, dimension: int, index_type: Union[IndexType, str] = IndexType.BRUTE_FORCE,
                 metric: Union[DistanceMetric, str] = DistanceMetric.EUCLIDEAN, **kwargs):
        """Initialize the vector database.

        Args:
            dimension: Vector dimension.
            index_type: Type of index to use ("brute_force", "lsh", or "hnsw").
            metric: Distance metric ("euclidean", "cosine", or "inner_product").
            **kwargs: Additional arguments passed to the index constructor.
        """
        if isinstance(index_type, str):
            index_type = IndexType(index_type)
        if isinstance(metric, str):
            metric = DistanceMetric(metric)

        self.dimension = dimension
        self.index_type = index_type
        self.metric = metric

        # Create the appropriate index
        if index_type == IndexType.BRUTE_FORCE:
            self._index = BruteForceIndex(dimension, metric, **kwargs)
        elif index_type == IndexType.LSH:
            self._index = LSHIndex(dimension, metric, **kwargs)
        elif index_type == IndexType.HNSW:
            self._index = HNSWIndex(dimension, metric, **kwargs)
        else:
            raise ValueError(f"Unsupported index type: {index_type}")

    @property
    def size(self) -> int:
        """Number of vectors in the database."""
        return self._index.size

    # ──────────────────────────────────────────────
    # CRUD Operations
    # ──────────────────────────────────────────────

    def insert(self, id: str, vector: Union[np.ndarray, List[float]],
               metadata: Optional[Dict[str, Any]] = None) -> None:
        """Insert a vector with optional metadata.

        Args:
            id: Unique identifier for the vector.
            vector: Vector data (numpy array or list of floats).
            metadata: Optional metadata dictionary.

        Raises:
            ValueError: If vector dimension doesn't match.
        """
        if not isinstance(vector, np.ndarray):
            vector = np.array(vector, dtype=np.float32)
        self._index.add(id, vector, metadata)

    def insert_batch(self, ids: List[str], vectors: Union[np.ndarray, List[List[float]]],
                     metadata_list: Optional[List[Dict[str, Any]]] = None) -> None:
        """Insert multiple vectors in batch.

        Args:
            ids: List of unique identifiers.
            vectors: 2D array of vectors (n_vectors x dimension).
            metadata_list: Optional list of metadata dictionaries.

        Raises:
            ValueError: If lengths don't match or dimensions are wrong.
        """
        if not isinstance(vectors, np.ndarray):
            vectors = np.array(vectors, dtype=np.float32)

        if len(ids) != vectors.shape[0]:
            raise ValueError("Number of IDs must match number of vectors")

        if vectors.shape[1] != self.dimension:
            raise ValueError(
                f"Vector dimension {vectors.shape[1]} doesn't match database dimension {self.dimension}"
            )

        if metadata_list and len(metadata_list) != len(ids):
            raise ValueError("Number of metadata entries must match number of IDs")

        for i, id in enumerate(ids):
            meta = metadata_list[i] if metadata_list else None
            self.insert(id, vectors[i], meta)

    def delete(self, id: str) -> bool:
        """Delete a vector by ID.

        Args:
            id: Unique identifier for the vector.

        Returns:
            True if deleted, False if not found.
        """
        return self._index.remove(id)

    def delete_batch(self, ids: List[str]) -> int:
        """Delete multiple vectors by ID.

        Args:
            ids: List of unique identifiers.

        Returns:
            Number of vectors actually deleted.
        """
        count = 0
        for id in ids:
            if self._index.remove(id):
                count += 1
        return count

    def update(self, id: str, vector: Optional[Union[np.ndarray, List[float]]] = None,
               metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update a vector and/or its metadata.

        Args:
            id: Unique identifier for the vector.
            vector: New vector data (None to keep existing).
            metadata: New metadata (None to keep existing).

        Returns:
            True if updated, False if not found.
        """
        if vector is not None and not isinstance(vector, np.ndarray):
            vector = np.array(vector, dtype=np.float32)
        return self._index.update(id, vector, metadata)

    def get(self, id: str) -> Optional[Dict[str, Any]]:
        """Get a vector and its metadata by ID.

        Args:
            id: Unique identifier.

        Returns:
            Dictionary with 'id', 'vector', and 'metadata' keys, or None.
        """
        result = self._index.get(id)
        if result is None:
            return None
        vector, metadata = result
        return {"id": id, "vector": vector, "metadata": metadata}

    def exists(self, id: str) -> bool:
        """Check if a vector exists.

        Args:
            id: Unique identifier.

        Returns:
            True if the vector exists.
        """
        return self._index.get(id) is not None

    # ──────────────────────────────────────────────
    # Search / Query
    # ──────────────────────────────────────────────

    def search(self, query: Union[np.ndarray, List[float]], k: int = 10,
               metadata_filter: Optional[MetadataFilter] = None,
               **kwargs) -> List[Dict[str, Any]]:
        """Search for k nearest neighbors.

        Args:
            query: Query vector.
            k: Number of results to return.
            metadata_filter: Optional metadata filter.
            **kwargs: Additional arguments passed to the index search.

        Returns:
            List of result dictionaries with 'id', 'distance', and 'metadata' keys.
        """
        if not isinstance(query, np.ndarray):
            query = np.array(query, dtype=np.float32)

        results = self._index.search(query, k, metadata_filter, **kwargs)

        return [
            {"id": id, "distance": dist, "metadata": meta}
            for id, dist, meta in results
        ]

    def search_by_id(self, id: str, k: int = 10,
                     metadata_filter: Optional[MetadataFilter] = None,
                     **kwargs) -> List[Dict[str, Any]]:
        """Search for neighbors of an existing vector.

        Args:
            id: ID of the vector to search around.
            k: Number of results to return (including the query vector itself).
            metadata_filter: Optional metadata filter.
            **kwargs: Additional arguments passed to the index search.

        Returns:
            List of result dictionaries.
        """
        result = self._index.get(id)
        if result is None:
            return []
        vector, _ = result
        results = self.search(vector, k, metadata_filter, **kwargs)
        # Optionally exclude the query vector itself
        return [r for r in results if r["id"] != id]

    def range_search(self, query: Union[np.ndarray, List[float]],
                     radius: float, metadata_filter: Optional[MetadataFilter] = None,
                     **kwargs) -> List[Dict[str, Any]]:
        """Search for all vectors within a distance radius.

        Args:
            query: Query vector.
            radius: Maximum distance threshold.
            metadata_filter: Optional metadata filter.

        Returns:
            List of result dictionaries within the radius.
        """
        if not isinstance(query, np.ndarray):
            query = np.array(query, dtype=np.float32)

        # Use a large k for brute-force, or search more for other indexes
        all_results = self._index.search(query, self.size, metadata_filter, **kwargs)

        return [
            {"id": id, "distance": dist, "metadata": meta}
            for id, dist, meta in all_results
            if dist <= radius
        ]

    # ──────────────────────────────────────────────
    # Metadata Filtering Helpers
    # ──────────────────────────────────────────────

    @staticmethod
    def filter_eq(field: str, value: Any) -> MetadataFilter:
        """Create an equality filter."""
        f = MetadataFilter()
        f.add_condition(field, FilterOperator.EQ, value)
        return f

    @staticmethod
    def filter_gt(field: str, value: Any) -> MetadataFilter:
        """Create a greater-than filter."""
        f = MetadataFilter()
        f.add_condition(field, FilterOperator.GT, value)
        return f

    @staticmethod
    def filter_range(field: str, min_val: Any, max_val: Any) -> MetadataFilter:
        """Create a range filter (min <= value <= max)."""
        f = MetadataFilter()
        f.add_condition(field, FilterOperator.GTE, min_val)
        f.add_condition(field, FilterOperator.LTE, max_val)
        return f

    # ──────────────────────────────────────────────
    # Persistence
    # ──────────────────────────────────────────────

    def save(self, path: str) -> None:
        """Save the database to disk (JSON format).

        Args:
            path: Directory path to save to.
        """
        os.makedirs(path, exist_ok=True)

        # Save metadata
        meta = {
            "dimension": self.dimension,
            "index_type": self.index_type.value,
            "metric": self.metric.value,
            "size": self.size,
        }
        with open(os.path.join(path, "meta.json"), "w") as f:
            json.dump(meta, f, indent=2)

        # Save vectors and metadata
        data = {}
        for id in self._index._vectors:
            vector, metadata = self._index.get(id)
            data[id] = {
                "vector": vector.tolist(),
                "metadata": metadata,
            }
        with open(os.path.join(path, "data.json"), "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: str, **kwargs) -> "VectorDB":
        """Load a database from disk.

        Args:
            path: Directory path to load from.
            **kwargs: Additional arguments passed to the index constructor.

        Returns:
            VectorDB instance.
        """
        with open(os.path.join(path, "meta.json"), "r") as f:
            meta = json.load(f)

        db = cls(
            dimension=meta["dimension"],
            index_type=meta["index_type"],
            metric=meta["metric"],
            **kwargs,
        )

        with open(os.path.join(path, "data.json"), "r") as f:
            data = json.load(f)

        for id, item in data.items():
            db.insert(id, np.array(item["vector"]), item["metadata"])

        return db

    # ──────────────────────────────────────────────
    # Utility
    # ──────────────────────────────────────────────

    def list_ids(self) -> List[str]:
        """List all vector IDs in the database."""
        return list(self._index._vectors.keys())

    def clear(self) -> None:
        """Remove all vectors from the database."""
        ids = self.list_ids()
        for id in ids:
            self._index.remove(id)

    def __len__(self) -> int:
        return self.size

    def __contains__(self, id: str) -> bool:
        return self.exists(id)

    def __repr__(self) -> str:
        return (
            f"VectorDB(dimension={self.dimension}, "
            f"index_type={self.index_type.value}, "
            f"metric={self.metric.value}, "
            f"size={self.size})"
        )
