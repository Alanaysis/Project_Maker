"""Base class for vector index implementations."""

import numpy as np
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from ..metrics import DistanceMetric


class BaseIndex(ABC):
    """Abstract base class for vector index implementations."""

    def __init__(self, dimension: int, metric: DistanceMetric = DistanceMetric.EUCLIDEAN):
        """Initialize the index.

        Args:
            dimension: Vector dimension.
            metric: Distance metric to use.
        """
        self.dimension = dimension
        self.metric = metric
        self._vectors: Dict[str, np.ndarray] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}

    @property
    def size(self) -> int:
        """Number of vectors in the index."""
        return len(self._vectors)

    def add(self, id: str, vector: np.ndarray, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a vector to the index.

        Args:
            id: Unique identifier for the vector.
            vector: The vector data.
            metadata: Optional metadata associated with the vector.

        Raises:
            ValueError: If vector dimension doesn't match.
        """
        if vector.shape[0] != self.dimension:
            raise ValueError(
                f"Vector dimension {vector.shape[0]} doesn't match index dimension {self.dimension}"
            )
        self._vectors[id] = vector.copy()
        self._metadata[id] = metadata or {}
        self._on_add(id, vector, metadata)

    def remove(self, id: str) -> bool:
        """Remove a vector from the index.

        Args:
            id: Unique identifier for the vector.

        Returns:
            True if the vector was removed, False if not found.
        """
        if id not in self._vectors:
            return False
        del self._vectors[id]
        del self._metadata[id]
        self._on_remove(id)
        return True

    def get(self, id: str) -> Optional[Tuple[np.ndarray, Dict[str, Any]]]:
        """Get a vector and its metadata by ID.

        Args:
            id: Unique identifier for the vector.

        Returns:
            Tuple of (vector, metadata) or None if not found.
        """
        if id not in self._vectors:
            return None
        return self._vectors[id].copy(), self._metadata[id].copy()

    def update(self, id: str, vector: Optional[np.ndarray] = None,
               metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update a vector and/or its metadata.

        Args:
            id: Unique identifier for the vector.
            vector: New vector data (None to keep existing).
            metadata: New metadata (None to keep existing).

        Returns:
            True if updated, False if not found.
        """
        if id not in self._vectors:
            return False

        if vector is not None:
            if vector.shape[0] != self.dimension:
                raise ValueError(
                    f"Vector dimension {vector.shape[0]} doesn't match index dimension {self.dimension}"
                )
            self._remove_from_index(id)
            self._vectors[id] = vector.copy()
            self._on_add(id, vector, self._metadata[id])
        if metadata is not None:
            self._metadata[id] = metadata.copy()
        return True

    @abstractmethod
    def search(self, query: np.ndarray, k: int = 10,
               metadata_filter: Optional[Any] = None) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for k nearest neighbors.

        Args:
            query: Query vector.
            k: Number of results to return.
            metadata_filter: Optional metadata filter.

        Returns:
            List of (id, distance, metadata) tuples sorted by distance.
        """
        pass

    def _on_add(self, id: str, vector: np.ndarray, metadata: Optional[Dict[str, Any]]) -> None:
        """Hook called after a vector is added. Override in subclasses."""
        pass

    def _on_remove(self, id: str) -> None:
        """Hook called after a vector is removed. Override in subclasses."""
        pass

    def _remove_from_index(self, id: str) -> None:
        """Remove vector from internal index structure before re-adding."""
        pass
