"""
NCCL Communication Abstraction
===============================

Provides a communication layer for multi-GPU collective operations.

Key Concepts:
- Communicator: Abstract base class for inter-GPU communication
- NCCLCommunicator: Real NCCL-based implementation (requires CUDA)
- SimulationCommunicator: CPU-based simulation for learning/testing

Collective Operations:
- AllReduce: Reduce data across all GPUs and broadcast result
- Broadcast: Send data from one GPU to all others
- AllGather: Gather data from all GPUs to all GPUs
- ReduceScatter: Reduce and scatter data across GPUs

Architecture:
    GPU0  GPU1  GPU2  GPU3
     |     |     |     |
     +-----+-----+-----+
     |  Communicator     |   <-- NCCL or Simulation
     +-------------------+
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from .tensor import GPUTensor, Device, get_device
import numpy as np
import logging
import time

logger = logging.getLogger(__name__)


class Communicator(ABC):
    """
    Abstract base class for inter-GPU communication.

    This defines the interface that all communication backends must implement.
    """

    def __init__(self, world_size: int, rank: int = 0):
        """
        Args:
            world_size: Total number of GPUs/processes
            rank: This process's rank (0-indexed)
        """
        self.world_size = world_size
        self.rank = rank
        self._initialized = False

    @abstractmethod
    def init(self):
        """Initialize the communication backend."""
        pass

    @abstractmethod
    def allreduce(self, tensor: GPUTensor, op: str = "sum") -> GPUTensor:
        """
        AllReduce operation: reduce tensor across all GPUs.

        Args:
            tensor: Input tensor (different on each GPU)
            op: Reduction operation ('sum', 'mean', 'max', 'min')

        Returns:
            Reduced tensor (same on all GPUs)
        """
        pass

    @abstractmethod
    def broadcast(self, tensor: GPUTensor, root: int = 0) -> GPUTensor:
        """
        Broadcast tensor from root to all GPUs.

        Args:
            tensor: Input tensor (only meaningful on root)
            root: Source GPU rank

        Returns:
            Broadcast tensor
        """
        pass

    @abstractmethod
    def allgather(self, tensor: GPUTensor) -> List[GPUTensor]:
        """
        AllGather: gather tensors from all GPUs to all GPUs.

        Args:
            tensor: Input tensor (different on each GPU)

        Returns:
            List of tensors from all GPUs
        """
        pass

    @abstractmethod
    def reducescatter(self, tensor: GPUTensor, op: str = "sum") -> GPUTensor:
        """
        ReduceScatter: reduce and scatter tensor across GPUs.

        Args:
            tensor: Input tensor (must be divisible by world_size)
            op: Reduction operation

        Returns:
            Scattered portion of reduced result
        """
        pass

    def barrier(self):
        """Synchronize all processes (no-op in simulation)."""
        pass

    def destroy(self):
        """Clean up communication resources."""
        self._initialized = False


class NCCLCommunicator(Communicator):
    """
    Real NCCL-based communicator.

    This wraps the NVIDIA NCCL library for actual multi-GPU communication.
    Requires CUDA-capable GPUs and the nccl library.

    Note: In a real implementation, this would use:
    - ncclCommInitRank for initialization
    - ncclAllReduce for AllReduce
    - ncclBroadcast for Broadcast
    - CUDA streams for async execution
    """

    def __init__(self, world_size: int, rank: int = 0):
        super().__init__(world_size, rank)
        self._comm = None  # ncclComm_t handle
        self._stream = None  # cudaStream_t

    def init(self):
        """
        Initialize NCCL communicator.

        In production code this would call:
            ncclGetUniqueId(&id)
            ncclCommInitRank(&comm, world_size, id, rank)
            cudaStreamCreate(&stream)
        """
        logger.info(f"Initializing NCCL communicator: rank={self.rank}, world_size={self.world_size}")
        # Simulation placeholder - real implementation needs CUDA bindings
        self._initialized = True
        logger.warning(
            "NCCLCommunicator is in placeholder mode. "
            "Use SimulationCommunicator for CPU-based testing."
        )

    def allreduce(self, tensor: GPUTensor, op: str = "sum") -> GPUTensor:
        if not self._initialized:
            raise RuntimeError("Communicator not initialized. Call init() first.")
        raise NotImplementedError(
            "NCCL AllReduce requires CUDA. Use SimulationCommunicator."
        )

    def broadcast(self, tensor: GPUTensor, root: int = 0) -> GPUTensor:
        if not self._initialized:
            raise RuntimeError("Communicator not initialized. Call init() first.")
        raise NotImplementedError(
            "NCCL Broadcast requires CUDA. Use SimulationCommunicator."
        )

    def allgather(self, tensor: GPUTensor) -> List[GPUTensor]:
        if not self._initialized:
            raise RuntimeError("Communicator not initialized. Call init() first.")
        raise NotImplementedError(
            "NCCL AllGather requires CUDA. Use SimulationCommunicator."
        )

    def reducescatter(self, tensor: GPUTensor, op: str = "sum") -> GPUTensor:
        if not self._initialized:
            raise RuntimeError("Communicator not initialized. Call init() first.")
        raise NotImplementedError(
            "NCCL ReduceScatter requires CUDA. Use SimulationCommunicator."
        )


class SimulationCommunicator(Communicator):
    """
    CPU-based simulation communicator for learning and testing.

    This simulates NCCL collective operations using numpy arrays.
    It maintains a "tensor store" where each GPU's tensor is stored,
    and collective operations are performed by manipulating these arrays.

    Architecture:
        GPU0_tensor  GPU1_tensor  GPU2_tensor  GPU3_tensor
             \          |          |          /
              +---------+----------+---------+
              |    SimulationCommunicator     |
              |   (numpy-based operations)   |
              +------------------------------+
    """

    def __init__(self, world_size: int, rank: int = 0):
        super().__init__(world_size, rank)
        # Shared tensor store simulating GPU memory across all devices
        self._tensor_store: Dict[int, Dict[str, GPUTensor]] = {
            i: {} for i in range(world_size)
        }
        self._tag_counter = 0
        self._comm_time = 0.0  # Track communication time for benchmarking

    def init(self):
        """Initialize simulation communicator."""
        logger.info(
            f"SimulationCommunicator initialized: rank={self.rank}, "
            f"world_size={self.world_size}"
        )
        self._initialized = True

    def _get_unique_tag(self) -> str:
        """Generate unique tag for tensor identification."""
        self._tag_counter += 1
        return f"tensor_{self._tag_counter}"

    @property
    def comm_time(self) -> float:
        """Total time spent in communication."""
        return self._comm_time

    def reset_comm_time(self):
        """Reset communication time counter."""
        self._comm_time = 0.0

    def put_tensor(self, tag: str, tensor: GPUTensor):
        """Store a tensor for this rank."""
        self._tensor_store[self.rank][tag] = tensor

    def get_tensor(self, rank: int, tag: str) -> Optional[GPUTensor]:
        """Get a tensor from a specific rank."""
        return self._tensor_store[rank].get(tag)

    def allreduce(self, tensor: GPUTensor, op: str = "sum") -> GPUTensor:
        """
        AllReduce simulation: gather all tensors, apply reduction, broadcast.

        This simulates what NCCL does internally:
        1. Each GPU has a different tensor
        2. We reduce (sum/mean/max/min) all tensors element-wise
        3. Result is available on all GPUs

        Args:
            tensor: This rank's tensor
            op: Reduction operation

        Returns:
            Reduced tensor
        """
        if not self._initialized:
            raise RuntimeError("Communicator not initialized. Call init() first.")

        start_time = time.perf_counter()

        tag = self._get_unique_tag()
        self.put_tensor(tag, tensor)

        # Wait for all "GPUs" to register their tensors
        # In real NCCL this happens automatically via GPU-to-GPU communication
        all_data = []
        for rank in range(self.world_size):
            t = self._tensor_store[rank].get(tag)
            if t is not None:
                all_data.append(t._data)

        if not all_data:
            return tensor

        # Apply reduction operation
        stacked = np.stack(all_data, axis=0)
        if op == "sum":
            result_data = np.sum(stacked, axis=0)
        elif op == "mean":
            result_data = np.mean(stacked, axis=0)
        elif op == "max":
            result_data = np.max(stacked, axis=0)
        elif op == "min":
            result_data = np.min(stacked, axis=0)
        else:
            raise ValueError(f"Unsupported reduction operation: {op}")

        elapsed = time.perf_counter() - start_time
        self._comm_time += elapsed

        logger.debug(
            f"AllReduce ({op}) completed: {self.world_size} tensors, "
            f"shape={tensor.shape}, time={elapsed*1000:.3f}ms"
        )

        return GPUTensor(result_data, tensor.device, tensor.dtype)

    def broadcast(self, tensor: GPUTensor, root: int = 0) -> GPUTensor:
        """
        Broadcast simulation: send tensor from root to all ranks.

        Args:
            tensor: Tensor on root rank
            root: Source rank

        Returns:
            Broadcast tensor (same data on all ranks)
        """
        if not self._initialized:
            raise RuntimeError("Communicator not initialized. Call init() first.")

        start_time = time.perf_counter()

        tag = self._get_unique_tag()
        self._tensor_store[root][tag] = tensor

        # All ranks receive the same data from root
        result_data = tensor._data.copy()

        elapsed = time.perf_counter() - start_time
        self._comm_time += elapsed

        logger.debug(
            f"Broadcast from rank {root} completed: "
            f"shape={tensor.shape}, time={elapsed*1000:.3f}ms"
        )

        return GPUTensor(result_data, tensor.device, tensor.dtype)

    def allgather(self, tensor: GPUTensor) -> List[GPUTensor]:
        """
        AllGather simulation: gather tensors from all ranks.

        Args:
            tensor: This rank's tensor

        Returns:
            List of tensors from all ranks
        """
        if not self._initialized:
            raise RuntimeError("Communicator not initialized. Call init() first.")

        start_time = time.perf_counter()

        tag = self._get_unique_tag()
        self.put_tensor(tag, tensor)

        results = []
        for rank in range(self.world_size):
            t = self._tensor_store[rank].get(tag)
            if t is not None:
                results.append(GPUTensor(t._data.copy(), tensor.device, tensor.dtype))

        elapsed = time.perf_counter() - start_time
        self._comm_time += elapsed

        logger.debug(
            f"AllGather completed: {self.world_size} tensors, "
            f"shape={tensor.shape}, time={elapsed*1000:.3f}ms"
        )

        return results

    def reducescatter(self, tensor: GPUTensor, op: str = "sum") -> GPUTensor:
        """
        ReduceScatter simulation: reduce then scatter.

        Args:
            tensor: Input tensor (first dim must be divisible by world_size)

        Returns:
            Reduced and scattered portion
        """
        if not self._initialized:
            raise RuntimeError("Communicator not initialized. Call init() first.")

        start_time = time.perf_counter()

        tag = self._get_unique_tag()
        self.put_tensor(tag, tensor)

        all_data = []
        for rank in range(self.world_size):
            t = self._tensor_store[rank].get(tag)
            if t is not None:
                all_data.append(t._data)

        stacked = np.stack(all_data, axis=0)

        if op == "sum":
            reduced = np.sum(stacked, axis=0)
        elif op == "mean":
            reduced = np.mean(stacked, axis=0)
        elif op == "max":
            reduced = np.max(stacked, axis=0)
        elif op == "min":
            reduced = np.min(stacked, axis=0)
        else:
            raise ValueError(f"Unsupported reduction operation: {op}")

        # Scatter: split along first dimension
        chunks = np.array_split(reduced, self.world_size, axis=0)
        result_data = chunks[self.rank]

        elapsed = time.perf_counter() - start_time
        self._comm_time += elapsed

        logger.debug(
            f"ReduceScatter ({op}) completed: rank={self.rank}, "
            f"output_shape=result_data.shape, time={elapsed*1000:.3f}ms"
        )

        return GPUTensor(result_data, tensor.device, tensor.dtype)


def create_communicator(
    world_size: int,
    rank: int = 0,
    backend: str = "simulation",
) -> Communicator:
    """
    Factory function to create a communicator.

    Args:
        world_size: Number of GPUs/processes
        rank: This process's rank
        backend: 'nccl' or 'simulation'

    Returns:
        Initialized communicator
    """
    if backend == "nccl":
        comm = NCCLCommunicator(world_size, rank)
    elif backend == "simulation":
        comm = SimulationCommunicator(world_size, rank)
    else:
        raise ValueError(f"Unknown backend: {backend}. Use 'nccl' or 'simulation'.")

    comm.init()
    return comm
