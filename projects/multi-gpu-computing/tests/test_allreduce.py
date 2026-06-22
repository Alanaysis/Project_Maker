"""
Tests for AllReduce algorithms.
"""

import pytest
import numpy as np
from src.core.tensor import GPUTensor, get_device
from src.core.allreduce import (
    NaiveAllReduce,
    RingAllReduce,
    TreeAllReduce,
    create_allreduce,
    compare_allreduce_algorithms,
)


class TestNaiveAllReduce:
    """Test NaiveAllReduce algorithm."""

    def test_sum_two_tensors(self):
        allreduce = NaiveAllReduce()
        t0 = GPUTensor(np.array([1.0, 2.0, 3.0]), get_device(0))
        t1 = GPUTensor(np.array([4.0, 5.0, 6.0]), get_device(1))

        results = allreduce.reduce([t0, t1], op="sum")

        np.testing.assert_array_almost_equal(results[0].data, [5.0, 7.0, 9.0])
        np.testing.assert_array_almost_equal(results[1].data, [5.0, 7.0, 9.0])

    def test_mean_two_tensors(self):
        allreduce = NaiveAllReduce()
        t0 = GPUTensor(np.array([2.0, 4.0, 6.0]), get_device(0))
        t1 = GPUTensor(np.array([4.0, 8.0, 12.0]), get_device(1))

        results = allreduce.reduce([t0, t1], op="mean")

        np.testing.assert_array_almost_equal(results[0].data, [3.0, 6.0, 9.0])
        np.testing.assert_array_almost_equal(results[1].data, [3.0, 6.0, 9.0])

    def test_sum_four_tensors(self):
        allreduce = NaiveAllReduce()
        tensors = [
            GPUTensor(np.array([1.0, 2.0]), get_device(i))
            for i in range(4)
        ]

        results = allreduce.reduce(tensors, op="sum")

        expected = np.array([4.0, 8.0])
        for r in results:
            np.testing.assert_array_almost_equal(r.data, expected)

    def test_single_tensor(self):
        allreduce = NaiveAllReduce()
        t = GPUTensor(np.array([5.0, 10.0]), get_device(0))

        results = allreduce.reduce([t], op="sum")

        np.testing.assert_array_almost_equal(results[0].data, [5.0, 10.0])

    def test_empty_list(self):
        allreduce = NaiveAllReduce()
        results = allreduce.reduce([], op="sum")
        assert results == []


class TestRingAllReduce:
    """Test RingAllReduce algorithm."""

    def test_sum_two_tensors(self):
        allreduce = RingAllReduce()
        t0 = GPUTensor(np.array([1.0, 2.0, 3.0, 4.0]), get_device(0))
        t1 = GPUTensor(np.array([5.0, 6.0, 7.0, 8.0]), get_device(1))

        results = allreduce.reduce([t0, t1], op="sum")

        np.testing.assert_array_almost_equal(results[0].data, [6.0, 8.0, 10.0, 12.0])
        np.testing.assert_array_almost_equal(results[1].data, [6.0, 8.0, 10.0, 12.0])

    def test_sum_four_tensors(self):
        allreduce = RingAllReduce()
        tensors = [
            GPUTensor(np.array([float(i), float(i + 1)]), get_device(i))
            for i in range(4)
        ]

        results = allreduce.reduce(tensors, op="sum")

        expected_sum = sum(range(4)) + sum(range(1, 5))
        # Each element should be the sum of all GPUs' values
        for r in results:
            assert abs(r.data[0] - sum(float(i) for i in range(4))) < 1e-5

    def test_mean_two_tensors(self):
        allreduce = RingAllReduce()
        t0 = GPUTensor(np.array([2.0, 4.0, 6.0, 8.0]), get_device(0))
        t1 = GPUTensor(np.array([4.0, 8.0, 12.0, 16.0]), get_device(1))

        results = allreduce.reduce([t0, t1], op="mean")

        np.testing.assert_array_almost_equal(results[0].data, [3.0, 6.0, 9.0, 12.0])
        np.testing.assert_array_almost_equal(results[1].data, [3.0, 6.0, 9.0, 12.0])

    def test_consistency_with_naive(self):
        """RingAllReduce and NaiveAllReduce should produce the same result."""
        np.random.seed(42)
        tensors = [
            GPUTensor(np.random.randn(100), get_device(i))
            for i in range(4)
        ]

        naive = NaiveAllReduce()
        ring = RingAllReduce()

        naive_results = naive.reduce([t.detach() for t in tensors], op="sum")
        ring_results = ring.reduce([t.detach() for t in tensors], op="sum")

        for nr, rr in zip(naive_results, ring_results):
            np.testing.assert_array_almost_equal(nr.data, rr.data, decimal=5)

    def test_2d_tensors(self):
        allreduce = RingAllReduce()
        t0 = GPUTensor(np.ones((3, 4)), get_device(0))
        t1 = GPUTensor(np.ones((3, 4)) * 2, get_device(1))

        results = allreduce.reduce([t0, t1], op="sum")

        np.testing.assert_array_almost_equal(results[0].data, np.ones((3, 4)) * 3)


class TestTreeAllReduce:
    """Test TreeAllReduce algorithm."""

    def test_sum_two_tensors(self):
        allreduce = TreeAllReduce()
        t0 = GPUTensor(np.array([1.0, 2.0, 3.0]), get_device(0))
        t1 = GPUTensor(np.array([4.0, 5.0, 6.0]), get_device(1))

        results = allreduce.reduce([t0, t1], op="sum")

        np.testing.assert_array_almost_equal(results[0].data, [5.0, 7.0, 9.0])
        np.testing.assert_array_almost_equal(results[1].data, [5.0, 7.0, 9.0])

    def test_sum_four_tensors(self):
        allreduce = TreeAllReduce()
        tensors = [
            GPUTensor(np.array([1.0, 2.0]), get_device(i))
            for i in range(4)
        ]

        results = allreduce.reduce(tensors, op="sum")

        for r in results:
            np.testing.assert_array_almost_equal(r.data, [4.0, 8.0])

    def test_consistency_with_naive(self):
        """TreeAllReduce and NaiveAllReduce should produce the same result."""
        np.random.seed(42)
        tensors = [
            GPUTensor(np.random.randn(50), get_device(i))
            for i in range(4)
        ]

        naive = NaiveAllReduce()
        tree = TreeAllReduce()

        naive_results = naive.reduce([t.detach() for t in tensors], op="sum")
        tree_results = tree.reduce([t.detach() for t in tensors], op="sum")

        for nr, tr in zip(naive_results, tree_results):
            np.testing.assert_array_almost_equal(nr.data, tr.data, decimal=5)


class TestFactory:
    """Test factory function."""

    def test_create_naive(self):
        a = create_allreduce("naive")
        assert isinstance(a, NaiveAllReduce)

    def test_create_ring(self):
        a = create_allreduce("ring")
        assert isinstance(a, RingAllReduce)

    def test_create_tree(self):
        a = create_allreduce("tree")
        assert isinstance(a, TreeAllReduce)

    def test_create_invalid(self):
        with pytest.raises(ValueError):
            create_allreduce("invalid")


class TestComparison:
    """Test compare_allreduce_algorithms function."""

    def test_comparison(self):
        np.random.seed(42)
        tensors = [
            GPUTensor(np.random.randn(100), get_device(i))
            for i in range(4)
        ]

        results = compare_allreduce_algorithms(tensors, op="sum")

        assert "naive" in results
        assert "ring" in results
        assert "tree" in results

        # All should produce the same result
        for name in ["ring", "tree"]:
            np.testing.assert_array_almost_equal(
                results["naive"]["result"].data,
                results[name]["result"].data,
                decimal=5,
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
