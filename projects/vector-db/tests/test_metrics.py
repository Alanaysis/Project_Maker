"""Tests for distance metrics."""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.metrics import (
    euclidean_distance, cosine_similarity, inner_product,
    compute_distance, DistanceMetric
)


def test_euclidean_distance():
    """Test Euclidean distance computation."""
    a = np.array([0, 0, 0], dtype=np.float32)
    b = np.array([3, 4, 0], dtype=np.float32)
    assert abs(euclidean_distance(a, b) - 5.0) < 1e-6

    # Same point
    assert euclidean_distance(a, a) == 0.0

    # 1D
    a = np.array([1.0])
    b = np.array([4.0])
    assert abs(euclidean_distance(a, b) - 3.0) < 1e-6
    print("PASS: test_euclidean_distance")


def test_cosine_similarity():
    """Test cosine similarity computation."""
    # Same direction
    a = np.array([1, 0, 0], dtype=np.float32)
    b = np.array([2, 0, 0], dtype=np.float32)
    assert abs(cosine_similarity(a, b) - 1.0) < 1e-6

    # Orthogonal
    c = np.array([0, 1, 0], dtype=np.float32)
    assert abs(cosine_similarity(a, c)) < 1e-6

    # Opposite direction
    d = np.array([-1, 0, 0], dtype=np.float32)
    assert abs(cosine_similarity(a, d) - (-1.0)) < 1e-6

    # Zero vector
    z = np.zeros(3)
    assert cosine_similarity(a, z) == 0.0
    print("PASS: test_cosine_similarity")


def test_inner_product():
    """Test inner product computation."""
    a = np.array([1, 2, 3], dtype=np.float32)
    b = np.array([4, 5, 6], dtype=np.float32)
    expected = 1*4 + 2*5 + 3*6  # 32
    assert abs(inner_product(a, b) - expected) < 1e-6

    # Orthogonal
    c = np.array([0, 0, 0], dtype=np.float32)
    assert inner_product(a, c) == 0.0
    print("PASS: test_inner_product")


def test_compute_distance():
    """Test compute_distance dispatcher."""
    a = np.array([1, 0], dtype=np.float32)
    b = np.array([0, 1], dtype=np.float32)

    # Euclidean
    dist = compute_distance(a, b, DistanceMetric.EUCLIDEAN)
    assert abs(dist - np.sqrt(2)) < 1e-6

    # Cosine
    sim = compute_distance(a, b, DistanceMetric.COSINE)
    assert abs(sim) < 1e-6  # Orthogonal

    # Inner product
    ip = compute_distance(a, b, DistanceMetric.INNER_PRODUCT)
    assert abs(ip) < 1e-6  # Orthogonal
    print("PASS: test_compute_distance")


def test_metric_with_db():
    """Test metrics work correctly through the database."""
    from src.vector_db import VectorDB

    # Cosine similarity should find most similar by angle, not magnitude
    db = VectorDB(dimension=3, index_type="brute_force", metric="cosine")

    db.insert("a", [1, 0, 0])
    db.insert("b", [10, 0, 0])  # Same direction, different magnitude
    db.insert("c", [0, 1, 0])   # Orthogonal

    # Query in direction [1,0,0] should match a and b (both cosine sim = 1.0)
    results = db.search([1, 0, 0], k=3)
    top_ids = [r["id"] for r in results[:2]]
    assert "a" in top_ids
    assert "b" in top_ids
    print("PASS: test_metric_with_db")


if __name__ == "__main__":
    test_euclidean_distance()
    test_cosine_similarity()
    test_inner_product()
    test_compute_distance()
    test_metric_with_db()
    print("\nAll metrics tests passed!")
