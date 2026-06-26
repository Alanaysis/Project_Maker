"""KD-Tree module for exact nearest neighbor search.

Implements a KD-Tree (k-dimensional tree) data structure for efficient
nearest neighbor search in metric spaces. The tree recursively partitions
space along alternating dimensions.

Time complexity:
    - Build: O(n * d * log(n))
    - Query: O(log(n)) average, O(n) worst case
    - Degenerates in high dimensions (>20D) — the "curse of dimensionality"

Reference:
    "Multidimensional Binary Search Trees in Database Applications" -
    Bentley, 1975
"""

import heapq
import numpy as np
from .metrics import euclidean_distance


class KDNode:
    """A node in the KD-Tree.

    Attributes:
        point: The data point stored at this node (1D array)
        left: Left child node (points with smaller value on split dimension)
        right: Right child node (points with larger value on split dimension)
        axis: The dimension used for splitting at this node
        index: Original index of the point in the dataset
    """

    __slots__ = ["point", "left", "right", "axis", "index"]

    def __init__(
        self,
        point: np.ndarray,
        axis: int,
        index: int,
        left: "KDNode" = None,
        right: "KDNode" = None,
    ):
        self.point = point
        self.axis = axis
        self.index = index
        self.left = left
        self.right = right


class KDTree:
    """KD-Tree for exact nearest neighbor search.

    Builds a binary tree that recursively partitions the data space.
    Each node splits along one dimension, alternating at each level.

    The search uses branch-and-bound: it prunes branches that cannot
    contain a closer neighbor than the current best.

    Attributes:
        root: Root node of the tree
        dim: Vector dimensionality
        n_points: Number of points stored
    """

    def __init__(self, dim: int = 0):
        """Initialize KD-Tree.

        Args:
            dim: Dimensionality of the vectors
        """
        self.root: KDNode = None
        self.dim = dim
        self.n_points = 0

    def build(self, vectors: np.ndarray) -> None:
        """Build the KD-Tree from a set of vectors.

        Recursively partitions the data, choosing the dimension with
        the largest variance at each node for splitting.

        Args:
            vectors: Array of vectors of shape [n, dim]
        """
        vectors = np.array(vectors, dtype=np.float64)
        self.n_points = len(vectors)
        if self.n_points == 0:
            self.root = None
            return
        self.dim = vectors.shape[1]
        self.root = self._build(vectors, 0)

    def _build(self, vectors: np.ndarray, depth: int) -> KDNode:
        """Recursively build the KD-Tree.

        At each level, picks the axis with the largest spread,
        finds the median along that axis, and splits.

        Args:
            vectors: Points to insert at this level
            depth: Current tree depth (used to determine split axis)

        Returns:
            The root node of this subtree
        """
        if len(vectors) == 0:
            return None

        axis = depth % self.dim

        # Choose axis with largest variance for better balance
        if len(vectors) > 1:
            variances = np.var(vectors, axis=0)
            axis = int(np.argmax(variances))

        # Find median along the chosen axis
        median_idx = len(vectors) // 2
        sorted_idx = np.argsort(vectors[:, axis])
        vectors_sorted = vectors[sorted_idx]
        median_point = vectors_sorted[median_idx]

        # Split into left and right halves
        left_vectors = vectors_sorted[:median_idx]
        right_vectors = vectors_sorted[median_idx + 1 :]

        return KDNode(
            point=median_point,
            axis=axis,
            index=sorted_idx[median_idx],
            left=self._build(left_vectors, depth + 1),
            right=self._build(right_vectors, depth + 1),
        )

    def search(self, query: np.ndarray, k: int = 10) -> tuple:
        """Search for the k nearest neighbors.

        Uses recursive traversal with pruning: if a subtree cannot
        possibly contain a closer point than the current best, skip it.

        Args:
            query: Query vector of shape [dim]
            k: Number of nearest neighbors to return

        Returns:
            Tuple of (distances, indices, points) where:
                distances: k distances to nearest neighbors
                indices: k indices into the original dataset
                points: k nearest neighbor points
        """
        if self.root is None or self.n_points == 0:
            return np.array([]), np.array([]), np.array([])

        query = np.asarray(query, dtype=np.float64)
        k = min(k, self.n_points)

        # Use a max-heap to track top-k closest points.
        # Python's heapq is a min-heap, so we negate distances.
        # Include index as tiebreaker to avoid comparing numpy arrays.
        heap = []  # entries: (-distance, insertion_order, index, point)
        self._heap_counter = 0

        self._search_recursive(self.root, query, k, heap)

        if not heap:
            return np.array([]), np.array([]), np.array([])

        # Extract from heap and sort by distance (ascending)
        results = [(-d, idx, pt) for d, _, idx, pt in heap]
        results.sort(key=lambda x: x[0])

        dists = np.array([r[0] for r in results])
        indices = np.array([r[1] for r in results])
        points = np.array([r[2] for r in results])

        return dists, indices, points

    def _search_recursive(
        self,
        node: KDNode,
        query: np.ndarray,
        k: int,
        heap: list,
    ) -> None:
        """Recursively traverse the tree to find nearest neighbors.

        The pruning logic:
        1. Go down the appropriate side based on the split dimension
        2. Check if the other side could contain a closer point
           (if the distance to the splitting plane < best distance found)
        3. Update best results if current node is closer

        Args:
            node: Current node being visited
            query: Query vector
            k: Number of nearest neighbors to find
            heap: Max-heap of (-distance, index, point) for top-k
        """
        if node is None:
            return

        # Compute distance to current node's point
        dist = euclidean_distance(query, node.point)

        # Add to heap if we have room or this is closer than the worst
        if len(heap) < k or dist < -heap[0][0]:
            self._heap_counter += 1
            heapq.heappush(heap, (-dist, self._heap_counter, node.index, node.point))
            if len(heap) > k:
                heapq.heappop(heap)

        # Get current worst distance in heap (as positive value)
        worst_dist = -heap[0][0] if heap else float('inf')

        # Decide which subtree to visit first
        axis = node.axis
        split_value = node.point[axis]
        query_value = query[axis]

        if query_value < split_value:
            near_side = node.left
            far_side = node.right
        else:
            near_side = node.right
            far_side = node.left

        # Visit the closer side first
        self._search_recursive(near_side, query, k, heap)

        # Re-check worst distance after visiting near side
        worst_dist = -heap[0][0] if heap else float('inf')

        # Check if we need to visit the far side
        # Only if the splitting hyperplane is closer than our worst result
        if abs(query_value - split_value) < worst_dist:
            self._search_recursive(far_side, query, k, heap)

    def range_search(
        self,
        query: np.ndarray,
        radius: float,
    ) -> tuple:
        """Find all points within a given radius of the query.

        Args:
            query: Query vector
            radius: Maximum distance threshold

        Returns:
            Tuple of (distances, indices, points) for all points within radius
        """
        if self.root is None:
            return np.array([]), np.array([]), np.array([])

        results_dists = []
        results_indices = []
        results_points = []

        self._range_recursive(self.root, query, radius, 0, results_dists, results_indices, results_points)

        order = np.argsort(results_dists)
        return (
            np.array([results_dists[i] for i in order]),
            np.array([results_indices[i] for i in order]),
            np.array([results_points[i] for i in order]),
        )

    def _range_recursive(
        self,
        node: KDNode,
        query: np.ndarray,
        radius: float,
        depth: int,
        results_dists: list,
        results_indices: list,
        results_points: list,
    ) -> None:
        """Recursively find all points within radius.

        Args:
            node: Current node
            query: Query vector
            radius: Distance threshold
            depth: Current depth
            results_dists: Accumulated distances
            results_indices: Accumulated indices
            results_points: Accumulated points
        """
        if node is None:
            return

        dist = euclidean_distance(query, node.point)
        if dist <= radius:
            results_dists.append(dist)
            results_indices.append(node.index)
            results_points.append(node.point)

        axis = node.axis
        split_value = node.point[axis]
        query_value = query[axis]

        # Decide which sides to search
        if query_value - radius <= split_value:
            self._range_recursive(
                node.left, query, radius, depth + 1,
                results_dists, results_indices, results_points,
            )
        if query_value + radius >= split_value:
            self._range_recursive(
                node.right, query, radius, depth + 1,
                results_dists, results_indices, results_points,
            )
