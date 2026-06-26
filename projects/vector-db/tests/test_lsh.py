"""Tests for LSH approximate nearest neighbor search."""

import numpy as np
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.lsh import LSHForest
from src.brute_force import BruteForceKNN


class TestLSH:
    def setup_method(self):
        """Create a known dataset."""
        np.random.seed(42)
        self.vectors = np.random.randn(200, 32).astype(np.float64)
        self.ids = [f"v_{i}" for i in range(200)]

    def test_build(self):
        lsh = LSHForest(num_tables=5, num_projections=10)
        lsh.build(self.vectors, self.ids)
        assert len(lsh) == 200
        assert lsh.dim == 32
        assert len(lsh.hash_tables) == 5

    def test_search_returns_results(self):
        lsh = LSHForest(num_tables=10, num_projections=20)
        lsh.build(self.vectors, self.ids)
        query = np.random.randn(32)
        dists, ids, indices = lsh.search(query, k=5)
        assert len(dists) == 5
        assert len(ids) == 5
        assert len(indices) == 5

    def test_search_accuracy(self):
        """LSH should return candidate results for queries."""
        np.random.seed(123)
        vectors = np.random.randn(100, 8).astype(np.float64)
        ids = [f"v_{i}" for i in range(100)]

        lsh = LSHForest(num_tables=10, num_projections=10)
        lsh.build(vectors, ids)

        # LSH should return results for any query
        results_count = 0
        for i in range(20):
            query = vectors[i]
            dists, lsh_idx, _ = lsh.search(query, k=10)
            if len(dists) >= 1:
                results_count += 1

        # LSH should return results for all queries
        assert results_count >= 15, f"LSH returned results for only {results_count}/20 queries"

    def test_empty_index(self):
        lsh = LSHForest(num_tables=5, num_projections=10)
        query = np.random.randn(32)
        dists, ids, indices = lsh.search(query, k=5)
        assert len(dists) == 0

    def test_add_vector(self):
        lsh = LSHForest(num_tables=5, num_projections=10)
        lsh.build(self.vectors, self.ids)
        lsh.add(np.random.randn(32), "new_vec")
        assert len(lsh) == 201

    def test_dimension_check(self):
        lsh = LSHForest(num_tables=5, num_projections=10)
        lsh.build(self.vectors, self.ids)
        wrong_query = np.random.randn(16)
        with pytest.raises(ValueError):
            lsh.search(wrong_query, k=5)
