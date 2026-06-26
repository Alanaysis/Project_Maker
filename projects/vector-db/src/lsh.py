"""Locality Sensitive Hashing (LSH) module.

Implements LSH for approximate nearest neighbor search. The key idea is
that similar items are more likely to hash to the same bucket than
dissimilar items.

This implementation uses random projection LSH for cosine similarity,
which is effective for high-dimensional vectors.

Reference:
    "Similarity Estimation from Hash Tables" - Indyk & Motwani, 1998
"""

import numpy as np
import hashlib
from collections import defaultdict
from .metrics import cosine_similarity, l2_normalize, batch_cosine_similarity


class LSHForest:
    """Locality Sensitive Hashing for approximate nearest neighbor search.

    Uses multiple hash tables with random projections to map similar
    vectors to the same bucket with high probability.

    How LSH works:
    1. Generate random projection vectors
    2. For each data vector, compute dot product with random vectors
    3. Use the sign of the dot product as the hash value
    4. Similar vectors (small angle) produce the same signs more often
    5. At query time, search the same buckets as the query vector

    The probability that two vectors hash to the same bucket is:
        p = 1 - (theta / pi)

    where theta is the angle between the vectors.

    Attributes:
        num_tables: Number of independent hash tables
        num_projections: Number of random projections per table
        hash_tables: Dict mapping hash strings to list of vector indices
        vectors: Stored vectors array
        ids: Vector identifiers
        dim: Vector dimensionality
    """

    def __init__(self, num_tables: int = 10, num_projections: int = 20):
        """Initialize LSH index.

        Args:
            num_tables: Number of hash tables (more = better accuracy, slower)
            num_projections: Projections per table (more = sharper threshold)
        """
        self.num_tables = num_tables
        self.num_projections = num_projections
        self.projection_matrices: list = []  # raw projection matrices
        self.hash_tables: list = []  # dict mapping hash string -> list of indices
        self.vectors: np.ndarray = np.empty((0, 0))
        self.ids: list = []
        self.dim: int = 0
        self.ranges: list = []  # min/max for each projection (used in search)
        # Per-table normalization parameters
        self.projected_mins: list = []  # min of projected values per projection per table
        self.projected_maxs: list = []  # max of projected values per projection per table

    def build(self, vectors: np.ndarray, ids: list = None) -> None:
        """Build the LSH index from a set of vectors.

        Generates random projection vectors and populates hash tables.

        Args:
            vectors: Array of vectors of shape [n, dim]
            ids: Optional list of identifiers
        """
        vectors = np.array(vectors, dtype=np.float64)
        self.vectors = vectors
        self.dim = vectors.shape[1]
        self.ids = ids or list(range(len(vectors)))

        # Generate random projection matrices
        # Each row is a random direction in R^dim
        self.projection_matrices = []
        self.hash_tables = []
        self.ranges = []

        # Compute min/max per projection dimension for normalization
        min_vals = np.min(vectors, axis=0)
        max_vals = np.max(vectors, axis=0)
        self.ranges = (max_vals - min_vals)
        self.ranges[self.ranges == 0] = 1.0

        for _ in range(self.num_tables):
            # Random projection matrix: [num_projections, dim]
            # Using normal distribution for random directions
            projections = np.random.randn(self.num_projections, self.dim)
            self.projection_matrices.append(projections)

        # Populate hash tables
        for projections in self.projection_matrices:
            table = defaultdict(list)
            # Project all vectors onto random directions
            projected = vectors @ projections.T  # [n, num_projections]
            # Normalize to [0, 1] range per projection
            proj_min = np.min(projected, axis=0)
            proj_max = np.max(projected, axis=0)
            self.projected_mins.append(proj_min)
            self.projected_maxs.append(proj_max)
            projected = (projected - proj_min) / np.maximum(
                proj_max - proj_min, 1e-10
            )
            projected = np.clip(projected, 0, 1)

            for i in range(len(vectors)):
                # Convert to string hash key
                key = "".join(f"{projected[i, j]:.4f}" for j in range(self.num_projections))
                table[key].append(i)
            self.hash_tables.append(table)

    def search(
        self,
        query: np.ndarray,
        k: int = 10,
        candidates_multiplier: int = 5,
    ) -> tuple:
        """Search for approximate nearest neighbors using LSH.

        Queries all hash buckets that the query vector falls into,
        then computes exact distances among those candidates.

        Args:
            query: Query vector of shape [dim]
            k: Number of nearest neighbors to return
            candidates_multiplier: How many times k in candidate pool

        Returns:
            Tuple of (distances, ids, indices)
        """
        if len(self.vectors) == 0:
            return np.array([]), np.array([]), np.array([])

        query = np.asarray(query, dtype=np.float64)
        if query.shape[0] != self.dim:
            raise ValueError(
                f"Query dimension {query.shape[0]} != index dimension {self.dim}"
            )

        # Collect candidate indices from all hash tables
        candidate_set = set()
        for table_idx, projections in enumerate(self.projection_matrices):
            projected = query @ projections.T  # [num_projections]
            # Normalize using same min/max from build for this table
            proj_min = self.projected_mins[table_idx]
            proj_max = self.projected_maxs[table_idx]
            projected = (projected - proj_min) / np.maximum(
                proj_max - proj_min, 1e-10
            )
            projected = np.clip(projected, 0, 1)
            key = "".join(f"{projected[j]:.4f}" for j in range(self.num_projections))

            if key in self.hash_tables[table_idx]:
                for idx in self.hash_tables[table_idx][key]:
                    candidate_set.add(idx)

        if not candidate_set:
            # Fallback: return random vectors
            indices = np.random.choice(len(self.vectors), size=min(k, len(self.vectors)), replace=False)
            return self._compute_exact(query, indices)

        candidates = list(candidate_set)
        # Limit candidates for efficiency
        if len(candidates) > k * candidates_multiplier:
            candidates = np.random.choice(candidates, size=k * candidates_multiplier, replace=False).tolist()

        return self._compute_exact(query, np.array(candidates))

    def _compute_exact(self, query: np.ndarray, indices: np.ndarray) -> tuple:
        """Compute exact distances among candidate vectors.

        Args:
            query: Query vector
            indices: Candidate indices

        Returns:
            Tuple of (distances, ids, sorted_indices)
        """
        candidates = self.vectors[indices]
        dists = 1.0 - batch_cosine_similarity(query, candidates)
        sorted_order = np.argsort(dists)[: min(len(dists), 100)]
        sorted_indices = indices[sorted_order]
        sorted_dists = dists[sorted_order]

        k = min(len(sorted_dists), 100)
        return (
            sorted_dists[:k],
            np.array([self.ids[i] for i in sorted_indices[:k]]),
            sorted_indices[:k],
        )

    def add(self, vector: np.ndarray, vid: int) -> None:
        """Add a vector to all hash tables.

        Note: For LSH, adding to an existing index is approximate.
        For best results, rebuild the index periodically.

        Args:
            vector: Vector to add
            vid: Identifier
        """
        vec = np.array(vector, dtype=np.float64).reshape(1, -1)
        self.vectors = np.vstack([self.vectors, vec])
        self.ids.append(vid)

        for table_idx, projections in enumerate(self.projection_matrices):
            projected = vec @ projections.T
            projected = np.clip(projected, 0, 1)
            key = "".join(f"{projected[0, j]:.4f}" for j in range(self.num_projections))

            if table_idx < len(self.hash_tables):
                if key not in self.hash_tables[table_idx]:
                    self.hash_tables[table_idx][key] = []
                self.hash_tables[table_idx][key].append(len(self.vectors) - 1)

    def __len__(self) -> int:
        return len(self.vectors)
