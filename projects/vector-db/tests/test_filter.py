"""Tests for metadata filtering."""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.filter import MetadataFilter, FilterOperator, eq, gt, gte, lt, lte, range_filter
from src.vector_db import VectorDB


def test_eq_filter():
    """Test equality filter."""
    f = eq("category", "A")
    assert f.match({"category": "A"}) is True
    assert f.match({"category": "B"}) is False
    assert f.match({}) is False
    print("PASS: test_eq_filter")


def test_gt_filter():
    """Test greater-than filter."""
    f = gt("score", 5)
    assert f.match({"score": 10}) is True
    assert f.match({"score": 5}) is False
    assert f.match({"score": 3}) is False
    print("PASS: test_gt_filter")


def test_range_filter():
    """Test range filter."""
    f = range_filter("price", 10, 50)
    assert f.match({"price": 30}) is True
    assert f.match({"price": 10}) is True  # inclusive
    assert f.match({"price": 50}) is True  # inclusive
    assert f.match({"price": 5}) is False
    assert f.match({"price": 100}) is False
    print("PASS: test_range_filter")


def test_combined_filter():
    """Test AND-combined filters."""
    f = MetadataFilter()
    f.add_condition("category", FilterOperator.EQ, "electronics")
    f.add_condition("price", FilterOperator.LTE, 1000)
    f.add_condition("rating", FilterOperator.GTE, 4.0)

    good = {"category": "electronics", "price": 500, "rating": 4.5}
    assert f.match(good) is True

    bad_price = {"category": "electronics", "price": 2000, "rating": 4.5}
    assert f.match(bad_price) is False

    bad_category = {"category": "books", "price": 500, "rating": 4.5}
    assert f.match(bad_category) is False
    print("PASS: test_combined_filter")


def test_or_logic():
    """Test OR logic for filters."""
    f = MetadataFilter()
    f.set_logic("or")
    f.add_condition("color", FilterOperator.EQ, "red")
    f.add_condition("color", FilterOperator.EQ, "blue")

    assert f.match({"color": "red"}) is True
    assert f.match({"color": "blue"}) is True
    assert f.match({"color": "green"}) is False
    print("PASS: test_or_logic")


def test_in_filter():
    """Test IN filter."""
    f = MetadataFilter()
    f.add_condition("status", FilterOperator.IN, ["active", "pending"])

    assert f.match({"status": "active"}) is True
    assert f.match({"status": "pending"}) is True
    assert f.match({"status": "deleted"}) is False
    print("PASS: test_in_filter")


def test_contains_filter():
    """Test CONTAINS filter."""
    f = MetadataFilter()
    f.add_condition("name", FilterOperator.CONTAINS, "test")

    assert f.match({"name": "test_item_1"}) is True
    assert f.match({"name": "my_test"}) is True
    assert f.match({"name": "item"}) is False
    print("PASS: test_contains_filter")


def test_exists_filter():
    """Test EXISTS filter."""
    f = MetadataFilter()
    f.add_condition("tag", FilterOperator.EXISTS)

    assert f.match({"tag": "value"}) is True
    assert f.match({"tag": None}) is True
    assert f.match({"other": "value"}) is False
    print("PASS: test_exists_filter")


def test_search_with_filter():
    """Test searching with metadata filters."""
    db = VectorDB(dimension=16, index_type="brute_force", metric="euclidean")

    # Insert items with different categories and scores
    for i in range(20):
        db.insert(
            f"item_{i}",
            np.random.randn(16),
            {"category": "A" if i < 10 else "B", "score": float(i)}
        )

    # Search with category filter
    cat_filter = eq("category", "A")
    results = db.search(np.zeros(16), k=5, metadata_filter=cat_filter)
    assert len(results) <= 5
    for r in results:
        assert r["metadata"]["category"] == "A"

    # Search with range filter
    score_filter = range_filter("score", 5, 15)
    results = db.search(np.zeros(16), k=100, metadata_filter=score_filter)
    for r in results:
        assert 5 <= r["metadata"]["score"] <= 15
    print("PASS: test_search_with_filter")


def test_chain_filter():
    """Test chaining filter methods."""
    f = eq("type", "image").set_logic("and")
    assert f.match({"type": "image"}) is True

    f = MetadataFilter()
    f.add_condition("a", FilterOperator.GT, 0)
    f.add_condition("b", FilterOperator.LT, 10)
    assert f.match({"a": 5, "b": 5}) is True
    print("PASS: test_chain_filter")


if __name__ == "__main__":
    test_eq_filter()
    test_gt_filter()
    test_range_filter()
    test_combined_filter()
    test_or_logic()
    test_in_filter()
    test_contains_filter()
    test_exists_filter()
    test_search_with_filter()
    test_chain_filter()
    print("\nAll filter tests passed!")
