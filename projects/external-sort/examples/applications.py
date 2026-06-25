#!/usr/bin/env python3
"""
外部排序实际应用示例

演示外部排序在实际场景中的应用:
1. 大文件排序
2. 日志排序
3. 数据库排序
"""

import os
import random
import sys
import tempfile
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.external_sort import LargeFileSorter, LogSorter, DatabaseSorter


def demo_large_file_sort():
    """大文件排序演示"""
    print("\n=== 大文件排序演示 ===")

    temp_dir = tempfile.mkdtemp()
    input_file = os.path.join(temp_dir, "large_data.txt")
    output_file = os.path.join(temp_dir, "sorted_data.txt")

    try:
        # 创建大文件 (100万条记录)
        num_records = 1000000
        print(f"Creating large file with {num_records} records...")

        with open(input_file, 'w') as f:
            for _ in range(num_records):
                f.write(f"{random.randint(1, 10000000)}\n")

        file_size = os.path.getsize(input_file)
        print(f"File size: {file_size / (1024*1024):.2f} MB")

        # 使用大文件排序器
        sorter = LargeFileSorter(
            memory_limit=50 * 1024 * 1024,  # 50MB 内存
            max_merge_ways=8,
        )

        total = sorter.sort(input_file, output_file)

        print(f"Sorted {total} records")
        print(f"Output file size: {os.path.getsize(output_file) / (1024*1024):.2f} MB")

    finally:
        for f in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, f))
        os.rmdir(temp_dir)


def demo_log_sort():
    """日志排序演示"""
    print("\n=== 日志排序演示 ===")

    temp_dir = tempfile.mkdtemp()
    log_file = os.path.join(temp_dir, "app.log")
    sorted_file = os.path.join(temp_dir, "sorted.log")

    try:
        # 创建模拟日志文件
        print("Creating sample log file...")

        base_time = datetime(2024, 1, 1, 0, 0, 0)
        log_entries = []

        for i in range(10000):
            # 随机时间偏移
            offset = timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59),
            )
            timestamp = base_time + offset

            level = random.choice(["INFO", "WARN", "ERROR", "DEBUG"])
            message = f"Log entry {i}: {level} event occurred"

            log_entries.append(f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} {message}")

        # 打乱顺序写入文件
        random.shuffle(log_entries)
        with open(log_file, 'w') as f:
            for entry in log_entries:
                f.write(f"{entry}\n")

        print(f"Log file created with {len(log_entries)} entries")

        # 按时间戳排序
        sorter = LogSorter(memory_limit=10 * 1024 * 1024)
        total = sorter.sort_by_timestamp(
            log_file, sorted_file,
            timestamp_field=0,
            separator=" "
        )

        print(f"Sorted {total} log entries")

        # 显示前 10 条排序后的日志
        print("\nFirst 10 sorted log entries:")
        with open(sorted_file, 'r') as f:
            for i, line in enumerate(f):
                if i >= 10:
                    break
                print(f"  {line.strip()}")

    finally:
        for f in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, f))
        os.rmdir(temp_dir)


def demo_log_sort_by_level():
    """按日志级别排序演示"""
    print("\n=== 按日志级别排序演示 ===")

    temp_dir = tempfile.mkdtemp()
    log_file = os.path.join(temp_dir, "levels.log")
    sorted_file = os.path.join(temp_dir, "sorted_levels.log")

    try:
        # 创建日志文件
        levels = ["DEBUG", "INFO", "WARN", "ERROR"]
        with open(log_file, 'w') as f:
            for i in range(1000):
                level = random.choice(levels)
                f.write(f"{level} Message {i}\n")

        # 按级别排序
        sorter = LogSorter()
        total = sorter.sort_by_field(
            log_file, sorted_file,
            field_index=0,
            separator=" "
        )

        print(f"Sorted {total} entries by log level")

        # 统计各级别数量
        level_counts = {}
        with open(sorted_file, 'r') as f:
            for line in f:
                level = line.strip().split(" ")[0]
                level_counts[level] = level_counts.get(level, 0) + 1

        print("Level distribution:")
        for level in sorted(level_counts.keys()):
            print(f"  {level}: {level_counts[level]}")

    finally:
        for f in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, f))
        os.rmdir(temp_dir)


def demo_database_sort():
    """数据库排序演示"""
    print("\n=== 数据库排序演示 ===")

    temp_dir = tempfile.mkdtemp()
    csv_file = os.path.join(temp_dir, "employees.csv")
    sorted_file = os.path.join(temp_dir, "sorted_employees.csv")

    try:
        # 创建 CSV 数据
        print("Creating employee CSV file...")

        names = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Henry"]
        departments = ["Engineering", "Sales", "Marketing", "HR"]

        with open(csv_file, 'w') as f:
            f.write("name,age,department,salary\n")
            for i in range(1000):
                name = random.choice(names) + str(i)
                age = random.randint(22, 65)
                dept = random.choice(departments)
                salary = random.randint(30000, 150000)
                f.write(f"{name},{age},{dept},{salary}\n")

        print(f"CSV file created with 1000 records")

        # 按薪资排序
        sorter = DatabaseSorter(memory_limit=10 * 1024 * 1024)
        total = sorter.sort_by_columns(
            csv_file, sorted_file,
            sort_columns=[3],  # 按薪资列排序
            separator=",",
            header=True,
        )

        print(f"Sorted {total} records by salary")

        # 显示前 10 条记录
        print("\nTop 10 highest salaries:")
        with open(sorted_file, 'r') as f:
            lines = f.readlines()
            for line in lines[-11:]:  # 最后 10 条 + 表头
                print(f"  {line.strip()}")

    finally:
        for f in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, f))
        os.rmdir(temp_dir)


def demo_multi_column_sort():
    """多列排序演示"""
    print("\n=== 多列排序演示 ===")

    temp_dir = tempfile.mkdtemp()
    csv_file = os.path.join(temp_dir, "scores.csv")
    sorted_file = os.path.join(temp_dir, "sorted_scores.csv")

    try:
        # 创建学生成绩数据
        print("Creating student scores CSV...")

        with open(csv_file, 'w') as f:
            f.write("name,math,english,science\n")
            for i in range(500):
                name = f"Student{i}"
                math = random.randint(60, 100)
                english = random.randint(60, 100)
                science = random.randint(60, 100)
                f.write(f"{name},{math},{english},{science}\n")

        # 按数学、英语、科学多列排序
        sorter = DatabaseSorter()
        total = sorter.sort_by_columns(
            csv_file, sorted_file,
            sort_columns=[1, 2, 3],  # 数学、英语、科学
            separator=",",
            header=True,
        )

        print(f"Sorted {total} records by math, english, science")

        # 显示前 10 条记录
        print("\nFirst 10 sorted records:")
        with open(sorted_file, 'r') as f:
            for i, line in enumerate(f):
                if i >= 11:  # 表头 + 10 条数据
                    break
                print(f"  {line.strip()}")

    finally:
        for f in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, f))
        os.rmdir(temp_dir)


def demo_performance_comparison():
    """性能对比演示"""
    print("\n=== 性能对比演示 ===")

    temp_dir = tempfile.mkdtemp()
    input_file = os.path.join(temp_dir, "perf_test.txt")

    try:
        # 创建测试数据
        num_records = 100000
        print(f"Creating test data with {num_records} records...")

        with open(input_file, 'w') as f:
            for _ in range(num_records):
                f.write(f"{random.randint(1, 1000000)}\n")

        # 测试不同的内存限制
        memory_limits = [10*1024, 50*1024, 100*1024, 500*1024]

        print("\nPerformance comparison (different memory limits):")
        print("-" * 60)
        print(f"{'Memory Limit':<15} {'Runs':<10} {'Time (s)':<15}")
        print("-" * 60)

        for mem_limit in memory_limits:
            output_file = os.path.join(temp_dir, f"output_{mem_limit}.txt")

            sorter = ExternalSorter(
                memory_limit=mem_limit,
                use_replacement_selection=True,
            )

            sorter.sort_file(input_file, output_file)
            stats = sorter.stats

            print(f"{mem_limit/1024:.0f} KB{'':<10} {stats['total_runs']:<10} {stats['total_time']:.4f}")

            os.remove(output_file)

    finally:
        for f in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, f))
        os.rmdir(temp_dir)


if __name__ == '__main__':
    from src.external_sort import ExternalSorter

    demo_large_file_sort()
    demo_log_sort()
    demo_log_sort_by_level()
    demo_database_sort()
    demo_multi_column_sort()
    demo_performance_comparison()
    print("\n所有应用演示完成!")
