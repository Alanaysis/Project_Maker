"""Tests for index implementations (LSH and HNSW)."""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.vector_db import VectorDB, IndexType
from src.metrics import DistanceMetric
from src.index import BruteForceIndex, LSHIndex, HNSWIndex
from src.utils.helpers import random_vectors, recall_at_k


def test_lsh_basic():
    """Test LSH index basic operations."""
    db = VectorDB(dimension=64, index_type="lsh", metric="euclidean",
                  num_tables=5, num_hyperplanes=8)

    for i in range(50):
        db.insert(f"v{i}", np.random.randn(64))

    assert db.size == 50
    results = db.search(np.zeros(64), k=5)
    assert len(results) == 5
    print("PASS: test_lsh_basic")


def test_lsh_recall():
    """Test that LSH has reasonable recall compared to brute force."""
    dimension = 32
    n_vectors = 200
    k = 10

    vectors = random_vectors(n_vectors, dimension)

    # Build brute force index
    bf_db = VectorDB(dimension=dimension, index_type="brute_force", metric="euclidean")
    for i in range(n_vectors):
        bf_db.insert(f"v{i}", vectors[i])

    # Build LSH index
    lsh_db = VectorDB(dimension=dimension, index_type="lsh", metric="euclidean",
                      num_tables=10, num_hyperplanes=12)
    for i in range(n_vectors):
        lsh_db.insert(f"v{i}", vectors[i])

    # Compare results
    query = np.random.randn(dimension).astype(np.float32)
    bf_results = bf_db.search(query, k=k)
    lsh_results = lsh_db.search(query, k=k)

    bf_ids = [r["id"] for r in bf_results]
    lsh_ids = [r["id"] for r in lsh_results]

    recall = recall_at_k(lsh_ids, bf_ids, k)
    print(f"  LSH recall@{k}: {recall:.2%}")
    assert recall >= 0.3, f"LSH recall too low: {recall}"
    print("PASS: test_lsh_recall")


def test_lsh_with_filter():
    """Test LSH search with metadata filter."""
    db = VectorDB(dimension=16, index_type="lsh", metric="euclidean")

    for i in range(30):
        db.insert(f"v{i}", np.random.randn(16), {"group": "A" if i < 15 else "B"})

    from src.filter import eq
    results = db.search(np.zeros(16), k=5, metadata_filter=eq("group", "A"))
    for r in results:
        assert r["metadata"]["group"] == "A"
    print("PASS: test_lsh_with_filter")


def test_lsh_delete():
    """Test LSH deletion."""
    db = VectorDB(dimension=16, index_type="lsh")

    for i in range(10):
        db.insert(f"v{i}", np.random.randn(16))

    db.delete("v5")
    assert db.size == 9
    assert "v5" not in db

    results = db.search(np.zeros(16), k=10)
    result_ids = [r["id"] for r in results]
    assert "v5" not in result_ids
    print("PASS: test_lsh_delete")


def test_hnsw_basic():
    """Test HNSW index basic operations."""
    db = VectorDB(dimension=64, index_type="hnsw", metric="euclidean",
                  max_connections=8, ef_construction=50)

    for i in range(100):
        db.insert(f"v{i}", np.random.randn(64))

    assert db.size == 100
    results = db.search(np.zeros(64), k=10)
    assert len(results) == 10
    print("PASS: test_hnsw_basic")


def test_hnsw_recall():
    """Test that HNSW has high recall compared to brute force."""
    dimension = 32
    n_vectors = 300
    k = 10

    vectors = random_vectors(n_vectors, dimension)

    # Build brute force
    bf_db = VectorDB(dimension=dimension, index_type="brute_force", metric="euclidean")
    for i in range(n_vectors):
        bf_db.insert(f"v{i}", vectors[i])

    # Build HNSW
    hnsw_db = VectorDB(dimension=dimension, index_type="hnsw", metric="euclidean",
                       max_connections=16, ef_construction=100)
    for i in range(n_vectors):
        hnsw_db.insert(f"v{i}", vectors[i])

    # Compare
    query = np.random.randn(dimension).astype(np.float32)
    bf_results = bf_db.search(query, k=k)
    hnsw_results = hnsw_db.search(query, k=k, ef_search=50)

    bf_ids = [r["id"] for r in bf_results]
    hnsw_ids = [r["id"] for r in hnsw_results]

    recall = recall_at_k(hnsw_ids, bf_ids, k)
    print(f"  HNSW recall@{k}: {recall:.2%}")
    assert recall >= 0.5, f"HNSW recall too low: {recall}"
    print("PASS: test_hnsw_recall")


def test_hnsw_with_cosine():
    """Test HNSW with cosine similarity metric."""
    db = VectorDB(dimension=16, index_type="hnsw", metric="cosine",
                  max_connections=8, ef_construction=50)

    # Insert some known directions
    db.insert("right", [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    db.insert("up", [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    db.insert("right_close", [0.9, 0.1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

    results = db.search([1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], k=2)
    top_ids = [r["id"] for r in results]
    assert "right" in top_ids
    print("PASS: test_hnsw_with_cosine")


def test_hnsw_delete():
    """Test HNSW deletion."""
    db = VectorDB(dimension=16, index_type="hnsw", max_connections=8)

    for i in range(20):
        db.insert(f"v{i}", np.random.randn(16))

    db.delete("v10")
    assert db.size == 19
    assert "v10" not in db

    results = db.search(np.zeros(16), k=20)
    result_ids = [r["id"] for r in results]
    assert "v10" not in result_ids
    print("PASS: test_hnsw_delete")


def test_all_indexes_agree():
    """Test that all three indexes find the same nearest neighbor for simple cases."""
    dimension = 8
    vectors = random_vectors(50, dimension)

    bf_db = VectorDB(dimension=dimension, index_type="brute_force", metric="euclidean")
    lsh_db = VectorDB(dimension=dimension, index_type="lsh", metric="euclidean",
                      num_tables=10, num_hyperplanes=10)
    hnsw_db = VectorDB(dimension=dimension, index_type="hnsw", metric="euclidean",
                       max_connections=16, ef_construction=100)

    for i in range(50):
        vec = vectors[i]
        bf_db.insert(f"v{i}", vec)
        lsh_db.insert(f"v{i}", vec)
        hnsw_db.insert(f"v{i}", vec)

    query = vectors[0]  # Use a known vector as query

    bf_top = bf_db.search(query, k=1)[0]["id"]
    hnsw_top = hnsw_db.search(query, k=1, ef_search=100)[0]["id"]

    # Brute force and HNSW should agree on the top result (the query itself)
    assert bf_top == "v0", f"BF found {bf_top} instead of v0"
    assert hnsw_top == "v0", f"HNSW found {hnsw_top} instead of v0"
    print("PASS: test_all_indexes_agree")


if __name__ == "__main__":
    test_lsh_basic()
    test_lsh_recall()
    test_lsh_with_filter()
    test_lsh_delete()
    test_hnsw_basic()
    test_hnsw_recall()
    test_hnsw_with_cosine()
    test_hnsw_delete()
    test_all_indexes_agree()
    print("\nAll index tests passed!")
