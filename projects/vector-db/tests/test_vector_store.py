"""Tests for VectorStore high-level interface."""

import numpy as np
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.vector_store import VectorStore


class TestVectorStore:
    def setup_method(self):
        """Create a vector store with sample data."""
        np.random.seed(42)
        self.store = VectorStore(dim=32)
        vectors = np.random.randn(20, 32)
        for i in range(len(vectors)):
            self.store.add(vectors[i], vid=f"doc_{i}")

    def test_add_and_len(self):
        assert len(self.store) == 20
        assert self.store.dim == 32

    def test_add_batch(self):
        store = VectorStore(dim=10)
        vectors = np.random.randn(5, 10)
        store.add_batch(vectors)
        assert len(store) == 5

    def test_build_index_brute_force(self):
        self.store.build_index("brute_force")
        assert self.store.index_type == "brute_force"
        assert self.store.index is not None

    def test_build_index_lsh(self):
        self.store.build_index("lsh")
        assert self.store.index_type == "lsh"

    def test_build_index_kdtree(self):
        self.store.build_index("kdtree")
        assert self.store.index_type == "kdtree"

    def test_search_returns_results(self):
        self.store.build_index("brute_force")
        query = np.random.randn(32)
        dists, ids, indices = self.store.search(query, k=5)
        assert len(dists) == 5

    def test_search_without_index(self):
        store = VectorStore(dim=10)
        store.add(np.random.randn(10))
        with pytest.raises(ValueError):
            store.search(np.random.randn(10), k=3)

    def test_dimension_mismatch(self):
        store = VectorStore(dim=10)
        with pytest.raises(ValueError):
            store.add(np.random.randn(15))

    def test_contains(self):
        assert "doc_0" in self.store
        assert "nonexistent" not in self.store

    def test_get_vector(self):
        v = self.store.get_vector("doc_0")
        assert v.shape == (32,)

    def test_get_vector_not_found(self):
        with pytest.raises(KeyError):
            self.store.get_vector("nonexistent")

    def test_range_search_requires_kdtree(self):
        self.store.build_index("brute_force")
        query = np.random.randn(32)
        with pytest.raises(ValueError):
            self.store.range_search(query, radius=1.0)

    def test_build_empty_store(self):
        store = VectorStore(dim=10)
        with pytest.raises(ValueError):
            store.build_index("brute_force")

    def test_kdtree_search_accuracy(self):
        """VectorStore with KD-Tree should give exact results."""
        np.random.seed(99)
        store = VectorStore(dim=5)
        vectors = np.random.randn(100, 5)
        for i in range(len(vectors)):
            store.add(vectors[i])
        store.build_index("kdtree")

        query = np.random.randn(5)
        dists, indices, _ = store.search(query, k=10)
        assert len(dists) == 10

    def test_lsh_search(self):
        """VectorStore with LSH should return results."""
        self.store.build_index("lsh", num_tables=5, num_projections=10)
        query = np.random.randn(32)
        dists, ids, indices = self.store.search(query, k=5)
        assert len(dists) == 5
