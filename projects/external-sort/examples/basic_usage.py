#!/usr/bin/env python3
"""
外部排序基本用法示例

演示如何使用外部排序库对大文件进行排序。
"""

import os
import random
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.external_sort import ExternalSorter


def create_test_file(filepath, num_records=10000):
    """创建测试数据文件"""
    print(f"Creating test file with {num_records} records...")
    with open(filepath, 'w') as f:
        for _ in range(num_records):
            f.write(f"{random.randint(1, 1000000)}\n")
    file_size = os.path.getsize(filepath)
    print(f"Test file created: {filepath}")
    print(f"File size: {file_size / 1024:.2f} KB")
    return filepath


def demo_basic_sort():
    """基本排序演示"""
    print("\n=== 基本排序演示 ===")

    temp_dir = tempfile.mkdtemp()
    input_file = os.path.join(temp_dir, "input.txt")
    output_file = os.path.join(temp_dir, "output.txt")

    try:
        # 创建测试数据
        create_test_file(input_file, 10000)

        # 执行外部排序
        sorter = ExternalSorter(
            memory_limit=50 * 1024,  # 50KB 内存限制
            max_merge_ways=5,
            buffer_size=10 * 1024,   # 10KB 缓冲区
        )

        total = sorter.sort_file(input_file, output_file)

        # 显示统计信息
        stats = sorter.stats
        print(f"\n排序完成!")
        print(f"总记录数: {stats['total_records']}")
        print(f"归并段数: {stats['total_runs']}")
        print(f"归并趟数: {stats['merge_passes']}")
        print(f"生成归并段时间: {stats['run_generation_time']:.4f}s")
        print(f"归并时间: {stats['merge_time']:.4f}s")
        print(f"总时间: {stats['total_time']:.4f}s")

        # 验证结果
        with open(output_file, 'r') as f:
            values = [int(line.strip()) for line in f if line.strip()]

        is_sorted = all(values[i] <= values[i+1] for i in range(len(values)-1))
        print(f"排序正确: {is_sorted}")

    finally:
        # 清理
        for f in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, f))
        os.rmdir(temp_dir)


def demo_custom_key_sort():
    """自定义键排序演示"""
    print("\n=== 自定义键排序演示 ===")

    temp_dir = tempfile.mkdtemp()
    input_file = os.path.join(temp_dir, "input.txt")
    output_file = os.path.join(temp_dir, "output.txt")

    try:
        # 创建测试数据 (带负数)
        with open(input_file, 'w') as f:
            for _ in range(1000):
                f.write(f"{random.randint(-1000, 1000)}\n")

        # 按绝对值排序
        sorter = ExternalSorter(
            memory_limit=10 * 1024,
            key_func=lambda x: abs(x) if isinstance(x, (int, float)) else x,
        )

        total = sorter.sort_file(input_file, output_file)

        # 显示前 20 个结果
        with open(output_file, 'r') as f:
            values = [int(line.strip()) for line in f if line.strip()]

        print(f"按绝对值排序的前 20 个数: {values[:20]}")

    finally:
        for f in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, f))
        os.rmdir(temp_dir)


def demo_sort_data():
    """内存数据排序演示"""
    print("\n=== 内存数据排序演示 ===")

    data = [random.randint(1, 100) for _ in range(100)]
    print(f"原始数据 (前 20 个): {data[:20]}")

    sorter = ExternalSorter(memory_limit=500)
    result = sorter.sort_data(data)

    print(f"排序结果 (前 20 个): {result[:20]}")
    print(f"排序正确: {result == sorted(data)}")


def demo_replacement_selection():
    """置换选择排序演示"""
    print("\n=== 置换选择排序演示 ===")

    temp_dir = tempfile.mkdtemp()
    input_file = os.path.join(temp_dir, "input.txt")
    output_rs = os.path.join(temp_dir, "output_rs.txt")
    output_is = os.path.join(temp_dir, "output_is.txt")

    try:
        # 创建测试数据
        create_test_file(input_file, 5000)

        # 置换选择排序
        sorter_rs = ExternalSorter(
            memory_limit=20 * 1024,
            use_replacement_selection=True,
        )
        sorter_rs.sort_file(input_file, output_rs)

        # 内部排序法
        sorter_is = ExternalSorter(
            memory_limit=20 * 1024,
            use_replacement_selection=False,
        )
        sorter_is.sort_file(input_file, output_is)

        stats_rs = sorter_rs.stats
        stats_is = sorter_is.stats

        print(f"置换选择排序 - 归并段数: {stats_rs['total_runs']}")
        print(f"内部排序法 - 归并段数: {stats_is['total_runs']}")
        print(f"置换选择排序生成更少的归并段: {stats_rs['total_runs'] <= stats_is['total_runs']}")

    finally:
        for f in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, f))
        os.rmdir(temp_dir)


if __name__ == '__main__':
    demo_basic_sort()
    demo_custom_key_sort()
    demo_sort_data()
    demo_replacement_selection()
    print("\n所有演示完成!")
