"""
GPU Tensor Abstraction
======================

Provides a unified tensor interface that works with both real CUDA GPUs
and a CPU simulation mode for learning and testing purposes.

Key Concepts:
- Device management: assigning tensors to specific GPUs
- Memory allocation: tracking GPU memory usage
- Tensor operations: basic arithmetic on GPU tensors

Note: In simulation mode, tensors are stored in numpy arrays but
follow the same API as real CUDA tensors.
"""

import numpy as np
from typing import Optional, Tuple, List, Union
import logging

logger = logging.getLogger(__name__)


class Device:
    """Represents a compute device (GPU or CPU)."""

    def __init__(self, device_id: int = -1, device_type: str = "cuda"):
        """
        Args:
            device_id: GPU index (-1 for CPU)
            device_type: 'cuda' or 'cpu'
        """
        self.device_id = device_id
        self.device_type = device_type

    def __repr__(self):
        if self.device_id == -1:
            return "Device(type='cpu')"
        return f"Device(type='{self.device_type}', id={self.device_id})"

    def __eq__(self, other):
        return self.device_id == other.device_id and self.device_type == other.device_type

    def __hash__(self):
        return hash((self.device_id, self.device_type))


# Global device registry
_CPU_DEVICE = Device(-1, "cpu")


def get_device(device_id: int) -> Device:
    """Get a Device object for the given GPU id."""
    return Device(device_id, "cuda")


def cpu_device() -> Device:
    """Get the CPU device."""
    return _CPU_DEVICE


class GPUTensor:
    """
    GPU Tensor abstraction for multi-GPU computing.

    In simulation mode, this wraps a numpy array. In production mode,
    this would wrap a CUDA device pointer with proper memory management.

    Key Design Decisions:
    - Uses numpy as backend for portability (no GPU required for learning)
    - Tracks which device the tensor lives on
    - Supports basic arithmetic needed for gradient computation
    """

    # Class-level memory tracking per device
    _memory_usage: dict = {}  # device_id -> bytes allocated

    def __init__(
        self,
        data: Union[np.ndarray, list, float, int],
        device: Optional[Device] = None,
        dtype: np.dtype = np.float32,
        requires_grad: bool = False,
    ):
        """
        Create a GPUTensor.

        Args:
            data: Input data (numpy array, list, or scalar)
            device: Target device (defaults to CPU)
            dtype: Data type
            requires_grad: Whether to track gradients
        """
        if isinstance(data, (int, float)):
            data = np.array([data], dtype=dtype)
        elif isinstance(data, list):
            data = np.array(data, dtype=dtype)
        elif isinstance(data, np.ndarray):
            data = data.astype(dtype)
        else:
            raise TypeError(f"Unsupported data type: {type(data)}")

        self._data = data
        self.device = device or _CPU_DEVICE
        self.requires_grad = requires_grad
        self.grad: Optional["GPUTensor"] = None

        # Track memory allocation
        device_key = self.device.device_id
        if device_key not in GPUTensor._memory_usage:
            GPUTensor._memory_usage[device_key] = 0
        GPUTensor._memory_usage[device_key] += self._data.nbytes

    @property
    def data(self) -> np.ndarray:
        """Access the underlying numpy data."""
        return self._data

    @property
    def shape(self) -> Tuple[int, ...]:
        """Tensor shape."""
        return self._data.shape

    @property
    def dtype(self) -> np.dtype:
        """Tensor data type."""
        return self._data.dtype

    @property
    def nbytes(self) -> int:
        """Memory size in bytes."""
        return self._data.nbytes

    @property
    def ndim(self) -> int:
        """Number of dimensions."""
        return self._data.ndim

    @property
    def size(self) -> int:
        """Total number of elements."""
        return self._data.size

    def to(self, device: Device) -> "GPUTensor":
        """
        Move tensor to a different device.

        In simulation mode this is a no-op for the data, but updates the device tag.
        In real CUDA, this would involve cudaMemcpyPeer.

        Args:
            device: Target device

        Returns:
            Self (moved tensor)
        """
        old_device = self.device
        self.device = device

        # Update memory tracking
        old_key = old_device.device_id
        new_key = device.device_id
        if old_key in GPUTensor._memory_usage:
            GPUTensor._memory_usage[old_key] -= self._data.nbytes
        if new_key not in GPUTensor._memory_usage:
            GPUTensor._memory_usage[new_key] = 0
        GPUTensor._memory_usage[new_key] += self._data.nbytes

        logger.debug(f"Tensor moved from {old_device} to {device}")
        return self

    def numpy(self) -> np.ndarray:
        """Return data as numpy array."""
        return self._data.copy()

    def zero_(self) -> "GPUTensor":
        """Fill tensor with zeros (in-place)."""
        self._data = np.zeros_like(self._data)
        return self

    def fill_(self, value: float) -> "GPUTensor":
        """Fill tensor with a scalar value (in-place)."""
        self._data = np.full_like(self._data, value)
        return self

    def copy_(self, other: "GPUTensor") -> "GPUTensor":
        """Copy data from another tensor (in-place)."""
        self._data = other._data.copy()
        return self

    def detach(self) -> "GPUTensor":
        """Return a new tensor detached from computation graph."""
        return GPUTensor(self._data.copy(), self.device, self.dtype, requires_grad=False)

    def sum(self) -> "GPUTensor":
        """Sum all elements."""
        return GPUTensor(np.array(self._data.sum()), self.device)

    def mean(self) -> "GPUTensor":
        """Mean of all elements."""
        return GPUTensor(np.array(self._data.mean()), self.device)

    def __add__(self, other: Union["GPUTensor", float, int]) -> "GPUTensor":
        if isinstance(other, GPUTensor):
            return GPUTensor(self._data + other._data, self.device)
        return GPUTensor(self._data + other, self.device)

    def __sub__(self, other: Union["GPUTensor", float, int]) -> "GPUTensor":
        if isinstance(other, GPUTensor):
            return GPUTensor(self._data - other._data, self.device)
        return GPUTensor(self._data - other, self.device)

    def __mul__(self, other: Union["GPUTensor", float, int]) -> "GPUTensor":
        if isinstance(other, GPUTensor):
            return GPUTensor(self._data * other._data, self.device)
        return GPUTensor(self._data * other, self.device)

    def __truediv__(self, other: Union["GPUTensor", float, int]) -> "GPUTensor":
        if isinstance(other, GPUTensor):
            return GPUTensor(self._data / other._data, self.device)
        return GPUTensor(self._data / other, self.device)

    def __matmul__(self, other: "GPUTensor") -> "GPUTensor":
        return GPUTensor(self._data @ other._data, self.device)

    def __neg__(self) -> "GPUTensor":
        return GPUTensor(-self._data, self.device)

    def __repr__(self):
        data_preview = str(self._data.flat[:5])
        if self.size > 5:
            data_preview = data_preview[:-1] + ", ...]"
        return (
            f"GPUTensor({data_preview}, shape={self.shape}, "
            f"device={self.device}, dtype={self.dtype})"
        )

    @staticmethod
    def zeros(shape: Tuple[int, ...], device: Optional[Device] = None, **kwargs) -> "GPUTensor":
        """Create a tensor of zeros."""
        return GPUTensor(np.zeros(shape, dtype=kwargs.get("dtype", np.float32)), device)

    @staticmethod
    def ones(shape: Tuple[int, ...], device: Optional[Device] = None, **kwargs) -> "GPUTensor":
        """Create a tensor of ones."""
        return GPUTensor(np.ones(shape, dtype=kwargs.get("dtype", np.float32)), device)

    @staticmethod
    def randn(shape: Tuple[int, ...], device: Optional[Device] = None, **kwargs) -> "GPUTensor":
        """Create a tensor with random normal values."""
        return GPUTensor(np.random.randn(*shape).astype(kwargs.get("dtype", np.float32)), device)

    @staticmethod
    def from_numpy(arr: np.ndarray, device: Optional[Device] = None) -> "GPUTensor":
        """Create a tensor from a numpy array."""
        return GPUTensor(arr, device)

    @staticmethod
    def get_memory_usage() -> dict:
        """Get current memory usage per device."""
        return dict(GPUTensor._memory_usage)

    @staticmethod
    def reset_memory_tracking():
        """Reset memory tracking (for testing)."""
        GPUTensor._memory_usage = {}
