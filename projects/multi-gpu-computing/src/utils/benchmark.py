"""
Benchmarking Utilities
=======================

Performance benchmarking for the multi-GPU framework.
Measures:
- AllReduce throughput (GB/s)
- Training throughput (samples/sec)
- Communication overhead ratio
- Scaling efficiency (speedup vs number of GPUs)
"""

import time
import numpy as np
from typing import List, Dict, Any, Optional
from ..core.tensor import GPUTensor, get_device
from ..core.allreduce import create_allreduce, compare_allreduce_algorithms
from ..core.communicator import create_communicator
from ..core.data_parallel import DataParallelTrainer, SimpleModel

import logging
logger = logging.getLogger(__name__)


class Benchmark:
    """
    Benchmark suite for multi-GPU operations.

    Usage:
        bench = Benchmark()
        results = bench.run_all()
        bench.print_report(results)
    """

    def __init__(self, gpu_counts: Optional[List[int]] = None):
        """
        Args:
            gpu_counts: List of GPU counts to benchmark (default: [1,2,4])
        """
        self.gpu_counts = gpu_counts or [1, 2, 4]

    def benchmark_allreduce(
        self,
        tensor_sizes: Optional[List[int]] = None,
        num_gpus_list: Optional[List[int]] = None,
        algorithms: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Benchmark AllReduce algorithms.

        Args:
            tensor_sizes: List of tensor sizes to test
            num_gpus_list: List of GPU counts to test
            algorithms: List of algorithm names to test

        Returns:
            Nested dict: algorithm -> num_gpus -> tensor_size -> stats
        """
        if tensor_sizes is None:
            tensor_sizes = [1024, 4096, 16384, 65536, 262144]
        if num_gpus_list is None:
            num_gpus_list = self.gpu_counts
        if algorithms is None:
            algorithms = ["naive", "ring", "tree"]

        results = {}
        for algo_name in algorithms:
            results[algo_name] = {}
            allreduce = create_allreduce(algo_name)

            for num_gpus in num_gpus_list:
                results[algo_name][num_gpus] = {}
                for size in tensor_sizes:
                    # Create tensors for each GPU
                    tensors = [
                        GPUTensor(np.random.randn(size).astype(np.float32), get_device(i))
                        for i in range(num_gpus)
                    ]

                    # Warmup
                    allreduce.reduce(tensors, op="sum")

                    # Benchmark (average over multiple runs)
                    num_runs = 10
                    times = []
                    for _ in range(num_runs):
                        start = time.perf_counter()
                        allreduce.reduce(tensors, op="sum")
                        elapsed = (time.perf_counter() - start) * 1000
                        times.append(elapsed)

                    avg_time = np.mean(times)
                    data_size_bytes = size * 4  # float32
                    # Bandwidth = data moved / time
                    # In AllReduce, each byte is sent 2*(n-1)/n times
                    data_moved = data_size_bytes * 2 * (num_gpus - 1) / num_gpus
                    bandwidth_gbps = (data_moved / (avg_time / 1000)) / 1e9

                    results[algo_name][num_gpus][size] = {
                        "avg_time_ms": avg_time,
                        "std_time_ms": np.std(times),
                        "bandwidth_gbps": bandwidth_gbps,
                        "data_size_bytes": data_size_bytes,
                        "data_moved_bytes": data_moved,
                    }

        return results

    def benchmark_data_parallel(
        self,
        num_gpus_list: Optional[List[int]] = None,
        input_dim: int = 128,
        hidden_dim: int = 256,
        output_dim: int = 10,
        num_samples: int = 1000,
        num_steps: int = 10,
    ) -> Dict[str, Any]:
        """
        Benchmark data parallel training.

        Args:
            num_gpus_list: List of GPU counts to test
            input_dim: Input dimension
            hidden_dim: Hidden dimension
            output_dim: Output dimension
            num_samples: Number of training samples
            num_steps: Number of training steps

        Returns:
            Dict: num_gpus -> stats
        """
        if num_gpus_list is None:
            num_gpus_list = self.gpu_counts

        results = {}

        # Generate synthetic data
        X = np.random.randn(num_samples, input_dim).astype(np.float32)
        y = np.random.randn(num_samples, output_dim).astype(np.float32)

        for num_gpus in num_gpus_list:
            trainer = DataParallelTrainer(
                model_fn=lambda device: SimpleModel(input_dim, hidden_dim, output_dim, device),
                world_size=num_gpus,
                learning_rate=0.001,
            )

            # Warmup
            for _ in range(2):
                trainer.train_step(X[:32], y[:32])

            # Reset stats
            trainer.stats = {
                "total_time": 0.0,
                "comm_time": 0.0,
                "compute_time": 0.0,
                "steps": 0,
                "losses": [],
            }

            # Benchmark
            times = []
            for step in range(num_steps):
                batch_size = min(64, num_samples)
                indices = np.random.choice(num_samples, batch_size, replace=False)
                X_batch = X[indices]
                y_batch = y[indices]

                start = time.perf_counter()
                trainer.train_step(X_batch, y_batch)
                elapsed = time.perf_counter() - start
                times.append(elapsed)

            stats = trainer.get_stats()
            results[num_gpus] = {
                "avg_step_time_ms": np.mean(times) * 1000,
                "throughput_samples_per_sec": batch_size / np.mean(times),
                "comm_time_ms": stats["comm_time"] * 1000,
                "compute_time_ms": stats["compute_time"] * 1000,
                "comm_percentage": stats["comm_percentage"],
                "final_loss": stats["losses"][-1] if stats["losses"] else 0,
            }

            # Calculate speedup vs single GPU
            if 1 in results and num_gpus > 1:
                speedup = results[1]["avg_step_time_ms"] / results[num_gpus]["avg_step_time_ms"]
                efficiency = speedup / num_gpus * 100
                results[num_gpus]["speedup"] = speedup
                results[num_gpus]["efficiency_pct"] = efficiency

        return results

    def run_all(self) -> Dict[str, Any]:
        """Run all benchmarks."""
        logger.info("Running AllReduce benchmarks...")
        allreduce_results = self.benchmark_allreduce()

        logger.info("Running Data Parallel benchmarks...")
        dp_results = self.benchmark_data_parallel()

        return {
            "allreduce": allreduce_results,
            "data_parallel": dp_results,
        }

    def print_report(self, results: Dict[str, Any]):
        """Print a formatted benchmark report."""
        print("\n" + "=" * 70)
        print("MULTI-GPU BENCHMARK REPORT")
        print("=" * 70)

        # AllReduce results
        print("\n--- AllReduce Performance ---")
        for algo_name, algo_results in results["allreduce"].items():
            print(f"\n  Algorithm: {algo_name}")
            for num_gpus, gpu_results in algo_results.items():
                print(f"    {num_gpus} GPUs:")
                for size, stats in gpu_results.items():
                    print(
                        f"      Size {size:>8d}: "
                        f"{stats['avg_time_ms']:8.3f} ms, "
                        f"{stats['bandwidth_gbps']:6.2f} GB/s"
                    )

        # Data Parallel results
        print("\n--- Data Parallel Training ---")
        for num_gpus, stats in results["data_parallel"].items():
            print(f"\n  {num_gpus} GPUs:")
            print(f"    Step time:    {stats['avg_step_time_ms']:8.3f} ms")
            print(f"    Throughput:   {stats['throughput_samples_per_sec']:8.1f} samples/sec")
            print(f"    Comm time:    {stats['comm_time_ms']:8.3f} ms ({stats['comm_percentage']:.1f}%)")
            if "speedup" in stats:
                print(f"    Speedup:      {stats['speedup']:8.2f}x")
                print(f"    Efficiency:   {stats['efficiency_pct']:8.1f}%")

        print("\n" + "=" * 70)


def benchmark_allreduce() -> Dict[str, Any]:
    """Convenience function to benchmark AllReduce."""
    bench = Benchmark()
    return bench.benchmark_allreduce()


def benchmark_data_parallel() -> Dict[str, Any]:
    """Convenience function to benchmark data parallel training."""
    bench = Benchmark()
    return bench.benchmark_data_parallel()
