"""
外部排序主模块测试
"""

import os
import tempfile
import unittest
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.external_sort import (
    ExternalSorter,
    LargeFileSorter,
    LogSorter,
    DatabaseSorter,
)


class TestExternalSorter(unittest.TestCase):
    """外部排序器测试"""

    def setUp(self):
        """创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理临时文件"""
        for f in os.listdir(self.temp_dir):
            filepath = os.path.join(self.temp_dir, f)
            if os.path.isfile(filepath):
                os.remove(filepath)
        try:
            os.rmdir(self.temp_dir)
        except OSError:
            pass

    def test_sort_file_basic(self):
        """测试基本文件排序"""
        input_file = os.path.join(self.temp_dir, "input.txt")
        output_file = os.path.join(self.temp_dir, "output.txt")

        # 写入测试数据
        data = [5, 3, 8, 1, 9, 2, 7, 4, 6]
        with open(input_file, 'w') as f:
            for v in data:
                f.write(f"{v}\n")

        sorter = ExternalSorter(memory_limit=100)
        total = sorter.sort_file(input_file, output_file)

        self.assertEqual(total, 9)

        with open(output_file, 'r') as f:
            result = [int(line.strip()) for line in f if line.strip()]

        self.assertEqual(result, sorted(data))

    def test_sort_file_sorted(self):
        """测试已排序文件"""
        input_file = os.path.join(self.temp_dir, "input.txt")
        output_file = os.path.join(self.temp_dir, "output.txt")

        data = list(range(100))
        with open(input_file, 'w') as f:
            for v in data:
                f.write(f"{v}\n")

        sorter = ExternalSorter(memory_limit=500)
        total = sorter.sort_file(input_file, output_file)

        self.assertEqual(total, 100)

        with open(output_file, 'r') as f:
            result = [int(line.strip()) for line in f if line.strip()]

        self.assertEqual(result, data)

    def test_sort_file_reverse(self):
        """测试逆序文件"""
        input_file = os.path.join(self.temp_dir, "input.txt")
        output_file = os.path.join(self.temp_dir, "output.txt")

        data = list(range(100, 0, -1))
        with open(input_file, 'w') as f:
            for v in data:
                f.write(f"{v}\n")

        sorter = ExternalSorter(memory_limit=500)
        total = sorter.sort_file(input_file, output_file)

        self.assertEqual(total, 100)

        with open(output_file, 'r') as f:
            result = [int(line.strip()) for line in f if line.strip()]

        self.assertEqual(result, list(range(1, 101)))

    def test_sort_file_empty(self):
        """测试空文件"""
        input_file = os.path.join(self.temp_dir, "input.txt")
        output_file = os.path.join(self.temp_dir, "output.txt")

        with open(input_file, 'w') as f:
            pass

        sorter = ExternalSorter(memory_limit=100)
        total = sorter.sort_file(input_file, output_file)

        self.assertEqual(total, 0)

    def test_sort_file_with_duplicates(self):
        """测试有重复元素的文件"""
        input_file = os.path.join(self.temp_dir, "input.txt")
        output_file = os.path.join(self.temp_dir, "output.txt")

        data = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
        with open(input_file, 'w') as f:
            for v in data:
                f.write(f"{v}\n")

        sorter = ExternalSorter(memory_limit=100)
        total = sorter.sort_file(input_file, output_file)

        self.assertEqual(total, 11)

        with open(output_file, 'r') as f:
            result = [int(line.strip()) for line in f if line.strip()]

        self.assertEqual(result, sorted(data))

    def test_sort_iterator(self):
        """测试从迭代器排序"""
        output_file = os.path.join(self.temp_dir, "output.txt")

        data = [5, 3, 8, 1, 9, 2, 7, 4, 6]
        sorter = ExternalSorter(memory_limit=100)
        total = sorter.sort_iterator(iter(data), output_file)

        self.assertEqual(total, 9)

        with open(output_file, 'r') as f:
            result = [int(line.strip()) for line in f if line.strip()]

        self.assertEqual(result, sorted(data))

    def test_sort_data(self):
        """测试内存数据排序"""
        data = [5, 3, 8, 1, 9, 2, 7, 4, 6]

        sorter = ExternalSorter(memory_limit=100)
        result = sorter.sort_data(data)

        self.assertEqual(result, sorted(data))

    def test_custom_key_function(self):
        """测试自定义键函数"""
        input_file = os.path.join(self.temp_dir, "input.txt")
        output_file = os.path.join(self.temp_dir, "output.txt")

        # 按绝对值排序
        data = [-5, 3, -8, 1, 9, -2, 7, -4, 6]
        with open(input_file, 'w') as f:
            for v in data:
                f.write(f"{v}\n")

        sorter = ExternalSorter(
            memory_limit=100,
            key_func=lambda x: abs(x) if isinstance(x, (int, float)) else x
        )
        total = sorter.sort_file(input_file, output_file)

        with open(output_file, 'r') as f:
            result = [int(line.strip()) for line in f if line.strip()]

        self.assertEqual(result, sorted(data, key=abs))

    def test_statistics(self):
        """测试统计信息"""
        input_file = os.path.join(self.temp_dir, "input.txt")
        output_file = os.path.join(self.temp_dir, "output.txt")

        data = list(range(100))
        with open(input_file, 'w') as f:
            for v in data:
                f.write(f"{v}\n")

        sorter = ExternalSorter(memory_limit=500)
        sorter.sort_file(input_file, output_file)

        stats = sorter.stats

        self.assertEqual(stats['total_records'], 100)
        self.assertGreater(stats['total_runs'], 0)
        self.assertGreater(stats['total_time'], 0)
        self.assertGreater(stats['run_generation_time'], 0)
        self.assertGreater(stats['merge_time'], 0)

    def test_large_dataset(self):
        """测试大数据集"""
        input_file = os.path.join(self.temp_dir, "input.txt")
        output_file = os.path.join(self.temp_dir, "output.txt")

        data = [random.randint(1, 100000) for _ in range(10000)]
        with open(input_file, 'w') as f:
            for v in data:
                f.write(f"{v}\n")

        sorter = ExternalSorter(memory_limit=10000)
        total = sorter.sort_file(input_file, output_file)

        self.assertEqual(total, 10000)

        with open(output_file, 'r') as f:
            result = [int(line.strip()) for line in f if line.strip()]

        self.assertEqual(result, sorted(data))

    def test_string_data(self):
        """测试字符串数据"""
        input_file = os.path.join(self.temp_dir, "input.txt")
        output_file = os.path.join(self.temp_dir, "output.txt")

        data = ["banana", "apple", "cherry", "date", "elderberry"]
        with open(input_file, 'w') as f:
            for v in data:
                f.write(f"{v}\n")

        sorter = ExternalSorter(memory_limit=100)
        total = sorter.sort_file(input_file, output_file)

        self.assertEqual(total, 5)

        with open(output_file, 'r') as f:
            result = [line.strip() for line in f if line.strip()]

        self.assertEqual(result, sorted(data))

    def test_replacement_selection_vs_internal_sort(self):
        """测试置换选择排序与内部排序法的对比"""
        input_file = os.path.join(self.temp_dir, "input.txt")
        output_rs = os.path.join(self.temp_dir, "output_rs.txt")
        output_is = os.path.join(self.temp_dir, "output_is.txt")

        data = [random.randint(1, 1000) for _ in range(1000)]
        with open(input_file, 'w') as f:
            for v in data:
                f.write(f"{v}\n")

        # 置换选择排序
        sorter_rs = ExternalSorter(
            memory_limit=500,
            use_replacement_selection=True
        )
        sorter_rs.sort_file(input_file, output_rs)

        # 内部排序法
        sorter_is = ExternalSorter(
            memory_limit=500,
            use_replacement_selection=False
        )
        sorter_is.sort_file(input_file, output_is)

        # 两个结果应该相同
        with open(output_rs, 'r') as f:
            result_rs = [int(line.strip()) for line in f if line.strip()]
        with open(output_is, 'r') as f:
            result_is = [int(line.strip()) for line in f if line.strip()]

        self.assertEqual(result_rs, result_is)


class TestLargeFileSorter(unittest.TestCase):
    """大文件排序器测试"""

    def setUp(self):
        """创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理临时文件"""
        for f in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, f))
        os.rmdir(self.temp_dir)

    def test_sort(self):
        """测试大文件排序"""
        input_file = os.path.join(self.temp_dir, "input.txt")
        output_file = os.path.join(self.temp_dir, "output.txt")

        data = [random.randint(1, 10000) for _ in range(5000)]
        with open(input_file, 'w') as f:
            for v in data:
                f.write(f"{v}\n")

        sorter = LargeFileSorter(memory_limit=10000)
        total = sorter.sort(input_file, output_file)

        self.assertEqual(total, 5000)

        with open(output_file, 'r') as f:
            result = [int(line.strip()) for line in f if line.strip()]

        self.assertEqual(result, sorted(data))


class TestLogSorter(unittest.TestCase):
    """日志排序器测试"""

    def setUp(self):
        """创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理临时文件"""
        for f in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, f))
        os.rmdir(self.temp_dir)

    def test_sort_by_timestamp(self):
        """测试按时间戳排序"""
        input_file = os.path.join(self.temp_dir, "logs.txt")
        output_file = os.path.join(self.temp_dir, "sorted.txt")

        logs = [
            "2024-01-03 10:00:00 Error occurred",
            "2024-01-01 08:00:00 System started",
            "2024-01-02 12:00:00 Warning issued",
            "2024-01-01 09:00:00 User logged in",
        ]

        with open(input_file, 'w') as f:
            for log in logs:
                f.write(f"{log}\n")

        sorter = LogSorter()
        total = sorter.sort_by_timestamp(input_file, output_file)

        self.assertEqual(total, 4)

        with open(output_file, 'r') as f:
            result = [line.strip() for line in f if line.strip()]

        # 验证按时间排序
        self.assertIn("2024-01-01 08:00:00", result[0])
        self.assertIn("2024-01-01 09:00:00", result[1])
        self.assertIn("2024-01-02 12:00:00", result[2])
        self.assertIn("2024-01-03 10:00:00", result[3])

    def test_sort_by_field(self):
        """测试按字段排序"""
        input_file = os.path.join(self.temp_dir, "data.csv")
        output_file = os.path.join(self.temp_dir, "sorted.csv")

        data = [
            "alice,85,A",
            "bob,92,B",
            "charlie,78,C",
            "david,95,A",
        ]

        with open(input_file, 'w') as f:
            for line in data:
                f.write(f"{line}\n")

        sorter = LogSorter()
        total = sorter.sort_by_field(
            input_file, output_file,
            field_index=1, separator=","
        )

        self.assertEqual(total, 4)

        with open(output_file, 'r') as f:
            result = [line.strip() for line in f if line.strip()]

        # 按分数排序
        self.assertIn("78", result[0])
        self.assertIn("85", result[1])
        self.assertIn("92", result[2])
        self.assertIn("95", result[3])


class TestDatabaseSorter(unittest.TestCase):
    """数据库排序器测试"""

    def setUp(self):
        """创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理临时文件"""
        for f in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, f))
        os.rmdir(self.temp_dir)

    def test_sort_by_single_column(self):
        """测试单列排序"""
        input_file = os.path.join(self.temp_dir, "data.csv")
        output_file = os.path.join(self.temp_dir, "sorted.csv")

        data = [
            "name,age,city",
            "alice,30,beijing",
            "bob,25,shanghai",
            "charlie,35,guangzhou",
            "david,28,shenzhen",
        ]

        with open(input_file, 'w') as f:
            for line in data:
                f.write(f"{line}\n")

        sorter = DatabaseSorter()
        total = sorter.sort_by_columns(
            input_file, output_file,
            sort_columns=[1], separator=",",
            header=True
        )

        self.assertEqual(total, 4)

        with open(output_file, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]

        # 第一行应该是表头
        self.assertEqual(lines[0], "name,age,city")

        # 验证按年龄排序
        ages = [int(line.split(',')[1]) for line in lines[1:]]
        self.assertEqual(ages, sorted(ages))

    def test_sort_by_multiple_columns(self):
        """测试多列排序"""
        input_file = os.path.join(self.temp_dir, "data.csv")
        output_file = os.path.join(self.temp_dir, "sorted.csv")

        data = [
            "name,age,score",
            "alice,25,85",
            "bob,25,92",
            "charlie,30,78",
            "david,30,95",
        ]

        with open(input_file, 'w') as f:
            for line in data:
                f.write(f"{line}\n")

        sorter = DatabaseSorter()
        total = sorter.sort_by_columns(
            input_file, output_file,
            sort_columns=[1, 2], separator=",",
            header=True
        )

        self.assertEqual(total, 4)

        with open(output_file, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]

        # 验证多列排序
        self.assertEqual(lines[0], "name,age,score")
        self.assertIn("alice", lines[1])  # age=25, score=85
        self.assertIn("bob", lines[2])    # age=25, score=92
        self.assertIn("charlie", lines[3])  # age=30, score=78
        self.assertIn("david", lines[4])   # age=30, score=95

    def test_sort_without_header(self):
        """测试无表头排序"""
        input_file = os.path.join(self.temp_dir, "data.csv")
        output_file = os.path.join(self.temp_dir, "sorted.csv")

        data = [
            "alice,30",
            "bob,25",
            "charlie,35",
        ]

        with open(input_file, 'w') as f:
            for line in data:
                f.write(f"{line}\n")

        sorter = DatabaseSorter()
        total = sorter.sort_by_columns(
            input_file, output_file,
            sort_columns=[1], separator=",",
            header=False
        )

        self.assertEqual(total, 3)

        with open(output_file, 'r') as f:
            result = [line.strip() for line in f if line.strip()]

        ages = [int(line.split(',')[1]) for line in result]
        self.assertEqual(ages, sorted(ages))


if __name__ == '__main__':
    unittest.main()
