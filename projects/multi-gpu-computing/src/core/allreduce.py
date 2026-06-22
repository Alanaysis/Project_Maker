"""
AllReduce Algorithms Implementation
=====================================

AllReduce is the core collective operation for distributed gradient synchronization.
This module implements multiple AllReduce strategies to understand their trade-offs.

Key Algorithms:
- Naive AllReduce: Simple gather-reduce-broadcast (baseline)
- Ring AllReduce: Bandwidth-optimal, used by NCCL
- Tree AllReduce: Latency-optimal for small messages

AllReduce in Distributed Training:
    1. Each GPU computes gradients on its data shard
    2. AllReduce sums gradients across all GPUs
    3. Each GPU has the same averaged gradient
    4. Each GPU applies the same parameter update

Ring AllReduce Steps:
    Step 1: Scatter-Reduce (n-1 steps)
        Each GPU sends a chunk to the next GPU in the ring
        Each GPU reduces the received chunk with its local chunk
    Step 2: AllGather (n-1 steps)
        Each GPU sends the reduced chunk to the next GPU
        All GPUs end up with the full reduced result
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from .tensor import GPUTensor
import numpy as np
import logging
import time

logger = logging.getLogger(__name__)


class AllReduce(ABC):
    """Abstract base class for AllReduce algorithms."""

    @abstractmethod
    def reduce(
        self,
        tensors: List[GPUTensor],
        op: str = "sum",
    ) -> List[GPUTensor]:
        """
        Perform AllReduce across all tensors.

        Args:
            tensors: List of tensors, one per GPU
            op: Reduction operation ('sum', 'mean')

        Returns:
            List of reduced tensors (same on all GPUs)
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return the algorithm name."""
        pass


class NaiveAllReduce(AllReduce):
    """
    Naive AllReduce: gather all tensors, reduce, broadcast.

    Communication pattern:
        All-to-One (Gather) -> Reduce -> One-to-All (Broadcast)

    Complexity:
        - Time: O(n * message_size)  [n = world_size]
        - Bandwidth: NOT optimal (bottleneck at rank 0)

    Use case: Simple baseline, small clusters
    """

    def get_name(self) -> str:
        return "NaiveAllReduce"

    def reduce(
        self,
        tensors: List[GPUTensor],
        op: str = "sum",
    ) -> List[GPUTensor]:
        """
        Naive AllReduce implementation.

        Step 1: Gather all tensors to rank 0
        Step 2: Apply reduction
        Step 3: Broadcast result to all ranks
        """
        start_time = time.perf_counter()

        if not tensors:
            return []

        # Step 1: Gather (all tensors are already available in simulation)
        data_list = [t._data for t in tensors]

        # Step 2: Reduce
        stacked = np.stack(data_list, axis=0)
        if op == "sum":
            reduced = np.sum(stacked, axis=0)
        elif op == "mean":
            reduced = np.mean(stacked, axis=0)
        elif op == "max":
            reduced = np.max(stacked, axis=0)
        elif op == "min":
            reduced = np.min(stacked, axis=0)
        else:
            raise ValueError(f"Unsupported op: {op}")

        # Step 3: Broadcast (create result for each rank)
        elapsed = time.perf_counter() - start_time
        logger.debug(
            f"NaiveAllReduce completed: {len(tensors)} tensors, "
            f"shape={tensors[0].shape}, time={elapsed*1000:.3f}ms"
        )

        return [
            GPUTensor(reduced.copy(), t.device, t.dtype)
            for t in tensors
        ]


class RingAllReduce(AllReduce):
    """
    Ring AllReduce: bandwidth-optimal algorithm used by NCCL.

    This is the most important algorithm for distributed training.

    Communication pattern:
        Ring topology: 0 -> 1 -> 2 -> ... -> n-1 -> 0

    Two phases:
        Phase 1 - ScatterReduce (n-1 steps):
            Each GPU sends chunk[i] to next, receives chunk[i-1] from prev
            After n-1 steps, each GPU has one fully reduced chunk

        Phase 2 - AllGather (n-1 steps):
            Each GPU sends its reduced chunk to next
            After n-1 steps, all GPUs have all reduced chunks

    Complexity:
        - Time: 2 * (n-1) * message_size / n
        - Bandwidth: OPTIMAL (all links used at full bandwidth)

    Key Insight:
        Total data moved = 2 * (n-1)/n * total_data_size
        As n grows, this approaches 2 * total_data_size
        (factor of 2 because each byte is sent twice: once in scatter, once in gather)
    """

    def get_name(self) -> str:
        return "RingAllReduce"

    def reduce(
        self,
        tensors: List[GPUTensor],
        op: str = "sum",
    ) -> List[GPUTensor]:
        """
        Ring AllReduce implementation.

        Detailed steps for n GPUs with m chunks:
        Phase 1 (ScatterReduce):
            for step in range(n-1):
                send chunk[(rank+1)%n] to rank+1
                receive chunk[(rank-1)%n] from rank-1
                accumulate received chunk

        Phase 2 (AllGather):
            for step in range(n-1):
                send chunk[(rank+1)%n] to rank+1
                receive chunk[rank] from rank-1
                copy received chunk
        """
        start_time = time.perf_counter()
        n = len(tensors)

        if n == 0:
            return []
        if n == 1:
            return [tensors[0].detach()]

        # Convert to numpy arrays for manipulation
        data_list = [t._data.copy() for t in tensors]
        original_shape = data_list[0].shape

        # Flatten for chunking
        flat_data = [d.flatten() for d in data_list]
        total_size = flat_data[0].size

        # Split into n chunks
        chunks_per_gpu = []
        for rank in range(n):
            chunks = []
            for i in range(n):
                start_idx = i * (total_size // n)
                end_idx = (i + 1) * (total_size // n) if i < n - 1 else total_size
                chunks.append(flat_data[rank][start_idx:end_idx].copy())
            chunks_per_gpu.append(chunks)

        # Phase 1: ScatterReduce
        # After this phase, chunk[i] on GPU i contains the sum of all GPUs' chunk[i]
        for step in range(n - 1):
            for rank in range(n):
                send_chunk_idx = (rank + step) % n
                recv_chunk_idx = (rank + step - 1) % n
                send_to = (rank + 1) % n
                recv_from = (rank - 1 + n) % n

                # In real NCCL, this is async send/recv over NVLink/PCIe
                # In simulation, we directly access other GPUs' data
                if op == "sum":
                    chunks_per_gpu[rank][recv_chunk_idx] += chunks_per_gpu[recv_from][recv_chunk_idx]
                elif op == "mean":
                    chunks_per_gpu[rank][recv_chunk_idx] += chunks_per_gpu[recv_from][recv_chunk_idx]

        # Phase 2: AllGather
        # After this phase, all GPUs have all reduced chunks
        for step in range(n - 1):
            for rank in range(n):
                send_chunk_idx = (rank + step + 1) % n
                recv_chunk_idx = (rank + step) % n
                send_to = (rank + 1) % n
                recv_from = (rank - 1 + n) % n

                # Copy received chunk
                chunks_per_gpu[rank][recv_chunk_idx] = chunks_per_gpu[recv_from][recv_chunk_idx].copy()

        # Reassemble chunks for each GPU
        results = []
        for rank in range(n):
            full_data = np.concatenate(chunks_per_gpu[rank])
            if op == "mean":
                full_data = full_data / n
            result = full_data.reshape(original_shape)
            results.append(GPUTensor(result, tensors[rank].device, tensors[rank].dtype))

        elapsed = time.perf_counter() - start_time
        logger.debug(
            f"RingAllReduce completed: {n} GPUs, shape={original_shape}, "
            f"data_size={total_size*4} bytes, time={elapsed*1000:.3f}ms"
        )

        return results


class TreeAllReduce(AllReduce):
    """
    Tree AllReduce: latency-optimal algorithm.

    Communication pattern:
        Binary tree reduction, then broadcast

    Two phases:
        Phase 1 - Reduce (log2(n) steps):
            Pairs of GPUs reduce their tensors up the tree
        Phase 2 - Broadcast (log2(n) steps):
            Root broadcasts result down the tree

    Complexity:
        - Time: 2 * log2(n) * latency + message_size * log2(n) / bandwidth
        - Latency: OPTIMAL (log2(n) steps vs n-1 for ring)

    Trade-off vs Ring:
        - Tree: better for small messages (latency-dominated)
        - Ring: better for large messages (bandwidth-dominated)
    """

    def get_name(self) -> str:
        return "TreeAllReduce"

    def reduce(
        self,
        tensors: List[GPUTensor],
        op: str = "sum",
    ) -> List[GPUTensor]:
        """Tree AllReduce implementation."""
        start_time = time.perf_counter()
        n = len(tensors)

        if n == 0:
            return []
        if n == 1:
            return [tensors[0].detach()]

        # Phase 1: Reduce up the tree
        # We simulate a binary tree reduction
        current_data = [t._data.copy() for t in tensors]
        level = 0
        active_count = n

        while active_count > 1:
            new_data = []
            pairs = active_count // 2
            remainder = active_count % 2

            for i in range(pairs):
                left = current_data[2 * i]
                right = current_data[2 * i + 1]
                if op == "sum":
                    new_data.append(left + right)
                elif op == "mean":
                    new_data.append(left + right)
                else:
                    raise ValueError(f"Unsupported op: {op}")

            # Handle odd GPU out
            if remainder:
                new_data.append(current_data[-1])

            current_data = new_data
            active_count = len(new_data)
            level += 1

        # Phase 2: Broadcast down the tree (simplified: just replicate)
        reduced = current_data[0]
        if op == "mean":
            reduced = reduced / n

        elapsed = time.perf_counter() - start_time
        logger.debug(
            f"TreeAllReduce completed: {n} GPUs, shape={tensors[0].shape}, "
            f"levels={level}, time={elapsed*1000:.3f}ms"
        )

        return [
            GPUTensor(reduced.copy(), t.device, t.dtype)
            for t in tensors
        ]


def create_allreduce(algorithm: str = "ring") -> AllReduce:
    """
    Factory function to create an AllReduce instance.

    Args:
        algorithm: 'naive', 'ring', or 'tree'

    Returns:
        AllReduce instance
    """
    algorithms = {
        "naive": NaiveAllReduce,
        "ring": RingAllReduce,
        "tree": TreeAllReduce,
    }
    if algorithm not in algorithms:
        raise ValueError(f"Unknown algorithm: {algorithm}. Choose from {list(algorithms.keys())}")
    return algorithms[algorithm]()


def compare_allreduce_algorithms(
    tensors: List[GPUTensor],
    op: str = "sum",
) -> dict:
    """
    Compare all AllReduce algorithms on the same input.

    Args:
        tensors: Input tensors (one per GPU)
        op: Reduction operation

    Returns:
        dict with algorithm name -> (result, time_ms)
    """
    results = {}
    for algo_name in ["naive", "ring", "tree"]:
        allreduce = create_allreduce(algo_name)
        start = time.perf_counter()
        output = allreduce.reduce(tensors, op)
        elapsed = (time.perf_counter() - start) * 1000
        results[algo_name] = {
            "result": output[0],
            "time_ms": elapsed,
            "name": allreduce.get_name(),
        }
    return results
