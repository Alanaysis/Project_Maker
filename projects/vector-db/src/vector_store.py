"""Vector store module.

Provides a high-level VectorStore that manages vector insertion,
index building, and query operations. Supports switching between
different indexing strategies.

Core loop:
    vector insert -> index build -> query vector -> ANN search -> results
"""

import numpy as np
from .brute_force import BruteForceKNN
from .lsh import LSHForest
from .kdtree import KDTree
from .metrics import cosine_similarity, euclidean_distance


class VectorStore:
    """High-level vector store with multiple indexing strategies.

    Manages a collection of vectors and provides different indexing
    backends for search operations.

    Usage:
        store = VectorStore(dim=128)
        store.add(np.random.randn(128), "doc1")
        store.build_index("brute_force")
        distances, ids, indices = store.search(query, k=10)

    Attributes:
        dim: Vector dimensionality
        vectors: All stored vectors
        ids: Vector identifiers
        index: Active index object (BruteForceKNN, LSHForest, or KDTree)
        index_type: Currently active index type
    """

    def __init__(self, dim: int = 0):
        """Initialize the vector store.

        Args:
            dim: Default vector dimensionality (used if known upfront)
        """
        self.dim = dim
        self.vectors: list = []
        self.ids: list = []
        self.index = None
        self.index_type: str = None

    def add(self, vector: np.ndarray, vid: str = None) -> None:
        """Add a vector to the store.

        The vector is stored but the index is NOT automatically updated.
        Call build_index() after adding vectors to update the index.

        Args:
            vector: Vector to add (1D array)
            vid: Optional identifier. Auto-generated if None.
        """
        vec = np.array(vector, dtype=np.float64)
        if self.dim == 0:
            self.dim = vec.shape[0]
        elif vec.shape[0] != self.dim:
            raise ValueError(
                f"Vector dim {vec.shape[0]} != store dim {self.dim}"
            )
        self.vectors.append(vec)
        if vid is None:
            vid = f"vec_{len(self.ids)}"
        self.ids.append(vid)

    def add_batch(self, vectors: np.ndarray, ids: list = None) -> None:
        """Add multiple vectors at once.

        Args:
            vectors: 2D array of vectors [n, dim]
            ids: Optional list of identifiers
        """
        vectors = np.array(vectors, dtype=np.float64)
        if self.dim == 0:
            self.dim = vectors.shape[1]
        elif vectors.shape[1] != self.dim:
            raise ValueError(
                f"Vector dim {vectors.shape[1]} != store dim {self.dim}"
            )
        for i in range(len(vectors)):
            vid = ids[i] if ids else f"vec_{len(self.ids)}"
            self.add(vectors[i], vid)

    def build_index(self, index_type: str = "brute_force", **kwargs) -> None:
        """Build or rebuild the search index.

        Supported index types:
            'brute_force': Exhaustive search (exact, slow)
            'lsh': Locality Sensitive Hashing (approximate, fast)
            'kdtree': KD-Tree (exact, good for low dimensions)

        Args:
            index_type: Type of index to build
            **kwargs: Additional arguments for the index constructor
        """
        if len(self.vectors) == 0:
            raise ValueError("Cannot build index on empty store")

        vectors_arr = np.array(self.vectors)

        if index_type == "brute_force":
            self.index = BruteForceKNN(**kwargs)
            self.index.build(vectors_arr, self.ids)
        elif index_type == "lsh":
            self.index = LSHForest(**kwargs)
            self.index.build(vectors_arr, self.ids)
        elif index_type == "kdtree":
            self.index = KDTree(self.dim)
            self.index.build(vectors_arr)
        else:
            raise ValueError(f"Unknown index type: {index_type}")

        self.index_type = index_type

    def search(self, query: np.ndarray, k: int = 10) -> tuple:
        """Search for the k nearest neighbors.

        Requires an index to be built first via build_index().

        Args:
            query: Query vector (1D array)
            k: Number of nearest neighbors

        Returns:
            Tuple of (distances, ids, indices)
        """
        if self.index is None:
            raise ValueError("No index built. Call build_index() first.")

        query = np.asarray(query, dtype=np.float64)
        if query.shape[0] != self.dim:
            raise ValueError(
                f"Query dim {query.shape[0]} != store dim {self.dim}"
            )

        if self.index_type == "kdtree":
            dists, indices, points = self.index.search(query, k)
            # Convert indices to ids
            search_ids = np.array([self.ids[i] for i in indices])
            return dists, search_ids, indices
        else:
            return self.index.search(query, k)

    def range_search(self, query: np.ndarray, radius: float) -> tuple:
        """Find all vectors within the given radius.

        Only supported for KD-Tree index.

        Args:
            query: Query vector
            radius: Distance threshold

        Returns:
            Tuple of (distances, ids, indices)
        """
        if self.index_type != "kdtree":
            raise ValueError("Range search only supported with KD-Tree index")
        return self.index.range_search(query, radius)

    def __len__(self) -> int:
        return len(self.vectors)

    def __contains__(self, vid: str) -> bool:
        return vid in self.ids

    def get_vector(self, vid: str) -> np.ndarray:
        """Get a vector by its ID.

        Args:
            vid: Vector identifier

        Returns:
            The vector as a numpy array

        Raises:
            KeyError: If the ID is not found
        """
        if vid not in self.ids:
            raise KeyError(f"Vector ID '{vid}' not found")
        idx = self.ids.index(vid)
        return self.vectors[idx]
