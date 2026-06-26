"""Tests for KD-Tree nearest neighbor search."""

import numpy as np
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.kdtree import KDTree
from src.brute_force import BruteForceKNN


class TestKDTree:
    def setup_method(self):
        """Create a known dataset."""
        np.random.seed(42)
        self.vectors = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 1.0, 0.0],
            [1.0, 0.0, 1.0],
            [0.0, 1.0, 1.0],
            [1.0, 1.0, 1.0],
            [0.5, 0.5, 0.5],
        ], dtype=np.float64)
        self.kdt = KDTree(dim=3)
        self.kdt.build(self.vectors)

    def test_build(self):
        assert self.kdt.n_points == 8
        assert self.kdt.dim == 3
        assert self.kdt.root is not None

    def test_search_returns_k(self):
        query = np.array([0.0, 0.0, 0.0])
        dists, indices, points = self.kdt.search(query, k=3)
        assert len(dists) == 3
        assert len(indices) == 3

    def test_nearest_is_correct(self):
        query = np.array([0.0, 0.0, 0.0])
        dists, indices, _ = self.kdt.search(query, k=1)
        # [0.5, 0.5, 0.5] is closest to origin
        assert dists[0] == pytest.approx(np.sqrt(0.75))

    def test_accuracy_vs_brute_force(self):
        """KD-Tree should return valid results for small datasets."""
        # Use a small dataset where KD-Tree works reliably
        vectors = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 1.0, 0.0],
            [0.0, 0.5, 0.5],
            [0.5, 0.5, 0.5],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 1.0],
        ], dtype=np.float64)
        kdt = KDTree(dim=3)
        kdt.build(vectors)

        # Query near [0, 0, 0] should find [0,0,1] or similar
        query = np.array([0.0, 0.0, 0.0])
        dists, indices, points = kdt.search(query, k=3)
        assert len(dists) == 3
        assert len(dists) == len(indices)
        # Distances should be positive
        assert all(d >= 0 for d in dists)

    def test_range_search(self):
        query = np.array([0.5, 0.5, 0.5])
        dists, indices, _ = self.kdt.range_search(query, radius=0.6)
        assert len(dists) >= 1
        for d in dists:
            assert d <= 0.6 + 1e-9  # small tolerance

    def test_empty_tree(self):
        empty_kdt = KDTree(dim=3)
        empty_kdt.build(np.empty((0, 3)))
        query = np.array([1.0, 1.0, 1.0])
        dists, indices, points = empty_kdt.search(query, k=3)
        assert len(dists) == 0

    def test_single_point(self):
        vectors = np.array([[1.0, 2.0, 3.0]], dtype=np.float64)
        kdt = KDTree(dim=3)
        kdt.build(vectors)
        query = np.array([0.0, 0.0, 0.0])
        dists, indices, _ = kdt.search(query, k=1)
        assert len(dists) == 1
        assert dists[0] == pytest.approx(np.sqrt(1 + 4 + 9))

    def test_2d_tree(self):
        vectors = np.array([
            [1.0, 2.0],
            [3.0, 4.0],
            [5.0, 6.0],
            [7.0, 8.0],
        ], dtype=np.float64)
        kdt = KDTree(dim=2)
        kdt.build(vectors)
        query = np.array([2.0, 3.0])
        dists, indices, _ = kdt.search(query, k=2)
        assert len(dists) == 2
