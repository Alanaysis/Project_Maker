"""Tests for VectorDB core CRUD operations."""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.vector_db import VectorDB, IndexType
from src.metrics import DistanceMetric


def test_insert_and_get():
    """Test inserting and retrieving vectors."""
    db = VectorDB(dimension=128, index_type="brute_force", metric="euclidean")

    vec = np.random.randn(128).astype(np.float32)
    db.insert("vec1", vec, {"category": "test", "score": 0.9})

    assert db.size == 1
    assert "vec1" in db

    result = db.get("vec1")
    assert result is not None
    assert result["id"] == "vec1"
    assert np.allclose(result["vector"], vec)
    assert result["metadata"]["category"] == "test"
    assert result["metadata"]["score"] == 0.9
    print("PASS: test_insert_and_get")


def test_insert_batch():
    """Test batch insertion."""
    db = VectorDB(dimension=64, index_type="brute_force", metric="euclidean")

    vectors = np.random.randn(10, 64).astype(np.float32)
    ids = [f"vec_{i}" for i in range(10)]
    metadata_list = [{"index": i} for i in range(10)]

    db.insert_batch(ids, vectors, metadata_list)
    assert db.size == 10

    for i, id in enumerate(ids):
        assert id in db
        result = db.get(id)
        assert result["metadata"]["index"] == i
    print("PASS: test_insert_batch")


def test_delete():
    """Test deleting vectors."""
    db = VectorDB(dimension=32, index_type="brute_force")

    db.insert("a", np.random.randn(32))
    db.insert("b", np.random.randn(32))
    assert db.size == 2

    assert db.delete("a") is True
    assert db.size == 1
    assert "a" not in db
    assert db.delete("nonexistent") is False
    print("PASS: test_delete")


def test_delete_batch():
    """Test batch deletion."""
    db = VectorDB(dimension=32, index_type="brute_force")

    for i in range(5):
        db.insert(f"v{i}", np.random.randn(32))

    deleted = db.delete_batch(["v0", "v1", "v_nonexistent"])
    assert deleted == 2
    assert db.size == 3
    print("PASS: test_delete_batch")


def test_update_vector():
    """Test updating a vector."""
    db = VectorDB(dimension=16, index_type="brute_force")

    db.insert("v1", np.zeros(16), {"version": 1})

    new_vec = np.ones(16)
    assert db.update("v1", vector=new_vec, metadata={"version": 2}) is True

    result = db.get("v1")
    assert np.allclose(result["vector"], new_vec)
    assert result["metadata"]["version"] == 2

    assert db.update("nonexistent") is False
    print("PASS: test_update_vector")


def test_update_metadata_only():
    """Test updating only metadata."""
    db = VectorDB(dimension=16, index_type="brute_force")

    vec = np.random.randn(16)
    db.insert("v1", vec, {"tag": "old"})

    db.update("v1", metadata={"tag": "new"})
    result = db.get("v1")
    assert result["metadata"]["tag"] == "new"
    assert np.allclose(result["vector"], vec)
    print("PASS: test_update_metadata_only")


def test_search():
    """Test basic search."""
    db = VectorDB(dimension=32, index_type="brute_force", metric="euclidean")

    # Insert vectors close to origin and far from origin
    db.insert("close", np.ones(32) * 0.1)
    db.insert("far", np.ones(32) * 10.0)

    results = db.search(np.zeros(32), k=2)
    assert len(results) == 2
    assert results[0]["id"] == "close"
    assert results[1]["id"] == "far"
    print("PASS: test_search")


def test_search_with_list():
    """Test search with list input instead of numpy array."""
    db = VectorDB(dimension=4, index_type="brute_force", metric="euclidean")

    db.insert("v1", [1.0, 0.0, 0.0, 0.0])
    db.insert("v2", [0.0, 1.0, 0.0, 0.0])

    results = db.search([1.0, 0.0, 0.0, 0.0], k=1)
    assert results[0]["id"] == "v1"
    print("PASS: test_search_with_list")


def test_range_search():
    """Test range search."""
    db = VectorDB(dimension=16, index_type="brute_force", metric="euclidean")

    db.insert("close", np.ones(16) * 0.1)    # dist = sqrt(16*0.01) = 0.4
    db.insert("medium", np.ones(16) * 0.5)    # dist = sqrt(16*0.25) = 2.0
    db.insert("far", np.ones(16) * 10.0)      # dist = sqrt(16*100) = 40.0

    # Only vectors within distance 3.0
    results = db.range_search(np.zeros(16), radius=3.0)
    ids = [r["id"] for r in results]
    assert "close" in ids
    assert "medium" in ids
    assert "far" not in ids
    print("PASS: test_range_search")


def test_exists():
    """Test exists check."""
    db = VectorDB(dimension=8, index_type="brute_force")

    db.insert("exists", np.ones(8))
    assert db.exists("exists") is True
    assert db.exists("not_here") is False
    print("PASS: test_exists")


def test_list_ids():
    """Test listing all IDs."""
    db = VectorDB(dimension=8, index_type="brute_force")

    for i in range(5):
        db.insert(f"v{i}", np.random.randn(8))

    ids = db.list_ids()
    assert len(ids) == 5
    assert set(ids) == {"v0", "v1", "v2", "v3", "v4"}
    print("PASS: test_list_ids")


def test_clear():
    """Test clearing the database."""
    db = VectorDB(dimension=8, index_type="brute_force")

    for i in range(10):
        db.insert(f"v{i}", np.random.randn(8))

    db.clear()
    assert db.size == 0
    assert db.list_ids() == []
    print("PASS: test_clear")


def test_dimension_mismatch():
    """Test that dimension mismatch raises error."""
    db = VectorDB(dimension=16, index_type="brute_force")

    try:
        db.insert("bad", np.random.randn(32))
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    print("PASS: test_dimension_mismatch")


def test_save_load():
    """Test saving and loading database."""
    import tempfile
    import shutil

    db = VectorDB(dimension=16, index_type="brute_force", metric="euclidean")
    db.insert("v1", np.ones(16), {"tag": "test"})
    db.insert("v2", np.zeros(16), {"tag": "other"})

    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = os.path.join(tmpdir, "test_db")
        db.save(save_path)

        loaded = VectorDB.load(save_path)
        assert loaded.size == 2
        assert loaded.dimension == 16

        result = loaded.get("v1")
        assert np.allclose(result["vector"], np.ones(16))
        assert result["metadata"]["tag"] == "test"
    print("PASS: test_save_load")


def test_repr():
    """Test string representation."""
    db = VectorDB(dimension=128, index_type="brute_force", metric="euclidean")
    r = repr(db)
    assert "dimension=128" in r
    assert "brute_force" in r
    assert "euclidean" in r
    assert "size=0" in r
    print("PASS: test_repr")


def test_contains():
    """Test __contains__ operator."""
    db = VectorDB(dimension=8, index_type="brute_force")
    db.insert("v1", np.ones(8))

    assert "v1" in db
    assert "v2" not in db
    print("PASS: test_contains")


def test_len():
    """Test __len__ operator."""
    db = VectorDB(dimension=8, index_type="brute_force")
    assert len(db) == 0

    db.insert("v1", np.ones(8))
    assert len(db) == 1
    print("PASS: test_len")


if __name__ == "__main__":
    test_insert_and_get()
    test_insert_batch()
    test_delete()
    test_delete_batch()
    test_update_vector()
    test_update_metadata_only()
    test_search()
    test_search_with_list()
    test_range_search()
    test_exists()
    test_list_ids()
    test_clear()
    test_dimension_mismatch()
    test_save_load()
    test_repr()
    test_contains()
    test_len()
    print("\nAll VectorDB CRUD tests passed!")
