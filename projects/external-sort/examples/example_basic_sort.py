"""
示例 1: 基本外部排序演示

Demonstrates basic external sorting with a file that exceeds memory.
"""

import os
import sys
import random
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.external_sort import ExternalSort


def generate_test_file(filepath: str, num_records: int, max_value: int = 1000000):
    """生成测试文件。

    Generate a test file with random integers.
    """
    random.seed(42)
    print(f"Generating test file: {num_records} records -> {filepath}")
    with open(filepath, 'w') as f:
        for _ in range(num_records):
            f.write(f"{random.randint(1, max_value)}\n")
    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    print(f"  File size: {size_mb:.2f} MB")
    return size_mb


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(base_dir)
    data_dir = os.path.join(project_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    input_file = os.path.join(data_dir, "unsorted_large.txt")
    output_file = os.path.join(data_dir, "sorted_external.txt")

    # 配置
    num_records = 100000
    chunk_size_mb = 1.0

    print("=" * 60)
    print("示例 1: 外部排序基本演示")
    print("Example 1: Basic External Sort Demo")
    print("=" * 60)
    print(f"记录数 / Records: {num_records:,}")
    print(f"块大小 / Chunk size: {chunk_size_mb} MB")
    print()

    # 生成测试数据
    file_size = generate_test_file(input_file, num_records)

    # 执行外部排序
    print("-" * 60)
    print("执行外部排序 / Running external sort...")
    print("-" * 60)

    temp_dir = os.path.join(data_dir, "temp")
    start = time.perf_counter()

    with ExternalSort(temp_dir=temp_dir, chunk_size_mb=chunk_size_mb) as sorter:
        result = sorter.sort(input_file, output_file)

    elapsed = time.perf_counter() - start

    # 输出结果
    print()
    print(result.summary())
    print()
    print(f"总耗时 / Total time: {elapsed:.4f}s")

    # 显示前 10 行结果
    print()
    print("排序结果前 10 行 / First 10 lines of sorted output:")
    with open(output_file, 'r') as f:
        for i, line in enumerate(f):
            if i >= 10:
                break
            print(f"  {line.strip()}")

    print()
    print("验证结果 / Validation:", "通过 ✓" if result.is_valid else "失败 ✗")


if __name__ == "__main__":
    main()
