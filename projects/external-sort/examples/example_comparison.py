"""
示例 2: 与内存排序对比

Compares external sorting with in-memory sorting.
Demonstrates when external sorting is necessary.

对比内存排序与外部排序：
- 小数据：内存排序更快
- 大数据：外部排序是唯一选择
"""

import os
import sys
import random
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.external_sort import ExternalSort
from src.in_memory_sort import sort_chunk


def generate_data(n: int) -> list:
    """生成随机数据。"""
    random.seed(42)
    return [random.randint(1, 1000000) for _ in range(n)]


def benchmark_in_memory(data: list, name: str = "test") -> float:
    """基准测试内存排序。"""
    start = time.perf_counter()
    sorted_data = sort_chunk(data, 'tim_sort')
    elapsed = time.perf_counter() - start

    is_sorted = all(sorted_data[i] <= sorted_data[i + 1]
                    for i in range(len(sorted_data) - 1))
    print(f"  {name}: {elapsed:.4f}s (correct: {is_sorted})")
    return elapsed


def benchmark_external(data: list, input_path: str, output_path: str,
                       chunk_size_mb: float = 0.5) -> float:
    """基准测试外部排序。"""
    # 写入文件
    with open(input_path, 'w') as f:
        for val in data:
            f.write(f"{val}\n")

    start = time.perf_counter()
    with ExternalSort(temp_dir="/tmp/ext-sort-compare",
                      chunk_size_mb=chunk_size_mb) as sorter:
        result = sorter.sort(input_path, output_path)
    elapsed = time.perf_counter() - start

    print(f"  external_sort ({chunk_size_mb}MB): {elapsed:.4f}s (valid: {result.is_valid})")
    return elapsed


def main():
    print("=" * 60)
    print("示例 2: 内存排序 vs 外部排序")
    print("Example 2: In-Memory Sort vs External Sort")
    print("=" * 60)
    print()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "..", "data")
    os.makedirs(data_dir, exist_ok=True)

    input_path = os.path.join(data_dir, "compare_input.txt")
    output_path = os.path.join(data_dir, "compare_output.txt")

    # 测试不同规模的数据
    sizes = [1000, 10000, 100000, 500000]

    print(f"{'数据规模':<15} {'内存排序(s)':<15} {'外部排序(s)':<15} {'差异':<10}")
    print("-" * 55)

    for size in sizes:
        data = generate_data(size)

        # 内存排序
        mem_time = benchmark_in_memory(data, f"mem_{size}")

        # 外部排序
        ext_time = benchmark_external(data, input_path, output_path,
                                      chunk_size_mb=0.1)

        ratio = ext_time / mem_time if mem_time > 0 else float('inf')
        print(f"  {'差异比':>50} {ratio:.2f}x")
        print()

    print("=" * 60)
    print("结论 / Conclusion:")
    print("  - 小数据 (< 10K): 内存排序更快 (无 I/O 开销)")
    print("  - 中等数据 (10K-100K): 两者相当")
    print("  - 大数据 (> 100K): 外部排序优势显现")
    print("  - 超大文件: 外部排序是唯一可行方案")
    print()
    print("  For small data (< 10K): in-memory sort is faster (no I/O)")
    print("  For medium data (10K-100K): both are comparable")
    print("  For large data (> 100K): external sort advantage appears")
    print("  For very large files: external sort is the only option")


if __name__ == "__main__":
    main()
