"""Tests for brute-force KNN search."""

import numpy as np
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.brute_force import BruteForceKNN
from src.metrics import euclidean_distance


class TestBruteForceKNN:
    def setup_method(self):
        """Create a known dataset for testing."""
        np.random.seed(42)
        self.vectors = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 1.0, 0.0],
            [1.0, 0.0, 1.0],
            [0.0, 1.0, 1.0],
            [1.0, 1.0, 1.0],
        ], dtype=np.float64)
        self.ids = ["a", "b", "c", "d", "e", "f", "g"]
        self.bf = BruteForceKNN(metric="euclidean")
        self.bf.build(self.vectors, self.ids)

    def test_search_returns_k_results(self):
        query = np.array([0.1, 0.1, 0.1])
        dists, ids, indices = self.bf.search(query, k=3)
        assert len(dists) == 3
        assert len(ids) == 3
        assert len(indices) == 3

    def test_nearest_is_correct(self):
        query = np.array([0.1, 0.0, 0.0])
        dists, ids, indices = self.bf.search(query, k=1)
        assert ids[0] == "a"
        assert dists[0] == pytest.approx(0.9)

    def test_distances_are_sorted(self):
        query = np.array([0.5, 0.5, 0.5])
        dists, _, _ = self.bf.search(query, k=5)
        for i in range(len(dists) - 1):
            assert dists[i] <= dists[i + 1]

    def test_all_results_returned(self):
        query = np.array([0.5, 0.5, 0.5])
        dists, ids, _ = self.bf.search(query, k=7)
        assert len(dists) == 7
        assert set(ids) == set(self.ids)

    def test_empty_index(self):
        empty_bf = BruteForceKNN(metric="euclidean")
        dists, ids, indices = empty_bf.search(np.array([1.0, 2.0]))
        assert len(dists) == 0

    def test_cosine_metric(self):
        bf_cos = BruteForceKNN(metric="cosine")
        vectors = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.707, 0.707, 0.0],
        ], dtype=np.float64)
        bf_cos.build(vectors)
        query = np.array([1.0, 0.1, 0.0])
        dists, ids, indices = bf_cos.search(query, k=2)
        # First result should have smallest distance (highest similarity)
        assert dists[0] <= dists[1]

    def test_add_single_vector(self):
        self.bf.add(np.array([0.5, 0.5, 0.5]), "h")
        assert len(self.bf) == 8
        dists, ids, _ = self.bf.search(np.array([0.0, 0.0, 0.0]), k=1)
        # "h" is at [0.5, 0.5, 0.5], distance = sqrt(0.75)
        assert "h" in ids

    def test_dimension_check(self):
        query = np.array([1.0, 2.0])  # wrong dimension
        with pytest.raises(ValueError):
            self.bf.search(query, k=3)
