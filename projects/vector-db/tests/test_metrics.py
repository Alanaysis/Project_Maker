"""Tests for vector similarity metrics."""

import numpy as np
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.metrics import (
    euclidean_distance,
    cosine_similarity,
    dot_product,
    l2_normalize,
    batch_cosine_similarity,
    batch_euclidean_distances,
)


class TestEuclideanDistance:
    def test_identical_vectors(self):
        v = np.array([1.0, 2.0, 3.0])
        assert euclidean_distance(v, v) == 0.0

    def test_known_distance(self):
        a = np.array([0.0, 0.0])
        b = np.array([3.0, 4.0])
        assert euclidean_distance(a, b) == pytest.approx(5.0)

    def test_3d_distance(self):
        a = np.array([1.0, 2.0, 3.0])
        b = np.array([4.0, 6.0, 8.0])
        expected = np.sqrt(9 + 16 + 25)
        assert euclidean_distance(a, b) == pytest.approx(expected)

    def test_dimension_mismatch(self):
        a = np.array([1.0, 2.0])
        b = np.array([1.0, 2.0, 3.0])
        with pytest.raises(ValueError):
            euclidean_distance(a, b)


class TestCosineSimilarity:
    def test_identical_vectors(self):
        v = np.array([1.0, 2.0, 3.0])
        assert cosine_similarity(v, v) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        a = np.array([1.0, 0.0])
        b = np.array([0.0, 1.0])
        assert cosine_similarity(a, b) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        a = np.array([1.0, 0.0])
        b = np.array([-1.0, 0.0])
        assert cosine_similarity(a, b) == pytest.approx(-1.0)

    def test_parallel_vectors(self):
        a = np.array([1.0, 2.0])
        b = np.array([2.0, 4.0])  # 2 * a
        assert cosine_similarity(a, b) == pytest.approx(1.0)

    def test_dimension_mismatch(self):
        a = np.array([1.0, 2.0])
        b = np.array([1.0, 2.0, 3.0])
        with pytest.raises(ValueError):
            cosine_similarity(a, b)

    def test_zero_vector(self):
        a = np.array([0.0, 0.0])
        b = np.array([1.0, 2.0])
        with pytest.raises(ZeroDivisionError):
            cosine_similarity(a, b)


class TestDotProduct:
    def test_known_dot_product(self):
        a = np.array([1.0, 2.0, 3.0])
        b = np.array([4.0, 5.0, 6.0])
        assert dot_product(a, b) == pytest.approx(32.0)

    def test_orthogonal(self):
        a = np.array([1.0, 0.0])
        b = np.array([0.0, 1.0])
        assert dot_product(a, b) == pytest.approx(0.0)

    def test_dimension_mismatch(self):
        a = np.array([1.0, 2.0])
        b = np.array([1.0, 2.0, 3.0])
        with pytest.raises(ValueError):
            dot_product(a, b)


class TestL2Normalize:
    def test_normalize(self):
        v = np.array([3.0, 4.0])
        normalized = l2_normalize(v)
        assert np.linalg.norm(normalized) == pytest.approx(1.0)

    def test_normalize_preserves_direction(self):
        v = np.array([1.0, 2.0, 3.0])
        normalized = l2_normalize(v)
        # cosine similarity should be 1
        assert cosine_similarity(v, normalized) == pytest.approx(1.0)

    def test_zero_vector(self):
        v = np.array([0.0, 0.0])
        with pytest.raises(ZeroDivisionError):
            l2_normalize(v)

    def test_non_1d(self):
        v = np.array([[1.0, 2.0]])
        with pytest.raises(ValueError):
            l2_normalize(v)


class TestBatchCosineSimilarity:
    def test_batch_similarity(self):
        query = np.array([1.0, 0.0])
        database = np.array([
            [1.0, 0.0],
            [0.0, 1.0],
            [-1.0, 0.0],
        ])
        sim = batch_cosine_similarity(query, database)
        assert sim[0] == pytest.approx(1.0)
        assert sim[1] == pytest.approx(0.0)
        assert sim[2] == pytest.approx(-1.0)


class TestBatchEuclideanDistances:
    def test_batch_distances(self):
        query = np.array([0.0, 0.0])
        database = np.array([
            [3.0, 4.0],
            [0.0, 1.0],
            [1.0, 0.0],
        ])
        dists = batch_euclidean_distances(query, database)
        assert dists[0] == pytest.approx(5.0)
        assert dists[1] == pytest.approx(1.0)
        assert dists[2] == pytest.approx(1.0)
