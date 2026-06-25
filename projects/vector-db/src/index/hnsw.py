"""Hierarchical Navigable Small World (HNSW) index for fast approximate nearest neighbor search."""

import numpy as np
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict

from .base import BaseIndex
from ..metrics import DistanceMetric, get_distance_fn


class HNSWIndex(BaseIndex):
    """HNSW index for approximate nearest neighbor search.

    Builds a multi-layer graph where each layer is a navigable small world.
    Search starts from the top layer and descends, using greedy search at
    each layer to find good entry points.

    Provides excellent recall with logarithmic search time.
    """

    def __init__(self, dimension: int, metric: DistanceMetric = DistanceMetric.EUCLIDEAN,
                 max_connections: int = 16, max_connections_layer0: int = 32,
                 ef_construction: int = 200, max_layers: int = 16, seed: int = 42):
        """Initialize HNSW index.

        Args:
            dimension: Vector dimension.
            metric: Distance metric to use.
            max_connections: Maximum connections per node per layer (M).
            max_connections_layer0: Maximum connections for layer 0 (2*M).
            ef_construction: Size of the dynamic candidate list during construction.
            max_layers: Maximum number of layers.
            seed: Random seed for reproducibility.
        """
        super().__init__(dimension, metric)
        self.max_connections = max_connections
        self.max_connections_layer0 = max_connections_layer0
        self.ef_construction = ef_construction
        self.max_layers = max_layers
        self._distance_fn, self._is_similarity = get_distance_fn(metric)
        self._rng = np.random.RandomState(seed)

        # Graph structure: layer -> {node_id: set of neighbor_ids}
        self._graphs: List[Dict[str, Set[str]]] = [defaultdict(set) for _ in range(max_layers)]

        # Node layers: which layers each node appears in
        self._node_layers: Dict[str, int] = {}

        # Entry point (node at the highest layer)
        self._entry_point: Optional[str] = None
        self._entry_layer: int = -1

    def _assign_layer(self) -> int:
        """Assign a random layer to a new node.

        Uses exponential decay: P(layer=l) = (1/M) * exp(-l/M).

        Returns:
            Layer number.
        """
        if self.max_connections == 0:
            return 0
        layer = 0
        r = self._rng.random()
        while r < 0.5 and layer < self.max_layers - 1:
            layer += 1
            r = self._rng.random()
        return layer

    def _distance(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute distance between two vectors.

        Returns:
            Distance value (always interpreted as: lower = more similar for search).
        """
        raw = self._distance_fn(a, b)
        # For similarity metrics, negate so lower = better for consistent search
        if self._is_similarity:
            return -raw
        return raw

    def _search_layer(self, query: np.ndarray, entry_points: Set[str],
                      num_closest: int, layer: int) -> List[Tuple[str, float]]:
        """Search for nearest neighbors in a single layer using greedy search.

        Args:
            query: Query vector.
            entry_points: Starting points for the search.
            num_closest: Number of closest neighbors to return.
            layer: Layer to search in.

        Returns:
            List of (id, distance) tuples sorted by distance.
        """
        # Initialize candidates and visited set
        candidates = []
        visited = set()
        results = []

        for ep in entry_points:
            if ep not in self._vectors:
                continue
            dist = self._distance(query, self._vectors[ep])
            candidates.append((dist, ep))
            visited.add(ep)
            results.append((ep, dist))

        candidates.sort()
        results.sort(key=lambda x: x[1])

        while candidates:
            dist_c, current = candidates.pop(0)

            # Stop if current candidate is farther than the furthest result
            if results and dist_c > results[-1][1]:
                break

            # Explore neighbors
            neighbors = self._graphs[layer].get(current, set())
            for neighbor in neighbors:
                if neighbor in visited or neighbor not in self._vectors:
                    continue
                visited.add(neighbor)

                dist_n = self._distance(query, self._vectors[neighbor])

                # Add to results if better than worst result or we haven't filled results
                if len(results) < num_closest or dist_n < results[-1][1]:
                    candidates.append((dist_n, neighbor))
                    results.append((neighbor, dist_n))
                    results.sort(key=lambda x: x[1])
                    if len(results) > num_closest:
                        results = results[:num_closest]
                    candidates.sort()

        return results

    def _select_neighbors(self, candidates: List[Tuple[str, float]],
                          max_neighbors: int) -> List[str]:
        """Select the best neighbors from candidates (simple nearest selection).

        Args:
            candidates: List of (id, distance) tuples.
            max_neighbors: Maximum number of neighbors to select.

        Returns:
            List of selected neighbor IDs.
        """
        candidates.sort(key=lambda x: x[1])
        return [c[0] for c in candidates[:max_neighbors]]

    def _on_add(self, id: str, vector: np.ndarray, metadata: Optional[Dict[str, Any]]) -> None:
        """Add a node to the HNSW graph."""
        # Assign layer to new node
        layer = self._assign_layer()
        self._node_layers[id] = layer

        # If this is the first node, make it the entry point
        if self._entry_point is None:
            self._entry_point = id
            self._entry_layer = layer
            return

        # Search for nearest neighbors from top layer down to layer+1
        current_entry = {self._entry_point}
        for l in range(self._entry_layer, layer, -1):
            results = self._search_layer(vector, current_entry, 1, l)
            if results:
                current_entry = {results[0][0]}

        # For layers 0 to layer, add edges
        max_conn = self.max_connections
        for l in range(min(layer, self._entry_layer), -1, -1):
            if l == 0:
                max_conn = self.max_connections_layer0

            # Search for neighbors in this layer
            results = self._search_layer(vector, current_entry, self.ef_construction, l)
            neighbors = self._select_neighbors(results, max_conn)

            # Add bidirectional edges
            self._graphs[l][id] = set(neighbors)
            for neighbor in neighbors:
                self._graphs[l][neighbor].add(id)
                # Prune neighbors if they have too many
                if len(self._graphs[l][neighbor]) > max_conn:
                    neighbor_results = []
                    for nn in self._graphs[l][neighbor]:
                        if nn in self._vectors:
                            dist = self._distance(self._vectors[neighbor], self._vectors[nn])
                            neighbor_results.append((nn, dist))
                    pruned = self._select_neighbors(neighbor_results, max_conn)
                    self._graphs[l][neighbor] = set(pruned)

            # Use results as entry points for next layer
            current_entry = {r[0] for r in results[:1]}

        # Update entry point if new node is at a higher layer
        if layer > self._entry_layer:
            self._entry_point = id
            self._entry_layer = layer

    def _on_remove(self, id: str) -> None:
        """Remove a node from the HNSW graph."""
        layer = self._node_layers.get(id, 0)

        # Remove edges from all layers
        for l in range(layer + 1):
            neighbors = self._graphs[l].get(id, set())
            for neighbor in neighbors:
                self._graphs[l][neighbor].discard(id)
            if id in self._graphs[l]:
                del self._graphs[l][id]

        if id in self._node_layers:
            del self._node_layers[id]

        # Update entry point if necessary
        if id == self._entry_point:
            self._entry_point = None
            self._entry_layer = -1
            # Find new entry point (node at highest layer)
            for node, node_layer in self._node_layers.items():
                if node_layer > self._entry_layer:
                    self._entry_point = node
                    self._entry_layer = node_layer

    def _remove_from_index(self, id: str) -> None:
        """Remove from graph before re-adding."""
        self._on_remove(id)

    def search(self, query: np.ndarray, k: int = 10,
               metadata_filter: Optional[Any] = None,
               ef_search: int = 50) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for approximate k nearest neighbors.

        Args:
            query: Query vector.
            k: Number of results to return.
            metadata_filter: Optional metadata filter.
            ef_search: Size of the dynamic candidate list during search.

        Returns:
            List of (id, distance, metadata) tuples sorted by distance.
        """
        if query.shape[0] != self.dimension:
            raise ValueError(
                f"Query dimension {query.shape[0]} doesn't match index dimension {self.dimension}"
            )

        if not self._vectors or self._entry_point is None:
            return []

        # Search from top layer down to layer 1
        current_entry = {self._entry_point}
        for l in range(self._entry_layer, 0, -1):
            results = self._search_layer(query, current_entry, 1, l)
            if results:
                current_entry = {results[0][0]}

        # Search layer 0 with larger ef
        results = self._search_layer(query, current_entry, max(ef_search, k), 0)

        # Convert distances back to original metric and apply filters
        final_results = []
        for id, dist in results:
            if id not in self._vectors:
                continue
            if metadata_filter is not None and not metadata_filter.match(self._metadata[id]):
                continue

            # Convert back to original distance/similarity
            original_dist = -dist if self._is_similarity else dist
            final_results.append((id, original_dist, self._metadata[id].copy()))

        # Sort by original metric
        if self._is_similarity:
            final_results.sort(key=lambda x: x[1], reverse=True)
        else:
            final_results.sort(key=lambda x: x[1])

        return final_results[:k]
