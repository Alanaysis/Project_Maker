"""
Tests for GPUTensor module.
"""

import pytest
import numpy as np
from src.core.tensor import GPUTensor, Device, get_device, cpu_device


class TestDevice:
    """Test Device class."""

    def test_create_cuda_device(self):
        device = Device(0, "cuda")
        assert device.device_id == 0
        assert device.device_type == "cuda"

    def test_create_cpu_device(self):
        device = Device(-1, "cpu")
        assert device.device_id == -1
        assert device.device_type == "cpu"

    def test_device_repr(self):
        device = Device(0, "cuda")
        assert "cuda" in repr(device)
        assert "0" in repr(device)

    def test_device_equality(self):
        d1 = Device(0, "cuda")
        d2 = Device(0, "cuda")
        d3 = Device(1, "cuda")
        assert d1 == d2
        assert d1 != d3


class TestGPUTensor:
    """Test GPUTensor class."""

    def setup_method(self):
        """Reset memory tracking before each test."""
        GPUTensor.reset_memory_tracking()

    def test_create_from_numpy(self):
        arr = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        t = GPUTensor(arr)
        np.testing.assert_array_equal(t.data, arr)

    def test_create_from_list(self):
        t = GPUTensor([1.0, 2.0, 3.0])
        np.testing.assert_array_almost_equal(t.data, [1.0, 2.0, 3.0])

    def test_create_from_scalar(self):
        t = GPUTensor(5.0)
        assert t.size == 1

    def test_shape(self):
        t = GPUTensor(np.zeros((3, 4)))
        assert t.shape == (3, 4)

    def test_dtype(self):
        t = GPUTensor(np.zeros(3, dtype=np.float64))
        assert t.dtype == np.float64

    def test_device(self):
        device = get_device(0)
        t = GPUTensor([1.0, 2.0], device=device)
        assert t.device == device

    def test_to_device(self):
        t = GPUTensor([1.0, 2.0])
        device = get_device(1)
        t.to(device)
        assert t.device == device

    def test_zeros(self):
        t = GPUTensor.zeros((3, 4))
        np.testing.assert_array_equal(t.data, np.zeros((3, 4)))

    def test_ones(self):
        t = GPUTensor.ones((2, 3))
        np.testing.assert_array_equal(t.data, np.ones((2, 3)))

    def test_randn(self):
        t = GPUTensor.randn((100,))
        assert t.shape == (100,)
        # Statistical test: mean should be close to 0
        assert abs(t.data.mean()) < 0.5

    def test_add(self):
        a = GPUTensor([1.0, 2.0, 3.0])
        b = GPUTensor([4.0, 5.0, 6.0])
        c = a + b
        np.testing.assert_array_almost_equal(c.data, [5.0, 7.0, 9.0])

    def test_sub(self):
        a = GPUTensor([5.0, 7.0, 9.0])
        b = GPUTensor([1.0, 2.0, 3.0])
        c = a - b
        np.testing.assert_array_almost_equal(c.data, [4.0, 5.0, 6.0])

    def test_mul(self):
        a = GPUTensor([2.0, 3.0, 4.0])
        b = GPUTensor([5.0, 6.0, 7.0])
        c = a * b
        np.testing.assert_array_almost_equal(c.data, [10.0, 18.0, 28.0])

    def test_div(self):
        a = GPUTensor([10.0, 20.0, 30.0])
        b = GPUTensor([2.0, 4.0, 5.0])
        c = a / b
        np.testing.assert_array_almost_equal(c.data, [5.0, 5.0, 6.0])

    def test_matmul(self):
        a = GPUTensor(np.random.randn(3, 4))
        b = GPUTensor(np.random.randn(4, 5))
        c = a @ b
        expected = a.data @ b.data
        np.testing.assert_array_almost_equal(c.data, expected)

    def test_neg(self):
        t = GPUTensor([1.0, -2.0, 3.0])
        result = -t
        np.testing.assert_array_almost_equal(result.data, [-1.0, 2.0, -3.0])

    def test_sum(self):
        t = GPUTensor([1.0, 2.0, 3.0, 4.0])
        result = t.sum()
        np.testing.assert_almost_equal(result.data[0], 10.0)

    def test_mean(self):
        t = GPUTensor([1.0, 2.0, 3.0, 4.0])
        result = t.mean()
        np.testing.assert_almost_equal(result.data[0], 2.5)

    def test_zero_inplace(self):
        t = GPUTensor([1.0, 2.0, 3.0])
        t.zero_()
        np.testing.assert_array_equal(t.data, [0.0, 0.0, 0.0])

    def test_fill_inplace(self):
        t = GPUTensor([1.0, 2.0, 3.0])
        t.fill_(7.0)
        np.testing.assert_array_equal(t.data, [7.0, 7.0, 7.0])

    def test_detach(self):
        t = GPUTensor([1.0, 2.0], requires_grad=True)
        d = t.detach()
        assert d.requires_grad == False

    def test_nbytes(self):
        t = GPUTensor(np.zeros(10, dtype=np.float32))
        assert t.nbytes == 40  # 10 * 4 bytes

    def test_memory_tracking(self):
        GPUTensor.reset_memory_tracking()
        device = get_device(0)
        t = GPUTensor(np.zeros(10, dtype=np.float32), device)
        usage = GPUTensor.get_memory_usage()
        assert 0 in usage
        assert usage[0] == 40

    def test_repr(self):
        t = GPUTensor([1.0, 2.0, 3.0])
        r = repr(t)
        assert "GPUTensor" in r


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
