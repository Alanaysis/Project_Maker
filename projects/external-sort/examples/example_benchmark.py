"""
示例 3: 性能基准测试

Performance benchmarking for external sorting with various configurations.

测试不同参数对性能的影响：
- 块大小
- 归并路数
- 数据规模
"""

import os
import sys
import random
import time
import statistics

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.external_sort import ExternalSort
from src.memory_management import compute_memory_profile, estimate_io_cost


def generate_file(filepath: str, num_records: int):
    """生成测试文件。"""
    random.seed(42)
    with open(filepath, 'w') as f:
        for _ in range(num_records):
            f.write(f"{random.randint(1, 10000000)}\n")


def benchmark_chunk_sizes(input_path: str, output_base: str,
                          chunk_sizes_mb: list) -> list:
    """测试不同块大小的性能。"""
    print(f"\n{'块大小 (MB)':<15} {'耗时 (s)':<15} {'Runs 数':<15}")
    print("-" * 45)

    results = []
    for size_mb in chunk_sizes_mb:
        output = f"{output_base}_chunk{size_mb}.txt"
        temp_dir = f"/tmp/ext-sort-chunk-{size_mb}"

        start = time.perf_counter()
        with ExternalSort(temp_dir=temp_dir, chunk_size_mb=size_mb) as sorter:
            result = sorter.sort(input_path, output)
        elapsed = time.perf_counter() - start

        results.append({
            'chunk_size_mb': size_mb,
            'elapsed': elapsed,
            'num_runs': result.num_runs,
        })

        print(f"{size_mb:<15.2f} {elapsed:<15.4f} {result.num_runs:<15}")

    return results


def benchmark_data_sizes(chunk_size_mb: float,
                         sizes: list) -> list:
    """测试不同数据规模的性能。"""
    print(f"\n{'记录数':<15} {'耗时 (s)':<15} {'Runs 数':<15}")
    print("-" * 45)

    results = []
    for size in sizes:
        input_file = f"/tmp/ext-sort-size-{size}.txt"
        output_file = f"/tmp/ext-sort-size-{size}-out.txt"

        generate_file(input_file, size)

        start = time.perf_counter()
        with ExternalSort(temp_dir="/tmp/ext-sort-size-temp",
                          chunk_size_mb=chunk_size_mb) as sorter:
            result = sorter.sort(input_file, output_file)
        elapsed = time.perf_counter() - start

        results.append({
            'num_records': size,
            'elapsed': elapsed,
            'num_runs': result.num_runs,
        })

        print(f"{size:<15,} {elapsed:<15.4f} {result.num_runs:<15}")

        # 清理
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)

    return results


def main():
    print("=" * 60)
    print("示例 3: 性能基准测试")
    print("Example 3: Performance Benchmarking")
    print("=" * 60)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "..", "data")
    os.makedirs(data_dir, exist_ok=True)

    input_file = os.path.join(data_dir, "benchmark_input.txt")
    output_base = os.path.join(data_dir, "benchmark_output")

    # 生成测试数据
    num_records = 200000
    print(f"\n生成 {num_records:,} 条记录...")
    generate_file(input_file, num_records)
    print(f"文件大小: {os.path.getsize(input_file) / (1024*1024):.2f} MB")

    # 测试 1: 不同块大小
    print("\n" + "=" * 60)
    print("测试 1: 块大小对性能的影响")
    print("Test 1: Impact of chunk size on performance")
    print("=" * 60)

    chunk_sizes = [0.1, 0.5, 1.0, 2.0, 5.0]
    chunk_results = benchmark_chunk_sizes(input_file, output_base, chunk_sizes)

    # 找出最佳块大小
    best = min(chunk_results, key=lambda r: r['elapsed'])
    print(f"\n最佳块大小: {best['chunk_size_mb']} MB ({best['elapsed']:.4f}s)")

    # 测试 2: 不同数据规模
    print("\n" + "=" * 60)
    print("测试 2: 数据规模对性能的影响")
    print("Test 2: Impact of data size on performance")
    print("=" * 60)

    sizes = [10000, 50000, 100000, 200000]
    size_results = benchmark_data_sizes(1.0, sizes)

    # I/O 成本分析
    print("\n" + "=" * 60)
    print("I/O 成本分析")
    print("I/O Cost Analysis")
    print("=" * 60)

    profile = compute_memory_profile(
        target_chunk_records=100000,
        record_size_bytes=10,
    )
    io_cost = estimate_io_cost(
        num_records=num_records,
        chunk_size=int(profile.chunk_size_mb * 1024 * 1024),
        num_runs=best['num_runs'],
        merge_degree=10,
    )

    print(f"  通过成本 (Pass-through): {io_cost['pass_through_io']:,} I/O ops")
    print(f"  归并成本 (Merge):        {io_cost['merge_io']:,} I/O ops")
    print(f"  总成本 (Total):          {io_cost['total_io']:,} I/O ops")
    print(f"  归并轮数 (Merge rounds): {io_cost['merge_rounds']}")


if __name__ == "__main__":
    main()
