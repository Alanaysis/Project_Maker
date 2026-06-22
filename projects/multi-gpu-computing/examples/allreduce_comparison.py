#!/usr/bin/env python3
"""
AllReduce Algorithm Comparison Example
========================================

This example compares different AllReduce algorithms:
- Naive (gather-reduce-broadcast)
- Ring (bandwidth-optimal, used by NCCL)
- Tree (latency-optimal)

Key Learning Points:
- Ring AllReduce is bandwidth-optimal for large messages
- Tree AllReduce is latency-optimal for small messages
- The choice depends on message size and cluster topology

Usage:
    python examples/allreduce_comparison.py
"""

import sys
import os
import numpy as np
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.tensor import GPUTensor, get_device
from src.core.allreduce import (
    NaiveAllReduce,
    RingAllReduce,
    TreeAllReduce,
    compare_allreduce_algorithms,
)
from src.utils.logger import setup_logger


def benchmark_algorithm(algo, tensors, op="sum", num_runs=100):
    """Benchmark a single algorithm."""
    # Warmup
    algo.reduce(tensors, op)

    times = []
    for _ in range(num_runs):
        start = time.perf_counter()
        algo.reduce(tensors, op)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)

    return {
        "mean_ms": np.mean(times),
        "std_ms": np.std(times),
        "min_ms": np.min(times),
        "max_ms": np.max(times),
    }


def main():
    logger = setup_logger("allreduce_comparison")

    logger.info("=" * 60)
    logger.info("ALLREDUCE ALGORITHM COMPARISON")
    logger.info("=" * 60)

    # Test configurations
    tensor_sizes = [1024, 4096, 16384, 65536, 262144]
    gpu_counts = [2, 4]

    algorithms = {
        "naive": NaiveAllReduce(),
        "ring": RingAllReduce(),
        "tree": TreeAllReduce(),
    }

    # 1. Correctness test
    logger.info("\n[1] Correctness Test")
    logger.info("-" * 40)

    np.random.seed(42)
    test_tensors = [
        GPUTensor(np.random.randn(100).astype(np.float32), get_device(i))
        for i in range(4)
    ]

    results = compare_allreduce_algorithms(test_tensors, op="sum")
    reference = results["naive"]["result"].data

    for name in ["ring", "tree"]:
        diff = np.max(np.abs(results[name]["result"].data - reference))
        status = "PASS" if diff < 1e-5 else "FAIL"
        logger.info(f"  {name:>6s} vs naive: max_diff={diff:.2e} [{status}]")

    # 2. Performance comparison
    logger.info("\n[2] Performance Comparison")
    logger.info("-" * 40)

    for num_gpus in gpu_counts:
        logger.info(f"\n  --- {num_gpus} GPUs ---")

        for size in tensor_sizes:
            logger.info(f"\n  Tensor size: {size} elements ({size * 4 / 1024:.1f} KB)")

            tensors = [
                GPUTensor(np.random.randn(size).astype(np.float32), get_device(i))
                for i in range(num_gpus)
            ]

            for algo_name, algo in algorithms.items():
                stats = benchmark_algorithm(algo, [t.detach() for t in tensors])
                logger.info(
                    f"    {algo_name:>6s}: "
                    f"{stats['mean_ms']:8.3f} ms "
                    f"(std={stats['std_ms']:.3f}, "
                    f"min={stats['min_ms']:.3f})"
                )

    # 3. Scaling analysis
    logger.info("\n[3] Scaling Analysis (Ring AllReduce)")
    logger.info("-" * 40)

    ring = RingAllReduce()
    size = 65536  # 256KB

    for num_gpus in [1, 2, 4, 8]:
        tensors = [
            GPUTensor(np.random.randn(size).astype(np.float32), get_device(i))
            for i in range(num_gpus)
        ]
        stats = benchmark_algorithm(ring, tensors)

        # Theoretical data moved: 2*(n-1)/n * data_size
        data_size = size * 4  # bytes
        data_moved = data_size * 2 * (num_gpus - 1) / num_gpus
        bandwidth = data_moved / (stats["mean_ms"] / 1000) / 1e9

        logger.info(
            f"  {num_gpus} GPUs: {stats['mean_ms']:.3f} ms, "
            f"data_moved={data_moved/1024:.1f} KB, "
            f"bandwidth={bandwidth:.2f} GB/s"
        )

    logger.info("\nDone!")


if __name__ == "__main__":
    main()
